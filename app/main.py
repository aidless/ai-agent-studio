"""
AI Agent Studio local demo (version string: settings.app_version).

Importing this module imports app.api.routes, which constructs the
orchestrator and therefore a chat client. DEEPSEEK_API_KEY must be
non-empty or that construction raises openai.OpenAIError. A placeholder
value only gets past construction; it does not measure model output.

Startup indexes data/knowledge with app.rag.loader (Chroma's default
ONNX embedder; first use downloads a model). That is not the offline
hash-trigram path `make check` runs.

This repository has no Dockerfile and no compose file.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import settings
from app.rag.loader import DocumentLoader

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Local demo. Offline checks do not measure semantic search or LLM answers. Not a release.",
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
    print("[Agents] 可用: research | coder | writer")

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
