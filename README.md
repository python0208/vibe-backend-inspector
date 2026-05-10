# Vibe Backend Inspector

[简体中文](README.md) | [English](README.zh-En.md)

Vibe Backend Inspector 是一个面向 AI 辅助后端开发的本地检查与验收工具。它可以通过 OpenAPI / Swagger 自动发现接口，通过数据库连接读取 SQLite、MySQL、PostgreSQL 的表结构，并支持单接口测试、测试前后数据库变化对比、AI 辅助接口测试和验收报告生成。

它适合用于检查使用 AI 编程工具生成或修改的后端项目，例如 Codex、Cursor、Claude Code、OpenCode、Windsurf、Trae 等工具参与开发的后端代码。

本项目的核心目标不是替代 Postman、Swagger 或数据库管理工具，而是提供一个面向 AI 开发流程的后端验收工作台：

> AI 写后端，我帮你看清它到底写成了什么。

当前阶段：Phase 8。

---

## 核心能力

- 项目配置管理
- OpenAPI / Swagger 接口发现
- API Map 接口地图
- SQLite / MySQL / PostgreSQL 数据库连接测试
- SQLite / MySQL / PostgreSQL 数据库结构解析
- Database Map 数据库结构可视化
- 单接口真实 HTTP 测试
- 接口测试前后数据库快照对比
- 数据库变化追踪
- LLM-assisted Smart API Testing 大模型辅助接口测试
- 测试运行历史记录
- 基于真实测试证据生成验收报告
- Markdown 报告导出
- 中英文界面切换
- 本地化运行，不依赖云端服务

---

## 适用场景

Vibe Backend Inspector 适合以下场景：

- 使用 AI 编程工具快速生成后端项目后，需要检查接口是否真实可用
- 前端开发者接手 AI 生成的后端，需要快速理解接口和数据库
- 独立开发者需要轻量级接口验收工具
- 教学或实训场景中，需要检查学生后端项目完成情况
- 外包项目验收时，需要查看接口、数据库和测试结果
- 希望观察某个接口调用前后数据库是否发生变化
- 希望让大模型根据接口文档辅助生成测试参数和测试步骤
- 希望将接口测试结果、数据库变化和 AI 分析汇总成验收报告

---

## 已实现功能

- FastAPI 后端，提供 `/health` 健康检查接口
- React + Vite + TypeScript 前端
- 前端支持对后端进行健康检查
- 项目配置 CRUD
- 使用本地 SQLite 存储工具自身状态
- OpenAPI URL 连接测试
- SQLite、MySQL、PostgreSQL 数据库连接测试
- OpenAPI 接口发现与接口地图
- SQLite、MySQL、PostgreSQL 数据库结构解析与数据库地图
- 单接口测试运行器，支持真实 HTTP 请求执行
- 通过统一数据库适配器层，在单接口测试前后进行数据库快照对比
- 支持 OpenAI-compatible 和 mock provider 的大模型配置，用于 AI 辅助接口测试
- Test Runner 中支持 AI Smart Test 测试计划、半自动步骤执行和结果分析
- 测试运行历史会存储到工具本地 SQLite 数据库中
- 可基于真实接口状态、测试记录、数据库变化和 AI Smart Test 结果生成验收报告
- 支持 Markdown 报告导出
- 参考原型设计的仪表盘布局，包含 Sidebar、TopHeader、卡片组件，以及中英文双语界面

---

## 暂未实现

- 批量 API 测试运行器
- 文件监听器
- PDF 报告导出
- 云端分享或团队协作
- 导入 OpenAPI JSON / YAML 文件
- 手动添加接口
- 框架源码扫描路由
- 自动修复后端代码

---

## 整体工作流程

典型使用流程如下：

1. 启动被检查的后端项目
2. 启动 Vibe Backend Inspector 后端和前端
3. 在 Project Setup 中创建项目配置
4. 填写后端服务地址
5. 填写 OpenAPI / Swagger 文档地址
6. 填写数据库连接信息
7. 在 API Map 中同步接口
8. 在 Database Map 中查看数据库结构
9. 在 Test Runner 中执行接口测试
10. 查看接口响应和数据库变化
11. 使用 AI Smart Testing 生成测试计划
12. 在 Reports 中生成验收报告
13. 导出 Markdown 报告

---

## 如何接入自己的后端项目

Vibe Backend Inspector 不仅可以检查本项目自身的后端，也可以检查你自己的任意后端项目，例如：

- FastAPI 项目
- Django / Django REST Framework 项目
- Spring Boot / Java 项目
- Go Gin / Echo 项目
- NestJS / Express 项目
- Laravel / PHP 项目
- 其他能够提供 OpenAPI / Swagger 文档的后端项目

接入一个后端项目时，通常需要准备三类信息：

### 1. 后端服务地址

例如：

```text
http://localhost:8000
```

或者：

```text
http://localhost:8080
```

这个地址用于让工具执行真实 HTTP 请求。

### 2. OpenAPI / Swagger 接口文档地址

例如：

```text
http://localhost:8000/openapi.json
http://localhost:8080/v3/api-docs
http://localhost:3000/api-json
http://localhost:8080/swagger/doc.json
```

这个地址用于让工具自动发现接口，生成 API Map，并为 Test Runner 和 AI Smart Testing 提供接口结构信息。

### 3. 数据库连接信息

当前支持：

- SQLite
- MySQL
- PostgreSQL

数据库连接信息用于 Database Map 展示表结构，也用于 Test Runner 在接口测试前后捕获数据库快照。

---

## 什么是 OpenAPI / Swagger？

OpenAPI 是一种描述 HTTP API 的标准格式。它通常是一个 JSON 或 YAML 文件，用来告诉工具：

- 当前后端有哪些接口
- 每个接口的请求方法，例如 GET、POST、PUT、PATCH、DELETE
- 每个接口的路径，例如 `/api/users`
- 每个接口需要哪些 path params、query params、headers
- 每个接口需要什么 request body
- 每个接口可能返回什么 response schema

Swagger 是围绕 OpenAPI 生态的一套工具。很多开发者会把 OpenAPI 文档地址称为 Swagger 地址。

在本项目中，OpenAPI / Swagger 的作用是：

> 让 Vibe Backend Inspector 自动发现后端接口，并在 API Map、Test Runner、AI Smart Testing 和 Reports 中使用这些接口信息。

如果没有 OpenAPI / Swagger 文档，本工具当前版本无法自动完整发现接口。

---

## 不同后端框架如何提供 OpenAPI / Swagger？

### FastAPI

FastAPI 默认会生成 OpenAPI 文档。

启动 FastAPI 后，一般可以访问：

```text
http://localhost:8000/openapi.json
```

Swagger UI 地址通常是：

```text
http://localhost:8000/docs
```

在 Vibe Backend Inspector 的 Project Setup 中填写：

```text
Service URL: http://localhost:8000
OpenAPI URL: http://localhost:8000/openapi.json
```

---

### Spring Boot / Java

Spring Boot 项目通常可以使用 `springdoc-openapi` 生成 OpenAPI 文档。

常见接口文档地址：

```text
http://localhost:8080/v3/api-docs
```

Swagger UI 常见地址：

```text
http://localhost:8080/swagger-ui/index.html
```

在 Vibe Backend Inspector 中填写：

```text
Service URL: http://localhost:8080
OpenAPI URL: http://localhost:8080/v3/api-docs
```

---

### Django / Django REST Framework

Django REST Framework 本身不会默认生成 OpenAPI 文档，通常需要安装扩展，例如：

- `drf-spectacular`
- `drf-yasg`

生成后可能得到类似地址：

```text
http://localhost:8000/schema/
http://localhost:8000/swagger.json
http://localhost:8000/openapi.json
```

在 Vibe Backend Inspector 中填写实际生成的 OpenAPI JSON 地址。

如果你的 Django 项目还没有 OpenAPI 文档，建议先接入 `drf-spectacular` 或 `drf-yasg`。

---

### NestJS

NestJS 可以通过 `@nestjs/swagger` 生成 OpenAPI 文档。

常见 JSON 地址可能是：

```text
http://localhost:3000/api-json
```

或根据项目配置生成其他路径。

在 Vibe Backend Inspector 中填写：

```text
Service URL: http://localhost:3000
OpenAPI URL: http://localhost:3000/api-json
```

---

### Go / Gin

Go Gin 项目通常可以使用 `swaggo` 或 `gin-swagger` 生成 Swagger 文档。

常见地址：

```text
http://localhost:8080/swagger/doc.json
```

在 Vibe Backend Inspector 中填写：

```text
Service URL: http://localhost:8080
OpenAPI URL: http://localhost:8080/swagger/doc.json
```

---

### Express / Node.js

Express 项目可以使用：

- `swagger-jsdoc`
- `swagger-ui-express`

生成 Swagger JSON 或 OpenAPI 文档。

常见地址取决于项目配置，例如：

```text
http://localhost:3000/swagger.json
http://localhost:3000/api-docs.json
```

在 Vibe Backend Inspector 中填写实际 JSON 文档地址即可。

---

## 如果我的项目没有 OpenAPI / Swagger 怎么办？

当前版本主要依赖 OpenAPI / Swagger 来自动发现接口。如果你的后端项目没有 OpenAPI 文档，可以按下面方式处理。

### 推荐方式：先为项目生成 OpenAPI 文档

根据你的技术栈选择合适工具：

| 技术栈 | 推荐方式 |
|---|---|
| FastAPI | 默认自带 `/openapi.json` |
| Spring Boot | 使用 `springdoc-openapi` |
| Django REST Framework | 使用 `drf-spectacular` 或 `drf-yasg` |
| NestJS | 使用 `@nestjs/swagger` |
| Go Gin | 使用 `swaggo / gin-swagger` |
| Express | 使用 `swagger-jsdoc` 和 `swagger-ui-express` |

生成 OpenAPI 文档后，再把文档地址填入 Project Setup。

### 临时方式：只使用数据库结构查看能力

如果你的项目暂时没有 OpenAPI 文档，但已经有数据库，可以先使用 Database Map：

1. 在 Project Setup 中填写数据库连接信息
2. 打开 Database Map
3. 点击刷新数据库结构
4. 查看表、字段、索引、外键和样例数据

但此时 API Map、Test Runner 和 AI Smart Testing 的自动接口能力会受到限制。

### 后续计划

后续版本计划支持更多接口来源，例如：

- 导入 OpenAPI JSON / YAML 文件
- 手动添加接口
- 从框架源码扫描路由
- 从本地代理流量中发现接口

当前版本建议优先通过 OpenAPI / Swagger 接入。

---

## 如何在本工具中配置 OpenAPI？

打开前端页面后：

1. 进入 Project Setup
2. 创建或选择一个项目
3. 填写后端服务地址

```text
Service URL: http://localhost:8000
```

4. 填写 OpenAPI 文档地址

```text
OpenAPI URL: http://localhost:8000/openapi.json
```

5. 保存项目配置
6. 进入 API Map
7. 点击 Sync OpenAPI
8. 如果配置正确，页面会展示自动发现的接口列表

---

## 如何配置数据库连接？

当前支持：

- SQLite
- MySQL
- PostgreSQL

### SQLite

填写 SQLite 数据库文件路径，例如：

```text
D:\demo\app.db
```

### MySQL

填写：

```text
Host: localhost
Port: 3306
Database: your_database
Username: root
Password: your_password
```

### PostgreSQL

填写：

```text
Host: localhost
Port: 5432
Database: your_database
Username: postgres
Password: your_password
```

配置完成后，可以在 Database Map 中查看：

- 表列表
- 字段结构
- 主键
- 索引
- 外键
- 行数
- 样例数据
- 表关联关系

---

## Phase 4：单接口测试运行器

Test Runner 页面可以一次执行一个已发现的接口。使用方式如下：

1. 选择项目
2. 在 API Map 中同步 OpenAPI
3. 打开 Test Runner
4. 选择一个接口
5. 填写 path params、query params、headers、可选 Bearer Token 和 JSON body
6. 执行请求

后端会保存每一次测试记录，并暴露以下接口：

```text
POST /api/projects/{project_id}/endpoints/{endpoint_id}/test
GET  /api/projects/{project_id}/test-runs
GET  /api/projects/{project_id}/test-runs/{test_run_id}
```

`PUT`、`PATCH` 和 `DELETE` 请求在执行前需要前端确认。敏感 headers 会在保存和返回测试结果时进行脱敏处理。

---

## Phase 5：数据库变化检测

当项目配置了 SQLite、MySQL 或 PostgreSQL 数据库时，每一次单接口测试都会通过统一数据库适配器层，在 HTTP 请求前后分别捕获一次只读数据库快照。

Test Runner 会保存并展示以下变化：

- 表新增 / 删除
- 行数变化
- 表结构变化
- 样例数据变化

如果没有配置数据库，或者数据库快照捕获失败，HTTP 接口测试仍然会继续执行。快照状态会存储在每条测试记录的 `db_changes` 字段中。

---

## Phase 7：AI Smart Testing

Settings 页面可以存储本地 LLM 配置，用于 AI 辅助接口测试。

第一版支持通过 `base_url`、`api_key` 和 `model_name` 接入 OpenAI-compatible Chat Completion API，同时也提供内置 mock provider，方便在没有真实 API Key 的情况下进行本地演示。

### 安全说明

当前 API Key 会存储在工具本地 SQLite 数据库中，仅适合本地开发使用。普通 API 响应中会对 API Key 进行脱敏。

如果用于生产环境，需要先加入加密存储或操作系统密钥链集成。

### 使用 mock 模式

如果你没有真实大模型 API Key，可以先使用 mock 模式：

```text
Provider: mock
Base URL: mock://local
Model: mock
API Key: 留空
```

mock 模式不会调用外部模型，但可以验证完整 UI 流程。

### 使用 OpenAI-compatible 模型

如果你有 OpenAI、DeepSeek、Qwen 或其他兼容 OpenAI Chat Completion API 的服务，可以填写：

```text
Provider: openai_compatible
Base URL: 你的模型服务地址
Model: 模型名称
API Key: 你的 API Key
```

保存后，在 Test Runner 中：

1. 选择接口
2. 选择模型配置
3. 点击 Generate AI Test Plan
4. 查看 AI 生成的测试步骤
5. 确认高风险步骤
6. 执行测试
7. 查看请求参数、响应结果、数据库变化和 AI 分析

注意：AI 只负责生成测试计划和分析结果，真实 HTTP 请求仍然由本工具后端执行。

---

## Phase 8：验收报告

Reports 页面会汇总工具已经采集到的真实证据，包括：

- 已发现的接口
- 接口测试状态
- 最近测试记录
- `db_changes`
- AI Smart Test 测试计划、步骤和分析结果

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

1. 打开 Reports 页面
2. 选择项目
3. 如果当前证据不足，先运行接口测试或 AI Smart Test
4. 点击 Generate Report

生成的报告会保存到工具本地 SQLite 数据库中，并且可以导出为 Markdown。本阶段有意不实现 PDF 导出。

---

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

---

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

---

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

---

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

---

## 安全说明

Phase 5 会对以下位置中的敏感信息进行脱敏：

- API 响应
- 项目配置
- 已保存的测试运行 headers
- 数据库 sample diff 字段

当字段名包含以下关键词时会进行脱敏：

```text
password
token
secret
credential
```

本地密钥加密存储计划在后续阶段实现。

验证数据库连接和接口执行时，请尽量使用测试数据库，不要直接连接生产数据库。

---

## 使用建议

为了获得最佳体验，建议按照以下顺序使用本工具：

1. 先保证被检查项目可以正常启动
2. 确认被检查项目能提供 OpenAPI / Swagger 文档
3. 在 Project Setup 中填写服务地址和 OpenAPI 地址
4. 在 API Map 中同步接口
5. 配置数据库连接
6. 在 Database Map 中检查表结构
7. 使用 Test Runner 执行关键接口
8. 查看数据库变化
9. 使用 AI Smart Testing 辅助生成测试计划
10. 在 Reports 中生成验收报告

---

## 项目定位

Vibe Backend Inspector 面向的是 AI 辅助开发时代的后端验收流程。

它更关注：

- AI 到底创建了哪些接口
- 接口是否能真实请求成功
- 请求参数是否完整
- 数据库表是否创建成功
- 接口执行后数据库是否发生预期变化
- 接口文档、真实响应和数据库状态是否一致
- 能否形成一份可交付的验收报告

它不是一个单纯的接口请求工具，也不是传统数据库客户端，而是一个围绕 AI 后端开发过程构建的本地检查与验收工作台。
