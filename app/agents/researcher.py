"""研究员 Agent - RAG 检索 + 深度分析"""
from langchain_core.tools import tool
from app.agents.base import BaseAgent
from app.rag.loader import DocumentLoader
from app.tools.file_tools import read_file, list_directory, get_current_time

doc_loader = DocumentLoader()

@tool
def search_knowledge(query: str) -> str:
    """搜索本地知识库，获取相关文档片段。参数: query - 搜索关键词或问题。返回相关知识库内容。"""
    results = doc_loader.search(query, top_k=5)
    if not results:
        return "知识库中未找到相关内容，请尝试其他关键词。"
    formatted = []
    for i, r in enumerate(results):
        src = r["metadata"].get("source", "unknown")
        formatted.append(f"[结果{i+1}] 来源: {src} | 相关度: {r['distance']}\n{r['content']}")
    return "\n\n---\n".join(formatted)


class ResearcherAgent(BaseAgent):
    name = "researcher"
    description = "研究员 Agent - 知识库检索与深度分析"

    SYSTEM_PROMPT = """你是一个专业的研究分析 Agent。你的工作流程:

1. **检索知识库**: 使用 search_knowledge 工具查找相关信息
2. **查看文件**: 必要时使用 read_file 查看完整文档
3. **综合分析**: 基于检索结果进行深度分析，给出有洞见的结论
4. **诚实表达**: 如果知识库没有相关信息，明确说明"根据现有资料，无法确认..."

规则:
- 先检索再说话，不要凭空猜测
- 分析要有依据，引用检索到的具体内容
- 用中文回复，语言专业但易懂
- 结构化输出: 概述 → 分析 → 结论"""

    def __init__(self):
        super().__init__(tools=[search_knowledge, read_file, list_directory, get_current_time])
