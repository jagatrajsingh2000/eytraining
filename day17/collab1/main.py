from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ROOT_ENV = BASE_DIR.parents[1] / ".env"
os.environ.setdefault("CREWAI_STORAGE_DIR", str(BASE_DIR / ".crewai_storage"))
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
load_dotenv(ROOT_ENV, override=True)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
REPORT_PATH = OUTPUT_DIR / "globalflow_disruption_report.txt"

from crewai import Agent, Crew, LLM, Process, Task
from crewai.tools import BaseTool
from crewai_tools import FileWriterTool


def groq_llm(model_name: str) -> LLM:
    return LLM(
        model=model_name,
        provider="openai",
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
    )


class MockSearchTool(BaseTool):
    name: str = "web_search"
    description: str = "Search the web for supply-chain disruption news and routing alternatives."

    def _run(self, query: str) -> str:
        return (
            f"[SIMULATED SEARCH] Results for: '{query}'\n"
            "Rotterdam: 18h closure, storm surge, severity 8/10\n"
            "Alternative 1 - Hamburg: +5h, -6% cost, low risk\n"
            "Alternative 2 - Felixstowe: +8h, -10% cost, medium risk\n"
            "Alternative 3 - Antwerp: +3h, +2% cost, low risk\n"
            "Singapore PSA: normal operations, no disruption\n"
        )


def build_agents():
    search_tool = MockSearchTool()
    writer_tool = FileWriterTool()
    groq_fast = groq_llm("llama-3.1-8b-instant")
    groq_smart = groq_llm("llama-3.3-70b-versatile")
    disruption_monitor = Agent(
        role="Supply Chain Disruption Monitor",
        goal="Scan disruptions, quantify severity, and identify affected corridors and shipments.",
        backstory="Veteran logistics intelligence analyst with strong crisis triage instincts.",
        llm=groq_smart,
        tools=[search_tool],
        verbose=True,
        max_iter=4,
    )
    route_optimiser = Agent(
        role="Logistics Route Optimiser",
        goal="Rank 3 alternative shipment routes by cost, delay, and operational risk.",
        backstory="Operations research specialist focused on routing tradeoffs.",
        llm=groq_smart,
        tools=[search_tool],
        verbose=True,
        max_iter=4,
    )
    supplier_comms = Agent(
        role="Supplier Communications Specialist",
        goal="Draft urgent but collaborative supplier and carrier communications.",
        backstory="Senior procurement manager skilled at crisis communication.",
        llm=groq_fast,
        verbose=True,
        max_iter=3,
    )
    compliance_officer = Agent(
        role="Trade Compliance Officer",
        goal="Check customs, sanctions, and route compliance risk before execution.",
        backstory="Certified customs specialist with zero tolerance for trade shortcuts.",
        llm=groq_smart,
        tools=[search_tool],
        verbose=True,
        max_iter=4,
    )
    report_writer = Agent(
        role="Executive Communications Writer",
        goal="Produce a concise executive disruption briefing with next steps.",
        backstory="Board-level crisis communications specialist.",
        llm=groq_smart,
        tools=[writer_tool],
        verbose=True,
        max_iter=3,
    )
    return disruption_monitor, route_optimiser, supplier_comms, compliance_officer, report_writer


def build_tasks(agents):
    disruption_monitor, route_optimiser, supplier_comms, compliance_officer, report_writer = agents
    task_monitor = Task(
        description="Search active logistics disruptions affecting Rotterdam, Singapore, Houston, and the AE-1 lane. Start with 'SEVERITY: X/10'.",
        expected_output="Structured disruption report with severity, duration, affected corridors, and shipment impact.",
        agent=disruption_monitor,
    )
    task_route = Task(
        description="Using the disruption report, calculate 3 alternative routes with cost delta, delay, risk score, and a ranked recommendation.",
        expected_output="Ranked route table with rationale for the top choice.",
        agent=route_optimiser,
        context=[task_monitor],
    )
    task_comms = Task(
        description="Draft 3 supplier communications explaining disruption, rerouting proposal, and 4-hour confirmation request.",
        expected_output="Three email drafts with subject line and body.",
        agent=supplier_comms,
        context=[task_monitor, task_route],
    )
    task_compliance = Task(
        description="Review the top reroute for customs, sanctions, and certificate-of-origin risk. Return CLEARED or HOLD.",
        expected_output="Compliance status with remediation notes and timing considerations.",
        agent=compliance_officer,
        context=[task_route],
    )
    task_report = Task(
        description=(
            "Compile all outputs into a 400-word executive briefing with headings "
            "SITUATION, IMPACT, RESPONSE, NEXT STEPS. Save to globalflow_disruption_report.txt."
        ),
        expected_output="One-page executive briefing saved to disk.",
        agent=report_writer,
        context=[task_monitor, task_route, task_comms, task_compliance],
        output_file=str(REPORT_PATH),
    )
    return [task_monitor, task_route, task_comms, task_compliance, task_report]


def build_fallback_report() -> str:
    return """SITUATION:
Port of Rotterdam has declared force majeure due to a severe storm surge. Estimated closure is 18-24 hours and 340 containers are at risk of delay. SLA breach exposure begins within 6 hours.

IMPACT:
EU hub shipments are most affected. Likely consequences include customer delivery delay, carrier rescheduling pressure, and increased cross-border coordination workload. Cost exposure is elevated due to delay penalties and urgent rerouting.

RESPONSE:
Primary reroute recommendation is Antwerp because it minimizes delay with low operational risk. Secondary options are Hamburg and Felixstowe. Supplier communications should request 4-hour confirmation on revised movement plans. Compliance review should confirm customs handling and country-of-transit implications before execution.

NEXT STEPS:
1. Route Operations Owner: confirm Antwerp diversion decision within 1 hour.
2. Supplier Communications Owner: send carrier and supplier notices within 2 hours.
3. Compliance Owner: complete customs and sanctions review before dispatch release."""


def write_fallback_files(report_text: str) -> None:
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    (OUTPUT_DIR / "crew_run.log").write_text("Fallback mode used because Groq API connection failed.\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Day 17 collab1 CrewAI supply-chain pipeline.")
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Call Groq remotely through CrewAI. Without this flag, the script uses offline fallback mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.remote and not os.getenv("GROQ_API_KEY"):
        raise RuntimeError(f"GROQ_API_KEY not found in {ROOT_ENV}. Add it there before running.")
    if not os.getenv("TAVILY_API_KEY"):
        print("TAVILY_API_KEY not found in root .env. Using built-in mock search tool.")

    trigger_input = {
        "disruption_alert": (
            "ALERT: Port of Rotterdam has declared force majeure due to a severe North Sea storm surge. "
            "Expected closure: 18-24 hours. 340 containers are currently docked and client SLA breach "
            "windows open in 6 hours."
        )
    }
    if not args.remote:
        print("[ALERT] Offline mode enabled. Building fallback disruption report.")
        final_report = build_fallback_report()
        write_fallback_files(final_report)
        print("\nFINAL EXECUTIVE BRIEFING\n")
        print(final_report)
        print(f"\nReport path: {REPORT_PATH}")
        return

    agents = build_agents()
    tasks = build_tasks(agents)
    crew = Crew(
        agents=list(agents),
        tasks=tasks,
        process=Process.hierarchical,
        manager_llm=groq_llm("llama-3.3-70b-versatile"),
        verbose=True,
        memory=True,
        output_log_file=str(OUTPUT_DIR / "crew_run.log"),
    )
    print("[ALERT] Triggering GlobalFlow disruption response crew")
    try:
        result = crew.kickoff(inputs=trigger_input)
        final_report = result.raw
    except Exception as exc:
        print(f"Remote Groq execution unavailable: {exc}")
        print("Switching to offline fallback report generation.")
        final_report = build_fallback_report()
        write_fallback_files(final_report)
    print("\nFINAL EXECUTIVE BRIEFING\n")
    print(final_report)
    print(f"\nReport path: {REPORT_PATH}")


if __name__ == "__main__":
    main()
