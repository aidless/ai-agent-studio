"""
AI Agent Studio - 多 Agent 协作平台
简历项目: LangChain概念 + RAG + Multi-Agent + FastAPI + Tool Use

技术栈:
- FastAPI: 异步 Web 框架
- LangChain: Agent 框架理念 (Tool Use / Memory / Chain)
- RAG: 文档检索 + 上下文增强
- Multi-Agent: 研究员 + 代码审查 + 报告撰写
- DeepSeek: LLM 后端

启动: python agent_studio.py
文档: http://localhost:8000/docs
"""
import os, re, json, hashlib
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx

app = FastAPI(title="AI Agent Studio", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ----- Settings -----
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")  # SECURITY: never hardcode API keys; set DEEPSEEK_API_KEY env var
DEEPSEEK_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1") + "/chat/completions"
MODEL = "deepseek-chat"
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "data", "knowledge")

# ===== RAG Engine =====
class RAGEngine:
    """简易 RAG: TF-IDF + 关键词检索 (概念演示)"""

    def __init__(self):
        self.documents: list[dict] = []

    def ingest(self, content: str, metadata: dict = None) -> int:
        """文档入库并分块"""
        chunks = self._chunk(content)
        for i, chunk in enumerate(chunks):
            self.documents.append({
                "id": hashlib.md5(chunk.encode()).hexdigest()[:8],
                "content": chunk,
                "metadata": metadata or {},
                "chunk_index": i,
                "length": len(chunk)
            })
        return len(chunks)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """TF-IDF 词频检索"""
        query_terms = set(query.lower().split())
        scored = []
        for doc in self.documents:
            content_lower = doc["content"].lower()
            score = sum(content_lower.count(term) for term in query_terms)
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"content": s[1]["content"][:800], "metadata": s[1]["metadata"], "score": s[0]} for s in scored[:top_k]]

    def load_directory(self, directory: str = KNOWLEDGE_DIR) -> int:
        total = 0
        if os.path.exists(directory):
            for f in os.listdir(directory):
                if f.endswith((".md", ".txt", ".py", ".json")):
                    path = os.path.join(directory, f)
                    with open(path, encoding="utf-8") as fh:
                        total += self.ingest(fh.read(), {"source": f})
        return total

    def _chunk(self, text: str, size: int = 400, overlap: int = 50) -> list[str]:
        paragraphs = text.split("\n\n")
        chunks = []
        current = ""
        for p in paragraphs:
            if len(current) + len(p) > size and current:
                chunks.append(current)
                current = p[-overlap:] + "\n\n" + p if len(current) > overlap else p
            else:
                current += ("\n\n" if current else "") + p
        if current:
            chunks.append(current)
        return chunks

# ===== LLM Client =====
async def call_llm(system_prompt: str, user_message: str, context: str = "", temperature: float = 0.7) -> str:
    """调用 DeepSeek API"""
    messages = [{"role": "system", "content": system_prompt}]
    if context:
        messages.append({"role": "system", "content": f"[参考上下文]\n{context}"})
    messages.append({"role": "user", "content": user_message})
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(DEEPSEEK_URL, headers={
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json"
        }, json={"model": MODEL, "messages": messages, "temperature": temperature, "max_tokens": 2000})
        data = resp.json()
        return data["choices"][0]["message"]["content"]

# ===== Multi-Agent =====
class Agent:
    """LangChain Agent 概念: System Prompt = Agent 定义, RAG = Tool"""
    def __init__(self, name: str, role_prompt: str, tools: list[str]):
        self.name = name
        self.role_prompt = role_prompt
        self.tools = tools

    async def run(self, task: str, rag: RAGEngine = None) -> dict:
        context = ""
        if rag:
            results = rag.search(task)
            if results:
                context = "\n\n".join([f"[{r['metadata'].get('source','?')}]\n{r['content'][:500]}" for r in results[:3]])
        result = await call_llm(self.role_prompt, task, context)
        return {"agent": self.name, "tools_used": self.tools, "context_length": len(context), "result": result}

# 三个 Agent
AGENTS = {
    "researcher": Agent("研究员", """
你是一个专业的研究分析师。你会获得知识库检索结果作为上下文。
请基于上下文回答用户问题，如果上下文中没有相关信息，请诚实说明。
分析要有深度，给出有洞见的结论。用中文回复。
""", ["knowledge_search", "document_read"]),

    "coder": Agent("代码审查专家", """
你是一个资深代码审查专家。请分析用户提供的代码：
1. 找出潜在的 bug 和安全漏洞
2. 评估代码质量和可读性
3. 给出具体的改进建议（带上行号或位置）
4. 建议更好的实现方式
用中文回复，格式清晰。
""", ["file_read", "code_analyze"]),

    "writer": Agent("技术报告撰写", """
你是一个专业的技术文档撰写专家。请根据输入信息生成结构化的报告：
1. 使用 Markdown 格式
2. 包含日期、主题、详细内容、总结
3. 语言专业、逻辑清晰
用中文回复。
""", ["knowledge_search", "save_report"]),
}

# ===== API Routes =====
class AgentRequest(BaseModel):
    type: str  # researcher | coder | writer
    task: str

class RAGIngestRequest(BaseModel):
    content: str
    source: str = "api"

class RAGSearchRequest(BaseModel):
    query: str
    top_k: int = 5

rag = RAGEngine()

@app.on_event("startup")
async def startup():
    count = rag.load_directory()
    print(f"[RAG] 加载 {count} 个文档块到知识库")

@app.post("/api/v1/agent/run")
async def run_agent(req: AgentRequest):
    agent = AGENTS.get(req.type)
    if not agent:
        raise HTTPException(400, f"无效Agent类型: {req.type}，可选: {list(AGENTS.keys())}")
    return await agent.run(req.task, rag)

@app.post("/api/v1/agent/run-all")
async def run_all(task: str):
    """多 Agent 协作: 研究员先调研, 报告生成器输出最终报告"""
    research = await AGENTS["researcher"].run(task, rag)
    report = await AGENTS["writer"].run(f"基于以下调研生成报告:\n{research['result']}", rag)
    return {
        "pipeline": ["researcher", "writer"],
        "research": research["result"][:1000],
        "report": report["result"],
        "time": datetime.now().isoformat()
    }

@app.post("/api/v1/rag/search")
async def rag_search(req: RAGSearchRequest):
    results = rag.search(req.query, req.top_k)
    return {"query": req.query, "results": results, "total": len(results)}

@app.post("/api/v1/rag/ingest")
async def rag_ingest(req: RAGIngestRequest):
    count = rag.ingest(req.content, {"source": req.source})
    return {"ingested_chunks": count, "source": req.source}

@app.get("/api/v1/rag/stats")
async def rag_stats():
    return {"total_documents": len(rag.documents), "knowledge_dir": KNOWLEDGE_DIR}

@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "agents": list(AGENTS.keys()), "rag_docs": len(rag.documents)}

# ===== Web UI =====
@app.get("/", response_class=HTMLResponse)
async def web_ui():
    return HTMLResponse("""
<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AI Agent Studio</title>
<style>
:root{--bg:#0d1117;--card:#161b22;--border:#30363d;--accent:#58a6ff;--green:#3fb950;--text:#c9d1d9;--sub:#8b949e}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.header{background:var(--card);border-bottom:1px solid var(--border);padding:16px 24px;display:flex;justify-content:space-between;align-items:center}
.header h1{font-size:20px;color:var(--accent)}.header span{color:var(--sub);font-size:13px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:24px;max-width:1400px;margin:0 auto}
@media(max-width:900px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:20px}
.card h3{font-size:15px;color:var(--accent);margin-bottom:12px;display:flex;align-items:center;gap:8px}
.card h3 .dot{width:8px;height:8px;border-radius:50%;background:var(--green)}
textarea,select,input{width:100%;padding:10px;background:var(--bg);border:1px solid var(--border);border-radius:6px;color:var(--text);font-size:14px;margin:6px 0;font-family:inherit;resize:vertical}
textarea{min-height:80px}
.btn{padding:8px 18px;border:none;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600;margin:4px;transition:opacity .2s}
.btn:hover{opacity:.85}
.btn-primary{background:var(--accent);color:#fff}
.btn-green{background:#238636;color:#fff}
.btn-outline{background:transparent;border:1px solid var(--border);color:var(--text)}
pre{background:var(--bg);padding:12px;border-radius:6px;font-size:12px;max-height:400px;overflow:auto;white-space:pre-wrap;margin-top:8px;line-height:1.5;border:1px solid var(--border)}
.badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;background:#1f6feb22;color:var(--accent);border:1px solid var(--accent);margin:2px}
</style></head><body>
<div class="header"><h1>AI Agent Studio</h1><span id="clock"></span></div>
<div class="grid">
<div class="card">
<h3><span class="dot"></span> Multi-Agent 任务中心</h3>
<select id="agentType"><option value="researcher">研究员 - RAG检索分析</option><option value="coder">代码审查专家</option><option value="writer">报告撰写</option></select>
<textarea id="taskInput" placeholder="输入任务...&#10;例：AI Agent Studio 的 RAG 架构是什么？&#10;例：审查 agent_studio.py 代码质量&#10;例：生成今日项目日报"></textarea>
<div style="display:flex;gap:8px">
<button class="btn btn-primary" onclick="runSingle()">启动 Agent</button>
<button class="btn btn-green" onclick="runAll()">多 Agent 协作</button>
</div>
<pre id="agentOutput" style="display:none"></pre>
</div>
<div class="card">
<h3>RAG 知识库</h3>
<div style="color:var(--sub);font-size:13px;margin-bottom:8px" id="ragStats">加载中...</div>
<textarea id="searchQuery" placeholder="搜索知识库..." rows="2"></textarea>
<button class="btn btn-primary" onclick="searchRAG()">检索</button>
<div id="ragResults"></div>
</div>
</div>
<script>
const API="/api/v1"
async function runSingle(){
  document.getElementById("agentOutput").style.display="block"
  document.getElementById("agentOutput").textContent="Agent 思考中..."
  const r=await fetch(API+"/agent/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({type:document.getElementById("agentType").value,task:document.getElementById("taskInput").value})})
  const d=await r.json()
  document.getElementById("agentOutput").innerHTML="<b>Agent:</b> <span class='badge'>"+d.agent+"</span> | <b>上下文:</b> "+d.context_length+" 字符<br><br>"+d.result
}
async function runAll(){
  document.getElementById("agentOutput").style.display="block"
  document.getElementById("agentOutput").textContent="多 Agent 协作中 (Researcher -> Writer)..."
  const r=await fetch(API+"/agent/run-all?task="+encodeURIComponent(document.getElementById("taskInput").value),{method:"POST"})
  const d=await r.json()
  document.getElementById("agentOutput").innerHTML="<b>Pipeline:</b> <span class='badge'>"+d.pipeline.join(" -> ")+"</span><br><br><b>研究结果:</b><br>"+d.research+"<br><br><b>最终报告:</b><br>"+d.report
}
async function searchRAG(){
  const r=await fetch(API+"/rag/search",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:document.getElementById("searchQuery").value,top_k:5})})
  const d=await r.json()
  document.getElementById("ragResults").innerHTML=d.results.map(r=>`<div style="border-bottom:1px solid var(--border);padding:8px 0;font-size:13px"><b style="color:var(--accent)">score:${r.score}</b> ${r.metadata.source||""}<br>${r.content.substring(0,200)}...</div>`).join("")
}
setInterval(async()=>{
  document.getElementById("clock").textContent=new Date().toLocaleString("zh-CN")
  const r=await fetch(API+"/rag/stats");const d=await r.json()
  document.getElementById("ragStats").innerHTML="已索引 <b>"+d.total_documents+"</b> 个文档块 | 目录: "+d.knowledge_dir
},3000)
</script>
</body></html>""")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
