"""用户相关模型"""
from datetime import datetime, date
from app.extensions import db


def _default_calorie_coefficient(health_goal):
    return {
        1: 1.00,
        2: 0.85,
        3: 1.15,
    }.get(health_goal, 1.00)


def _default_nutrient_ratios(health_goal):
    return {
        1: {'protein': 0.20, 'fat': 0.25, 'carb': 0.55},
        2: {'protein': 0.30, 'fat': 0.25, 'carb': 0.45},
        3: {'protein': 0.25, 'fat': 0.20, 'carb': 0.55},
    }.get(health_goal, {'protein': 0.20, 'fat': 0.25, 'carb': 0.55})


class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone = db.Column(db.String(20), unique=True, comment='手机号')
    email = db.Column(db.String(100), unique=True, comment='邮箱')
    nickname = db.Column(db.String(50), comment='昵称')
    avatar = db.Column(db.String(255), comment='头像URL')
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希')
    gender = db.Column(db.SmallInteger, nullable=False, comment='0=男, 1=女, 2=其他')
    birthday = db.Column(db.Date, nullable=False, comment='出生日期')
    height_cm = db.Column(db.Integer, nullable=False, comment='身高(cm)')
    weight_kg = db.Column(db.Numeric(5, 2), nullable=False, comment='体重(kg)')
    activity_level = db.Column(db.SmallInteger, nullable=False, comment='1=久坐, 2=轻度, 3=中度, 4=高强度')
    health_goal = db.Column(db.SmallInteger, default=1, comment='1=维持, 2=减脂, 3=增肌')
    calorie_coefficient = db.Column(db.Numeric(4, 2), nullable=False, default=1.00, comment='热量目标系数')
    diet_preference = db.Column(db.String(100), comment='饮食偏好标签,逗号分隔')
    bmr = db.Column(db.Integer, nullable=False, comment='基础代谢率(kcal/天)')
    daily_calorie_goal = db.Column(db.Integer, nullable=False, comment='每日推荐热量(kcal)')
    protein_ratio = db.Column(db.Numeric(3, 2), default=0.20, comment='蛋白质占比(默认0.20)')
    fat_ratio = db.Column(db.Numeric(3, 2), default=0.25, comment='脂肪占比(默认0.25)')
    carb_ratio = db.Column(db.Numeric(3, 2), default=0.55, comment='碳水占比(默认0.55)')
    bmi = db.Column(db.Numeric(4, 2), nullable=False, comment='BMI值')
    wechat_openid = db.Column(db.String(100), comment='微信OpenID')
    last_weight_update = db.Column(db.Date, comment='最近体重更新日期')
    is_frozen = db.Column(db.Boolean, default=False, comment='是否冻结')
    is_deleted = db.Column(db.Boolean, default=False, comment='软删除标志')
    daily_ai_calls = db.Column(db.Integer, default=0, comment='今日AI调用次数')
    last_ai_call_date = db.Column(db.Date, comment='上次AI调用日期')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    body_records = db.relationship('BodyRecord', backref='user', lazy='dynamic')
    meal_records = db.relationship('MealRecord', backref='user', lazy='dynamic')
    favorite_foods = db.relationship('FavoriteFood', backref='user', lazy='dynamic')
    user_recipes = db.relationship('UserRecipe', backref='user', lazy='dynamic')
    ai_suggestions = db.relationship('AISuggestion', backref='user', lazy='dynamic')
    
    @property
    def age(self):
        """计算年龄"""
        today = date.today()
        return today.year - self.birthday.year - (
            (today.month, today.day) < (self.birthday.month, self.birthday.day)
        )
    
    def to_dict(self):
        """转换为字典"""
        default_ratios = _default_nutrient_ratios(self.health_goal)
        return {
            'id': self.id,
            'phone': self.phone,
            'email': self.email,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'gender': self.gender,
            'birthday': self.birthday.isoformat() if self.birthday else None,
            'age': self.age,
            'height_cm': self.height_cm,
            'weight_kg': float(self.weight_kg) if self.weight_kg else None,
            'activity_level': self.activity_level,
            'health_goal': self.health_goal,
            'calorie_coefficient': float(self.calorie_coefficient) if self.calorie_coefficient is not None else _default_calorie_coefficient(self.health_goal),
            'diet_preference': self.diet_preference,
            'bmr': self.bmr,
            'daily_calorie_goal': self.daily_calorie_goal,
            'protein_ratio': float(self.protein_ratio) if self.protein_ratio is not None else default_ratios['protein'],
            'fat_ratio': float(self.fat_ratio) if self.fat_ratio is not None else default_ratios['fat'],
            'carb_ratio': float(self.carb_ratio) if self.carb_ratio is not None else default_ratios['carb'],
            'bmi': float(self.bmi) if self.bmi else None,
            'last_weight_update': self.last_weight_update.isoformat() if self.last_weight_update else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BodyRecord(db.Model):
    """身体状态快照表"""
    __tablename__ = 'body_records'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    height_cm = db.Column(db.Integer, nullable=False, comment='身高(cm)')
    weight_kg = db.Column(db.Numeric(5, 2), nullable=False, comment='体重(kg)')
    age = db.Column(db.Integer, nullable=False, comment='记录时的年龄')
    gender = db.Column(db.SmallInteger, nullable=False, comment='0=男,1=女,2=其他')
    activity_level = db.Column(db.SmallInteger, nullable=False, comment='1=久坐,2=轻度,3=中度,4=高强度')
    bmi = db.Column(db.Numeric(4, 2), nullable=False, comment='BMI值')
    bmr = db.Column(db.Integer, nullable=False, comment='基础代谢率(kcal/天)')
    daily_calorie_goal = db.Column(db.Integer, nullable=False, comment='当日推荐总热量(kcal)')
    calorie_coefficient = db.Column(db.Numeric(4, 2), nullable=False, default=1.00, comment='当日热量目标系数')
    protein_ratio = db.Column(db.Numeric(3, 2), default=0.20, comment='蛋白质占比')
    fat_ratio = db.Column(db.Numeric(3, 2), default=0.25, comment='脂肪占比')
    carb_ratio = db.Column(db.Numeric(3, 2), default=0.55, comment='碳水占比')
    metabolic_coefficient = db.Column(db.Numeric(5, 3), default=1.000, comment='个人代谢系数校准值')
    recorded_at = db.Column(db.DateTime, default=datetime.now, comment='快照时间')
    
    # 关系
    meal_records = db.relationship('MealRecord', backref='body_record', lazy='dynamic')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'height_cm': self.height_cm,
            'weight_kg': float(self.weight_kg) if self.weight_kg else None,
            'age': self.age,
            'gender': self.gender,
            'activity_level': self.activity_level,
            'bmi': float(self.bmi) if self.bmi else None,
            'bmr': self.bmr,
            'daily_calorie_goal': self.daily_calorie_goal,
            'calorie_coefficient': float(self.calorie_coefficient) if self.calorie_coefficient is not None else 1.0,
            'protein_ratio': float(self.protein_ratio) if self.protein_ratio is not None else 0.20,
            'fat_ratio': float(self.fat_ratio) if self.fat_ratio is not None else 0.25,
            'carb_ratio': float(self.carb_ratio) if self.carb_ratio is not None else 0.55,
            'metabolic_coefficient': float(self.metabolic_coefficient) if self.metabolic_coefficient else 1.0,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }
