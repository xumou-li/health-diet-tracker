"""CSV数据导入脚本
导入中国食物分类表和食物成分表到数据库
"""
import os
import sys
import csv

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import FoodCategory, Food


def safe_float(value, default=0):
    """安全转换为浮点数"""
    if value is None or value == '' or value == '—' or value == '-':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """安全转换为整数"""
    if value is None or value == '' or value == '—' or value == '-':
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def import_categories(csv_path):
    """导入食物分类表"""
    print(f"正在导入分类数据: {csv_path}")
    
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = str(row.get('编码', '')).strip()
            parent_code = row.get('父级编码', '')
            name = row.get('名称', '').strip()
            
            if not code or not name:
                continue
            
            # 处理父级编码
            if parent_code:
                parent_code = str(parent_code).replace('.0', '').strip()
                if not parent_code or parent_code == 'nan':
                    parent_code = None
            else:
                parent_code = None
            
            # 检查是否已存在
            existing = FoodCategory.query.filter_by(code=code).first()
            if existing:
                existing.name = name
                existing.parent_code = parent_code
            else:
                category = FoodCategory(
                    code=code,
                    parent_code=parent_code,
                    name=name,
                    sort_order=count
                )
                db.session.add(category)
            
            count += 1
    
    db.session.commit()
    print(f"成功导入 {count} 条分类数据")
    return count


def import_foods(csv_path):
    """导入食物成分表"""
    print(f"正在导入食物数据: {csv_path}")
    
    # 食物成分表CSV中的旧编码 -> 分类表中的新编码映射
    # 谷类和薯类的二级分类编码需要映射
    old_to_new_code = {
        '11': '1001',  # 小麦
        '12': '1002',  # 稻米
        '13': '1003',  # 玉米
        '14': '1004',  # 大麦
        '15': '1005',  # 小米、黄米
        '19': '1009',  # 谷类其他
        '21': '2001',  # 薯类
        '22': '2002',  # 淀粉类
    }
    
    # 预加载分类映射表（二级分类code -> 一级分类code）
    category_parent_map = {}
    for cat in FoodCategory.query.all():
        if cat.parent_code:
            # 二级分类，记录其父级编码
            category_parent_map[cat.code] = cat.parent_code
    print(f"已加载 {len(category_parent_map)} 条分类映射")
    
    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('名  称', '').strip()
            if not name:
                continue
            
            # CSV的"一级分类编码"实际是二级分类code
            raw_sub_code = str(row.get('一级分类编码', '')).strip()
            
            # 映射旧编码到新编码
            sub_category_code = old_to_new_code.get(raw_sub_code, raw_sub_code)
            
            # 通过分类表查找真正的一级分类code
            category_code = category_parent_map.get(sub_category_code, '')
            
            # 如果找不到映射，尝试直接作为一级分类处理
            if not category_code and sub_category_code:
                # 检查是否本身就是一级分类
                existing_cat = FoodCategory.query.filter_by(code=sub_category_code, parent_code=None).first()
                if existing_cat:
                    category_code = sub_category_code
                    sub_category_code = ''
            
            # 营养数据
            edible_portion = safe_int(row.get('食部(%)'), 100)
            calorie = safe_int(row.get('能量（千卡）'), 0)
            protein = safe_float(row.get('蛋白质(g)'), 0)
            fat = safe_float(row.get('脂肪(g)'), 0)
            carb = safe_float(row.get('碳水化物(g)'), 0)
            fiber = safe_float(row.get('膳食纤维(g)'))
            cholesterol = safe_float(row.get('胆固醇(mg)'))
            sodium = safe_float(row.get('钠(mg)'))
            calcium = safe_float(row.get('钙(mg)'))
            iron = safe_float(row.get('铁(mg)'))
            vitamin_c = safe_float(row.get('维生素C(mg)'))
            
            # 跳过无效数据
            if calorie <= 0 and protein <= 0 and fat <= 0 and carb <= 0:
                continue
            
            # 检查是否已存在同名食物
            existing = Food.query.filter_by(name=name).first()
            if existing:
                # 更新已存在的食物
                existing.category_code = category_code
                existing.sub_category_code = sub_category_code
                existing.edible_portion = edible_portion
                existing.calorie_per_100g = calorie
                existing.protein_per_100g = protein
                existing.carb_per_100g = carb
                existing.fat_per_100g = fat
                existing.fiber_per_100g = fiber
                existing.cholesterol_per_100g = cholesterol
                existing.sodium_per_100g = sodium
                existing.calcium_per_100g = calcium
                existing.iron_per_100g = iron
                existing.vitamin_c_per_100g = vitamin_c
            else:
                food = Food(
                    name=name,
                    category_code=category_code,
                    sub_category_code=sub_category_code,
                    edible_portion=edible_portion,
                    calorie_per_100g=calorie,
                    protein_per_100g=protein,
                    carb_per_100g=carb,
                    fat_per_100g=fat,
                    fiber_per_100g=fiber if fiber else None,
                    cholesterol_per_100g=cholesterol if cholesterol else None,
                    sodium_per_100g=sodium if sodium else None,
                    calcium_per_100g=calcium if calcium else None,
                    iron_per_100g=iron if iron else None,
                    vitamin_c_per_100g=vitamin_c if vitamin_c else None,
                    is_approved=True
                )
                db.session.add(food)
            
            count += 1
            
            # 每500条提交一次
            if count % 500 == 0:
                db.session.commit()
                print(f"已导入 {count} 条...")
    
    db.session.commit()
    print(f"成功导入 {count} 条食物数据")
    return count


def main():
    """主函数"""
    app = create_app()
    
    with app.app_context():
        # CSV文件路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        category_csv = os.path.join(base_dir, 'csv_data', '中国食物分类表.csv')
        food_csv = os.path.join(base_dir, 'csv_data', '中国食物成分表.csv')
        
        # 检查文件是否存在
        if not os.path.exists(category_csv):
            print(f"错误: 找不到分类文件 {category_csv}")
            return
        
        if not os.path.exists(food_csv):
            print(f"错误: 找不到食物文件 {food_csv}")
            return
        
        # 导入数据
        print("=" * 50)
        print("开始导入食物数据")
        print("=" * 50)
        
        cat_count = import_categories(category_csv)
        food_count = import_foods(food_csv)
        
        print("=" * 50)
        print(f"导入完成: {cat_count} 条分类, {food_count} 条食物")
        print("=" * 50)


if __name__ == '__main__':
    main()
