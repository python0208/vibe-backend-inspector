# Phase 3 + UI Polish 阶段交接文档

## 1. 当前项目整体进度

Vibe Backend Inspector 当前已完成：

1. Phase 0：项目骨架、后端健康检查、前后端基础打通。
2. Phase 1：项目配置 CRUD、工具自身 SQLite 存储、OpenAPI 地址测试、数据库连接测试基础实现。
3. 前端基础 UI 重构：统一 Layout、Sidebar、TopHeader、中英文切换、静态占位页。
4. Phase 2：OpenAPI 接口发现、Endpoint 持久化、API Map 真实数据接入。
5. Phase 3：SQLite 数据库结构发现、Database Map 真实数据接入。
6. UI Polish：整体前端视觉统一、响应式加固、页面完成度提升。

当前仍未实现：

1. Phase 4 接口真实请求测试。
2. Phase 5 数据库快照对比。
3. Phase 6 文件监听。
4. Phase 7 验收报告。
5. AI 分析能力。

## 2. Phase 0 完成内容

已完成：

1. 创建 monorepo 结构：
   - `backend/`
   - `frontend/`
   - `scripts/`
   - `docs/`
2. 后端 FastAPI 项目初始化。
3. 前端 React + Vite + TypeScript 项目初始化。
4. 后端提供 `/health` 健康检查接口。
5. 前端 Dashboard 可请求后端 `/health` 并显示连接状态。
6. Windows 启动脚本：
   - `scripts/dev_backend.bat`
   - `scripts/dev_frontend.bat`
   - `scripts/dev_all.bat`
   - 对应 PowerShell 脚本。
7. README 中已写本地启动方式。

## 3. Phase 1 完成内容

已完成：

1. 项目配置数据模型 `Project`。
2. 项目配置 CRUD：
   - 创建项目配置
   - 读取项目列表
   - 读取项目详情
   - 编辑项目配置
   - 删除项目配置
3. 使用工具自身 SQLite 存储项目配置。
4. ProjectSetup 页面可保存、读取、编辑、删除配置。
5. 支持配置：
   - 项目名称
   - 项目目录
   - 服务地址
   - OpenAPI 地址
   - 数据库类型
   - 数据库连接信息
   - 鉴权配置
6. OpenAPI 地址测试接口。
7. 数据库连接测试基础实现：
   - SQLite
   - MySQL
   - PostgreSQL
8. 密码和 token 返回前端时会脱敏。
9. 编辑保存脱敏值 `********` 时，后端会保留原 secret，避免覆盖真实值。

## 4. 前端基础 UI 重构完成内容

已完成：

1. 统一应用布局：
   - Sidebar
   - TopHeader
   - MainContent
2. Sidebar 包含：
   - Dashboard
   - Project Setup
   - API Map
   - Database Map
   - Test Runner
   - Reports
   - Settings
3. TopHeader 包含：
   - 项目选择器
   - 搜索框
   - Local Agent Online 状态
   - 中英文切换按钮
   - 用户区域
4. 新增公共 UI 组件：
   - `AppLayout`
   - `Sidebar`
   - `TopHeader`
   - `LanguageToggle`
   - `Card`
   - `PageHeader`
   - `StatCard`
   - `StatusBadge`
5. 新增页面：
   - `ApiMap`
   - `DatabaseMap`
   - `TestRunner`
   - `Reports`
   - `Settings`
6. TestRunner、Reports、Settings 当前仍主要是 UI 占位，不接真实业务。

## 5. Phase 2 OpenAPI 接口发现完成内容

已完成：

1. 新增 Endpoint 数据模型 `ApiEndpoint`。
2. 新增 Endpoint schema 和 service。
3. OpenAPI Discovery Service 支持：
   - 从项目配置中的 `openapi_url` 拉取 OpenAPI/Swagger JSON。
   - 自动尝试常见 OpenAPI 路径：
     - `/openapi.json`
     - `/swagger.json`
     - `/v3/api-docs`
     - `/api-docs`
     - `/docs-json`
   - 解析 `paths`。
   - 转换为统一 Endpoint 模型。
4. Endpoint 保存到工具自身 SQLite。
5. 重复同步 OpenAPI 时按 `project_id + method + path` 更新已有 Endpoint，不重复插入。
6. 同步时不覆盖测试状态字段：
   - `test_status`
   - `last_status_code`
   - `last_response_time_ms`
7. API Map 页面已接入真实 Endpoint 数据。
8. API Map 支持：
   - Sync OpenAPI
   - Auto Detect OpenAPI
   - path / summary 搜索
   - method 筛选
   - test status 筛选
   - 点击 endpoint 查看右侧详情
9. 右侧详情展示：
   - request schema
   - response schema
   - tags
   - operation_id
   - auth_required
   - query params
   - path params

## 6. Phase 3 SQLite 数据库结构发现完成内容

已完成：

1. 扩展数据库 adapter 基础接口：
   - `test_connection`
   - `inspect_schema`
2. 完整实现 `SqliteAdapter.inspect_schema`。
3. SQLite introspection 支持读取：
   - database_name
   - tables
   - columns
   - column type
   - nullable
   - default value
   - primary key
   - indexes
   - foreign keys
   - row_count
   - sample_rows
4. 新增 DatabaseSchema Pydantic schema：
   - `DatabaseSchema`
   - `DatabaseTable`
   - `DatabaseColumn`
   - `DatabaseIndex`
   - `DatabaseForeignKey`
   - `DatabaseInspectResponse`
5. 新增 Database router：
   - 项目级数据库连接测试
   - 项目级数据库结构读取
   - 项目级 schema 获取
6. MySQL/PostgreSQL 保留 adapter 接口，但 introspection 当前明确返回 Phase 3 未实现。
7. Database Map 页面已接入真实 SQLite schema 数据。
8. Database Map 支持：
   - Refresh Schema
   - Test Connection
   - 表名搜索
   - 左侧真实表列表
   - 中间轻量关系概览
   - 右侧选中表详情
9. 右侧表详情展示：
   - columns
   - indexes
   - foreign keys
   - sample rows
   - row_count

当前 Phase 3 默认不保存 schema snapshot，只做实时 introspection。快照保存和对比留给 Phase 5。

## 7. 本轮 UI Polish 完成内容

已完成：

1. 只修改前端文件，没有修改后端代码。
2. 优化整体浅色科技风背景：
   - radial glow
   - 轻量网格纹理
   - 更接近 SaaS Dashboard 的视觉层次
3. 收敛圆角：
   - Card 约 14px
   - 控件约 10px
   - 小元素约 8px
4. 收敛字号、间距和阴影，降低页面“过圆、过大、过散”的感觉。
5. Sidebar Polish：
   - 品牌区更明显
   - 导航选中状态更清晰
   - Local Agent 状态卡片更精致
6. TopHeader Polish：
   - 项目选择器、搜索框、Agent 状态、语言切换、用户区域高度和风格统一
   - 中英文切换按钮保持右上角清晰可见
7. Card/Button/Badge/Table/Code block 统一：
   - 更稳定的 hover
   - 更清晰的 method/status badge
   - 更像开发者工具的 schema/code 区域
8. Dashboard、ProjectSetup、API Map、Database Map 局部布局密度优化。
9. 响应式加固：
   - 中等宽度下 Header 和页面网格可换行
   - 窄屏下降低标题和控件字号
   - 中英文切换后减少溢出风险

## 8. 当前后端主要模块说明

### FastAPI 入口

`backend/app/main.py`

负责：

1. 初始化日志。
2. 初始化 SQLite 表。
3. 配置 CORS。
4. 注册 routers。

### Core

`backend/app/core/`

主要包含：

1. `config.py`：应用配置、SQLite URL、CORS 配置。
2. `database.py`：SQLAlchemy engine、Session、Base、init_db。
3. `exceptions.py`：通用异常。
4. `logging.py`：日志配置。

### Models

`backend/app/models/`

当前模型：

1. `Project`
2. `ApiEndpoint`

### Services

`backend/app/services/`

当前主要服务：

1. `project_service.py`
   - 项目配置 CRUD
   - secret 脱敏和保留
2. `openapi_service.py`
   - OpenAPI URL 测试
   - OpenAPI 文档拉取
   - 常见路径自动检测
   - paths 解析
   - endpoint 保存
3. `endpoint_service.py`
   - Endpoint 查询
   - Endpoint upsert
   - ORM 到 schema 转换
4. `database_service.py`
   - 数据库连接测试分发
   - 项目级数据库连接测试
   - 项目级数据库 schema inspect

### Database Adapters

`backend/app/adapters/database/`

当前 adapter：

1. `base.py`
   - 定义 `test_connection`
   - 定义 `inspect_schema`
2. `sqlite_adapter.py`
   - 完整连接测试
   - 完整 SQLite introspection
3. `mysql_adapter.py`
   - 连接测试
   - introspection 暂未实现
4. `postgres_adapter.py`
   - 连接测试
   - introspection 暂未实现

## 9. 当前前端主要页面、组件和布局说明

### 应用入口

`frontend/src/App.tsx`

负责：

1. 当前页面 state。
2. 当前语言 state。
3. 当前项目列表。
4. 当前选中项目。
5. 给页面传递公共 props。

当前页面切换仍使用 React state，没有引入 router。

### Layout

`frontend/src/components/layout/`

主要组件：

1. `AppLayout.tsx`
2. `Sidebar.tsx`
3. `TopHeader.tsx`
4. `LanguageToggle.tsx`

### UI Components

`frontend/src/components/ui/`

主要组件：

1. `Card`
2. `PageHeader`
3. `StatCard`
4. `StatusBadge`

### Pages

`frontend/src/pages/`

当前页面：

1. `Dashboard.tsx`
   - 健康检查
   - 项目摘要
   - 快捷操作
2. `ProjectSetup.tsx`
   - 项目配置 CRUD
   - OpenAPI 测试
   - 数据库连接测试
3. `ApiMap.tsx`
   - 真实 Endpoint 数据
   - OpenAPI 同步
   - 搜索/筛选/详情
4. `DatabaseMap.tsx`
   - 真实 SQLite schema 数据
   - schema inspect
   - 表搜索/详情
5. `TestRunner.tsx`
   - 当前为 UI 占位
6. `Reports.tsx`
   - 当前为 UI 占位
7. `Settings.tsx`
   - 当前主要用于展示语言设置和 Agent 状态

## 10. 当前已实现的后端接口列表

### Health

```text
GET /health
```

### Project

```text
GET    /api/projects
POST   /api/projects
GET    /api/projects/{project_id}
PUT    /api/projects/{project_id}
DELETE /api/projects/{project_id}
```

### Connection Tests

```text
POST /api/connection-tests/openapi
POST /api/connection-tests/database
```

### OpenAPI Discovery / Endpoint

```text
POST /api/projects/{project_id}/openapi/discover
POST /api/projects/{project_id}/openapi/auto-detect
GET  /api/projects/{project_id}/endpoints
GET  /api/projects/{project_id}/endpoints/{endpoint_id}
```

### Database

```text
POST /api/projects/{project_id}/database/test-connection
POST /api/projects/{project_id}/database/inspect
GET  /api/projects/{project_id}/database/schema
```

## 11. 当前已实现的前端页面列表

1. Dashboard
2. Project Setup
3. API Map
4. Database Map
5. Test Runner
6. Reports
7. Settings

其中：

1. Dashboard、Project Setup、API Map、Database Map 已接真实功能。
2. Test Runner、Reports 仍是后续阶段占位页。
3. Settings 当前主要展示语言和 Agent 相关 UI。

## 12. 当前中英文切换实现方式

实现位置：

```text
frontend/src/i18n/
```

文件：

1. `types.ts`
2. `en.ts`
3. `zh.ts`
4. `index.ts`

实现方式：

1. `Language = "zh" | "en"`。
2. `Messages` 类型约束中英文文案结构。
3. `App.tsx` 中维护当前语言 state。
4. 初始语言从 `localStorage.getItem("vbi-language")` 读取。
5. 切换后调用 `persistLanguage` 写回 localStorage。
6. 当前 `t = messages[language]` 作为 props 传给 Layout 和页面。
7. 目前没有引入第三方 i18n 库。

注意：

1. 新页面或新按钮必须同步更新 `Messages` 类型、`en.ts`、`zh.ts`。
2. 如果漏文案，TypeScript 通常会在 build 时发现。

## 13. 当前测试命令和测试结果

后端测试命令：

```bash
cd backend
pytest
```

最近结果：

```text
13 passed
```

前端构建命令：

```bash
cd frontend
npm run build
```

最近结果：

```text
tsc -b && vite build passed
```

说明：

1. UI Polish 最后一轮只运行了前端 `npm run build`，结果通过。
2. Phase 3 完成时后端 `pytest` 为 `13 passed`。

## 14. 已知 warning、限制或待优化问题

已知 warning：

1. 本机 Python 全局环境偶尔出现 `requests` 依赖版本 warning。
2. 本机 pytest 环境偶尔出现 `pytest-asyncio` 配置 warning。
3. 上述 warning 不影响当前项目测试通过。

当前限制：

1. Test Runner 还未接真实接口请求。
2. Reports 还未接真实报告数据。
3. Database Map 当前完整支持 SQLite；MySQL/PostgreSQL introspection 暂未实现。
4. Database schema 当前实时读取，不保存 snapshot。
5. OpenAPI schema 中 `$ref` 没有展开，只原样保存 schema。
6. API Map 筛选目前主要在前端本地完成。
7. 没有引入路由库，页面切换使用 React state。
8. 移动端可用性已有基础加固，但还没有做专门移动端导航抽屉。

待优化：

1. 通过浏览器截图逐页对比设计原型。
2. 优化 API Map / Database Map 大表格横向滚动体验。
3. Settings 页面接入真实配置项。
4. 为 schema snapshot 设计持久化表，以支持 Phase 5 快照对比。

## 15. 下一轮 Phase 4 建议：单接口测试执行与 Test Runner 真实数据接入

Phase 4 建议优先做“单接口手动测试”，不要一上来做批量自动测试。

建议目标：

1. 从已发现的 Endpoint 中选择一个接口。
2. 根据 Endpoint schema 生成基础请求表单。
3. 用户可编辑：
   - path params
   - query params
   - headers
   - JSON body
4. 支持请求方法：
   - GET
   - POST
   - PUT
   - PATCH
   - DELETE
5. 执行请求并记录：
   - request headers
   - request body
   - response status
   - response body
   - response headers
   - response time
   - error message
6. Test Runner 页面接入真实数据。
7. API Map 中可以从 endpoint 跳转到 Test Runner 并带上 endpoint。
8. PUT/PATCH/DELETE 执行前必须二次确认。

建议后端新增：

1. TestRun / TestResult 模型。
2. Test request schema。
3. Test service。
4. Test router。

建议前端：

1. `frontend/src/api/tests.ts`
2. `frontend/src/types/tests.ts`
3. 重构 `TestRunner.tsx`，从静态页面变为真实测试页面。

## 16. Phase 4 需要重点查看哪些文件

后端重点查看：

```text
backend/app/models/api_endpoint.py
backend/app/schemas/api_endpoint.py
backend/app/services/endpoint_service.py
backend/app/routers/openapi.py
backend/app/services/project_service.py
backend/app/models/project.py
backend/app/schemas/project.py
backend/app/main.py
```

前端重点查看：

```text
frontend/src/pages/TestRunner.tsx
frontend/src/pages/ApiMap.tsx
frontend/src/api/endpoints.ts
frontend/src/types/api.ts
frontend/src/App.tsx
frontend/src/i18n/types.ts
frontend/src/i18n/en.ts
frontend/src/i18n/zh.ts
frontend/src/styles/app.css
```

可能新增：

```text
backend/app/models/test_run.py
backend/app/schemas/test_run.py
backend/app/services/test_service.py
backend/app/routers/tests.py
backend/tests/test_runner.py
frontend/src/api/tests.ts
frontend/src/types/tests.ts
```

## 17. Phase 4 不应该做的内容

Phase 4 不应该做：

1. 不做数据库快照对比。
2. 不做报告系统。
3. 不做文件监听。
4. 不做 AI 分析。
5. 不做复杂 OAuth。
6. 不做文件上传。
7. 不做 WebSocket、SSE、GraphQL。
8. 不做批量破坏性接口测试。
9. 不默认执行 DELETE / PUT / PATCH。
10. 不修改用户项目代码。
11. 不接生产数据库。
12. 不重构已可用的 ProjectSetup、API Map、Database Map 主流程。

Phase 4 应保持范围小而稳：先做单接口真实请求测试和 Test Runner 数据接入。
