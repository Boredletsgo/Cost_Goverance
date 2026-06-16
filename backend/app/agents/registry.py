"""Agent registry."""
from __future__ import annotations

from typing import Dict

from app.agents.base import BaseAgent
from app.agents.cost_agent import CostIntelligenceAgent
from app.agents.executive_agent import ExecutiveIntelligenceAgent
from app.agents.incident_agent import IncidentIntelligenceAgent
from app.agents.optimization_agent import OptimizationAgent
from app.agents.security_agent import SecurityIntelligenceAgent

AGENTS: Dict[str, BaseAgent] = {
    CostIntelligenceAgent.name: CostIntelligenceAgent(),
    IncidentIntelligenceAgent.name: IncidentIntelligenceAgent(),
    SecurityIntelligenceAgent.name: SecurityIntelligenceAgent(),
    OptimizationAgent.name: OptimizationAgent(),
    ExecutiveIntelligenceAgent.name: ExecutiveIntelligenceAgent(),
}


def get_agent(name: str) -> BaseAgent:
    if name not in AGENTS:
        raise KeyError(f"Unknown agent: {name}")
    return AGENTS[name]
