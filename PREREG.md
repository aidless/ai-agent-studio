# 预注册规格 — AI Agent Studio v3.0 多 Agent 协作平台

> 这份文档把本仓**真实**的假设、评测方案、成功标准与边界写下来，独立于任何
> "能力声明"。所有数字均来自本仓可复算的 pytest 套件与 RAG 冒烟路径，不虚构。

## 1. 研究对象

本仓是**多 Agent 协作平台演示**（FastAPI + LangChain/LangGraph + ChromaDB RAG +
DeepSeek LLM）：研究员检索知识库、代码审查员查 Bug、报告撰写员产出文档，三者经
`Orchestrator` 按步骤管道化执行。RAG 检索层注入**确定性哈希编码器**
（`app.rag.vector_store._hash_embedding`）做冒烟路径，避免 ~80MB 模型下载与
torch，使 CI 可复现。该编码器**非语义**，结果行不代表检索质量。

## 2. 假设（H1–H5）

- **H1（RAG 链路接线正确）**：注入确定性哈希编码器后，`DocumentLoader.load_directory()`
  应加载 5 篇知识库文档为 12 个片段；`search()` 应返回排序后的相关片段。
  这**只证明链路通**（load → store → retrieve），不证明相关性。
- **H2（哈希嵌入确定性）**：同一段文字两次编码应一致、维数 384、L2 范数为 1
  （`test_hash_embedding_is_deterministic_and_normalised`）。
- **H3（Agent 注册与路由正确）**：Researcher/Coder/Writer 三个专业 Agent 注册、
  路由与 Orchestrator 管道编排正确（`app/agents/` + `app/api/routes.py`）。
- **H4（无 Key 不伪造）**：`test_agent` 需要 `DEEPSEEK_API_KEY`（真实 LLM 调用），
  无 Key 时**跳过而非伪造**（`NEEDS_KEY` skipif）。
- **H5（可复算性）**：测试套件 `python3 -m pytest -q` → 2 passed + 1 skipped
  （RAG 冒烟 + 哈希嵌入确定性；真实 LLM 路径无 Key 跳过）。

## 3. 评测方案

### 3.1 pytest 套件（`tests/test_agents.py`）

```bash
python3 -m pytest -q    # 2 passed, 1 skipped
```

- `test_rag`：注入 `_hash_embedding`，冒烟 load+search，确定性、零模型下载。
- `test_hash_embedding_is_deterministic_and_normalised`：断言编码确定性、维数 384、
  L2 范数 1。
- `test_agent`（skip 无 Key）：真实 LLM 路径，无 Key 跳过不伪造。

### 3.2 RAG 冒烟复算（12 片段）

```bash
python3 -c "
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

真实执行 → **documents loaded: 12**（本树可复算）。

### 3.3 判定标准（成功 = 满足）

| 标准 | 目标 | 当前实测 |
|---|---|---|
| pytest | 2 passed, 1 skipped | 2 passed, 1 skipped（本树） |
| 文档片段数 | 12 | 12（本树） |
| 哈希嵌入 | 确定性、384 维、L2=1 | 断言通过（本树） |
| 无 Key 行为 | 跳过不伪造 | 跳过（本树） |

## 4. 明确边界（不证明什么）

1. **不证明检索质量**：`_hash_embedding` 是非语义哈希，测试里的检索结果只证明
   链路通，不证明相关性；跨语言/改写查询会 miss，绝不可用于能力声明。
2. **不证明模型输出质量**：`test_agent` 无 Key 即跳过，且无 Key 时不伪造结果；
   真实 LLM 路径需要 `DEEPSEEK_API_KEY`。
3. **不证明生产可靠性**：无真实用户流量、无 SLO、无监控；Docker 部署仍为规划
   （仓库暂无 Dockerfile/compose）。
4. **`sentence-transformers` 未列入 requirements**：默认编码器路径在
   `vector_store.py:17` 按需导入，CI 用 CPU torch 规避；本地需手动安装或始终注入
   `_hash_embedding`。
5. **演示平台，非框架**：本仓是单机演示（3 Agent + Orchestrator），不是可复用的
   通用 agent 框架或生产编排系统。

## 5. 预注册承诺

任何后续**质量**声明（"检索质量 X%""模型输出能力"）必须先在本仓补真实数据
（真语义编码器、真 embedding 检索基准、真实 LLM 路径评测）再写；本仓当前只声明
"RAG 链路接线正确 + 哈希嵌入确定性 + Agent 注册/路由/编排正确 + 无 Key 不伪造 +
测试可复现"，且明确该声明**不**外推到检索质量、模型质量或生产可靠性。
