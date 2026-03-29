# Tidewatch

Tidewatch 是一个基于 FastAPI 的股票观察、监控与组合管理项目，围绕以下几个核心场景构建：

- 持仓管理：维护当前持仓、成本、估值与盈亏
- 监控看板：对监控股票做估值、趋势、技术状态与动作标签判断
- 自定义组合：按组合维度管理多套持仓，并进入详情页查看持仓明细
- 复盘与分析：记录交易复盘，生成价格行为分析报告
- 数据工具：提供 K 线更新、导出、成本计算、股票列表维护等操作

## 当前功能

- 首页仪表盘
  - 展示总市值、累计盈亏、年度股息、股息率
  - 展示重点股票
  - 展示持仓预览
- 监控看板
  - 汇总监控股票的估值、趋势、技术状态、动作标签和评分
  - 支持按全部、持仓、接近买点、风险筛选
  - 支持触发 K 线更新
- 自定义组合
  - 组合列表页展示组合级别概览信息
  - 组合详情页展示持仓明细，并支持增删持仓
  - 支持创建和删除组合
- 分析与复盘
  - 分析报告列表、详情、创建、删除
  - 复盘记录列表、详情、创建、编辑、删除
- 学习页面
  - 学习文章列表
  - 文章详情读取本地 Markdown 内容
- 管理后台
  - 管理持仓
  - 管理监控股票
  - 管理股票列表
- 工具页
  - 成本计算
  - K 线导出
- 定时任务
  - 自动更新 K 线
  - 自动更新股票列表

## 技术栈

- Python 3.10+
- FastAPI
- Uvicorn
- PostgreSQL
- asyncpg / psycopg2-binary
- Jinja2
- APScheduler
- pandas / akshare / aiohttp

## 项目结构

```text
Tidewatch/
├─ api/                 # API 路由
├─ models/              # 数据模型
├─ repositories/        # 数据访问层
├─ schemas/             # 请求/响应 schema
├─ services/            # 业务逻辑
├─ sql/                 # PostgreSQL 初始化脚本
├─ static/              # 静态资源
├─ templates/           # 页面模板
├─ test/                # pytest 测试
├─ utils/               # 公共工具
├─ learn/               # 学习文章与索引
├─ app.py               # 应用入口
└─ requirements.txt
```

## 页面路由

- `/`：首页
- `/monitor`：监控页
- `/tools`：工具页
- `/portfolios`：组合列表页
- `/portfolios/{portfolio_id}`：组合详情页
- `/analysis`：分析列表页
- `/analysis/new`：新建分析页
- `/analysis/{report_id}`：分析详情页
- `/recaps`：复盘列表页
- `/recaps/new`：新建复盘页
- `/recaps/{record_id}`：复盘详情页
- `/recaps/{record_id}/edit`：复盘编辑页
- `/learn`：学习列表页
- `/learn/{slug}`：学习详情页
- `/admin`：管理后台

## API 路由

- `/api/dashboard`
- `/api/analysis`
- `/api/recaps`
- `/api/learn`
- `/api/portfolio`
- `/api/portfolios`
- `/api/monitor`
- `/api/admin`
- `/api/tools`
- `/api/stock-list`

## 环境变量

参考 [.env.example](/C:/Users/86158/Desktop/Tidewatch/.env.example)：

```env
AKSHARE_TOKEN=your_akshare_token_here

PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=xxxx
PG_USER=postgres
PG_PASSWORD=xxxx

AUTO_UPDATE_KLINE=true
UPDATE_ALL_STOCKS=false
KLINE_UPDATE_CONCURRENT=50
AUTO_UPDATE_STOCK_LIST=true
AUTO_UPDATE_INDUSTRY_BOARD=true
```

说明：

- `AKSHARE_TOKEN`：用于部分数据抓取
- `PG_*`：PostgreSQL 连接配置
- `AUTO_UPDATE_KLINE`：启动时和定时任务是否自动更新 K 线
- `UPDATE_ALL_STOCKS`：K 线更新时是否更新全部股票
- `KLINE_UPDATE_CONCURRENT`：K 线更新并发数
- `AUTO_UPDATE_STOCK_LIST`：是否自动更新股票列表

## 数据库初始化

初始化脚本位于 [sql/init_postgres.sql](/C:/Users/86158/Desktop/Tidewatch/sql/init_postgres.sql)。

当前核心表包括：

- `portfolio`
- `monitor_stocks`
- `monitor_data_cache`
- `stock_kline_data`
- `kline_update_log`
- `stock_list`
- `custom_portfolios` 相关表
- `analysis` / `recaps` 相关表

如果你的本地库结构早于当前版本，建议先对照 SQL 脚本确认表结构是否一致。

## 本地运行

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 配置环境变量

```bash
copy .env.example .env
```

然后按实际环境填写数据库和 token。

3. 初始化数据库

执行 [sql/init_postgres.sql](/C:/Users/86158/Desktop/Tidewatch/sql/init_postgres.sql)。

4. 启动服务

```bash
python app.py
```

默认访问地址：

```text
http://localhost:5000
```

## 测试

运行测试：

```bash
pytest
```

当前测试已覆盖主要服务端暴露接口，包括：

- dashboard
- analysis
- recaps
- learn
- portfolio
- portfolios
- monitor
- admin
- tools
- stock-list

最近一次补齐后，接口测试已覆盖主要成功路径、常见失败路径与部分边界分支。

## 首页说明

首页当前保留两块主要内容：

- 今日重点股票
- 持仓预览

顶部指标说明：

- 总市值：当前持仓总估值
- 累计盈亏：按最新价格估算
- 年度股息：按当前持仓测算
- 股息率：`年度股息 / 总市值`

## 监控规则摘要

监控页的估值、趋势、技术、动作标签、风险等级由 [services/monitor_service.py](/C:/Users/86158/Desktop/Tidewatch/services/monitor_service.py) 和 [services/monitor_scoring_service.py](/C:/Users/86158/Desktop/Tidewatch/services/monitor_scoring_service.py) 共同决定。

核心规则摘要：

- `valuation_status`
  - 现价低于合理下限：`低估`
  - 现价高于合理上限：`高估`
  - 否则：`正常`
- `technical_status`
  - 现价低于 `ema144` / `ema188` 下沿：`破位`
  - 现价落在 `ema144` 与 `ema188` 之间：`加仓`
  - 否则：`无信号`
- `trend`
  - 按不同周期均线排列判断：`多头 / 空头 / 震荡 / 未知`
- `action_label`
  - 高风险：`风险`
  - 高估：`高估谨慎`
  - 低估且技术为加仓：`可分批`
  - 技术为加仓，或估值正常/低估且趋势非空头：`接近买点`

## 说明

- 组合列表页当前只展示组合级别汇总信息，具体持仓操作放在组合详情页。
- 项目中仍有少量历史文案或编码问题，后续可以继续逐步清理。
