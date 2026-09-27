# agent.py
import requests
import nest_asyncio

nest_asyncio.apply()  # makes crew.kickoff() safe inside Streamlit's event loop

from crewai import Agent, Task, Crew, Process

from llm import build_llm
from tools.search_tools import web_search
from tools.map_tools import competitor_map_search


def read_github_readme(repo_url: str) -> str:
    if not repo_url:
        return ""
    normalized_url = repo_url.rstrip("/")
    try:
        for branch in ["main", "master"]:
            raw_url = normalized_url.replace("github.com", "raw.githubusercontent.com", 1) + f"/{branch}/README.md"
            response = requests.get(raw_url, timeout=15)
            if response.status_code == 200:
                return response.text[:8000]
    except Exception:
        pass
    return ""


def _build_context(business_description: str, business_type: str, city: str,
                   budget: str, repo_url: str = None) -> str:
    context = (
        f"Business description:\n{business_description or 'Not provided.'}\n\n"
        f"Business type: {business_type}\n"
        f"Target city/area: {city}\n"
        f"Approximate budget: {budget or 'Not specified.'}\n"
    )
    readme_content = read_github_readme(repo_url)
    if readme_content:
        context += f"\nGitHub README (tech product context):\n{readme_content}\n"
    return context


def _agent_specs() -> list:
    return [
        {
            "key": "market_research",
            "role": "Market Research Analyst",
            "goal": "Analyze the market, demand, and competitors for the given business in the given city",
            "backstory": "An analyst specialized in emerging markets with limited structured data.",
            "description": (
                "Analyze the market for this business: demand level, target customers, "
                "main competitors in the area, typical price ranges, and local market gaps. "
                "Use the Web Search tool for recent information."
            ),
            "expected_output": "A concise market analysis with competitors and demand summary.",
            "use_search": True,
            "use_map": False,
        },
        {
            "key": "location_feasibility",
            "role": "Location & Feasibility Analyst",
            "goal": "Recommend the best areas and give an initial feasibility estimate",
            "backstory": "Expert in geospatial analysis and local commercial feasibility.",
            "description": (
                "Based on the market analysis, recommend the 2-3 best areas/neighborhoods in the "
                "target city for this business, with pros and cons of each, and give an initial "
                "feasibility estimate: startup cost range and expected monthly running cost. "
                "Use the Competitor Map Search tool to get REAL competitor data from OpenStreetMap."
            ),
            "expected_output": "2-3 recommended areas with pros/cons and an initial feasibility estimate.",
            "use_search": False,
            "use_map": True,
        },
        {
            "key": "marketing_sales",
            "role": "Marketing & Sales Strategist",
            "goal": "Design an initial go-to-market and sales plan",
            "backstory": "A pragmatic strategist for early-stage startups with small budgets.",
            "description": (
                "Design an initial go-to-market plan: a positioning statement, the 2-3 best marketing "
                "channels for a small budget, the launch message, and a simple 90-day sales plan."
            ),
            "expected_output": "A practical go-to-market plan with channels, message, and 90-day sales steps.",
            "use_search": False,
            "use_map": False,
        },
        {
            "key": "inputs_resources",
            "role": "Inputs & Resources Planner",
            "goal": "List the essential inputs the business needs to produce its outputs",
            "backstory": "An operations planner who maps what a business needs to start producing.",
            "description": (
                "List the essential INPUTS this business needs to operate, grouped by category: "
                "raw materials, equipment, and digital tools/resources, with an estimated cost range "
                "for each category. "
                "IMPORTANT: only input categories — never name or recommend specific suppliers or vendors."
            ),
            "expected_output": "A categorized list of required inputs (materials, equipment, digital tools) with cost ranges.",
            "use_search": False,
            "use_map": False,
        },
    ]


EDITOR_SPEC = {
    "role": "Launch Report Editor",
    "goal": "Merge all analyses into one clear, structured launch report",
    "backstory": "An editor who turns multi-agent analyses into actionable founder-ready reports.",
}


def _pick_tools(spec: dict) -> list:
    tools = []
    if spec.get("use_search"):
        tools.append(web_search)
    if spec.get("use_map"):
        tools.append(competitor_map_search)
    return tools


def _make_agent(spec: dict, llm) -> Agent:
    return Agent(
        role=spec["role"],
        goal=spec["goal"],
        backstory=spec["backstory"],
        llm=llm,
        tools=_pick_tools(spec),
        verbose=True,
    )


def _run_single_task(context: str, spec: dict, extra_context: str = "") -> str:
    agent = _make_agent(spec, build_llm())
    task = Task(
        description=f"{context}\n\n{extra_context}\n\n{spec['description']}".strip(),
        expected_output=spec["expected_output"],
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    return str(crew.kickoff())  # sync — safe inside Streamlit thanks to nest_asyncio


def run_launch_plan(business_description: str = "", business_type: str = "", city: str = "",
                    budget: str = "", repo_url: str = None, on_section_done=None) -> dict:
    """
    Staged execution — each agent's output appears live in the UI as soon as
    it's done, and every stage receives the accumulated previous outputs.
    """
    context = _build_context(business_description, business_type, city, budget, repo_url)

    results = {}
    accumulated = ""
    for spec in _agent_specs():
        result = _run_single_task(context, spec, extra_context=accumulated)
        results[spec["key"]] = result
        accumulated += f"\n\n--- {spec['role']} output ---\n{result}"
        if on_section_done:
            on_section_done(spec["key"], result)

    editor = Agent(
        role=EDITOR_SPEC["role"],
        goal=EDITOR_SPEC["goal"],
        backstory=EDITOR_SPEC["backstory"],
        llm=build_llm(),
        verbose=True,
    )
    report_task = Task(
        description=(
            f"{context}\n{accumulated}\n\n"
            "Merge all the previous analyses into ONE structured launch report with sections: "
            "1) Market Summary 2) Recommended Locations 3) Feasibility Estimate "
            "4) Go-to-Market Plan 5) Required Inputs & Resources 6) Recommended Next Steps. "
            "Keep it clear, concise, and immediately actionable. Do not add information "
            "that is not in the previous analyses."
        ),
        expected_output="A single well-structured launch report in markdown with the 6 sections.",
        agent=editor,
    )
    crew = Crew(agents=[editor], tasks=[report_task], verbose=True)
    results["final_report"] = str(crew.kickoff())
    return results


def create_launch_crew(business_description: str = "", business_type: str = "", city: str = "",
                       budget: str = "", repo_url: str = None) -> Crew:
    """One sequential crew: 4 agents + final editor (CrewAI passes context automatically)."""
    context = _build_context(business_description, business_type, city, budget, repo_url)
    llm = build_llm()

    agents, tasks = [], []
    for spec in _agent_specs():
        agent = _make_agent(spec, llm)
        tasks.append(Task(
            description=f"{context}\n\n{spec['description']}",
            expected_output=spec["expected_output"],
            agent=agent,
        ))
        agents.append(agent)

    editor = Agent(
        role=EDITOR_SPEC["role"],
        goal=EDITOR_SPEC["goal"],
        backstory=EDITOR_SPEC["backstory"],
        llm=llm,
        verbose=True,
    )
    tasks.append(Task(
        description=(
            f"{context}\n\n"
            "Merge all the previous analyses into ONE structured launch report with sections: "
            "1) Market Summary 2) Recommended Locations 3) Feasibility Estimate "
            "4) Go-to-Market Plan 5) Required Inputs & Resources 6) Recommended Next Steps."
        ),
        expected_output="A single well-structured launch report in markdown with the 6 sections.",
        agent=editor,
    ))

    return Crew(agents=agents + [editor], tasks=tasks, process=Process.sequential, verbose=True)