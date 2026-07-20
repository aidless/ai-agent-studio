"""报告撰写 Agent - 日报/周报/技术文档"""
from langchain_core.tools import tool
from app.agents.base import BaseAgent
from app.rag.loader import DocumentLoader
from app.tools.file_tools import save_file, get_current_time, read_file

doc_loader = DocumentLoader()

@tool
def search_context(query: str) -> str:
    """搜索知识库获取项目上下文信息。用于撰写报告时参考项目文档。"""
    results = doc_loader.search(query, top_k=3)
    if not results:
        return "无所知库内容"
    return "\n---\n".join([f"[{r['metadata'].get('source','?')}] {r['content'][:400]}" for r in results])


class WriterAgent(BaseAgent):
    name = "writer"
    description = "报告撰写 Agent - 日报、周报、技术文档、项目总结"

    SYSTEM_PROMPT = """你是一个专业的技术文档撰写 Agent。你擅长:
- 日报/周报/项目总结
- 技术方案文档
- API 文档
- 部署运维手册
- 代码 README

## 工作流程
1. 使用 search_context 获取项目相关信息
2. 使用 get_current_time 获取当前日期
3. 根据主题生成结构化文档
4. 使用 save_file 保存生成的报告

## 输出格式
使用 Markdown 格式，包含:
- 标题和日期
- 清晰的段落结构
- 必要的代码块
- 总结部分

规则: 用中文撰写、语言专业、内容充实(至少300字)、逻辑清晰"""

    def __init__(self):
        super().__init__(tools=[search_context, save_file, get_current_time, read_file])
