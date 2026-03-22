# Tidewatch

Tidewatch 是一个基于 FastAPI 的股票观察与持仓管理项目，围绕三类核心场景构建：

- 持仓管理：维护当前持仓、成本、市值与盈亏
- 监控看板：对监控股票做估值、趋势、技术状态与动作标签判断
- 数据工具：提供 K 线更新、导出、股票列表维护等操作

当前前端页面已经收敛为一个较轻量的结构，重点保留首页、监控、工具、参考组合和管理后台。

## 当前功能

- 首页仪表盘
  - 展示总市值、累计盈亏、年度股息、股息率
  - 展示今日重点股票
  - 展示持仓预览
- 监控看板
  - 汇总监控股票的估值、趋势、技术状态、动作标签和评分
  - 支持按全部、持仓、接近买点、风险筛选
  - 支持触发 K 线更新
- 管理后台
  - 管理持仓
  - 管理监控股票
  - 管理雪球组合
  - 管理股票列表
- 工具页
  - 成本计算
  - K 线导出
  - 其它辅助工具
- 雪球组合页
  - 查看雪球组合调仓记录
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
├─ templates/           # Jinja2 页面模板
├─ test/                # pytest 测试
├─ utils/               # 公共工具
├─ app.py               # 应用入口
└─ requirements.txt
```

## 页面路由

- `/`：首页
- `/monitor`：监控看板
- `/tools`：工具页
- `/xueqiu`：雪球组合
- `/admin`：管理后台

## API 路由

- `/api/dashboard`
- `/api/portfolio`
- `/api/monitor`
- `/api/admin`
- `/api/tools`
- `/api/xueqiu`
- `/api/stock-list`

## 环境变量

参考 [`.env.example`](C:\Users\86158\Desktop\Tidewatch\.env.example)：

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

- `AKSHARE_TOKEN`
  - 用于部分数据抓取
- `PG_*`
  - PostgreSQL 连接配置
- `AUTO_UPDATE_KLINE`
  - 启动时和定时任务是否自动更新 K 线
- `UPDATE_ALL_STOCKS`
  - K 线更新时是否更新所有股票
- `KLINE_UPDATE_CONCURRENT`
  - K 线更新并发数
- `AUTO_UPDATE_STOCK_LIST`
  - 是否自动更新股票列表

## 数据库初始化

初始化脚本在 [sql/init_postgres.sql](C:\Users\86158\Desktop\Tidewatch\sql\init_postgres.sql)。

初始化方式示例：

```sql
sql/init_postgres.sql
```

脚本当前会创建这些核心表：

- `portfolio`
- `monitor_stocks`
- `monitor_data_cache`
- `stock_kline_data`
- `kline_update_log`
- `xueqiu_cubes`
- `stock_list`

注意：

- 初始化脚本里仍包含历史 `alerts` 表定义，但项目当前已经移除了提醒页面、提醒路由和提醒服务。
- 如果你要继续清理，可以把 `sql/init_postgres.sql` 中与 `alerts` 相关的建表和索引一起删掉。

## 本地运行

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 配置环境变量

```bash
copy .env.example .env
```

然后按实际环境填写数据库与 token。

3. 初始化数据库

执行 [sql/init_postgres.sql](C:\Users\86158\Desktop\Tidewatch\sql\init_postgres.sql)。

4. 启动服务

```bash
python app.py
```

默认监听：

```text
http://localhost:5000
```

## 测试

```bash
pytest
```

当前仓库中保留了页面/API 相关基础测试，例如：

- dashboard
- monitor
- portfolio
- admin
- tools
- stock-list
- xueqiu

## 首页说明

首页当前只保留两块主内容：

- 今日重点股票
- 持仓预览

顶部指标说明：

- 总市值：当前持仓总价值
- 累计盈亏：按最新价格估算
- 年度股息：按当前持仓测算
- 股息率：`年度股息 / 总市值`

## 监控页规则

监控页的估值、趋势、技术、动作标签、风险等级由 [services/monitor_service.py](C:\Users\86158\Desktop\Tidewatch\services\monitor_service.py) 和 [services/monitor_scoring_service.py](C:\Users\86158\Desktop\Tidewatch\services\monitor_scoring_service.py) 共同决定。

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
  - 按不同周期均线排列判断 `多头 / 空头 / 震荡 / 未知`
- `action_label`
  - 高风险：`风险`
  - 高估：`高估谨慎`
  - 低估且技术为加仓：`可分批`
  - 技术为加仓，或估值正常/低估且趋势非空头：`接近买点`

## 已移除内容

当前版本已经移除提醒功能：

- 页面：`/alerts`
- 页面模板：`templates/alerts.html`
- API：`/api/alerts`
- 路由注册与对应 service / repository / model

如果你要继续做数据库层清理，优先检查：

- [sql/init_postgres.sql](C:\Users\86158\Desktop\Tidewatch\sql\init_postgres.sql) 中的 `alerts` 表

## 后续建议

- 清理 SQL 初始化脚本中的历史 `alerts` 定义
- 修正仓库中残留的少量乱码文案
- 增加 README 中的页面截图或接口示例
- 补充部署说明，例如 `uvicorn` 或 `systemd`/Windows 服务启动方式
