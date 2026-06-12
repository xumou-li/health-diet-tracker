"""营养计算服务"""


class NutritionService:
    """营养计算服务"""
    
    # 活动系数
    ACTIVITY_FACTORS = {
        1: 1.2,    # 久坐
        2: 1.375,  # 轻度
        3: 1.55,   # 中度
        4: 1.725   # 高强度
    }
    
    # 健康目标系数
    GOAL_FACTORS = {
        1: 1.0,   # 维持
        2: 0.85,  # 减脂
        3: 1.15   # 增肌
    }
    
    # 健康目标默认营养素比例 (蛋白质, 脂肪, 碳水)
    GOAL_NUTRIENT_RATIOS = {
        1: {'protein': 0.20, 'fat': 0.25, 'carb': 0.55},  # 维持: 均衡
        2: {'protein': 0.30, 'fat': 0.25, 'carb': 0.45},  # 减脂: 更高蛋白
        3: {'protein': 0.25, 'fat': 0.20, 'carb': 0.55},  # 增肌: 高蛋白高碳水
    }

    @classmethod
    def get_default_goal_factor(cls, health_goal=1):
        """根据健康目标获取默认热量目标系数（0.85=减脂, 1.00=维持, 1.15=增肌）"""
        return cls.GOAL_FACTORS.get(health_goal, cls.GOAL_FACTORS[1])
    
    @staticmethod
    def calculate_bmi(weight_kg, height_cm):
        """
        计算BMI
        BMI = 体重(kg) / 身高(m)^2
        """
        if height_cm <= 0 or weight_kg <= 0:
            return 0
        height_m = height_cm / 100
        return round(weight_kg / (height_m ** 2), 2)
    
    @staticmethod
    def get_bmi_status(bmi):
        """
        BMI状态判定（中国标准）
        """
        if bmi < 18.5:
            return "偏瘦"
        elif bmi < 24:
            return "正常"
        elif bmi < 28:
            return "超重"
        else:
            return "肥胖"
    
    @staticmethod
    def calculate_bmr(weight_kg, height_cm, age, gender):
        """
        计算基础代谢率BMR（Mifflin-St Jeor公式）
        男性: BMR = 10 * 体重(kg) + 6.25 * 身高(cm) - 5 * 年龄 + 5
        女性: BMR = 10 * 体重(kg) + 6.25 * 身高(cm) - 5 * 年龄 - 161
        """
        base = 10 * float(weight_kg) + 6.25 * height_cm - 5 * age
        if gender == 0:  # 男性
            return round(base + 5)
        else:  # 女性或其他
            return round(base - 161)
    
    @classmethod
    def calculate_daily_calorie(cls, bmr, activity_level, health_goal, goal_factor=None):
        """
        计算每日推荐热量
        TDEE = BMR * 活动系数 * 目标系数(goal_factor)
        goal_factor 由用户指定或根据健康目标使用默认值
        """
        activity_factor = cls.ACTIVITY_FACTORS.get(activity_level, 1.2)
        effective_goal_factor = (
            float(goal_factor)
            if goal_factor is not None
            else cls.get_default_goal_factor(health_goal)
        )
        return round(bmr * activity_factor * effective_goal_factor)
    
    @classmethod
    def get_default_nutrient_ratios(cls, health_goal=1):
        """
        根据健康目标获取默认营养素比例
        返回: {'protein': 0.25, 'fat': 0.25, 'carb': 0.45}
        """
        return cls.GOAL_NUTRIENT_RATIOS.get(health_goal, cls.GOAL_NUTRIENT_RATIOS[1])
    
    @staticmethod
    def calculate_nutrient_targets(daily_calorie, protein_ratio=0.20, fat_ratio=0.25, carb_ratio=0.55):
        """
        计算营养素推荐量
        支持自定义比例，默认: 蛋白质15%, 脂肪25%, 碳水55%
        """
        # 确保比例总和为1，如果不对则按比例缩放
        total_ratio = protein_ratio + fat_ratio + carb_ratio
        if total_ratio != 1.0:
            protein_ratio /= total_ratio
            fat_ratio /= total_ratio
            carb_ratio /= total_ratio
        
        return {
            'calorie': daily_calorie,
            'protein': round(daily_calorie * protein_ratio / 4, 1),
            'fat': round(daily_calorie * fat_ratio / 9, 1),
            'carb': round(daily_calorie * carb_ratio / 4, 1)
        }
    
    @staticmethod
    def calculate_diet_score(actual, target):
        """
        计算膳食平衡评分 (0-100分)
        actual: {calorie, protein, carb, fat}
        target: {calorie, protein, carb, fat}
        """
        scores = []
        
        # 热量评分 (权重40%)
        if target['calorie'] > 0:
            calorie_ratio = actual['calorie'] / target['calorie']
            if 0.9 <= calorie_ratio <= 1.1:
                calorie_score = 100
            elif 0.8 <= calorie_ratio <= 1.2:
                calorie_score = 80
            else:
                calorie_score = max(0, 100 - abs(calorie_ratio - 1) * 100)
        else:
            calorie_score = 0
        scores.append(('calorie', calorie_score, 0.4))
        
        # 三大营养素评分 (各权重20%)
        for nutrient in ['protein', 'carb', 'fat']:
            if target[nutrient] > 0:
                ratio = actual[nutrient] / target[nutrient]
                if 0.8 <= ratio <= 1.2:
                    score = 100
                else:
                    score = max(0, 100 - abs(ratio - 1) * 80)
            else:
                score = 0
            scores.append((nutrient, score, 0.2))
        
        # 加权总分
        total = sum(score * weight for _, score, weight in scores)
        return round(total)
    
    @staticmethod
    def get_intake_status(actual, target):
        """
        获取摄入状态
        返回: normal / low / high / very_high
        """
        if target <= 0:
            return 'normal'
        ratio = actual / target
        if ratio < 0.8:
            return 'low'
        elif ratio <= 1.2:
            return 'normal'
        elif ratio <= 1.5:
            return 'high'
        else:
            return 'very_high'
    
    @classmethod
    def calculate_user_metrics(
        cls,
        weight_kg,
        height_cm,
        age,
        gender,
        activity_level,
        health_goal,
        goal_factor=None
    ):
        """
        一次性计算用户所有健康指标
        """
        bmi = cls.calculate_bmi(weight_kg, height_cm)
        bmr = cls.calculate_bmr(weight_kg, height_cm, age, gender)
        effective_goal_factor = (
            float(goal_factor)
            if goal_factor is not None
            else cls.get_default_goal_factor(health_goal)
        )
        daily_calorie = cls.calculate_daily_calorie(
            bmr,
            activity_level,
            health_goal,
            effective_goal_factor
        )

        return {
            'bmi': bmi,
            'bmi_status': cls.get_bmi_status(bmi),
            'bmr': bmr,
            'daily_calorie_goal': daily_calorie,
            'calorie_coefficient': effective_goal_factor,
            'nutrient_targets': cls.calculate_nutrient_targets(daily_calorie)
        }
    
    @staticmethod
    def calculate_excess_percent(actual, target):
        """计算超标百分比"""
        if target <= 0:
            return 0
        excess = actual - target
        if excess <= 0:
            return 0
        return round(excess / target * 100)
    
    @staticmethod
    def get_diet_suggestions(bmi_status, excess_nutrients, is_calorie_excess):
        """
        根据BMI和超标类型生成饮食建议
        """
        suggestions = []
        
        # 基于BMI的基础建议
        if bmi_status == '偏瘦':
            suggestions.append('你目前体重偏轻，建议适当增加热量摄入，选择营养密度高的食物。')
        elif bmi_status == '超重' or bmi_status == '肥胖':
            suggestions.append(f'你目前{bmi_status}，建议控制总热量摄入，增加蔬菜和优质蛋白比例。')
        
        # 基于超标营养素的建议
        if 'fat' in excess_nutrients:
            suggestions.append('今日脂肪摄入超标，建议晚餐减少油炸食品，替换为清蒸鱼、鸡胸肉等低脂高蛋白食物。')
        if 'carb' in excess_nutrients:
            suggestions.append('今日碳水摄入超标，建议减少精制米面，增加粗粮如燕麦、红薯、玉米等。')
        if 'protein' in excess_nutrients:
            suggestions.append('今日蛋白质摄入充足，注意保持，但不要过量以免增加肾脏负担。')
        
        # 热量不足建议
        if not is_calorie_excess and bmi_status == '偏瘦':
            suggestions.append('今日热量摄入不足，建议加餐坚果、全脂牛奶或香蕉等健康零食。')
        
        return suggestions
    
    @staticmethod
    def get_recommended_foods(excess_nutrients, is_calorie_excess, bmi_status):
        """
        根据营养状况推荐食物
        返回: [(食物名称, 推荐理由), ...]
        """
        recommendations = []
        
        if is_calorie_excess or 'fat' in excess_nutrients:
            # 热量/脂肪超标 - 推荐低热量高纤维食物
            recommendations.extend([
                {'name': '芹菜', 'reason': '低热量高纤维，增加饱腹感'},
                {'name': '鸡胸肉', 'reason': '高蛋白低脂肪，减脂首选'},
                {'name': '西兰花', 'reason': '富含维生素C和纤维，热量极低'},
                {'name': '燕麦', 'reason': '低GI碳水，稳定血糖'},
                {'name': '黄瓜', 'reason': '含水量高，热量几乎为零'}
            ])
        
        if not is_calorie_excess and bmi_status == '偏瘦':
            # 热量不足且偏瘦 - 推荐高热量营养食物
            recommendations.extend([
                {'name': '坚果混合', 'reason': '高热量高营养，健康脂肪来源'},
                {'name': '全脂牛奶', 'reason': '优质蛋白和钙，增重好选择'},
                {'name': '牛油果', 'reason': '富含健康脂肪，热量密度高'},
                {'name': '红薯', 'reason': '优质碳水，富含维生素A'},
                {'name': '鸡蛋', 'reason': '完全蛋白，营养全面'}
            ])
        
        if 'carb' in excess_nutrients:
            # 碳水超标 - 推荐低碳水高蛋白
            recommendations.extend([
                {'name': '豆腐', 'reason': '植物蛋白，低碳水'},
                {'name': '鸡蛋', 'reason': '零碳水，优质蛋白'},
                {'name': '三文鱼', 'reason': '优质蛋白和健康脂肪'}
            ])
        
        # 默认推荐（均衡饮食）
        if not recommendations:
            recommendations = [
                {'name': '深色蔬菜', 'reason': '富含维生素和矿物质'},
                {'name': '瘦肉', 'reason': '优质蛋白来源'},
                {'name': '全谷物', 'reason': '提供持久能量'}
            ]
        
        return recommendations
