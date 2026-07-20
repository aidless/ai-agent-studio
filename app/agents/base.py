"""LangChain Agent infrastructure - compatible with LangChain >= 1.0"""
import json, os, asyncio
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from app.config import settings


class LLMFactory:
    _instance: Optional[BaseChatModel] = None

    @classmethod
    def create(cls, temperature: float = None, max_tokens: int = None) -> BaseChatModel:
        return ChatOpenAI(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=temperature or settings.temperature,
            max_tokens=max_tokens or settings.max_tokens,
        )

    @classmethod
    def instance(cls) -> BaseChatModel:
        if cls._instance is None:
            cls._instance = cls.create()
        return cls._instance


class BaseAgent:
    """Agent base class using LangGraph's create_react_agent"""

    SYSTEM_PROMPT = "You are a helpful AI assistant. Reply in Chinese."
    name: str = "base"
    description: str = "Base Agent"

    def __init__(self, tools: list[BaseTool] = None, temperature: float = 0.7):
        self.llm = LLMFactory.create(temperature=temperature)
        self.tools = tools or []
        self._executor = None

    def _build_executor(self):
        if self._executor is not None:
            return self._executor
        from langgraph.prebuilt import create_react_agent
        self._executor = create_react_agent(self.llm, self.tools, prompt=self.SYSTEM_PROMPT)
        return self._executor

    def invoke(self, task: str, **kwargs) -> str:
        try:
            executor = self._build_executor()
            result = executor.invoke({"messages": [("user", task)]})
            msgs = result.get("messages", [])
            if msgs:
                last = msgs[-1]
                return last.content if hasattr(last, 'content') else str(last)
            return str(result)
        except Exception as e:
            return f"[Agent error] {e}"

    async def ainvoke(self, task: str, **kwargs) -> str:
        try:
            executor = self._build_executor()
            result = await executor.ainvoke({"messages": [("user", task)]})
            msgs = result.get("messages", [])
            if msgs:
                last = msgs[-1]
                return last.content if hasattr(last, 'content') else str(last)
            return str(result)
        except Exception as e:
            return f"[Agent error] {e}"
