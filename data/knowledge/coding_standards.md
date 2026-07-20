# 代码规范

## Python 代码规范
- 遵循 PEP 8 规范
- 使用 type hints 类型注解
- 函数命名使用 snake_case
- 类命名使用 PascalCase

## 项目结构
```
app/
  agents/    # LangChain Agent 模块
  rag/       # RAG 检索增强生成
  tools/     # Agent 工具集
  api/       # FastAPI 路由
  main.py    # 应用入口
```

## 安全规范
- API Key 放在 .env 文件中，不提交到 Git
- 密码使用 BCrypt 加密
- 使用参数化查询防止 SQL 注入
