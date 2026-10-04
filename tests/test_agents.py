"""AI Agent Studio 功能测试"""
import sys
sys.path.insert(0, ".")

from app.config import settings
from app.rag.document_loader import DocumentLoader
from app.rag.vector_store import VectorStore
from app.agents.orchestrator import Orchestrator


def test_rag():
    print("=" * 50)
    print("测试 1: RAG 向量检索")
    print("=" * 50)
    loader = DocumentLoader()
    count = loader.load_directory()
    print(f"[OK] 加载 {count} 个文档片段到向量数据库")

    results = loader.search("RAG 是什么")
    print(f"[OK] 检索到 {len(results)} 条相关文档")
    for r in results[:2]:
        print(f"  - {r['content'][:100]}...")
    print()

def test_agent(task_type: str, content: str):
    print("=" * 50)
    print(f"测试: Agent ({task_type})")
    print("=" * 50)
    orch = Orchestrator()
    result = orch.run(task_type, content)
    if "error" in result:
        print(f"[FAIL] {result['error']}")
    else:
        print(f"[OK] Agent: {result['agent']}")
        print(f"[输出] {result['result'][:500]}...")
    print()

if __name__ == "__main__":
    test_rag()
    test_agent("research", "AI Agent Studio 的 RAG 架构是什么样的？")
    test_agent("writer", "为 AI Agent Studio 项目生成一份项目日报")
    print("全部测试完成!")
