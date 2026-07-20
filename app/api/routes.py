"""API 路由 - RESTful 接口"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, AsyncGenerator
from app.agents.orchestrator import Orchestrator
from app.rag.loader import DocumentLoader
from app.rag.store import VectorStore
import json, asyncio

router = APIRouter(prefix="/api/v1")
orch = Orchestrator()
doc_loader = DocumentLoader()

# --- Pydantic Models ---
class AgentRunRequest(BaseModel):
    agent: str = Field(..., description="Agent类型: research | coder | writer")
    task: str = Field(..., min_length=1, max_length=5000, description="任务描述")

class PipelineRequest(BaseModel):
    task: str = Field(..., description="任务描述")
    steps: Optional[list[str]] = Field(None, description="Pipeline步骤，默认 research->coder->writer")

class RAGQuery(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)

class RAGIngestRequest(BaseModel):
    content: str = Field(..., min_length=1)
    source: str = Field("api", description="文档来源")

# --- Agent API ---
@router.post("/agent/run", tags=["Agent"])
async def run_agent(req: AgentRunRequest):
    """调用单个 Agent 执行任务。返回 Agent 名称、执行结果和耗时。"""
    result = await orch.arun(req.agent, req.task)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result

@router.post("/agent/pipeline", tags=["Agent"])
async def run_pipeline(req: PipelineRequest):
    """多 Agent Pipeline 协作。默认链条: 研究员 -> 代码审查 -> 报告生成。"""
    result = orch.pipeline(req.task, req.steps)
    return result

@router.get("/agent/list", tags=["Agent"])
async def list_agents():
    """获取所有可用 Agent 及其工具列表"""
    return {"agents": orch.list_agents()}

# --- RAG API ---
@router.post("/rag/search", tags=["RAG"])
async def rag_search(req: RAGQuery):
    """向量检索本地知识库，返回 top_k 个最相关文档片段"""
    results = doc_loader.search(req.query, req.top_k)
    return {"query": req.query, "total": len(results), "results": results}

@router.post("/rag/ingest", tags=["RAG"])
async def rag_ingest(req: RAGIngestRequest):
    """向知识库添加文档"""
    store = VectorStore()
    count = store.add([req.content], [{"source": req.source}])
    return {"ingested": count, "source": req.source}

@router.get("/rag/stats", tags=["RAG"])
async def rag_stats():
    """知识库统计"""
    return {"total_documents": doc_loader.count, "collection": "knowledge_base"}

@router.post("/rag/reload", tags=["RAG"])
async def rag_reload():
    """重新加载知识库目录中的所有文档"""
    VectorStore().clear()
    count = doc_loader.load_directory()
    return {"reloaded": count, "message": f"已重新加载 {count} 个文档块"}

# --- Health ---
@router.get("/health", tags=["System"])
async def health():
    return {"status": "healthy", "app": "AI Agent Studio", "version": "3.0.0"}
