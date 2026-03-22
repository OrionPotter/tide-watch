# Tidewatch 项目说明

Tidewatch 是一个基于 FastAPI 的股票数据与投资组合管理项目，集成了持仓管理、自选监控、雪球组合、股票列表、行业板块以及 K 线导出等能力，并使用 PostgreSQL 作为主要数据存储。

## 功能概览

- 投资组合管理：维护持仓股票、成本价、持仓数量，并汇总组合数据。
- 监控股票管理：维护重点观察股票，支持启停监控与手动更新 K 线。
- 雪球组合管理：管理雪球组合列表并查看组合详情。
- 股票列表服务：查询股票基础信息、数量统计、关键词搜索与手动更新。
- 行业板块数据：获取最新行业板块数据。
- 工具接口：提供成本计算、K 线导出等辅助功能。
- 定时任务：支持自动更新 K 线数据与股票列表。

## 技术栈

- Python 3
- FastAPI
- Uvicorn
- PostgreSQL / asyncpg / psycopg2
- Jinja2
- APScheduler
- AkShare
- Pytest

## 项目结构

```text
Tidewatch/
├─ api/             # 路由层，定义对外 API
├─ services/        # 业务服务层
├─ repositories/    # 数据访问层
├─ models/          # 数据模型
├─ templates/       # 页面模板
├─ sql/             # 数据库初始化脚本
├─ test/            # 接口测试
├─ utils/           # 日志、数据库等公共工具
├─ app.py           # 应用入口
├─ requirements.txt # Python 依赖
└─ .env.example     # 环境变量示例
```

## 运行前准备

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制示例文件：

```bash
cp .env.example .env
```

Windows PowerShell 可使用：

```powershell
Copy-Item .env.example .env
```

建议至少配置以下参数：

| 变量名 | 说明 |
|---|---|
| `AKSHARE_TOKEN` | AkShare/相关数据源访问 Token |
| `PG_HOST` | PostgreSQL 主机 |
| `PG_PORT` | PostgreSQL 端口 |
| `PG_DATABASE` | 数据库名 |
| `PG_USER` | 数据库用户名 |
| `PG_PASSWORD` | 数据库密码 |
| `PG_MIN_CONN` | 连接池最小连接数 |
| `PG_MAX_CONN` | 连接池最大连接数 |
| `AUTO_UPDATE_KLINE` | 是否自动更新 K 线 |
| `UPDATE_ALL_STOCKS` | 是否更新全部股票 K 线 |
| `KLINE_UPDATE_CONCURRENT` | K 线更新并发数 |
| `AUTO_UPDATE_STOCK_LIST` | 是否自动更新股票列表 |
| `AUTO_UPDATE_INDUSTRY_BOARD` | 是否自动更新行业板块 |

### 3. 初始化数据库

先创建 PostgreSQL 数据库，再执行：

```bash
psql -U postgres -d <your_database> -f sql/init_postgres.sql
```

## 启动项目

### 开发方式

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 5000
```

### 直接运行

```bash
python app.py
```

启动后可访问：

- 首页：`/`
- 管理页：`/admin`
- 监控页：`/monitor`
- 工具页：`/tools`
- 雪球页：`/xueqiu`
- 行业板块页：`/industry-board`

## 主要接口

### 投资组合

- `GET /api/portfolio`
- `POST /api/portfolio`
- `PUT /api/portfolio/{code}`
- `DELETE /api/portfolio/{code}`

### 监控股票

- `GET /api/monitor`
- `GET /api/monitor/stocks`
- `POST /api/monitor/stocks`
- `PUT /api/monitor/stocks/{code}`
- `DELETE /api/monitor/stocks/{code}`
- `POST /api/monitor/stocks/{code}/toggle`
- `POST /api/monitor/update-kline`

### 管理后台

- `GET /api/admin/stocks`
- `POST /api/admin/stocks`
- `PUT /api/admin/stocks/{code}`
- `DELETE /api/admin/stocks/{code}`
- `GET /api/admin/monitor-stocks`
- `POST /api/admin/monitor-stocks`
- `PUT /api/admin/monitor-stocks/{code}`
- `DELETE /api/admin/monitor-stocks/{code}`
- `POST /api/admin/monitor-stocks/{code}/toggle`
- `GET /api/admin/xueqiu-cubes`
- `POST /api/admin/xueqiu-cubes`
- `PUT /api/admin/xueqiu-cubes/{cube_symbol}`
- `DELETE /api/admin/xueqiu-cubes/{cube_symbol}`
- `POST /api/admin/xueqiu-cubes/{cube_symbol}/toggle`

### 股票列表

- `GET /api/stock-list`
- `GET /api/stock-list/count`
- `GET /api/stock-list/{code}`
- `GET /api/stock-list/search/{keyword}`
- `POST /api/stock-list/update`

### 雪球组合

- `GET /api/xueqiu`
- `GET /api/xueqiu/{cube_symbol}`

### 行业板块

- `GET /api/industry-board/latest`

### 工具接口

- `POST /api/tools/calculate-cost`
- `GET /api/tools/export-kline/stocks`
- `POST /api/tools/export-kline`

## 定时任务说明

应用启动时会初始化数据库连接池，并启动后台任务与调度器。

当前代码中默认包含以下定时任务：

- 每日 `15:05` 自动更新 K 线数据（由 `AUTO_UPDATE_KLINE` 控制）
- 每日 `12:00` 自动更新股票列表（由 `AUTO_UPDATE_STOCK_LIST` 控制）

此外，应用启动时还会触发一次后台 K 线更新任务。

## 测试

运行全部测试：

```bash
pytest
```

运行单个测试文件：

```bash
pytest test/test_portfolio_routes.py
```

更多测试说明可参考 `test/README.md`。

## 注意事项

- 项目依赖 PostgreSQL，未完成数据库初始化时接口可能无法正常使用。
- 若未正确配置 `AKSHARE_TOKEN`，部分行情或外部数据接口可能失败。
- 自动任务会在应用启动时执行，建议先确认数据库和外部数据源配置可用。

## 后续建议

- 补充接口鉴权与权限控制。
- 增加部署说明（如 Docker / systemd / Nginx）。
- 为核心服务层补充更多单元测试与集成测试。
