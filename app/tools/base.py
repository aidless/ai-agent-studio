"""
Agent 工具集 - Agent 可以调用的外部能力
"""
import os
import json
import httpx
from datetime import datetime
from pathlib import Path


class AgentTools:
    """暴露给 LangChain Agent 使用的工具函数"""

    @staticmethod
    def read_file(filepath: str) -> str:
        """读取本地文件内容"""
        path = Path(filepath)
        if not path.exists():
            return f"文件不存在: {filepath}"
        return path.read_text(encoding="utf-8")[:5000]

    @staticmethod
    def list_directory(directory: str) -> str:
        """列出目录内容"""
        path = Path(directory)
        if not path.exists():
            return f"目录不存在: {directory}"
        items = []
        for item in path.iterdir():
            kind = "📁" if item.is_dir() else "📄"
            items.append(f"{kind} {item.name}")
        return "\n".join(items[:50])

    @staticmethod
    def get_current_time() -> str:
        """获取当前时间"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def save_report(content: str, filename: str = None) -> str:
        """保存报告到文件"""
        path = Path("./data/reports")
        path.mkdir(parents=True, exist_ok=True)
        name = filename or f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        (path / name).write_text(content, encoding="utf-8")
        return f"报告已保存: {path / name}"


class WebTools:
    """网络工具 - Agent 可调用外部 API"""

    @staticmethod
    async def http_get(url: str) -> str:
        """HTTP GET 请求"""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            return resp.text[:3000]

    @staticmethod
    async def call_llm(prompt: str, api_key: str, base_url: str) -> str:
        """调用 LLM API"""
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}]}
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"]
