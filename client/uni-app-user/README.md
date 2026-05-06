# UniApp用户端开发说明

## 运行命令

```bash
cd uni-app-user

# H5开发模式
npm run dev:h5

# H5打包
npm run build:h5

# 微信小程序开发
npm run dev:mp-weixin

# 微信小程序打包
npm run build:mp-weixin

# App开发（需要HBuilderX）
npm run dev:app
```

## 项目结构

```
uni-app-user/
├── src/
│   ├── api/                 # API请求封装
│   │   ├── request.js       # 统一请求封装
│   │   ├── auth.js          # 认证API
│   │   ├── user.js          # 用户档案API
│   │   ├── food.js          # 食物库API
│   │   ├── meal.js          # 饮食记录API
│   │   ├── stats.js         # 统计API
│   │   └── ai.js            # AI助手API
│   ├── pages/
│   │   ├── index/           # 首页(今日概览)
│   │   ├── record/          # 饮食记录
│   │   ├── foods/           # 食物库
│   │   ├── stats/           # 统计分析
│   │   ├── ai/              # AI助手
│   │   ├── mine/            # 个人中心
│   │   └── login/           # 登录/注册
│   ├── store/               # Pinia状态管理
│   ├── utils/               # 工具函数
│   └── static/              # 静态资源
├── pages.json               # 页面路由配置
└── manifest.json            # 应用配置
```

## 后端API地址配置

修改 `src/api/request.js` 中的 `BASE_URL`：

```javascript
const BASE_URL = 'http://127.0.0.1:5000'  // 开发环境
// const BASE_URL = 'https://your-domain.com'  // 生产环境
```

## 后续优化

### 1. 添加TabBar图标

将图标文件放到 `src/static/tabbar/` 目录，然后修改 `pages.json`：

```json
{
  "pagePath": "pages/index/index",
  "text": "首页",
  "iconPath": "static/tabbar/home.png",
  "selectedIconPath": "static/tabbar/home-active.png"
}
```

图标要求：
- 格式：PNG
- 尺寸：81x81px（推荐）
- 大小：<40KB

### 2. 添加应用Logo

将 Logo 图片放到 `src/static/logo.png`，建议尺寸 200x200px。

### 3. 集成uCharts图表

统计页面目前使用简化的柱状图，可集成 uCharts 增强可视化：

```bash
# 通过 uni_modules 安装（推荐在HBuilderX中操作）
# 或手动下载 qiun-data-charts 组件
```

### 4. 添加下拉刷新

在 `pages.json` 中为页面启用下拉刷新：

```json
{
  "path": "pages/index/index",
  "style": {
    "enablePullDownRefresh": true
  }
}
```

### 5. 微信小程序适配

1. 在 `manifest.json` 中配置小程序 AppID
2. 注意 API 域名需要在小程序后台配置白名单
3. 部分 H5 API 在小程序中可能需要替换

## 已知问题

1. TabBar 暂未配置图标，仅显示文字
2. 统计页面图表使用简化实现，建议集成 uCharts
3. 需要配合后端 API 进行联调测试

## 依赖版本

- Vue 3.4
- Pinia 2.x
- dayjs
- @dcloudio/uni-ui
- sass
