# 个人健康饮食记录系统

基于 uni-app + Flask 的全栈健康饮食管理应用，支持饮食记录、营养分析、AI 饮食建议和后台管理。

## 功能概览

### 用户端（uni-app）
- 📱 **多端适配**：支持 H5、微信小程序、App
- 📝 **饮食记录**：按餐次记录饮食，支持食物库选择和自定义食物
- 🍱 **食谱管理**：一键添加常用食物组合，跨天复制
- 📊 **营养统计**：日/周/月热量与营养素（蛋白质/碳水/脂肪）分析，雷达图可视化
- 📈 **身体趋势**：体重、BMI 变化折线图
- 🤖 **AI 饮食助手**：基于用户身体数据和当日摄入的智能饮食问答（SSE 流式响应）
- 👤 **个人档案**：身高体重管理、健康目标（减脂/维持/增肌）、营养素比例自定义
- 🔐 **JWT 认证**：手机号/邮箱注册登录

### 管理端（Vue 3 + Element Plus）
- 📋 **仪表盘**：用户增长、记录活跃度、AI 调用统计
- 👥 **用户管理**：列表查询、账号冻结/解冻
- 🥗 **食物库管理**：食物 CRUD、分类管理、审核状态
- 🤖 **AI 监控**：调用次数、耗时、模型分布统计
- ⚙️ **系统配置**：AI 开关、每日限额、提示词模板、API 密钥

## 技术栈

| 层级 | 技术 |
|------|------|
| 用户端 | uni-app (Vue 3) + Pinia + uCharts + dayjs |
| 管理端 | Vue 3 + Vite + Element Plus + Pinia + Vue Router |
| 后端 | Python Flask + SQLAlchemy + Flask-JWT-Extended |
| 数据库 | SQLite |
| AI | DeepSeek Chat（可配 OpenAI 兼容 API）|
| 数据源 | 中国食物成分表（CSV）|

## 项目结构

```
├── server/                     # Flask 后端
│   ├── app/
│   │   ├── api/                # REST API 蓝图
│   │   │   ├── auth.py         # 认证（登录/注册）
│   │   │   ├── user.py         # 用户档案
│   │   │   ├── food.py         # 食物库
│   │   │   ├── meal.py         # 饮食记录
│   │   │   ├── recipe.py       # 食谱
│   │   │   ├── stats.py        # 营养统计 & 分析
│   │   │   ├── ai.py           # AI 问答（含流式 SSE）
│   │   │   └── admin/          # 管理端 API
│   │   ├── models/             # 数据模型
│   │   ├── services/           # 业务逻辑
│   │   │   ├── nutrition.py    # 营养计算 & 评分
│   │   │   ├── metabolism.py   # 个人代谢校准
│   │   │   └── ai_service.py   # LLM 调用封装
│   │   ├── utils/              # 工具函数
│   │   ├── config.py           # 应用配置
│   │   └── extensions.py       # Flask 扩展
│   ├── csv_data/               # 中国食物成分表
│   ├── scripts/                # 数据导入脚本
│   ├── main.py                 # 应用入口
│   └── requirements.txt
├── client/
│   ├── uni-app-user/           # uni-app 用户端
│   │   └── src/
│   │       ├── pages/          # 页面（首页/记录/食物库/统计/AI/我的）
│   │       ├── api/            # API 请求封装
│   │       ├── store/          # Pinia 状态管理
│   │       └── utils/          # 工具函数
│   └── admin-web/              # Vue 3 管理端
│       └── src/
│           ├── views/          # 页面（仪表盘/用户/食物/分类/AI/日志/系统）
│           ├── api/            # API 请求封装
│           └── layout/         # 布局组件
```

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- npm

### 1. 启动后端

```bash
cd server

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# 安装依赖
pip install -r requirements.txt

# 导入食物数据
python scripts/import_foods.py

# 启动服务（默认 http://localhost:5000）
python main.py
```

### 2. 启动用户端（H5）

```bash
cd client/uni-app-user
npm install
npm run dev:h5
```

访问 `http://localhost:5173`

> 修改 `src/api/request.js` 中的 `BASE_URL` 指向后端地址

### 3. 启动管理端

```bash
cd client/admin-web
npm install
npm run dev
```

访问 `http://localhost:5174`（默认）

> 首次使用需初始化管理员账号：访问 `/init-admin` 页面

### 4. 配置 AI 功能

在管理端 **系统配置** 页面设置：
- AI 功能开关
- API 密钥（支持 SiliconFlow / DeepSeek / OpenAI 兼容接口）
- 每日调用限额
- 提示词模板

或通过环境变量：
```bash
export AI_API_KEY=your-api-key
export AI_API_BASE_URL=https://api.siliconflow.cn/v1
```

## 核心功能说明

### 热量目标计算

系统根据用户身体数据自动计算：

```
BMR（Mifflin-St Jeor 公式）
  → TDEE = BMR × 活动系数
  → 日热量目标 = TDEE × 目标系数（减脂 0.85 / 维持 1.00 / 增肌 1.15）
```

### 营养评分

根据当日实际摄入与目标值的偏差，计算 0-100 分的饮食评分，并在统计页面可视化展示。

### 个人代谢校准

通过多次体重记录与饮食数据的回归分析，反推个人真实代谢系数，修正公式 TDEE 的偏差。

### AI 饮食助手

- 基于用户 BMI、健康目标、当日营养素摄入生成上下文
- 支持 SSE 流式输出，打字机效果
- 每日调用次数限制，防止滥用
- 对话历史记录可查可清

## API 概览

| 模块 | 端点 | 说明 |
|------|------|------|
| 认证 | `POST /api/auth/login` | 登录 |
| 认证 | `POST /api/auth/register` | 注册 |
| 用户 | `GET/PUT /api/user/profile` | 查询/更新档案 |
| 食物 | `GET /api/foods` | 食物搜索 |
| 记录 | `GET/POST /api/meals` | 饮食记录 CRUD |
| 记录 | `POST /api/meals/batch` | 批量添加（食谱）|
| 记录 | `POST /api/meals/copy` | 跨天复制 |
| 统计 | `GET /api/stats/today` | 今日汇总+评分 |
| 统计 | `GET /api/stats/week` | 7天趋势 |
| 统计 | `GET /api/stats/analysis` | 超标分析+建议 |
| AI | `GET /api/ai/status` | AI 状态查询 |
| AI | `POST /api/ai/chat` | AI 问答 |
| AI | `POST /api/ai/chat/stream` | AI 流式问答 |

管理端 API（需管理员权限）位于 `/api/admin/` 路径下。

## License

MIT
