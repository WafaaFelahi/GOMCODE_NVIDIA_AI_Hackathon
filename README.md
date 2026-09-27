🚀 Startup Launch Copilot
An Agentic AI platform that turns weeks of early-stage startup research into a launch-ready report — in minutes — running entirely on NVIDIA GPU infrastructure.

Built for the GOMYCODE × NVIDIA "Come Build With AI" Hackathon.

💡 The Problem
Early-stage founders spend weeks and significant money on market research, location analysis, and go-to-market planning — often with unstructured, hard-to-find data in local markets.

🧠 The Solution
A multi-agent AI system (CrewAI) where specialized agents collaborate to produce one actionable launch report:

Agent	Role
📊 Market Research Analyst	Demand, customers, competitors, price ranges, market gaps — using live web search
📍 Location & Feasibility Analyst	Recommends the 2–3 best areas with pros/cons + initial cost estimates — using real competitor data from OpenStreetMap (Nominatim + Overpass API)
📣 Marketing & Sales Strategist	Positioning, best low-budget channels, launch message, 90-day sales plan
🧰 Inputs & Resources Planner	Maps the essential inputs (materials, equipment, digital tools) needed to operate
📝 Launch Report Editor	Merges everything into ONE structured, founder-ready report
The user provides 3 inputs: business type, target city/area, and budget — and watches the agents work live.

🟩 NVIDIA Stack (How We Use Brev)
All agent inference runs on an NVIDIA A10G GPU instance launched via NVIDIA Brev (allocated voucher credits):

The instance serves nvidia/Llama-3.1-Nemotron-Nano-8B-v1 through vLLM, exposing an OpenAI-compatible endpoint on port 8000
All 5 CrewAI agents consume this endpoint
Port forwarding bridges the local Streamlit UI to the remote GPU
The inference backend is swappable by changing 3 environment variables only (Brev GPU → NVIDIA NIM API → Groq fallback), making the demo resilient
This usage of allocated NVIDIA Brev credits is part of the AI-use criterion: every LLM call in the demo is served by vLLM on the Brev NVIDIA GPU.

🛠️ Tech Stack
CrewAI — multi-agent orchestration
vLLM on NVIDIA Brev (A10G) — model serving (nvidia/Llama-3.1-Nemotron-Nano-8B-v1)
OpenStreetMap (Nominatim + Overpass API) — real geospatial competitor data, free, no API key
DDGS — free web search
Streamlit + Folium — live UI with interactive competitor map
🚀 Run It
Serve the model (on the Brev instance, inside tmux):
vllm serve nvidia/Llama-3.1-Nemotron-Nano-8B-v1 --port 8000 --max-model-len 8192
Forward the port (locally):
bash

brev port-forward seedora -p 8000:8000
Configure .env (copy from .env.example):
text

LLM_BASE_URL=http://localhost:8000/v1
MODEL_NAME=nvidia/Llama-3.1-Nemotron-Nano-8B-v1
LLM_API_KEY=not-needed
Launch:
bash

pip install -r requirements.txt
streamlit run app.py
🎬 Demo Scenario
"A founder wants to open a specialty café in Constantine, Algeria with a $10,000 budget."

Input: café · Constantine, Algeria · $10,000
The agents run live, the location agent queries OpenStreetMap for real competitor density
Output: one launch report — market summary, recommended locations, feasibility estimate, go-to-market plan, required inputs — plus an interactive competitor map
🔮 Roadmap
Expand industry coverage (OSM tag mapping)
Financial projections with editable assumptions
Multi-language reports (FR/AR) for local founders
Built with 🖤 and NVIDIA GPU power for the GOMYCODE × NVIDIA Hackathon.

