# AI Agent Studio v3.0

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**多 Agent 协作平台** - LangChain + ChromaDB RAG + DeepSeek LLM

一个把 RAG 检索、专业 Agent 路由和任务编排串成一条链的演示平台：
研究员检索知识库、代码审查员查 Bug、报告撰写员产出文档，三者经
`Orchestrator` 按步骤管道化执行。

## 技术栈

| 层级 | 技术 |
|------|------|
| Web框架 | FastAPI (异步) |
| Agent框架 | LangChain (Tool Use + Memory + Chain) |
| 向量数据库 | ChromaDB (持久化) |
| LLM | DeepSeek Chat (兼容 OpenAI API) |
| 部署 | 本地运行（Docker Compose 规划中，暂未附配置） |

## 项目结构

```
ai-agent-studio/
+-- agent_studio.py            # v2 单文件入口（演示）
+-- app/
|   +-- main.py                # v3 FastAPI 应用入口：python -m app.main
|   +-- config.py              # 环境变量配置
|   +-- api/routes.py          # REST 接口层（/api/v1/agent/*）
|   +-- agents/                # Researcher / Coder / Writer + Orchestrator
|   +-- rag/                   # 文档加载 + ChromaDB 向量存储
|   +-- tools/                 # 文件系统与代码分析工具
+-- data/
|   +-- knowledge/*.md         # 5 篇知识库文档（RAG 输入）
|   +-- chroma/                # ChromaDB 持久化目录
+-- tests/test_agents.py       # 2 passed + 1 skipped（RAG 冒烟 + 哈希嵌入）
+-- requirements.txt
```

## 三个专业 Agent

| Agent | 职责 | 工具 |
|-------|------|------|
| **Researcher** | 知识库检索 + 深度分析 | search_knowledge, read_file, list_directory |
| **Coder** | 代码审查 + Bug检测 + 改进建议 | read_file, list_directory |
| **Writer** | 日报/周报/技术文档生成 | search_context, save_file |

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

## 测试

```bash
python -m pytest -q    # 2 passed, 1 skipped
```

- `test_rag` 用**确定性哈希编码器**（`app.rag.vector_store._hash_embedding`）
  注入 RAG 冒烟路径，避免 ~80MB 的 sentence-transformers 模型下载和 torch，
  使 CI 可复现；该编码器**非语义**，结果行不代表检索质量。
- `test_hash_embedding_is_deterministic_and_normalised` 断言同一段文字两次编码
  一致、维数 384、L2 范数为 1。
- `test_agent` 需要 `DEEPSEEK_API_KEY`（真实 LLM 调用），无 Key 时**跳过而非伪造**。

## 证据

- 5 篇知识库文档加载到 ChromaDB（`python -m app.main` 启动时自动执行）。
- 12 个文档片段被 `DocumentLoader.load_directory()` 加载（可复算：见下）。
- 真实 LLM 路径需要 Key；无 Key 时 RAG 与编排仍可离线运行（哈希编码器）。

## 证明什么 / 不证明什么

**证明：** FastAPI 服务可启动；RAG 向量检索链路在注入确定性编码器后可跑通；
三个专业 Agent 的注册、路由与 Orchestrator 管道编排正确；测试套件可复现。

**不证明：** 知识库检索质量（`_hash_embedding` 是非语义哈希，测试里的检索结果
只证明链路通，不证明相关性）；模型输出质量（`test_agent` 无 Key 即跳过，且
无 Key 时不伪造结果）；生产可靠性（无真实用户流量、无 SLO、无监控）。

## 复现

```bash
cd ai-agent-studio
pip install -r requirements.txt
python -m pytest -q                          # 2 passed, 1 skipped
python -c "
import tempfile
from app.config import settings
from app.rag.vector_store import _hash_embedding
from app.rag.document_loader import DocumentLoader
with tempfile.TemporaryDirectory() as td:
    settings.chroma_persist_dir = td
    loader = DocumentLoader(embedding_fn=_hash_embedding)
    print('documents loaded:', loader.load_directory())  # 12
"
```

文档片段数 `12` 来自上述命令的实际输出，可在此树复算。

## 已知限制

- `requirements.txt` 未列出 `sentence-transformers`，但
  `app/rag/vector_store.py:17` 在默认编码器路径会按需导入它（CI 用 CPU torch
  规避；本地需手动安装或始终注入 `_hash_embedding`）。
- Docker 部署仍为规划，仓库暂无 Dockerfile / compose 配置。
