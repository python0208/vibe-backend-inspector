可以。你现在要给 Codex 的不是一句“帮我做个项目”，而是一份**可执行的项目规则文档 + 分阶段计划提示词**。

Codex 官方文档说明，Codex 会在开始工作前读取 `AGENTS.md`，可以用它给项目提供持续性的开发规范和上下文；复杂任务也适合使用类似 `PLANS.md / ExecPlan` 的方式先制定计划再实现。官方最佳实践也建议提示词包含 Goal、Context、Constraints、Done when 四类信息。([OpenAI 开发者][1])

下面这份你可以直接复制为项目根目录的：

```text
AGENTS.md
```

---

````markdown
# AGENTS.md

## 项目名称

Vibe Backend Inspector

## 项目定位

本项目是一个面向 AI Vibe Coding 后端开发过程的本地可视化验收工具。

目标不是替代 Postman、Swagger、Navicat、DBeaver 或数据库管理工具，而是为使用 Codex、Cursor、Claude Code、OpenCode、Windsurf、Trae 等 AI 编程工具进行后端开发的开发者提供一个“后端工程雷达”。

它需要帮助开发者在 AI 撰写后端项目的过程中和完成一轮开发后，清晰看到：

1. AI 新增或修改了哪些后端文件。
2. 当前项目暴露了哪些接口。
3. 接口文档是否可以被识别。
4. 当前数据库创建了哪些表。
5. 每张表有哪些字段、主键、外键、索引和样例数据。
6. 一轮接口测试是否通过。
7. 接口请求前后数据库是否发生了预期变化。
8. 接口返回结果、状态码、响应时间、错误信息是否清晰。
9. 本轮开发是否存在明显缺失、文档不一致、数据库未迁移、安全风险或异常处理不足。

一句话产品说明：

> AI 写后端，我帮你看清它到底写成了什么。

---

## 第一版产品边界

第一版不追求全语言、全框架、全自动。

第一版采用：

- 用户配置 40%
- 程序自动识别 45%
- AI 辅助分析 15%

第一版优先支持任何能够提供 OpenAPI / Swagger 文档的后端项目。

第一版重点支持：

1. OpenAPI / Swagger 接口发现
2. SQLite / MySQL / PostgreSQL 数据库连接与结构读取
3. 本地项目目录监听
4. 接口列表可视化
5. 数据库表结构可视化
6. 基础接口自动测试
7. 测试前后数据库快照对比
8. 单轮开发验收报告

第一版不做：

1. 不做所有框架源码级解析
2. 不做复杂微服务治理
3. 不做生产数据库实时 binlog / WAL 监听
4. 不做自动修复代码
5. 不做完整性能压测
6. 不做深度安全扫描
7. 不做多人协作
8. 不做云端部署
9. 不做文件上传、WebSocket、SSE、复杂 OAuth、支付回调等复杂接口场景

---

## 推荐技术栈

采用本地 Web Dashboard + Local Agent 架构。

### 后端 Agent

使用 Python + FastAPI 实现本地 Agent。

原因：

1. Python 适合做文件监听、接口请求、数据库 introspection、报告生成。
2. FastAPI 适合快速提供本地 API 给前端 Dashboard 使用。
3. httpx、SQLAlchemy、watchdog、pydantic、openapi-schema-pydantic 等生态成熟。
4. 后续容易扩展不同数据库、不同框架适配器。

### 前端 Dashboard

使用 React + Vite + TypeScript 实现。

推荐 UI：

1. React
2. Vite
3. TypeScript
4. TailwindCSS
5. shadcn/ui 或 Ant Design
6. Recharts 或 ECharts 用于统计图
7. React Flow 用于后续 ER 图和接口流程图

### 本地状态存储

使用 SQLite 存储工具自身的数据：

1. 项目配置
2. 扫描历史
3. 接口快照
4. 数据库快照
5. 测试记录
6. 验收报告

注意：这是工具自身的数据库，不是被测试项目的业务数据库。

---

## 项目目录建议

请按照以下结构组织项目：

```text
vibe-backend-inspector/
  AGENTS.md
  README.md
  docs/
    PRODUCT_REQUIREMENTS.md
    ARCHITECTURE.md
    DEV_FLOW.md
    TESTING_RULES.md
  backend/
    app/
      main.py
      core/
        config.py
        logging.py
        exceptions.py
      models/
        project.py
        api_endpoint.py
        db_schema.py
        test_run.py
        report.py
      schemas/
        project.py
        api_endpoint.py
        db_schema.py
        test_run.py
        report.py
      services/
        project_service.py
        openapi_service.py
        database_service.py
        watcher_service.py
        test_service.py
        snapshot_service.py
        report_service.py
      adapters/
        api_discovery/
          base.py
          openapi_adapter.py
          fallback_adapter.py
        database/
          base.py
          sqlite_adapter.py
          mysql_adapter.py
          postgres_adapter.py
        auth/
          base.py
          bearer_token.py
          basic_auth.py
      routers/
        projects.py
        discovery.py
        database.py
        tests.py
        reports.py
      utils/
        file_utils.py
        diff_utils.py
        http_utils.py
        schema_utils.py
    tests/
    requirements.txt
    pyproject.toml
  frontend/
    src/
      main.tsx
      App.tsx
      api/
        client.ts
        projects.ts
        discovery.ts
        database.ts
        tests.ts
        reports.ts
      pages/
        ProjectSetup.tsx
        Dashboard.tsx
        ApiMap.tsx
        DatabaseMap.tsx
        TestRunner.tsx
        ReportView.tsx
      components/
        layout/
        project/
        api/
        database/
        tests/
        reports/
      types/
        project.ts
        api.ts
        database.ts
        tests.ts
        report.ts
    package.json
    vite.config.ts
  scripts/
    dev_backend.sh
    dev_frontend.sh
    dev_all.sh
````

Windows 环境需要额外提供 `.bat` 或 PowerShell 启动脚本：

```text
scripts/
  dev_backend.bat
  dev_frontend.bat
  dev_all.bat
```

---

## 核心业务流程

### 1. 创建项目配置

用户在前端填写：

1. 项目名称
2. 项目目录
3. 后端启动命令
4. 服务地址
5. OpenAPI / Swagger 地址
6. 数据库类型
7. 数据库连接信息
8. 鉴权配置

OpenAPI 地址允许用户手动填写，也允许系统自动尝试检测：

```text
/openapi.json
/swagger.json
/v3/api-docs
/api-docs
/docs-json
```

### 2. 项目监听

工具监听用户选择的后端项目目录，记录：

1. 新增文件
2. 修改文件
3. 删除文件
4. 重点文件变化

重点关注：

```text
controller
router
routes
api
model
models
entity
entities
schema
schemas
migration
migrations
config
.env
pom.xml
build.gradle
package.json
requirements.txt
pyproject.toml
```

第一版只需要做到文件变化记录，不需要完整源码语义分析。

### 3. 接口发现

第一版接口发现优先基于 OpenAPI / Swagger。

流程：

1. 请求用户配置的 OpenAPI 地址。
2. 如果未填写，则自动尝试常见路径。
3. 获取 JSON 后解析 paths。
4. 转换为工具内部统一 Endpoint 模型。
5. 前端展示接口地图。

Endpoint 模型至少包含：

```json
{
  "id": "string",
  "method": "GET | POST | PUT | PATCH | DELETE",
  "path": "/api/users",
  "summary": "string",
  "description": "string",
  "operation_id": "string",
  "query_params": [],
  "path_params": [],
  "request_body_schema": {},
  "response_schema": {},
  "auth_required": false,
  "source": "openapi",
  "test_status": "untested | passed | failed | skipped"
}
```

如果 OpenAPI 不可用，第一版可以提示：

```text
未检测到 OpenAPI / Swagger 文档。
请先配置接口文档地址，或让后端项目开启 OpenAPI / Swagger。
源码扫描适配器将在后续版本支持。
```

不要在第一版强行做 Java、Node、Python 的源码路由扫描。

### 4. 数据库发现

第一版支持：

1. SQLite
2. MySQL
3. PostgreSQL

数据库服务需要读取：

1. 数据库名
2. 表名
3. 字段名
4. 字段类型
5. 是否可空
6. 默认值
7. 主键
8. 外键
9. 索引
10. 每张表前 20 条样例数据
11. 每张表数据量

数据库内部统一模型：

```json
{
  "database_type": "sqlite | mysql | postgres",
  "database_name": "string",
  "tables": [
    {
      "name": "users",
      "row_count": 10,
      "columns": [
        {
          "name": "id",
          "type": "integer",
          "nullable": false,
          "default": null,
          "primary_key": true
        }
      ],
      "indexes": [],
      "foreign_keys": [],
      "sample_rows": []
    }
  ]
}
```

数据库连接信息必须加密或至少不明文展示完整密码。前端展示时密码字段必须隐藏。

### 5. 接口测试

第一版接口测试支持：

1. GET
2. POST
3. PUT
4. PATCH
5. DELETE
6. query 参数
7. path 参数
8. JSON body
9. Bearer Token
10. Basic Auth
11. 自定义 Header

暂不支持：

1. 文件上传
2. WebSocket
3. SSE
4. GraphQL
5. 复杂 OAuth
6. 验证码
7. 支付回调
8. 多租户权限链路

测试流程：

1. 读取接口列表。
2. 根据 OpenAPI schema 生成基础测试参数。
3. 如果接口需要鉴权，先执行用户配置的登录流程。
4. 请求接口。
5. 记录请求参数、请求头、状态码、响应体、响应时间。
6. 测试前读取数据库快照。
7. 测试后读取数据库快照。
8. 对比数据库表行数和样例数据变化。
9. 生成测试结果。

测试结果模型：

```json
{
  "endpoint_id": "string",
  "method": "POST",
  "path": "/api/users",
  "status": "passed | failed | skipped",
  "http_status": 200,
  "response_time_ms": 120,
  "request_headers": {},
  "request_body": {},
  "response_body": {},
  "error_message": "string",
  "db_changes": {
    "tables_changed": [],
    "row_count_diff": {}
  }
}
```

### 6. 数据库快照对比

第一版做轻量快照，不做数据库底层日志监听。

快照内容：

1. 表数量
2. 字段结构
3. 每张表行数
4. 最近样例数据

接口测试前后对比：

1. 哪些表新增了数据
2. 哪些表删除了数据
3. 哪些表行数变化
4. 哪些表结构发生变化

如果 POST / PUT / DELETE 接口调用后数据库完全无变化，需要标记为“疑似无效操作”，但不能直接判断为错误，需要提示用户确认业务逻辑。

### 7. 验收报告

每轮测试结束后生成报告。

报告包括：

1. 项目基本信息
2. 本轮文件变化摘要
3. 接口总数
4. 已测试接口数
5. 通过接口数
6. 失败接口数
7. 跳过接口数
8. 数据库表数量
9. 数据库变化摘要
10. 严重问题
11. 中等问题
12. 建议优化
13. 原始请求与响应记录

报告可以先支持 Markdown 导出，后续再支持 PDF。

---

## 页面设计要求

第一版前端至少包含 6 个页面。

### 1. ProjectSetup

用于创建或编辑项目配置。

必须包含：

1. 项目名称
2. 项目目录
3. 服务地址
4. OpenAPI 地址
5. 数据库类型
6. 数据库连接表单
7. 鉴权配置
8. 测试连接按钮
9. 保存配置按钮

### 2. Dashboard

项目总览页。

展示：

1. 当前项目名称
2. 服务运行状态
3. OpenAPI 检测状态
4. 数据库连接状态
5. 接口数量
6. 数据表数量
7. 最近一次测试通过率
8. 最近文件变化

### 3. ApiMap

接口地图页。

表格展示：

1. 方法
2. 路径
3. 摘要
4. 是否需要鉴权
5. 测试状态
6. 最近状态码
7. 响应时间
8. 操作按钮

支持点击接口进入详情。

### 4. DatabaseMap

数据库地图页。

展示：

1. 表列表
2. 字段结构
3. 主键
4. 外键
5. 索引
6. 数据量
7. 样例数据

### 5. TestRunner

接口测试页。

展示：

1. 选择接口
2. 请求参数
3. 请求 Header
4. 请求 Body
5. 执行测试按钮
6. 返回状态码
7. 返回 JSON
8. 响应时间
9. 数据库变化

### 6. ReportView

验收报告页。

展示：

1. 本轮测试概览
2. 通过 / 失败 / 跳过统计
3. 问题列表
4. 数据库变化
5. 修复建议
6. 导出 Markdown

---

## 开发优先级

请严格按照以下阶段开发。

### Phase 0：项目骨架

完成：

1. 创建 monorepo 结构
2. 后端 FastAPI 项目初始化
3. 前端 Vite React TypeScript 初始化
4. 配置基础 lint / format
5. 提供开发启动脚本
6. README 写清楚启动方式

完成标准：

1. 后端可以启动。
2. 前端可以启动。
3. 前端可以访问后端健康检查接口。
4. README 中有明确本地运行步骤。

### Phase 1：项目配置模块

完成：

1. 项目配置表单
2. 后端项目配置 CRUD
3. 本地 SQLite 存储配置
4. 数据库连接测试
5. OpenAPI 地址测试

完成标准：

1. 用户可以创建项目配置。
2. 用户可以保存数据库连接。
3. 用户可以测试服务地址。
4. 用户可以测试 OpenAPI 地址。
5. 用户可以测试数据库连接。

### Phase 2：OpenAPI 接口发现

完成：

1. OpenAPI JSON 拉取
2. paths 解析
3. Endpoint 统一模型
4. 接口列表展示
5. 接口详情展示

完成标准：

1. 可以读取 FastAPI `/openapi.json`。
2. 可以读取 Spring Boot `/v3/api-docs`。
3. 可以将接口展示在 ApiMap。
4. 每个接口能显示 method、path、summary、request schema、response schema。

### Phase 3：数据库结构发现

完成：

1. SQLite introspection
2. MySQL introspection
3. PostgreSQL introspection
4. 表结构展示
5. 样例数据展示

完成标准：

1. 可以连接 SQLite。
2. 可以连接 MySQL。
3. 可以连接 PostgreSQL。
4. DatabaseMap 可以展示表、字段、主键、索引、样例数据。

### Phase 4：接口测试执行

完成：

1. 根据 Endpoint 生成基础请求
2. 支持 GET / POST / PUT / PATCH / DELETE
3. 支持 query 参数
4. 支持 path 参数
5. 支持 JSON body
6. 支持自定义 Header
7. 支持 Bearer Token
8. 展示请求与响应结果

完成标准：

1. 用户可以点击某个接口执行测试。
2. 可以看到请求参数、状态码、响应体、响应时间。
3. 测试失败时能看到错误原因。

### Phase 5：数据库快照对比

完成：

1. 测试前数据库快照
2. 测试后数据库快照
3. 表行数变化对比
4. 样例数据变化对比
5. 在测试结果中展示数据库变化

完成标准：

1. POST 接口测试后能看到相关表行数变化。
2. DELETE 接口测试后能看到相关表行数变化。
3. 数据库无变化时给出提示，但不直接判定错误。

### Phase 6：文件监听与开发过程记录

完成：

1. 监听项目目录文件变化
2. 记录新增 / 修改 / 删除文件
3. 重点识别 controller / router / model / entity / migration / config 文件
4. Dashboard 展示最近变化
5. ReportView 展示本轮文件变化摘要

完成标准：

1. AI 或开发者修改项目文件后，Dashboard 可以看到变化。
2. 一轮验收报告中包含文件变化摘要。

### Phase 7：验收报告

完成：

1. 测试统计
2. 接口通过率
3. 数据库变化摘要
4. 失败接口列表
5. 风险提示
6. Markdown 导出

完成标准：

1. 用户可以点击“生成验收报告”。
2. 报告可以在页面查看。
3. 报告可以导出为 Markdown 文件。

---

## 代码质量要求

1. 所有后端接口必须使用 Pydantic schema。
2. 后端服务层和路由层分离。
3. 数据库适配器必须通过统一 base interface 实现。
4. API discovery 适配器必须通过统一 base interface 实现。
5. 不允许在路由函数中堆大量业务逻辑。
6. 前端 API 请求必须统一封装在 `frontend/src/api/`。
7. 前端类型必须统一放在 `frontend/src/types/`。
8. 页面组件和业务组件分离。
9. 每完成一个 Phase，必须补充 README 或 docs 中对应说明。
10. 不要引入过重依赖，新增依赖前说明原因。

---

## 测试要求

后端至少提供：

1. OpenAPI 解析单元测试
2. SQLite introspection 测试
3. 测试请求生成测试
4. 数据库快照对比测试

前端至少保证：

1. 项目能正常构建
2. 主要页面没有 TypeScript 错误
3. API client 类型正确

每个 Phase 完成后必须运行：

```bash
# backend
pytest

# frontend
npm run build
```

如果测试暂时无法完整运行，需要说明原因，并提供下一步修复建议。

---

## 安全要求

1. 不要把数据库密码完整打印到日志。
2. 前端不要明文展示完整数据库密码。
3. 测试接口前要提醒用户使用测试数据库，不要直接连接生产数据库。
4. 接口测试产生的数据要标记为测试数据。
5. 不要默认执行破坏性接口批量测试。
6. DELETE / PUT / PATCH 接口第一版需要用户确认后再执行。
7. 不要自动修改用户项目代码。
8. 本工具第一版只做观察、测试和报告，不做自动修复。

---

## AI 分析边界

本项目可以使用 AI 辅助分析，但事实判断必须来自程序采集。

程序负责：

1. 接口是否存在
2. 状态码是多少
3. 响应体是什么
4. 响应时间是多少
5. 数据库表是否存在
6. 字段是否存在
7. 行数是否变化
8. 文件是否变化

AI 可以负责：

1. 解释错误原因
2. 总结风险
3. 生成修复建议
4. 判断接口命名是否清晰
5. 判断返回结构是否符合常见规范
6. 根据字段名生成测试数据

不要让 AI 直接替代真实测试结果。

---

## 开发方式要求

当任务较复杂或跨多个模块时，必须先制定 ExecPlan。

ExecPlan 是一个可执行开发计划，需要包括：

1. 目标
2. 当前代码状态
3. 涉及文件
4. 数据模型设计
5. API 设计
6. 前端页面设计
7. 实现步骤
8. 测试方式
9. 完成标准
10. 风险和限制

制定计划后，先等待用户确认，再开始改代码。

小任务可以直接实现，但必须在最终回复中说明：

1. 修改了哪些文件
2. 实现了什么功能
3. 如何运行
4. 如何测试
5. 还有哪些未完成

---

## 当前第一阶段目标

当前阶段只需要先完成 Phase 0 和 Phase 1，不要直接开发所有功能。

优先目标：

1. 建立项目骨架。
2. 后端 FastAPI 可启动。
3. 前端 React 可启动。
4. 前后端健康检查打通。
5. 完成项目配置模型。
6. 完成项目配置保存、读取、编辑。
7. 完成 OpenAPI 地址测试。
8. 完成数据库连接测试的接口框架。

不要在第一轮开发中实现复杂接口测试、数据库快照和报告系统。

---

## Done Definition

一个任务完成必须满足：

1. 代码已实现。
2. 没有明显语法错误。
3. 关键路径可以运行。
4. README 或 docs 有必要更新。
5. 有清晰的运行命令。
6. 有清晰的测试命令。
7. 最终回复中说明完成内容、测试结果和未完成事项。

## UI Design Reference

前端开发必须参考以下设计原型图：

```text
docs/design/prototypes/01-dashboard.png
docs/design/prototypes/02-project-setup.png
docs/design/prototypes/03-api-map.png
docs/design/prototypes/04-database-map.png
docs/design/prototypes/05-test-runner.png
docs/design/prototypes/06-reports.png
docs/design/UI_STYLE_GUIDE.md