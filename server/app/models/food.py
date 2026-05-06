"""食物相关模型"""
from datetime import datetime
from app.extensions import db


class FoodCategory(db.Model):
    """食物分类表"""
    __tablename__ = 'food_categories'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(10), nullable=False, unique=True, comment='分类编码')
    parent_code = db.Column(db.String(10), comment='父级编码，一级分类为空')
    name = db.Column(db.String(50), nullable=False, comment='分类名称')
    sort_order = db.Column(db.Integer, default=0, comment='排序')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'code': self.code,
            'parent_code': self.parent_code,
            'name': self.name,
            'sort_order': self.sort_order
        }


class Food(db.Model):
    """食物表"""
    __tablename__ = 'foods'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='食物名称')
    category_code = db.Column(db.String(10), comment='一级分类编码')
    sub_category_code = db.Column(db.String(10), comment='二级分类编码')
    edible_portion = db.Column(db.Integer, default=100, comment='可食部分(%)')
    calorie_per_100g = db.Column(db.Integer, nullable=False, comment='每100g热量(kcal)')
    protein_per_100g = db.Column(db.Numeric(5, 2), nullable=False, comment='蛋白质(g/100g)')
    carb_per_100g = db.Column(db.Numeric(5, 2), nullable=False, comment='碳水(g/100g)')
    fat_per_100g = db.Column(db.Numeric(5, 2), nullable=False, comment='脂肪(g/100g)')
    fiber_per_100g = db.Column(db.Numeric(5, 2), comment='膳食纤维(g/100g)')
    cholesterol_per_100g = db.Column(db.Numeric(5, 2), comment='胆固醇(mg/100g)')
    sodium_per_100g = db.Column(db.Numeric(5, 2), comment='钠(mg/100g)')
    calcium_per_100g = db.Column(db.Numeric(5, 2), comment='钙(mg/100g)')
    iron_per_100g = db.Column(db.Numeric(5, 2), comment='铁(mg/100g)')
    vitamin_c_per_100g = db.Column(db.Numeric(5, 2), comment='维生素C(mg/100g)')
    is_approved = db.Column(db.Boolean, default=True, comment='是否审核通过')
    created_by = db.Column(db.Integer, comment='创建者管理员ID')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    meal_records = db.relationship('MealRecord', backref='food', lazy='dynamic')
    favorite_foods = db.relationship('FavoriteFood', backref='food', lazy='dynamic')
    
    def to_dict(self, detail: bool = False, include_admin: bool = False):
        """转换为字典"""
        data = {
            'id': self.id,
            'name': self.name,
            'category_code': self.category_code,
            'sub_category_code': self.sub_category_code,
            'calorie_per_100g': self.calorie_per_100g,
            'protein_per_100g': float(self.protein_per_100g) if self.protein_per_100g else 0,
            'carb_per_100g': float(self.carb_per_100g) if self.carb_per_100g else 0,
            'fat_per_100g': float(self.fat_per_100g) if self.fat_per_100g else 0
        }
        if detail:
            data.update({
                'edible_portion': self.edible_portion,
                'fiber_per_100g': float(self.fiber_per_100g) if self.fiber_per_100g else None,
                'cholesterol_per_100g': float(self.cholesterol_per_100g) if self.cholesterol_per_100g else None,
                'sodium_per_100g': float(self.sodium_per_100g) if self.sodium_per_100g else None,
                'calcium_per_100g': float(self.calcium_per_100g) if self.calcium_per_100g else None,
                'iron_per_100g': float(self.iron_per_100g) if self.iron_per_100g else None,
                'vitamin_c_per_100g': float(self.vitamin_c_per_100g) if self.vitamin_c_per_100g else None
            })
        if include_admin:
            data.update({
                'is_approved': self.is_approved,
                'created_by': self.created_by,
                'created_at': self.created_at.isoformat() if self.created_at else None
            })
        return data


class FavoriteFood(db.Model):
    """用户收藏食物表"""
    __tablename__ = 'favorite_foods'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False, comment='食物ID')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'food_id', name='idx_favorite_user_food'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'food_id': self.food_id,
            'food': self.food.to_dict() if self.food else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserRecipe(db.Model):
    """用户食谱表"""
    __tablename__ = 'user_recipes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    name = db.Column(db.String(50), nullable=False, comment='食谱名称')
    items = db.Column(db.Text, nullable=False, comment='JSON数组:[{food_id, weight_g}, ...]')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        """转换为字典"""
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'items': json.loads(self.items) if self.items else [],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
