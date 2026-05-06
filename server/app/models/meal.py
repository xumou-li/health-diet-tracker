"""饮食记录模型"""
from datetime import datetime
from app.extensions import db


class MealRecord(db.Model):
    """饮食记录表"""
    __tablename__ = 'meal_records'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=True, comment='食物ID(自定义食物时为空)')
    body_record_id = db.Column(db.Integer, db.ForeignKey('body_records.id'), nullable=False, comment='对应的身体快照ID')
    date = db.Column(db.Date, nullable=False, comment='用餐日期')
    meal_type = db.Column(db.SmallInteger, nullable=False, comment='1=早餐, 2=午餐, 3=晚餐, 4=加餐')
    weight_g = db.Column(db.Numeric(7, 2), nullable=True, comment='实际摄入重量(克，自定义食物时为空)')
    calorie = db.Column(db.Integer, nullable=False, comment='实际热量(kcal)')
    protein = db.Column(db.Numeric(6, 2), nullable=False, comment='实际蛋白(g)')
    carb = db.Column(db.Numeric(6, 2), nullable=False, comment='实际碳水(g)')
    fat = db.Column(db.Numeric(6, 2), nullable=False, comment='实际脂肪(g)')
    custom_name = db.Column(db.String(50), nullable=True, comment='自定义食物名称')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        db.Index('idx_meals_user_date', 'user_id', 'date'),
        db.Index('idx_meals_body_record', 'body_record_id'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'food_id': self.food_id,
            'food': self.food.to_dict() if self.food else None,
            'food_name': self.food.name if self.food else (self.custom_name or '未知'),
            'is_custom': self.food_id is None,
            'body_record_id': self.body_record_id,
            'date': self.date.isoformat() if self.date else None,
            'meal_type': self.meal_type,
            'meal_type_name': self.meal_type_name,
            'weight_g': float(self.weight_g) if self.weight_g else 0,
            'calorie': self.calorie,
            'protein': float(self.protein) if self.protein else 0,
            'carb': float(self.carb) if self.carb else 0,
            'fat': float(self.fat) if self.fat else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @property
    def meal_type_name(self):
        """餐次名称"""
        names = {1: '早餐', 2: '午餐', 3: '晚餐', 4: '加餐'}
        return names.get(self.meal_type, '未知')
