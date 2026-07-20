# API 接口设计规范

## RESTful 设计原则

- 资源路径使用复数名词: `/agents`, `/rag/search`
- HTTP 方法语义: GET=查询, POST=创建/执行, PUT=更新, DELETE=删除
- 统一 JSON 响应格式: `{"code": 0, "data": {...}, "message": "ok"}`

## 核心接口

### Agent 执行
```
POST /api/v1/agent/run
{
    "agent": "research|coder|writer",
    "task": "任务描述"
}
Response: { "agent": "researcher", "result": "...", "elapsed_seconds": 2.5 }
```

### Multi-Agent Pipeline
```
POST /api/v1/agent/pipeline
{
    "task": "任务描述",
    "steps": ["research", "coder", "writer"]  // 可选，默认全部
}
```

### RAG 检索
```
POST /api/v1/rag/search
{ "query": "搜索关键词", "top_k": 5 }
Response: { "query": "...", "results": [{ "content": "...", "metadata": {}, "distance": 0.1 }] }
```

### 文档入库
```
POST /api/v1/rag/ingest
{ "content": "文档内容", "source": "来源标识" }
```

## 认证方案

当前版本: API Key 模式 (通过环境变量 DEEPSEEK_API_KEY)
规划: JWT Token + RBAC 权限控制

## 错误码

| code | 说明 |
|------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | LLM API 不可用 |
