````markdown
# Vibe Backend Inspector

[English](README.md) | [简体中文](README.zh-CN.md)

Vibe Backend Inspector 是一个本地化的后端检查仪表盘与 Agent 工具，用于检查 AI 辅助开发过程中生成的后端项目。

当前阶段：Phase 8。

## 已实现功能

- FastAPI 后端，提供 `/health` 健康检查接口。
- React + Vite + TypeScript 前端。
- 前端支持对后端进行健康检查。
- 项目配置 CRUD。
- 使用本地 SQLite 存储工具自身状态。
- OpenAPI URL 连接测试。
- SQLite、MySQL、PostgreSQL 数据库连接测试。
- OpenAPI 接口发现与接口地图。
- SQLite、MySQL、PostgreSQL 数据库结构解析与数据库地图。
- 单接口测试运行器，支持真实 HTTP 请求执行。
- 通过统一数据库适配器层，在单接口测试前后进行数据库快照对比。
- 支持 OpenAI-compatible 和 mock provider 的大模型配置，用于 AI 辅助接口测试。
- Test Runner 中支持 AI Smart Test 测试计划、半自动步骤执行和结果分析。
- 测试运行历史会存储到工具本地 SQLite 数据库中。
- 可基于真实接口状态、测试记录、数据库变化和 AI Smart Test 结果生成验收报告。
- 支持 Markdown 报告导出。
- 参考原型设计的仪表盘布局，包含 Sidebar、TopHeader、卡片组件，以及中英文双语界面。

## 暂未实现

- 批量 API 测试运行器。
- 文件监听器。
- PDF 报告导出。
- 云端分享或团队协作。

## Phase 4：单接口测试运行器

Test Runner 页面可以一次执行一个已发现的接口。使用方式如下：

1. 选择项目。
2. 在 API Map 中同步 OpenAPI。
3. 打开 Test Runner。
4. 选择一个接口。
5. 填写 path params、query params、headers、可选 Bearer Token 和 JSON body。
6. 执行请求。

后端会保存每一次测试记录，并暴露以下接口：

```text
POST /api/projects/{project_id}/endpoints/{endpoint_id}/test
GET  /api/projects/{project_id}/test-runs
GET  /api/projects/{project_id}/test-runs/{test_run_id}
````

`PUT`、`PATCH` 和 `DELETE` 请求在执行前需要前端确认。敏感 headers 会在保存和返回测试结果时进行脱敏处理。

## Phase 5：数据库变化检测

当项目配置了 SQLite、MySQL 或 PostgreSQL 数据库时，每一次单接口测试都会通过统一数据库适配器层，在 HTTP 请求前后分别捕获一次只读数据库快照。

Test Runner 会保存并展示以下变化：

* 表新增 / 删除
* 行数变化
* 表结构变化
* 样例数据变化

如果没有配置数据库，或者数据库快照捕获失败，HTTP 接口测试仍然会继续执行。快照状态会存储在每条测试记录的 `db_changes` 字段中。

## Phase 7：AI Smart Testing

Settings 页面可以存储本地 LLM 配置，用于 AI 辅助接口测试。第一版支持通过 `base_url`、`api_key` 和 `model_name` 接入 OpenAI-compatible Chat Completion API，同时也提供内置 mock provider，方便在没有真实 API Key 的情况下进行本地演示。

### 安全说明

当前 API Key 会存储在工具本地 SQLite 数据库中，仅适合本地开发使用。普通 API 响应中会对 API Key 进行脱敏。若用于生产环境，需要先加入加密存储或操作系统密钥链集成。

在 Test Runner 中，选择一个接口和一个已启用的模型，然后点击 **Generate AI Test Plan**。模型只会生成结构化测试步骤。后端会在展示之前校验 JSON 测试计划。

HTTP 执行仍然通过现有 Test Runner Service 完成，数据库变化检测仍然通过已有的 snapshot / `db_changes` 流程完成。`PUT`、`PATCH` 和 `DELETE` 步骤在执行前需要用户确认。

### Mock 模式

```text
Provider: mock
Base URL: mock://local
Model: mock
API Key: 留空
```

可以使用 mock 模式在不调用外部大模型的情况下验证以下流程：

* UI 流程
* 测试步骤列表生成
* 半自动执行
* `db_changes` 展示
* AI 分析面板

## Phase 8：验收报告

Reports 页面会汇总工具已经采集到的真实证据，包括：

* 已发现的接口
* 接口测试状态
* 最近测试记录
* `db_changes`
* AI Smart Test 测试计划、步骤和分析结果

Reports 页面不会执行新的测试，也不会修改被检查的后端项目。

报告相关 API：

```text
GET  /api/projects/{project_id}/reports/summary
GET  /api/projects/{project_id}/reports/latest
POST /api/projects/{project_id}/reports/generate
GET  /api/projects/{project_id}/reports/{report_id}
GET  /api/projects/{project_id}/reports/{report_id}/markdown
```

使用方式：

1. 打开 Reports 页面。
2. 选择项目。
3. 如果当前证据不足，先运行接口测试或 AI Smart Test。
4. 点击 **Generate Report**。

生成的报告会保存到工具本地 SQLite 数据库中，并且可以导出为 Markdown。本阶段有意不实现 PDF 导出。

## 后端启动

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

后端默认运行地址：

```text
http://localhost:8000
```

健康检查地址：

```text
http://localhost:8000/health
```

## 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端默认运行地址：

```text
http://localhost:5173
```

界面语言可以通过右上角语言切换按钮进行切换。语言选择会存储在浏览器 `localStorage` 中。

如果后端使用了不同地址，可以创建 `frontend/.env`：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Windows 启动脚本

在仓库根目录执行：

```bat
scripts\dev_backend.bat
scripts\dev_frontend.bat
scripts\dev_all.bat
```

也提供 PowerShell 版本：

```powershell
.\scripts\dev_backend.ps1
.\scripts\dev_frontend.ps1
.\scripts\dev_all.ps1
```

## 测试

后端测试：

```bash
cd backend
pytest
```

前端构建测试：

```bash
cd frontend
npm run build
```

## 安全说明

Phase 5 会对以下位置中的敏感信息进行脱敏：

* API 响应
* 项目配置
* 已保存的测试运行 headers
* 数据库 sample diff 字段

当字段名包含以下关键词时会进行脱敏：

```text
password
token
secret
credential
```

本地密钥加密存储计划在后续阶段实现。验证数据库连接和接口执行时，请尽量使用测试数据库，不要直接连接生产数据库。

```
```
