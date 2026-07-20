"""
AI Agent Studio v3.0 - 多 Agent 协作平台
=========================================
FastAPI + LangChain + ChromaDB + DeepSeek

架构层次:
  api/       RESTful 接口层
  agents/    Agent 层 (Researcher, Coder, Writer)
  rag/       RAG 层 (ChromaDB 向量存储 + 文档检索)
  tools/     Tool 层 (文件系统、代码分析)

启动:
  python -m app.main
  uvicorn app.main:app --reload --port 8000

Docker:
  docker compose up -d
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.config import settings
from app.rag.loader import DocumentLoader

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="多 Agent 协作平台 - LangChain + ChromaDB RAG + DeepSeek LLM",
    docs_url="/docs",
    redoc_url="/redoc"
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

@app.on_event("startup")
async def startup():
    loader = DocumentLoader()
    count = loader.load_directory()
    print(f"[Agent Studio v{settings.app_version}] 启动完成")
    print(f"[RAG] 向量库加载 {count} 个文档块")
    print(f"[API] 文档: http://localhost:{settings.port}/docs")
    print(f"[API] Redoc: http://localhost:{settings.port}/redoc")
    print(f"[Agents] 可用: research | coder | writer")

@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "agents": {
            "researcher": "知识库检索 + 深度分析",
            "coder": "代码审查 + Bug检测 + 改进建议",
            "writer": "报告撰写 + 日报/周报/技术文档"
        },
        "rag": {"status": "active", "documents": DocumentLoader().count},
        "endpoints": {
            "run_agent": "POST /api/v1/agent/run",
            "pipeline": "POST /api/v1/agent/pipeline",
            "agent_list": "GET /api/v1/agent/list",
            "rag_search": "POST /api/v1/rag/search",
            "rag_ingest": "POST /api/v1/rag/ingest",
            "rag_stats": "GET /api/v1/rag/stats",
            "health": "GET /api/v1/health"
        }
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
