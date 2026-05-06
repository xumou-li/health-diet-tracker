"""食物管理API"""
import json
import csv
import io
from flask import Blueprint, request, g
from app.extensions import db
from app.models import Food, FoodCategory, AdminLog
from app.utils.response import success, error
from app.utils.auth import admin_required

admin_foods_bp = Blueprint('admin_foods', __name__)


def serialize_admin_food(food: Food, detail: bool = True):
    """管理员食物序列化，补充审核与创建元数据"""
    return food.to_dict(detail=detail, include_admin=True)


def log_action(action, target_type, target_id, details=None):
    """记录管理员操作"""
    log = AdminLog(
        admin_id=g.current_admin.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details) if details else None,
        ip_address=request.remote_addr
    )
    db.session.add(log)


@admin_foods_bp.route('/foods', methods=['GET'])
@admin_required
def get_foods():
    """食物列表（含待审核）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '')
    category_code = request.args.get('category_code')
    approved = request.args.get('approved')  # true/false/all
    
    query = Food.query
    
    if keyword:
        query = query.filter(Food.name.like(f'%{keyword}%'))
    
    if category_code:
        query = query.filter_by(category_code=category_code)
    
    if approved == 'true':
        query = query.filter_by(is_approved=True)
    elif approved == 'false':
        query = query.filter_by(is_approved=False)
    
    pagination = query.order_by(Food.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return success({
        'items': [serialize_admin_food(food) for food in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@admin_foods_bp.route('/foods', methods=['POST'])
@admin_required
def create_food():
    """新增食物"""
    data = request.get_json() or {}
    
    name = data.get('name')
    if not name:
        return error('请输入食物名称')
    
    calorie = data.get('calorie_per_100g')
    if calorie is None or calorie < 0:
        return error('请输入有效的热量值')
    
    try:
        food = Food(
            name=name,
            category_code=data.get('category_code'),
            sub_category_code=data.get('sub_category_code'),
            edible_portion=data.get('edible_portion', 100),
            calorie_per_100g=calorie,
            protein_per_100g=data.get('protein_per_100g', 0),
            carb_per_100g=data.get('carb_per_100g', 0),
            fat_per_100g=data.get('fat_per_100g', 0),
            fiber_per_100g=data.get('fiber_per_100g'),
            cholesterol_per_100g=data.get('cholesterol_per_100g'),
            sodium_per_100g=data.get('sodium_per_100g'),
            calcium_per_100g=data.get('calcium_per_100g'),
            iron_per_100g=data.get('iron_per_100g'),
            vitamin_c_per_100g=data.get('vitamin_c_per_100g'),
            is_approved=data.get('is_approved', False),
            created_by=g.current_admin.id
        )
        db.session.add(food)
        log_action('create_food', 'food', None, {'name': name})
        db.session.commit()
        
        return success(serialize_admin_food(food), '创建成功')
        
    except Exception as e:
        db.session.rollback()
        return error(f'创建失败: {str(e)}')


@admin_foods_bp.route('/foods/<int:food_id>', methods=['PUT'])
@admin_required
def update_food(food_id):
    """编辑食物"""
    food = Food.query.get(food_id)
    
    if not food:
        return error('食物不存在', 404)
    
    data = request.get_json() or {}
    
    try:
        if 'name' in data:
            food.name = data['name']
        if 'category_code' in data:
            food.category_code = data['category_code']
        if 'sub_category_code' in data:
            food.sub_category_code = data['sub_category_code']
        if 'edible_portion' in data:
            food.edible_portion = data['edible_portion']
        if 'calorie_per_100g' in data:
            food.calorie_per_100g = data['calorie_per_100g']
        if 'protein_per_100g' in data:
            food.protein_per_100g = data['protein_per_100g']
        if 'carb_per_100g' in data:
            food.carb_per_100g = data['carb_per_100g']
        if 'fat_per_100g' in data:
            food.fat_per_100g = data['fat_per_100g']
        if 'fiber_per_100g' in data:
            food.fiber_per_100g = data['fiber_per_100g']
        if 'cholesterol_per_100g' in data:
            food.cholesterol_per_100g = data['cholesterol_per_100g']
        if 'sodium_per_100g' in data:
            food.sodium_per_100g = data['sodium_per_100g']
        if 'calcium_per_100g' in data:
            food.calcium_per_100g = data['calcium_per_100g']
        if 'iron_per_100g' in data:
            food.iron_per_100g = data['iron_per_100g']
        if 'vitamin_c_per_100g' in data:
            food.vitamin_c_per_100g = data['vitamin_c_per_100g']
        
        log_action('update_food', 'food', food_id, {'food_id': food_id, 'name': food.name})
        db.session.commit()
        
        return success(serialize_admin_food(food), '更新成功')
        
    except Exception as e:
        db.session.rollback()
        return error(f'更新失败: {str(e)}')


@admin_foods_bp.route('/foods/<int:food_id>', methods=['DELETE'])
@admin_required
def delete_food(food_id):
    """删除食物"""
    food = Food.query.get(food_id)
    
    if not food:
        return error('食物不存在', 404)
    
    try:
        log_action('delete_food', 'food', food_id, {'name': food.name})
        db.session.delete(food)
        db.session.commit()
        
        return success(message='删除成功')
        
    except Exception as e:
        db.session.rollback()
        return error(f'删除失败: {str(e)}')


@admin_foods_bp.route('/foods/<int:food_id>/approve', methods=['PUT'])
@admin_required
def approve_food(food_id):
    """审核通过"""
    food = Food.query.get(food_id)
    
    if not food:
        return error('食物不存在', 404)
    
    try:
        food.is_approved = True
        log_action('approve_food', 'food', food_id, {'food_id': food_id, 'name': food.name})
        db.session.commit()
        
        return success({'is_approved': True}, '审核通过')
        
    except Exception as e:
        db.session.rollback()
        return error(f'操作失败: {str(e)}')


@admin_foods_bp.route('/categories', methods=['GET'])
@admin_required
def get_categories():
    """分类列表"""
    categories = FoodCategory.query.order_by(FoodCategory.sort_order, FoodCategory.code).all()
    return success([cat.to_dict() for cat in categories])


@admin_foods_bp.route('/categories', methods=['POST'])
@admin_required
def create_category():
    """新增分类"""
    data = request.get_json() or {}
    
    code = data.get('code')
    name = data.get('name')
    
    if not code or not name:
        return error('请输入分类编码和名称')
    
    if FoodCategory.query.filter_by(code=code).first():
        return error('分类编码已存在')
    
    try:
        category = FoodCategory(
            code=code,
            parent_code=data.get('parent_code'),
            name=name,
            sort_order=data.get('sort_order', 0)
        )
        db.session.add(category)
        log_action('create_category', 'category', None, {'code': code, 'name': name})
        db.session.commit()
        
        return success(category.to_dict(), '创建成功')
        
    except Exception as e:
        db.session.rollback()
        return error(f'创建失败: {str(e)}')


@admin_foods_bp.route('/categories/<int:category_id>', methods=['PUT'])
@admin_required
def update_category(category_id):
    """编辑分类"""
    category = FoodCategory.query.get(category_id)
    
    if not category:
        return error('分类不存在', 404)
    
    data = request.get_json() or {}
    
    try:
        if 'name' in data:
            category.name = data['name']
        if 'parent_code' in data:
            category.parent_code = data['parent_code']
        if 'sort_order' in data:
            category.sort_order = data['sort_order']
        
        log_action('update_category', 'category', category_id, {'category_id': category_id, 'name': category.name, 'code': category.code})
        db.session.commit()
        
        return success(category.to_dict(), '更新成功')
        
    except Exception as e:
        db.session.rollback()
        return error(f'更新失败: {str(e)}')
