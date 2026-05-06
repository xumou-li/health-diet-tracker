"""用户食谱API"""
import json
from flask import Blueprint, request, g
from app.extensions import db
from app.models import UserRecipe, Food
from app.utils.response import success, error
from app.utils.auth import login_required

recipe_bp = Blueprint('recipe', __name__)


def _calc_custom_calorie(protein, fat, carb):
    """根据蛋白/脂肪/碳水(g)自动计算热量(kcal)"""
    return round(float(protein or 0) * 4 + float(fat or 0) * 9 + float(carb or 0) * 4)


def _validate_and_build_items(items):
    """
    校验并构建食谱条目列表。
    支持两种类型：
      - food:  从食物库选择，需 food_id + weight_g
      - custom: 手动输入，需 name + protein + fat + carb，calorie 可选（不填自动计算）
    返回 (valid_items, error_message)；如果 error_message 不为 None 则校验失败。
    """
    valid_items = []
    for item in items:
        item_type = item.get('type', 'food')  # 默认兼容旧数据

        if item_type == 'food':
            food_id = item.get('food_id')
            weight_g = item.get('weight_g', 100)
            food = Food.query.get(food_id)
            if food and food.is_approved:
                valid_items.append({
                    'type': 'food',
                    'food_id': food_id,
                    'weight_g': weight_g
                })
        elif item_type == 'custom':
            name = (item.get('name') or '').strip()
            if not name:
                continue
            protein = float(item.get('protein', 0) or 0)
            fat = float(item.get('fat', 0) or 0)
            carb = float(item.get('carb', 0) or 0)
            calorie = item.get('calorie')
            if calorie is None or str(calorie).strip() == '':
                calorie = _calc_custom_calorie(protein, fat, carb)
            else:
                calorie = float(calorie)
            valid_items.append({
                'type': 'custom',
                'name': name,
                'protein': round(protein, 2),
                'fat': round(fat, 2),
                'carb': round(carb, 2),
                'calorie': round(calorie, 2)
            })
        else:
            # 未知类型，尝试按旧格式兼容（无 type 字段 = food）
            food_id = item.get('food_id')
            weight_g = item.get('weight_g', 100)
            food = Food.query.get(food_id)
            if food and food.is_approved:
                valid_items.append({
                    'type': 'food',
                    'food_id': food_id,
                    'weight_g': weight_g
                })

    if not valid_items:
        return [], '没有有效的食物条目'
    return valid_items, None


def _enrich_items(items):
    """为 food 类型条目补充食物详情；custom 类型直接返回"""
    enriched = []
    for item in items:
        if item.get('type') == 'custom':
            enriched.append(item)
        else:
            # food 类型（包括旧数据无 type 字段）
            food = Food.query.get(item.get('food_id'))
            food_dict = food.to_dict() if food else None
            enriched.append({
                'type': 'food',
                'food_id': item.get('food_id'),
                'weight_g': item.get('weight_g', 100),
                'food': food_dict
            })
    return enriched


@recipe_bp.route('/recipes', methods=['GET'])
@login_required
def get_recipes():
    """获取我的食谱列表"""
    user = g.current_user

    recipes = UserRecipe.query.filter_by(user_id=user.id).order_by(
        UserRecipe.created_at.desc()
    ).all()

    result = []
    for recipe in recipes:
        recipe_dict = recipe.to_dict()
        recipe_dict['items'] = _enrich_items(recipe_dict['items'])
        # 计算汇总
        total_calorie = 0
        total_protein = 0.0
        total_fat = 0.0
        total_carb = 0.0
        item_count = len(recipe_dict['items'])
        for item in recipe_dict['items']:
            if item.get('type') == 'custom':
                total_calorie += item.get('calorie', 0)
                total_protein += item.get('protein', 0)
                total_fat += item.get('fat', 0)
                total_carb += item.get('carb', 0)
            else:
                food = item.get('food')
                if food:
                    weight_g = item.get('weight_g', 100)
                    ratio = weight_g / 100
                    total_calorie += int(food['calorie_per_100g'] * ratio)
                    total_protein += food['protein_per_100g'] * ratio
                    total_fat += food['fat_per_100g'] * ratio
                    total_carb += food['carb_per_100g'] * ratio
        recipe_dict['summary'] = {
            'calorie': total_calorie,
            'protein': round(total_protein, 2),
            'fat': round(total_fat, 2),
            'carb': round(total_carb, 2),
            'item_count': item_count
        }
        result.append(recipe_dict)

    return success(result)


@recipe_bp.route('/recipes', methods=['POST'])
@login_required
def create_recipe():
    """创建食谱"""
    user = g.current_user
    data = request.get_json() or {}

    name = (data.get('name') or '').strip()
    items = data.get('items', [])

    if not name:
        return error('请输入食谱名称')

    if not items:
        return error('请添加至少一种食物')

    valid_items, err = _validate_and_build_items(items)
    if err:
        return error(err)

    try:
        recipe = UserRecipe(
            user_id=user.id,
            name=name,
            items=json.dumps(valid_items)
        )
        db.session.add(recipe)
        db.session.commit()

        recipe_dict = recipe.to_dict()
        recipe_dict['items'] = _enrich_items(recipe_dict['items'])
        return success(recipe_dict, '创建成功')

    except Exception as e:
        db.session.rollback()
        return error(f'创建失败: {str(e)}')


@recipe_bp.route('/recipes/<int:recipe_id>', methods=['PUT'])
@login_required
def update_recipe(recipe_id):
    """更新食谱"""
    user = g.current_user
    data = request.get_json() or {}

    recipe = UserRecipe.query.filter_by(id=recipe_id, user_id=user.id).first()

    if not recipe:
        return error('食谱不存在', 404)

    name = data.get('name')
    items = data.get('items')

    try:
        if name is not None and str(name).strip():
            recipe.name = str(name).strip()

        if items is not None:
            valid_items, err = _validate_and_build_items(items)
            if err:
                return error(err)
            recipe.items = json.dumps(valid_items)

        db.session.commit()

        recipe_dict = recipe.to_dict()
        recipe_dict['items'] = _enrich_items(recipe_dict['items'])
        return success(recipe_dict, '更新成功')

    except Exception as e:
        db.session.rollback()
        return error(f'更新失败: {str(e)}')


@recipe_bp.route('/recipes/<int:recipe_id>', methods=['DELETE'])
@login_required
def delete_recipe(recipe_id):
    """删除食谱"""
    user = g.current_user

    recipe = UserRecipe.query.filter_by(id=recipe_id, user_id=user.id).first()

    if not recipe:
        return error('食谱不存在', 404)

    try:
        db.session.delete(recipe)
        db.session.commit()

        return success(message='删除成功')

    except Exception as e:
        db.session.rollback()
        return error(f'删除失败: {str(e)}')
