"""应用配置"""
import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_AI_API_BASE_URL = 'https://api.siliconflow.cn/v1'


class Config:
    """基础配置"""
    # 数据库
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "health_diet.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # AI配置
    AI_ENABLED = True
    AI_DAILY_LIMIT = 10
    AI_MODEL = 'deepseek-chat'
    AI_API_KEY = os.getenv('AI_API_KEY', '')
    AI_API_BASE_URL = os.getenv('AI_API_BASE_URL', DEFAULT_AI_API_BASE_URL)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
