# AI Agent Studio 架构设计文档

## 系统概述

AI Agent Studio 是一个基于 LangChain 框架的多 Agent 协作平台，集成了 RAG (检索增强生成) 能力，支持多个专业 Agent 协同完成复杂任务。

## 技术架构

```
┌─────────────────────────────────────┐
│           FastAPI Web Layer          │
│    /api/v1/agent/*   /api/v1/rag/*  │
├─────────────────────────────────────┤
│         Orchestrator 协调器          │
│    ┌──────────┬──────────┬────────┐ │
│    │Researcher│  Coder   │ Writer │ │
│    │  Agent   │  Agent   │ Agent  │ │
│    └────┬─────┴────┬─────┴───┬────┘ │
├─────────┼──────────┼─────────┼──────┤
│  Tools  │ File R/W │Code Scan│Save  │
├─────────┼──────────┼─────────┼──────┤
│   RAG   │ChromaDB Vector Store      │
│         │Document Loader & Chunker  │
├─────────┴───────────────────────────┤
│         DeepSeek LLM API             │
└─────────────────────────────────────┘
```

## RAG 工作流程

1. **文档加载**: DocumentLoader 扫描知识库目录，支持 .md / .txt / .py / .json / .html
2. **智能分块**: 按段落 + 代码块结构切分，块大小 600 字符，重叠 80 字符
3. **向量存储**: ChromaDB 持久化，all-MiniLM-L6-v2 embedding
4. **检索增强**: 用户 Query → 向量相似度检索 Top-K → 拼接上下文 → LLM 生成

## Agent 设计

### Researcher Agent
- **职责**: 知识检索 + 深度分析
- **工具**: search_knowledge, read_file, list_directory, get_current_time
- **工作流**: 检索 → 阅读 → 综合分析 → 结论

### Coder Agent
- **职责**: 代码审查 + Bug检测 + 质量评估
- **工具**: read_file, list_directory, get_current_time
- **审查维度**: 安全漏洞、逻辑Bug、代码质量、性能、架构

### Writer Agent
- **职责**: 报告撰写
- **工具**: search_context, save_file, get_current_time
- **输出**: Markdown 格式日报/周报/技术文档

## Multi-Agent Pipeline

```
用户任务 → Researcher(调研) → Coder(审查) → Writer(报告)
                ↓                 ↓              ↓
            知识库检索        代码分析        生成文档
```
