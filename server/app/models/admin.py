"""管理员相关模型"""
from datetime import datetime
from app.extensions import db


class Admin(db.Model):
    """管理员表"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True, comment='用户名')
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希')
    role = db.Column(db.SmallInteger, default=1, comment='1=普通管理员, 2=超级管理员')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login_at = db.Column(db.DateTime, comment='最后登录时间')
    
    # 关系
    logs = db.relationship('AdminLog', backref='admin', lazy='dynamic')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'role_name': '超级管理员' if self.role == 2 else '普通管理员',
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }


class AdminLog(db.Model):
    """管理员操作日志表"""
    __tablename__ = 'admin_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False, comment='管理员ID')
    action = db.Column(db.String(50), nullable=False, comment='操作类型')
    target_type = db.Column(db.String(30), comment='目标类型: user/food/config等')
    target_id = db.Column(db.Integer, comment='目标ID')
    details = db.Column(db.Text, comment='操作详情JSON')
    ip_address = db.Column(db.String(50), comment='IP地址')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        db.Index('idx_logs_admin', 'admin_id'),
        db.Index('idx_logs_date', db.func.date('created_at')),
    )
    
    def to_dict(self):
        """转换为字典"""
        import json
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'admin_name': self.admin.username if self.admin else None,
            'action': self.action,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'details': json.loads(self.details) if self.details else None,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
