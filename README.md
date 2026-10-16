# 🛡️ DAS-re: Autonomous Voice SRE & Zero-Trust Cloud Operator

> **Daytona HackSprint #6** — Friday, October 16, 2026 @ JFK27 Basement, 12 W 39th St, New York, NY  
> Built by **Ayush Shivhare, Sampat & Team**

---

## 🌟 The Problem & Mission
At 2:15 AM on a Saturday, production microservices collapse. PagerDuty is screaming. The on-call SRE is groggy in bed or driving. Today's triage requires fumbling through 14 open browser tabs, deciphe[...]

**Aegis** is an autonomous Voice SRE that bridges conversational voice intelligence with zero-trust cloud orchestration:
1. **Wakes the SRE over natural conversational voice** using ultra-low-latency bidirectional streaming (**ElevenLabs**).
2. **Reconnoiters dynamic web consoles & status dashboards** without API limits using stealth headless cloud browsers (**Anchor Browser**).
3. **Retrieves past incident topologies and postmortem solutions** using multi-model vector embeddings and dependency graphs (**SurrealDB**).
4. **Intercepts and evaluates every remediation action** through zero-trust security guardrails, **E2E OpenInference traces**, and **continue/terminate feedback gates** that block hallucinated or dest[...]
5. **Ephemerally reproduces the bug, runs tests, and applies code patches** inside 100% isolated, reproducible cloud developer environments (**Daytona**).

---

## 🏛️ 5-Way Sponsor Architecture

```
🎙️ ElevenLabs (Bidirectional Streaming <300ms)
         │
         ▼
🧠 Aegis Core Orchestrator (LangGraph / AsyncIO)
   ├── 🌐 Anchor Browser (Stealth Cloud Telemetry Recon without API keys)
   ├── 🗄️ SurrealDB (SurrealQL Vector Postmortem Search + Microservice Dependency Graph)
   ├── 🛡️ Arize AI Phoenix (OpenInference Trace Spans + Zero-Trust Destructive Command Veto)
   └── ⚡ Daytona (Ephemeral CDE Workspace `daytona.create()` -> Test -> Patch -> Destroy)
```

---

## 🚀 Quickstart & Team Setup

### 1. Installation
```bash
git clone https://github.com/Shivhare-Ayush/DAS-re.git
cd DAS-re

# Install dependencies with uv (or pip)
uv venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### 2. Environment Configuration
```bash
cp .env.template .env
# Edit .env with your sponsor API keys (or leave defaults for IS_MOCK_MODE=True)
```

### 3. Run the Deterministic Live Demo
```bash
python main.py --demo
```

### 4. Run Subsystem Test Suites
```bash
# Run all tests
pytest

# Test individual workstreams
pytest tests/test_core_schemas.py
pytest tests/test_arize_guardrails.py
pytest tests/test_daytona_runner.py
pytest tests/test_voice_stream.py
pytest tests/test_anchor_scrapers.py
pytest tests/test_surreal_memory.py
pytest tests/test_orchestrator.py
```

---

## 👥 3-Developer Conflict-Free Vibecoding Protocol

To eliminate git merge conflicts during rapid hackathon sprints:
1. **Frozen Core Rule:** `core/schemas.py` and `core/config.py` are frozen. No edits without team standup.
2. **Strict Folder Isolation:**
   - **Ayush (Lead):** `agent/voice/` + `agent/evals/` + `agent/orchestrator.py`
   - **Dev 2:** `agent/sandbox/` + `scenarios/` + `tests/daytona/`
   - **Dev 3:** `agent/browser/` + `agent/memory/` + `pitch/`
3. **Mock Client First:** Every client extends its respective mock to guarantee 100% demo uptime on hackathon Wi-Fi.

---

## 🎤 3-Minute Live Stage Pitch Script (180 Seconds)
See [`obsidian-code-agent/tasks/2026-10-16-001/030-plan.md`](../obsidian/obsidian-code-agent/tasks/2026-10-16-001/030-plan.md) for the second-by-second stage presentation walkthrough!

```
