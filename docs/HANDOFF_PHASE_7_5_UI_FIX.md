# HANDOFF_PHASE_7_5_UI_FIX

更新时间：2026-05-09

## 1. 当前项目整体进度

Vibe Backend Inspector 已完成本地后端验收工具的主要观察与测试链路。当前能力覆盖项目配置、OpenAPI 接口发现、API Map、SQLite/MySQL/PostgreSQL 数据库结构发现、Database Map、单接口真实请求测试、测试前后数据库快照对比，以及 LLM-assisted Smart API Testing。

最近阶段完成的是 Phase 7.5 UI 修复：在不改后端 API 和数据模型的前提下，修复 Database Map 页面，恢复 Structure Preview / 表关联关系展示，并优化 Sample Rows 紧凑展示，避免页面横向溢出。

## 2. 已完成的核心能力

- ProjectSetup：支持创建/编辑项目配置，包含项目路径、服务地址、OpenAPI 地址、数据库类型与数据库连接信息、认证配置等。
- OpenAPI 接口发现：支持按配置地址发现 OpenAPI，也支持常见路径 auto-detect，解析 paths 并持久化为统一 Endpoint 模型。
- API Map：展示真实接口列表、方法、路径、摘要、认证状态、测试状态和接口详情 schema。
- SQLite / MySQL / PostgreSQL 数据库结构发现：通过统一 database adapter 读取 database_name、tables、row_count、columns、indexes、foreign_keys、sample_rows。
- Database Map：展示表列表、结构预览、表详情、字段、索引、外键、样例数据。
- Test Runner 单接口测试：支持 GET/POST/PUT/PATCH/DELETE，支持 path/query/header/body/bearer token，真实请求由后端 TestService 执行。
- 422 参数生成与友好提示：根据 OpenAPI schema 自动生成基础参数，校验必填字段，并在 422 时提供更清晰提示。
- 测试前后数据库快照对比：Test Runner 执行前后通过 Snapshot/DatabaseService 获取 schema snapshot，对比表、行数、字段和样例数据变化；失败时返回 `db_changes.status = "error"`，不阻断 HTTP 测试。
- LLM-assisted Smart API Testing：支持 LLM 配置、AI 测试计划生成、半自动 step 执行、风险确认、结果分析；HTTP 执行继续复用 Test Runner Service。
- Database Map UI 修复：恢复结构预览/ER 关系预览；Sample Rows 默认展示前 8 个字段，支持显示更多/收起，单元格 ellipsis，避免整页横向溢出。
- AI Smart Testing UI 优化：Test Runner 中已有 AI 测试计划、当前步骤、请求参数、执行结果、AI 分析、流程时间线等可视化区域。

## 3. 当前后端主要模块说明

- `backend/app/main.py`：FastAPI app 创建、CORS、数据库初始化、路由注册。
- `backend/app/core/database.py`：工具自身 SQLite 状态库连接与初始化。
- `backend/app/models/`：SQLAlchemy 模型，包含项目、接口、测试记录、LLM 配置、AI 测试计划。
- `backend/app/schemas/`：Pydantic schema，负责所有 API 输入输出类型。
- `backend/app/routers/`：路由层，只做 HTTP 参数处理和 service 调用。
- `backend/app/services/project_service.py`：项目配置 CRUD 与敏感信息读写转换。
- `backend/app/services/openapi_service.py`：OpenAPI 拉取、auto-detect、解析和保存。
- `backend/app/services/endpoint_service.py`：Endpoint 查询与 schema 转换。
- `backend/app/services/database_service.py`：数据库连接测试、adapter 选择、schema inspect。
- `backend/app/services/snapshot_service.py`：测试前后数据库 snapshot 与 diff。
- `backend/app/services/test_service.py`：单接口真实 HTTP 请求执行、TestRun 保存、db_changes 注入。
- `backend/app/services/llm_config_service.py`：LLM 配置 CRUD、api_key masking。
- `backend/app/services/llm_service.py`：LLM provider 选择、连接测试、结构化生成/分析调用。
- `backend/app/services/ai_test_service.py`：AI 测试计划生成、计划持久化、step 执行编排、分析。
- `backend/app/adapters/database/`：SQLite/MySQL/PostgreSQL 统一 introspection adapter。
- `backend/app/adapters/llm/`：OpenAI-compatible 和 mock LLM provider。

## 4. 当前前端主要页面说明

- `frontend/src/pages/Dashboard.tsx`：总览页，展示项目与快捷入口。
- `frontend/src/pages/ProjectSetup.tsx`：项目配置页，保存服务、OpenAPI、数据库、认证配置。
- `frontend/src/pages/ApiMap.tsx`：接口地图页，展示 OpenAPI 发现到的 endpoints 和详情。
- `frontend/src/pages/DatabaseMap.tsx`：数据库结构页，当前最新布局为左侧表导航 + 右侧结构预览和表详情。
- `frontend/src/pages/TestRunner.tsx`：接口测试页，包含普通单接口测试和 AI Smart Testing 区域。
- `frontend/src/pages/Settings.tsx`：设置页，包含 LLM 配置管理。
- `frontend/src/pages/Reports.tsx`：报告页目前仍偏占位/静态方向，下一阶段建议重点接入真实数据。

## 5. 当前已实现的后端接口列表

- `GET /health`
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`
- `PUT /api/projects/{project_id}`
- `DELETE /api/projects/{project_id}`
- `POST /api/projects/{project_id}/openapi/discover`
- `POST /api/projects/{project_id}/openapi/auto-detect`
- `GET /api/projects/{project_id}/endpoints`
- `GET /api/projects/{project_id}/endpoints/{endpoint_id}`
- `POST /api/projects/{project_id}/database/test-connection`
- `POST /api/projects/{project_id}/database/inspect`
- `GET /api/projects/{project_id}/database/schema`
- `POST /api/projects/{project_id}/endpoints/{endpoint_id}/test`
- `GET /api/projects/{project_id}/test-runs`
- `GET /api/projects/{project_id}/test-runs/{test_run_id}`
- `GET /api/llm/configs`
- `POST /api/llm/configs`
- `PUT /api/llm/configs/{config_id}`
- `DELETE /api/llm/configs/{config_id}`
- `POST /api/llm/configs/{config_id}/test`
- `POST /api/projects/{project_id}/ai-tests/plans`
- `GET /api/projects/{project_id}/ai-tests/plans`
- `GET /api/projects/{project_id}/ai-tests/plans/{plan_id}`
- `POST /api/projects/{project_id}/ai-tests/plans/{plan_id}/execute-step/{step_id}`
- `POST /api/projects/{project_id}/ai-tests/plans/{plan_id}/analyze`
- `POST /api/connection-tests/openapi`
- `POST /api/connection-tests/database`

## 6. 当前已实现的前端页面列表

- Dashboard
- ProjectSetup
- ApiMap
- DatabaseMap
- TestRunner
- Reports
- Settings

前端 API 封装位于 `frontend/src/api/`，主要包括 `projects.ts`、`endpoints.ts`、`database.ts`、`tests.ts`、`llm.ts`、`aiTests.ts`、`connectionTests.ts`、`health.ts`。

前端类型位于 `frontend/src/types/`，主要包括 `project.ts`、`api.ts`、`database.ts`、`tests.ts`、`llm.ts`、`aiTest.ts`、`health.ts`、`navigation.ts`。

## 7. 当前 LLM 配置与 AI 智能测试实现方式

LLM 配置模型支持：

- `provider`：`openai_compatible`、`openai`、`deepseek`、`qwen`、`zhipu`、`ollama`、`custom`、`mock`
- `display_name`
- `base_url`
- `api_key`
- `model_name`
- `temperature`
- `timeout_seconds`
- `max_tokens`
- `enabled`

安全处理：

- 普通读取接口只返回 `masked_api_key` 和 `has_api_key`，不完整返回 `api_key`。
- 前端 Settings 页面默认隐藏 API Key。
- 后端不应在日志中输出 api_key、Bearer Token、数据库密码。
- 当前 api_key 存在本地 SQLite，适合本地开发，不建议生产部署。

AI Smart Testing 流程：

- Settings 中配置 LLM 或 mock provider。
- TestRunner 中选择 LLM 配置和 endpoints。
- 调用 `POST /api/projects/{project_id}/ai-tests/plans` 生成结构化 AI Test Plan。
- 后端对 LLM 输出做结构化解析和 Pydantic 校验；兼容部分模型返回包裹字段或格式漂移。
- 每个 step 包含 endpoint、method/path、params、headers、body、expected_status、destructive、requires_confirmation、status 等。
- 低风险 step 可直接执行；DELETE/PUT/PATCH 或 destructive/requires_confirmation step 必须确认。
- Step 执行调用 `AITestService.execute_step`，内部继续复用 `TestService.run_endpoint_test`，因此 db_changes 继续来自现有 Phase 5 snapshot diff。
- 分析阶段调用 `POST /api/projects/{project_id}/ai-tests/plans/{plan_id}/analyze`，AI 只解释真实结果，不替代程序采集事实。

## 8. 当前 Database Map 最新布局说明

当前 `DatabaseMap.tsx` 布局：

- 顶部：页面标题、测试连接、刷新结构。
- 统计卡片：数据库类型、表总数、关系数、总行数。
- 主体：`database-inspector-layout`
- 左侧：`TableNavigator`
- 右侧：`TableDetail`

左侧 Tables Navigator：

- 表搜索。
- 表列表。
- 每张表显示表名、row_count、字段数、FK 数。

右侧 Table Detail 当前顺序：

- `StructurePreview`：结构预览/表关联关系。
- `Table Overview`：当前表行数、字段数、索引数、外键数、主键数。
- `Columns`：字段名、类型、nullable、default、primary key。
- `Indexes`：索引名、字段、unique。
- `Foreign Keys`：本表外键字段、关联表、关联字段。
- `Sample Rows`：样例数据紧凑表格。

Structure Preview 逻辑：

- 基于 `schema.tables[].foreign_keys`。
- 优先展示与当前选中表相关的关系。
- 如果当前选中表没有直接关系，但数据库存在其他外键，则展示数据库中检测到的关系。
- 如果没有任何外键，显示 `No relationships detected / 未检测到表关联关系`。
- 不依赖大型图形库，不改变后端数据结构。

Sample Rows 防溢出策略：

- 默认展示前 8 个字段。
- 字段过多时提供 Show more columns / Show fewer columns。
- 使用 `table-layout: fixed`、`max-width: 100%`、单元格 ellipsis。
- 长文本通过 `title` 显示完整值。
- 只允许 Sample Rows 容器内部小范围横向滚动，不让整个页面横向溢出。

## 9. 当前测试命令和最近测试结果

后端推荐命令：

```powershell
cd backend
..\myvenv\Scripts\python.exe -m pytest
```

最近结果：

```text
27 passed in 7.12s
```

注意：直接运行系统 Python 的 `pytest` 会因为当前 shell 未激活虚拟环境而失败，报错为缺少 `sqlalchemy`。请使用项目虚拟环境或先安装 `backend/requirements.txt`。

前端推荐命令：

```powershell
cd frontend
npm run build
```

最近结果：

```text
tsc -b && vite build passed
1757 modules transformed
✓ built
```

## 10. 已知限制和待优化问题

- Reports 页面仍未完成真实验收报告数据接入，当前不是完整 Phase 7 报告系统。
- 文件监听与开发过程记录尚未作为完整真实功能接入 Dashboard/Reports。
- AI Smart Testing 暂不支持复杂登录流程自动编排、文件上传、WebSocket、SSE、GraphQL。
- LLM 输出虽然已做结构化校验和兼容处理，但真实模型仍可能返回空 steps 或语义不佳的参数，需继续优化 prompt 与 fallback。
- LLM API Key 当前本地 SQLite 存储，未加密，不适合生产环境。
- Database Map 结构预览是轻量关系列表/mini ER 表达，不是可拖拽图谱。
- Sample Rows 只做展示层紧凑化，不做复杂列选择器、排序、过滤。
- MySQL/PostgreSQL introspection 已有 mock/单元测试覆盖，但真实数据库连接仍需在本地环境手动验证。
- Test Runner 当前是单接口为主，不做批量全项目测试。
- 数据库快照 diff 是轻量 diff，不做复杂行级审计或 binlog/WAL 监听。

## 11. 下一阶段建议：Reports / 验收报告真实数据接入

建议下一阶段围绕 Reports 页面做真实数据接入，而不是新增新的测试能力。

目标建议：

- 后端新增或完善 report service/router/schema/model。
- 汇总项目基础信息、OpenAPI endpoint 数量、最近 test runs、通过/失败/跳过统计、db_changes 摘要、AI plan/analysis 摘要。
- 前端 Reports 页面接入真实 API，展示验收报告概览、接口测试结果、数据库变化摘要、风险提示。
- 支持 Markdown 导出可以作为小步增量，但不要直接做 PDF。
- 报告中的事实以程序采集数据为准，AI 只做解释/建议。

## 12. 下一阶段需要重点查看哪些文件

后端：

- `backend/app/main.py`
- `backend/app/models/test_run.py`
- `backend/app/models/api_endpoint.py`
- `backend/app/models/project.py`
- `backend/app/models/ai_test_plan.py`
- `backend/app/schemas/test_run.py`
- `backend/app/schemas/api_endpoint.py`
- `backend/app/schemas/ai_test.py`
- `backend/app/services/test_service.py`
- `backend/app/services/snapshot_service.py`
- `backend/app/services/endpoint_service.py`
- `backend/app/services/project_service.py`
- `backend/app/services/ai_test_service.py`
- `backend/app/routers/tests.py`
- `backend/app/routers/ai_tests.py`

如果开始 Reports 真实数据接入，建议新增或补齐：

- `backend/app/models/report.py`
- `backend/app/schemas/report.py`
- `backend/app/services/report_service.py`
- `backend/app/routers/reports.py`
- `backend/tests/test_reports.py`

前端：

- `frontend/src/pages/Reports.tsx`
- `frontend/src/api/tests.ts`
- `frontend/src/api/endpoints.ts`
- `frontend/src/api/aiTests.ts`
- `frontend/src/types/tests.ts`
- `frontend/src/types/api.ts`
- `frontend/src/types/aiTest.ts`
- `frontend/src/i18n/types.ts`
- `frontend/src/i18n/en.ts`
- `frontend/src/i18n/zh.ts`
- `frontend/src/styles/app.css`

如果开始 Reports API 接入，建议新增：

- `frontend/src/api/reports.ts`
- `frontend/src/types/report.ts`

## 13. 下一阶段不应该做的内容

- 不要修改被测试项目代码。
- 不要做自动修复代码。
- 不要做 OpenAPI 文件导入。
- 不要做手动添加接口。
- 不要做框架源码扫描。
- 不要做复杂登录流程自动编排。
- 不要做文件上传、WebSocket、SSE、GraphQL。
- 不要做生产级数据库 binlog/WAL 监听。
- 不要做复杂行级 diff。
- 不要做无确认的批量 destructive 测试。
- 不要做云端同步或多人协作。
- 不要把 LLM 解释当成真实测试结果。
- 不要在日志或前端完整展示 api_key、Bearer Token、数据库密码。
