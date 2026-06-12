"""食物库API"""
from flask import Blueprint, request, g
from app.extensions import db
from app.models import Food, FoodCategory, FavoriteFood
from app.utils.response import success, error
from app.utils.auth import login_required

food_bp = Blueprint('food', __name__)


@food_bp.route('/foods', methods=['GET'])
def search_foods():
    """搜索食物（支持分类、关键词、分页）"""
    # 参数
    keyword = request.args.get('keyword', '')
    category_code = request.args.get('category_code')
    sub_category_code = request.args.get('sub_category_code')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 构建查询
    query = Food.query.filter_by(is_approved=True)
    
    # 关键词搜索
    if keyword:
        query = query.filter(Food.name.like(f'%{keyword}%'))
    
    # 分类筛选
    if sub_category_code:
        query = query.filter_by(sub_category_code=sub_category_code)
    elif category_code:
        query = query.filter_by(category_code=category_code)
    
    # 分页
    pagination = query.order_by(Food.id).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return success({
        'items': [food.to_dict() for food in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@food_bp.route('/foods/<int:food_id>', methods=['GET'])
def get_food_detail(food_id):
    """食物详情"""
    food = Food.query.get(food_id)
    
    if not food or not food.is_approved:
        return error('食物不存在', 404)
    
    return success(food.to_dict(detail=True))


@food_bp.route('/foods/<int:food_id>/alternatives', methods=['GET'])
def get_food_alternatives(food_id):
    """获取相似低热量食物"""
    food = Food.query.get(food_id)
    
    if not food:
        return error('食物不存在', 404)
    
    # 查找同分类下热量更低的食物
    alternatives = Food.query.filter(
        Food.is_approved == True,
        Food.id != food_id,
        Food.category_code == food.category_code,
        Food.calorie_per_100g < food.calorie_per_100g
    ).order_by(Food.calorie_per_100g).limit(10).all()
    
    return success([f.to_dict() for f in alternatives])


@food_bp.route('/foods/popular', methods=['GET'])
def get_popular_foods():
    """热门食物排行（基于使用频次）"""
    from app.models import MealRecord
    from sqlalchemy import func
    
    limit = request.args.get('limit', 20, type=int)
    
    # 统计使用次数最多的食物
    popular = db.session.query(
        Food,
        func.count(MealRecord.id).label('usage_count')
    ).join(
        MealRecord, Food.id == MealRecord.food_id
    ).filter(
        Food.is_approved == True
    ).group_by(
        Food.id
    ).order_by(
        func.count(MealRecord.id).desc()
    ).limit(limit).all()
    
    result = []
    for food, count in popular:
        data = food.to_dict()
        data['usage_count'] = count
        result.append(data)
    
    return success(result)


@food_bp.route('/food-categories', methods=['GET'])
def get_categories():
    """获取分类树"""
    categories = FoodCategory.query.order_by(FoodCategory.sort_order, FoodCategory.code).all()
    
    # 构建树形结构
    tree = []
    category_map = {}
    
    for cat in categories:
        cat_dict = cat.to_dict()
        cat_dict['children'] = []
        category_map[cat.code] = cat_dict
        
        if not cat.parent_code:
            tree.append(cat_dict)
    
    # 建立父子关系
    for cat in categories:
        if cat.parent_code and cat.parent_code in category_map:
            category_map[cat.parent_code]['children'].append(category_map[cat.code])
    
    return success(tree)


@food_bp.route('/favorites', methods=['GET'])
@login_required
def get_favorites():
    """获取收藏列表"""
    user = g.current_user
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = FavoriteFood.query.filter_by(user_id=user.id).order_by(
        FavoriteFood.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return success({
        'items': [fav.to_dict() for fav in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@food_bp.route('/favorites', methods=['POST'])
@login_required
def add_favorite():
    """收藏食物"""
    user = g.current_user
    data = request.get_json() or {}
    
    food_id = data.get('food_id')
    
    if not food_id:
        return error('请指定食物ID')
    
    # 检查食物是否存在
    food = Food.query.get(food_id)
    if not food or not food.is_approved:
        return error('食物不存在')
    
    # 检查是否已收藏
    existing = FavoriteFood.query.filter_by(user_id=user.id, food_id=food_id).first()
    if existing:
        return error('已收藏过该食物')
    
    try:
        favorite = FavoriteFood(user_id=user.id, food_id=food_id)
        db.session.add(favorite)
        db.session.commit()
        
        return success(favorite.to_dict(), '收藏成功')
        
    except Exception as e:
        db.session.rollback()
        return error(f'收藏失败: {str(e)}')


@food_bp.route('/favorites/<int:food_id>', methods=['DELETE'])
@login_required
def remove_favorite(food_id):
    """取消收藏"""
    user = g.current_user
    
    favorite = FavoriteFood.query.filter_by(user_id=user.id, food_id=food_id).first()
    
    if not favorite:
        return error('未收藏该食物')
    
    try:
        db.session.delete(favorite)
        db.session.commit()
        
        return success(message='取消收藏成功')
        
    except Exception as e:
        db.session.rollback()
        return error(f'操作失败: {str(e)}')
