# app.py
import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from streamlit_folium import st_folium

from agent import run_launch_plan
from tools.map_tools import build_demo_map

st.set_page_config(page_title="Startup Launch Copilot", page_icon="🚀", layout="wide")
st.title("🚀 Startup Launch Copilot")
st.caption("Multi-agent launch report: market · location · go-to-market · required inputs — in minutes.")

SECTION_TITLES = {
    "market_research": "📊 Market Research",
    "location_feasibility": "📍 Location & Feasibility",
    "marketing_sales": "📣 Marketing & Sales Plan",
    "inputs_resources": "🧰 Required Inputs & Resources",
}

with st.sidebar:
    st.header("Your startup")
    business_type = st.text_input("Business type *", "café")
    city = st.text_input("Target city / area *", "Constantine, Algeria")
    budget = st.text_input("Approximate budget", "$10,000")
    business_description = st.text_area(
        "Describe your idea",
        "A specialty coffee shop for students and remote workers.",
    )
    repo_url = st.text_input("GitHub repo (tech products, optional)", "")

    run_btn = st.button("Generate Launch Report", type="primary",
                        disabled=not (business_type and city))

    st.divider()
    saved_path = "demo_outputs/launch_report.md"
    if os.path.exists(saved_path):
        if st.button("📼 Load saved demo report"):
            st.session_state["fallback_report"] = open(saved_path, encoding="utf-8").read()

if "fallback_report" in st.session_state:
    st.markdown(st.session_state["fallback_report"])
    m = build_demo_map(business_type, city)
    if m:
        st_folium(m, height=450)
    st.stop()

if run_btn:
    with st.status("🤖 Agents at work…", expanded=True) as status:
        slots = {k: st.container() for k in SECTION_TITLES}

        def on_done(key, text):
            with slots[key]:
                st.markdown(f"#### {SECTION_TITLES[key]}")
                st.markdown(text)

        results = run_launch_plan(
            business_description=business_description,
            business_type=business_type,
            city=city,
            budget=budget,
            repo_url=repo_url or None,
            on_section_done=on_done,
        )
        status.update(label="✅ All agents finished", state="complete", expanded=False)

    st.subheader("📄 Launch Report")
    st.markdown(results["final_report"])

    st.subheader("📍 Competitor Map (OpenStreetMap)")
    m = build_demo_map(business_type, city)
    if m:
        st_folium(m, height=450)
    else:
        st.info("Map unavailable for this city.")

    with st.expander("🔎 Individual agent outputs"):
        for key, title in SECTION_TITLES.items():
            st.markdown(f"#### {title}")
            st.markdown(results.get(key, "_not available_"))

    os.makedirs("demo_outputs", exist_ok=True)
    with open("demo_outputs/launch_report.md", "w", encoding="utf-8") as f:
        f.write(results["final_report"])