# AI Agent Studio v3.0

**多 Agent 协作平台** - LangChain + ChromaDB RAG + DeepSeek LLM

## 技术栈

| 层级 | 技术 |
|------|------|
| Web框架 | FastAPI (异步) |
| Agent框架 | LangChain (Tool Use + Memory + Chain) |
| 向量数据库 | ChromaDB (持久化) |
| LLM | DeepSeek Chat (兼容 OpenAI API) |
| 部署 | 本地运行（Docker Compose 规划中，暂未附配置） |

## 三个专业 Agent

| Agent | 职责 | 工具 |
|-------|------|------|
| **Researcher** | 知识库检索 + 深度分析 | search_knowledge, read_file, list_directory |
| **Coder** | 代码审查 + Bug检测 + 改进建议 | read_file, list_directory |
| **Writer** | 日报/周报/技术文档生成 | search_context, save_file |

## 启动

```bash
pip install -r requirements.txt
python -m app.main
```

浏览器打开 http://localhost:8000/docs

## Docker 部署（规划中）

当前仓库暂未附 Dockerfile / compose 配置，请先本地运行：

```bash
pip install -r requirements.txt
python -m app.main
```

## API 示例

```bash
# 研究员 Agent
curl -X POST http://localhost:8000/api/v1/agent/run \
  -H "Content-Type: application/json" \
  -d '{"agent":"research","task":"LangChain Agent 的最佳实践是什么？"}'

# 多 Agent Pipeline
curl -X POST http://localhost:8000/api/v1/agent/pipeline \
  -H "Content-Type: application/json" \
  -d '{"task":"审查 app/main.py 并生成代码质量报告"}'
```
