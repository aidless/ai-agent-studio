"""Multi-Agent Orchestrator - task routing + Pipeline coordination"""
from datetime import datetime
from app.agents.researcher import ResearcherAgent
from app.agents.coder import CoderAgent
from app.agents.writer import WriterAgent


class Orchestrator:
    def __init__(self):
        self.researcher = ResearcherAgent()
        self.coder = CoderAgent()
        self.writer = WriterAgent()
        self._tasks = {"research": self.researcher, "coder": self.coder, "writer": self.writer}

    def run(self, agent_type: str, task: str) -> dict:
        agent = self._tasks.get(agent_type)
        if not agent:
            return {"error": f"Unknown agent: {agent_type}", "available": list(self._tasks.keys())}
        start = datetime.now()
        result = agent.invoke(task)
        elapsed = (datetime.now() - start).total_seconds()
        return {"agent": agent.name, "task": task[:200], "result": result, "elapsed_seconds": round(elapsed, 1), "time": datetime.now().isoformat()}

    async def arun(self, agent_type: str, task: str) -> dict:
        agent = self._tasks.get(agent_type)
        if not agent:
            return {"error": f"Unknown agent: {agent_type}", "available": list(self._tasks.keys())}
        start = datetime.now()
        result = await agent.ainvoke(task)
        elapsed = (datetime.now() - start).total_seconds()
        return {"agent": agent.name, "task": task[:200], "result": result, "elapsed_seconds": round(elapsed, 1), "time": datetime.now().isoformat()}

    def pipeline(self, task: str, steps: list[str] = None) -> dict:
        if steps is None:
            steps = ["research", "coder", "writer"]
        current = task
        results = []
        for step in steps:
            r = self.run(step, current)
            if "error" not in r:
                results.append({"step": step, "agent": r["agent"], "output": r["result"][:500]})
                current = f"Original task: {task}\nPrevious step [{step}] output:\n{r['result']}"
        return {"pipeline": steps, "steps": results, "final_output": results[-1]["output"] if results else "", "time": datetime.now().isoformat()}

    def list_agents(self) -> list[dict]:
        return [{"type": k, "name": v.name, "description": v.description, "tools": [t.name for t in v.tools]} for k, v in self._tasks.items()]
