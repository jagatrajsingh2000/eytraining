from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from app.agents.meal_analyzer_agent import meal_analyzer_agent
from app.agents.health_risk_agent import health_risk_agent
from app.agents.report_agent import report_agent


def build_graph():
    workflow = StateGraph(dict)
    workflow.add_node("meal_analyzer", meal_analyzer_agent)
    workflow.add_node("health_risk", health_risk_agent)
    workflow.add_node("report", report_agent)

    workflow.set_entry_point("meal_analyzer")
    workflow.add_edge("meal_analyzer", "health_risk")
    workflow.add_edge("health_risk", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


graph = build_graph()
