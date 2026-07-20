# AI Agent Studio 项目概述

## 架构设计
本项目采用多 Agent 协作架构，基于 LangChain 框架构建。

### 三个专业 Agent
1. **Researcher Agent**: 负责 RAG 检索和信息分析
2. **Coder Agent**: 负责代码审查和 Bug 检测
3. **Writer Agent**: 负责报告生成和简报撰写

### 技术栈
- FastAPI 异步 Web 框架
- LangChain Agent 框架
- ChromaDB 向量数据库
- DeepSeek 大语言模型
- Sentence Transformers 文本嵌入

## RAG 工作流程
1. 文档加载 -> 文本分块
2. 文本嵌入 -> 向量存储
3. 用户查询 -> 向量检索
4. 检索结果 + 上下文 -> LLM 生成回答

## Tool Use 机制
每个 Agent 可以调用外部工具:
- search_knowledge: 搜索本地知识库
- read_file_tool: 读取本地文件
- list_dir_tool: 列出目录内容
- save_report_tool: 保存报告
- get_time_tool: 获取当前时间
