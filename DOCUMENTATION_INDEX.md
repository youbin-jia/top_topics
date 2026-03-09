# 项目文档索引

## 📚 文档导航

欢迎来到AI自媒体自动选题系统！本项目提供完整的文档体系，帮助您快速上手和深度使用。

### 🚀 快速开始

**新手必读**：
1. [README.md](README.md) - 项目总览和基本介绍
2. [QUICK_START.md](QUICK_START.md) - 5分钟快速启动指南

### 📖 详细文档

#### 架构与设计
- **[ARCHITECTURE.md](ARCHITECTURE.md)** (11KB)
  - 系统架构设计
  - 技术栈选择
  - 数据流和算法
  - 性能优化策略
  - 扩展性设计

#### 开发指南
- **[DEVELOPMENT.md](DEVELOPMENT.md)** (22KB)
  - 环境搭建
  - 模块开发详解
  - 测试指南
  - 部署指南
  - 最佳实践

- **[MODULE_GUIDE.md](docs/MODULE_GUIDE.md)** (11KB)
  - 各模块详细开发指南
  - 核心算法实现
  - 集成示例
  - 性能优化建议

#### 使用手册
- **[USER_GUIDE.md](USER_GUIDE.md)** (23KB)
  - 功能详解
  - API使用指南
  - 最佳实践
  - 常见问题
  - 故障排查

- **[API_REFERENCE.md](API_REFERENCE.md)** (15KB)
  - 完整API文档
  - 请求/响应示例
  - 错误处理
  - SDK使用

#### 部署运维
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** (19KB)
  - 生产环境部署
  - 服务器配置
  - 性能优化
  - 监控告警
  - 备份恢复
  - 安全加固

### 📊 项目概览

- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - 项目完成情况总结

---

## 🎯 按角色查找文档

### 系统管理员
1. [快速开始](QUICK_START.md) - 安装和部署
2. [部署运维手册](DEPLOYMENT_GUIDE.md) - 生产环境配置
3. [故障排查](USER_GUIDE.md#故障排查) - 问题诊断

### 后端开发者
1. [开发指南](DEVELOPMENT.md) - 环境搭建和开发
2. [模块开发指南](docs/MODULE_GUIDE.md) - 各模块实现
3. [API文档](API_REFERENCE.md) - API接口规范
4. [架构设计](ARCHITECTURE.md) - 系统架构

### 前端开发者
1. [API文档](API_REFERENCE.md) - API调用指南
2. [用户使用手册](USER_GUIDE.md) - 功能理解
3. [快速开始](QUICK_START.md) - 前端环境搭建

### 数据科学家
1. [模块指南 - 推荐算法](docs/MODULE_GUIDE.md#3-推荐引擎模块)
2. [架构设计 - 核心算法](ARCHITECTURE.md#核心算法)
3. [性能优化](DEVELOPMENT.md#性能优化)

### 产品经理
1. [项目总览](README.md) - 功能介绍
2. [用户使用手册](USER_GUIDE.md) - 用户流程
3. [API文档](API_REFERENCE.md) - 功能清单

---

## 📁 项目结构

```
top_topics/
├── backend/              # 后端服务
│   ├── config/          # 配置文件
│   ├── apps/            # 应用模块
│   ├── api/             # API接口
│   └── core/            # 核心功能
├── frontend/            # 前端应用
├── tests/               # 测试代码
├── docs/                # 详细文档
├── scripts/             # 脚本工具
└── docker/              # Docker配置
```

---

## 🔍 快速查找

### 按功能查找

| 功能 | 相关文档 |
|-----|---------|
| 数据采集 | [模块指南](docs/MODULE_GUIDE.md#1-数据收集模块) |
| 话题分析 | [模块指南](docs/MODULE_GUIDE.md#2-话题分析模块) |
| 推荐算法 | [模块指南](docs/MODULE_GUIDE.md#3-推荐引擎模块) |
| 内容生成 | [模块指南](docs/MODULE_GUIDE.md#4-内容生成模块) |
| 反馈学习 | [模块指南](docs/MODULE_GUIDE.md#5-反馈学习模块) |

### 按问题查找

| 问题 | 解决方案文档 |
|-----|-------------|
| 如何安装？ | [快速开始](QUICK_START.md) |
| 如何部署？ | [部署指南](DEPLOYMENT_GUIDE.md) |
| API如何使用？ | [API文档](API_REFERENCE.md) |
| 遇到错误？ | [用户手册-故障排查](USER_GUIDE.md#故障排查) |
| 性能优化？ | [部署指南-性能优化](DEPLOYMENT_GUIDE.md#性能优化) |
| 如何开发？ | [开发指南](DEVELOPMENT.md) |

---

## 💡 推荐阅读路径

### 路径1：快速上手（1小时）
```
README.md → QUICK_START.md → USER_GUIDE.md (功能详解部分)
```

### 路径2：深度开发（半天）
```
ARCHITECTURE.md → DEVELOPMENT.md → MODULE_GUIDE.md → API_REFERENCE.md
```

### 路径3：生产部署（半天）
```
DEPLOYMENT_GUIDE.md → USER_GUIDE.md (故障排查部分) → 监控配置
```

### 路径4：全面了解（1-2天）
```
README.md → ARCHITECTURE.md → DEVELOPMENT.md → MODULE_GUIDE.md
→ USER_GUIDE.md → API_REFERENCE.md → DEPLOYMENT_GUIDE.md
```

---

## 📞 获取帮助

### 在线资源
- 🌐 GitHub仓库: https://github.com/youbin-jia/top_topics
- 📖 API文档: http://localhost:8000/swagger/ (启动后访问)
- 💬 问题反馈: https://github.com/youbin-jia/top_topics/issues

### 文档更新
- 所有文档最后更新时间: 2026-03-10
- 文档版本: v1.0.0

---

## 🎓 学习资源

### 必备知识
- Python编程基础
- Django框架基础
- 数据库基础知识
- RESTful API概念

### 推荐学习
- 机器学习基础（推荐算法）
- 自然语言处理（NLP）
- Docker容器化
- 微服务架构

### 外部文档
- [Django官方文档](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery文档](https://docs.celeryproject.org/)
- [Gensim教程](https://radimrehurek.com/gensim/)

---

## 📝 文档贡献

欢迎改进文档！如果您发现：
- 文档错误或过时
- 缺少重要信息
- 可以改进的地方

请提交Issue或Pull Request。

---

## ✅ 检查清单

### 开始使用前
- [ ] 阅读 README.md 了解项目概况
- [ ] 按照 QUICK_START.md 完成环境搭建
- [ ] 确认所有服务正常运行
- [ ] 尝试基本API调用

### 开发前
- [ ] 阅读 ARCHITECTURE.md 理解架构
- [ ] 阅读 DEVELOPMENT.md 了解开发流程
- [ ] 阅读相关模块的 MODULE_GUIDE.md
- [ ] 配置开发环境和工具

### 部署前
- [ ] 阅读 DEPLOYMENT_GUIDE.md
- [ ] 准备生产服务器
- [ ] 配置安全设置
- [ ] 设置监控告警

---

**开始您的AI选题之旅吧！** 🚀

如有任何问题，请查看相关文档或提交Issue。
