# ARCHITECTURE.md

## 总体架构

本项目采用本地 Web Dashboard + Local Agent 架构。

前端负责可视化展示和用户配置。
后端负责项目扫描、接口发现、数据库连接、接口测试、快照对比和报告生成。

## 模块划分

### Project Module

负责项目配置管理。

### OpenAPI Discovery Module

负责读取 OpenAPI / Swagger 文档，并转换为统一 Endpoint 模型。

### Database Module

负责连接 SQLite / MySQL / PostgreSQL，并读取数据库结构、样例数据和快照。

### Watcher Module

负责监听用户项目目录的文件变化。

### Test Runner Module

负责执行接口测试，记录请求、响应和错误信息。

### Snapshot Module

负责测试前后数据库状态对比。

### Report Module

负责生成一轮开发验收报告。

## 数据流

用户创建项目配置
-> 后端保存配置
-> 检测服务地址
-> 拉取 OpenAPI
-> 解析接口
-> 连接数据库
-> 读取表结构
-> 执行接口测试
-> 记录数据库快照
-> 生成验收报告