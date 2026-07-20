"""文件操作 Tool 集合 - Agent 可调用的文件系统能力"""
import os
from pathlib import Path
from datetime import datetime
from langchain_core.tools import tool


@tool
def read_file(filepath: str) -> str:
    """读取本地文件内容。用于查看源代码、文档、配置文件等。参数: filepath - 文件绝对或相对路径"""
    path = Path(filepath)
    if not path.exists():
        return f"[错误] 文件不存在: {filepath}"
    try:
        content = path.read_text(encoding="utf-8")
        if len(content) > 5000:
            content = content[:5000] + f"\n... (文件共 {len(content)} 字符，仅显示前 5000)"
        return f"文件: {path.name}\n大小: {len(content)} 字符\n---\n{content}"
    except Exception as e:
        return f"[错误] 读取失败: {e}"


@tool
def list_directory(directory: str = ".") -> str:
    """列出目录中的文件和子目录。参数: directory - 目录路径，默认为当前目录"""
    path = Path(directory)
    if not path.exists():
        return f"[错误] 目录不存在: {directory}"
    if not path.is_dir():
        return f"[错误] 不是目录: {directory}"
    items = []
    for item in sorted(path.iterdir()):
        kind = "📁" if item.is_dir() else "📄"
        size = ""
        if item.is_file():
            try:
                s = item.stat().st_size
                size = f" ({s}B)" if s < 1024 else f" ({s//1024}KB)"
            except:
                pass
        items.append(f"{kind} {item.name}{size}")
    return f"目录: {path.absolute()}\n共 {len(items)} 项\n---\n" + "\n".join(items[:100])


@tool
def save_file(filepath: str, content: str) -> str:
    """保存内容到文件。用于生成报告、保存分析结果等。参数: filepath - 文件路径, content - 文件内容"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    size = path.stat().st_size
    return f"已保存: {path.absolute()} ({size} 字节)"


@tool
def get_current_time() -> str:
    """获取当前日期和时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")

FILE_TOOLS = [read_file, list_directory, save_file, get_current_time]
