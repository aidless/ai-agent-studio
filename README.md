# AI Agent Studio v3.0

[![CI](https://github.com/aidless/ai-agent-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/aidless/ai-agent-studio/actions/workflows/ci.yml)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

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

![API Docs](docs/api-docs.png)

## Quickstart

以下命令均为 2026-11-10 实跑验证（CPython 3.12）。

```bash
pip install -r requirements.txt

# 测试（无需 API key）
python3 -m pytest tests/ -q
# → 2 passed, 1 skipped in ~2s

# 启动服务（agents 在 import 时构造 ChatOpenAI，需要先设一个 key；
# 本地演示用占位 key 即可，真实调用时替换成你的 DeepSeek key）
DEEPSEEK_API_KEY=sk-demo PORT=8000 python3 -m app.main
```

浏览器打开 http://localhost:8000/docs —— 即上方 Swagger 截图（Agent / RAG / System
三组端点）。接口自检（真实输出，2026-11-10）：

```bash
curl -s http://localhost:8000/
# {"name":"AI Agent Studio","version":"3.0.0","docs":"/docs",
#  "agents":{...researcher/coder/writer...},
#  "rag":{"status":"active","documents":11},"endpoints":{...}}
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

## Limits

- **import 时即构造 LLM 客户端**：`agents/` 模块在 import 阶段创建 `ChatOpenAI`，
  不设 `DEEPSEEK_API_KEY` 会在启动时抛 `openai.OpenAIError`；本地演示可用占位 key。
- `POST /api/v1/agent/run`、`/pipeline` 需要真实 DeepSeek key 才会返回生成结果；
  无 key 时接口可达但 LLM 调用失败。
- ChromaDB 首次启动会写 `data/chroma/`（已随仓库附带 11 个文档块的索引）。
- Docker 部署规划中，仓库暂未附 Dockerfile / compose 配置。

## 结构导览

| 路径 | 内容 |
|------|------|
| `app/main.py` | FastAPI 入口 + 路由挂载 |
| `agent_studio.py` | 三个 Agent（researcher/coder/writer）+ 内嵌 Web UI |
| `tests/` | pytest 单测（2 passed / 1 skipped，无需 API key） |
| `data/chroma/` | ChromaDB 持久化向量库 |
| `docs/` | Swagger 截图等文档资产 |
