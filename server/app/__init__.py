"""Flask应用初始化"""
import os
from flask import Flask
from sqlalchemy import inspect, text
from .config import config
from .extensions import db, jwt, cors


def create_app(config_name=None):
    """应用工厂函数"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": "*",
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "supports_credentials": True
        }
    })

    # 注册蓝图
    register_blueprints(app)

    # 创建数据库表
    with app.app_context():
        db.create_all()
        patch_sqlite_schema(app)

    return app


def patch_sqlite_schema(app):
    """为SQLite旧库补齐轻量字段变更"""
    default_ai_api_base_url = app.config.get('AI_API_BASE_URL') or 'https://api.siliconflow.cn/v1'

    with db.engine.begin() as connection:
        if connection.dialect.name != 'sqlite':
            return

        inspector = inspect(connection)
        if 'system_configs' not in inspector.get_table_names():
            system_columns = set()
        else:
            system_columns = {column['name'] for column in inspector.get_columns('system_configs')}

        if 'users' in inspector.get_table_names():
            user_columns = {column['name'] for column in inspector.get_columns('users')}
            # 兼容旧列名：重命名 calorie_coefficient → goal_factor
            if 'calorie_coefficient' in user_columns and 'goal_factor' not in user_columns:
                connection.execute(text('ALTER TABLE users RENAME COLUMN calorie_coefficient TO goal_factor'))
                # 直接在内存中更新集合，避免 inspector 同一事务内缓存问题
                user_columns.discard('calorie_coefficient')
                user_columns.add('goal_factor')
            if 'goal_factor' not in user_columns:
                connection.execute(text('ALTER TABLE users ADD COLUMN goal_factor NUMERIC(4, 2)'))
            if 'daily_ai_calls' not in user_columns:
                connection.execute(text('ALTER TABLE users ADD COLUMN daily_ai_calls INTEGER DEFAULT 0'))
            if 'last_ai_call_date' not in user_columns:
                connection.execute(text('ALTER TABLE users ADD COLUMN last_ai_call_date DATE'))
            if 'nickname' not in user_columns:
                connection.execute(text('ALTER TABLE users ADD COLUMN nickname VARCHAR(50)'))
            if 'avatar' not in user_columns:
                connection.execute(text('ALTER TABLE users ADD COLUMN avatar VARCHAR(255)'))
            if 'metabolic_coefficient' not in user_columns:
                connection.execute(
                    text('ALTER TABLE users ADD COLUMN metabolic_coefficient NUMERIC(5, 3) DEFAULT 1.000'))

            connection.execute(
                text(
                    """
                    UPDATE users
                    SET goal_factor = ROUND(
                        CASE
                            WHEN bmr IS NOT NULL AND bmr > 0 THEN
                                CAST(daily_calorie_goal AS REAL) /
                                (bmr * CASE activity_level
                                    WHEN 1 THEN 1.2
                                    WHEN 2 THEN 1.375
                                    WHEN 3 THEN 1.55
                                    WHEN 4 THEN 1.725
                                    ELSE 1.2
                                END)
                            WHEN health_goal = 2 THEN 0.85
                            WHEN health_goal = 3 THEN 1.15
                            ELSE 1.00
                        END,
                        2
                    )
                    WHERE goal_factor IS NULL
                    """
                )
            )

        if 'body_records' in inspector.get_table_names():
            body_record_columns = {column['name'] for column in inspector.get_columns('body_records')}
            # 兼容旧列名：重命名 calorie_coefficient → goal_factor
            if 'calorie_coefficient' in body_record_columns and 'goal_factor' not in body_record_columns:
                connection.execute(text('ALTER TABLE body_records RENAME COLUMN calorie_coefficient TO goal_factor'))
                # 直接在内存中更新集合，避免 inspector 同一事务内缓存问题
                body_record_columns.discard('calorie_coefficient')
                body_record_columns.add('goal_factor')
            if 'goal_factor' not in body_record_columns:
                connection.execute(text('ALTER TABLE body_records ADD COLUMN goal_factor NUMERIC(4, 2)'))
            if 'metabolic_coefficient' not in body_record_columns:
                connection.execute(
                    text('ALTER TABLE body_records ADD COLUMN metabolic_coefficient NUMERIC(5, 3) DEFAULT 1.000'))

            connection.execute(
                text(
                    """
                    UPDATE body_records
                    SET goal_factor = ROUND(
                        CASE
                            WHEN bmr IS NOT NULL AND bmr > 0 THEN
                                CAST(daily_calorie_goal AS REAL) /
                                (bmr * CASE activity_level
                                    WHEN 1 THEN 1.2
                                    WHEN 2 THEN 1.375
                                    WHEN 3 THEN 1.55
                                    WHEN 4 THEN 1.725
                                    ELSE 1.2
                                END)
                            ELSE 1.00
                        END,
                        2
                    )
                    WHERE goal_factor IS NULL
                    """
                )
            )

        if 'ai_api_base_url' not in system_columns and 'system_configs' in inspector.get_table_names():
            connection.execute(text('ALTER TABLE system_configs ADD COLUMN ai_api_base_url VARCHAR(255)'))

        if 'meal_records' in inspector.get_table_names():
            meal_columns = {column['name'] for column in inspector.get_columns('meal_records')}
            if 'custom_name' not in meal_columns:
                # SQLite 不支持 ALTER COLUMN 改 nullable，需重建表
                connection.execute(text('ALTER TABLE meal_records RENAME TO meal_records_old'))
                connection.execute(text('''
                    CREATE TABLE meal_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        food_id INTEGER,
                        body_record_id INTEGER NOT NULL,
                        date DATE NOT NULL,
                        meal_type SMALLINT NOT NULL,
                        weight_g NUMERIC(7, 2),
                        calorie INTEGER NOT NULL,
                        protein NUMERIC(6, 2) NOT NULL,
                        carb NUMERIC(6, 2) NOT NULL,
                        fat NUMERIC(6, 2) NOT NULL,
                        custom_name VARCHAR(50),
                        created_at DATETIME,
                        FOREIGN KEY(user_id) REFERENCES users(id),
                        FOREIGN KEY(food_id) REFERENCES foods(id),
                        FOREIGN KEY(body_record_id) REFERENCES body_records(id)
                    )
                '''))
                connection.execute(text('''
                    INSERT INTO meal_records (id, user_id, food_id, body_record_id, date, meal_type, weight_g, calorie, protein, carb, fat, created_at)
                    SELECT id, user_id, food_id, body_record_id, date, meal_type, weight_g, calorie, protein, carb, fat, created_at
                    FROM meal_records_old
                '''))
                connection.execute(text('DROP TABLE meal_records_old'))
                connection.execute(
                    text('CREATE INDEX IF NOT EXISTS idx_meals_user_date ON meal_records (user_id, date)'))
                connection.execute(
                    text('CREATE INDEX IF NOT EXISTS idx_meals_body_record ON meal_records (body_record_id)'))

        if 'system_configs' in inspector.get_table_names():
            connection.execute(
                text(
                    """
                    UPDATE system_configs
                    SET ai_api_base_url = :ai_api_base_url
                    WHERE ai_api_base_url IS NULL OR TRIM(ai_api_base_url) = ''
                    """
                ),
                {'ai_api_base_url': default_ai_api_base_url}
            )

        if 'ai_suggestions' in inspector.get_table_names():
            ai_suggestion_columns = {column['name'] for column in inspector.get_columns('ai_suggestions')}
            if 'is_deleted' not in ai_suggestion_columns:
                connection.execute(text('ALTER TABLE ai_suggestions ADD COLUMN is_deleted BOOLEAN DEFAULT 0'))


def register_blueprints(app):
    """注册所有蓝图"""
    from .api.auth import auth_bp
    from .api.user import user_bp
    from .api.food import food_bp
    from .api.meal import meal_bp
    from .api.recipe import recipe_bp
    from .api.stats import stats_bp
    from .api.ai import ai_bp
    from .api.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(food_bp, url_prefix='/api')
    app.register_blueprint(meal_bp, url_prefix='/api')
    app.register_blueprint(recipe_bp, url_prefix='/api')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
