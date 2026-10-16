# 🎤 Pitch Deck Context & Slide-by-Slide Blueprint: Aegis

> **Event:** Daytona HackSprint #6 w/ Arize AI (Friday, Oct 16, 2026 @ JFK27 Basement, NYC)  
> **Target Track:** 1st Place Overall ($3,000 Cash + $10k credits) + Best Use of SurrealDB / Daytona / Arize / ElevenLabs / Anchor  
> **Presentation Window:** Strictly **3 Minutes (180 Seconds)** + 2 Minutes Q&A  
> **Team:** Ayush Shivhare, Sampat & Team  
> **Live GitHub:** https://github.com/Shivhare-Ayush/aegis-sre

---

## 🧭 Executive Narrative Arc (The Emotional Hook)
* **The Villain:** **Institutional Amnesia at 2:15 AM.**  
  When production crashes in the dead of night, on-call engineers aren't slow because they can't code—they're slow because institutional memory is fragmented across Slack, outdated Notion docs, and stale postmortems. They waste 45 minutes answering: *"Has this happened before? Who fixed it, and what was the diff?"*
* **The Hero:** **Aegis — The Autonomous On-Call SRE with Photographic Memory.**  
  An incident assistant that instantly recalls past root causes, graphs the blast radius across microservices, and spins up an ephemeral cloud sandbox in Daytona to verify the fix before touching live production.
* **The Punchline:** *"You don't fight cloud fires at 2:00 AM anymore. With Aegis, you sleep through the outage."*

---

## 📊 Slide-by-Slide Blueprint (6 Slides | Exactly 3 Minutes)

```
[Slide 1: Hook (0:00 - 0:30)] ──> The 2:15 AM SRE Nightmare
[Slide 2: Problem (0:30 - 0:55)] ──> Institutional Amnesia
[Slide 3: Solution (0:55 - 1:25)] ──> Aegis Multi-Model Architecture
[Slide 4: Live Demo (1:25 - 2:25)] ──> 3-Step Incident Recall & Verification
[Slide 5: Secret Moat (2:25 - 2:45)] ──> Zero-Trust Sandboxing & Shift Handover
[Slide 6: Vision & Close (2:45 - 3:00)] ──> Sleep Through the Outage
```

---

### Slide 1: Title & The Emotional Hook (0:00 – 0:30)
* **Header:** **Aegis**
* **Subheader:** The Autonomous Voice SRE with Photographic Memory
* **Visual:** Dark-mode SRE terminal with a stark red PagerDuty alert: `CRITICAL: auth-gateway 504 Timeout Spike (94.2%)`.
* **Speaker Script (Ayush):**
  > *"It’s 2:15 AM on a Saturday. Your phone screams. PagerDuty alert. Production is burning, users can't log in, and you are groggy in bed. Today, your only option is opening 14 browser tabs, deciphering cryptic stack traces, and praying you don't mistype a command that turns a minor hiccup into a multi-million-dollar outage. We built Aegis so on-call engineers never fight outages alone."*

---

### Slide 2: The Core Problem — "Institutional Amnesia" (0:30 – 0:55)
* **Header:** The Real Cost of Outages: Institutional Amnesia
* **Visual / 3 Pain Points:**
  1. **Forgotten Postmortems:** Past incident resolutions buried in stale Notion docs and Slack threads.
  2. **Shift Handover Blindspots:** Rotating on-call engineers have zero context on what the previous shift saw.
  3. **Fear of Execution:** LLMs running uncontained commands directly on production clusters.
* **Key Stat Callout:** *"70% of MTTR (Mean Time to Resolution) is spent diagnosing what broke, not fixing it."*
* **Speaker Script:**
  > *"The dirty secret of tech is that most outages aren't brand new. They've happened before. But at 2:00 AM, sleep-deprived engineers suffer from institutional amnesia. Who touched this service last? Did this lock fail last month? What was the fix? Today's tools don't remember."*

---

### Slide 3: The Architecture — 5 Sponsors as One Superpower (0:55 – 1:25)
* **Header:** Meet Aegis: Built on 5 Next-Gen Agent Protocols
* **Visual:** Clean modular system diagram showing how the 5 sponsors form an unbroken loop:
  * **SurrealDB:** Multi-Model Incident Memory (Vector Postmortems + Service Graph + Shift Scopes).
  * **Daytona:** Ephemeral Cloud Sandbox (Zero-risk test reproduction & patch verification).
  * **Arize AI Phoenix:** Zero-Trust Guardrails & OpenInference Tracing (*"A wrong answer returns 200"*).
  * **ElevenLabs:** Real-Time Duplex Voice Stream (<300ms audio dialogue).
  * **Anchor Browser:** Headless Cloud Telemetry Recon (Live Grafana/AWS canvas inspection).
* **Speaker Script:**
  > *"Aegis combines five breakthrough technologies into a unified incident copilot: ElevenLabs wakes you up with crisp voice streaming; Anchor Browser scrapes live Grafana telemetry without APIs; SurrealDB acts as the photographic memory brain; Arize Phoenix vetoes destructive hallucinated commands; and Daytona spins up isolated cloud sandboxes to verify the fix."*

---

### Slide 4: The Live Demo (1:25 – 2:25) — [THE CLIMAX]
* **Header:** Live Incident Triage: From Alert to Verified PR in 60s
* **Visual:** Split screen / Live Screen Share:
  * **Left:** ElevenLabs Voice dialogue + SurrealDB incident recall card (`INC-892 matched with 96% confidence`).
  * **Right:** Arize Phoenix trace view (Red Veto span on `FLUSHALL`) + Daytona CLI terminal verifying tests pass.
* **Speaker Flow & Voice Dialogue:**
  1. **Voice Alert:** ElevenLabs speaks: *"Ayush, wake up. auth-gateway is erroring at 94.2%. SurrealDB matched incident INC-892: Redis lock starvation."*
  2. **Safety Intercept:** Agent attempts `FLUSHALL`. Arize Phoenix triggers an instant **RED VETO** span. *"Command vetoed by Arize guardrails. Switching to surgical release."*
  3. **Daytona Verification:** Daytona spins up `ws-daytona-mock-42`, reproduces the failed pytest, applies surgical patch `finally: self.release(key)`, verifies 14 tests pass, and tears down the sandbox cleanly.
  4. **Voice Signoff:** *"Surgical lock release verified in Daytona. All tests passing. PR #42 opened. You can go back to sleep, Ayush."*

---

### Slide 5: The Secret Moat — Shift Handover & Zero-Trust Sandbox (2:25 – 2:45)
* **Header:** Why Enterprise SREs Trust Aegis
* **Visual:** Two comparison columns:
  * **The Competitor Approach (Unsafe):** Raw LLM with SSH access running uncontrolled bash on live production servers $\rightarrow$ High risk of catastrophic outage.
  * **The Aegis Approach (Zero-Trust):**
    1. **SurrealDB Scoped Memory:** Rotating on-call shifts automatically inherit past shift notes and uncertainty logs.
    2. **Daytona Sandbox Perimeter:** Code is *never* patched live. It is reproduced and verified in an isolated cloud workspace first.
    3. **Arize Supervisor:** Every remediation is graded against security policies before execution.

---

### Slide 6: Vision & Close (2:45 – 3:00)
* **Header:** The Future of Cloud Operations: Sleep Through the Outage
* **Visual:** Big bold text: **"Mean Time to Sleep: < 2 Minutes"** with GitHub QR code + Team Handles.
* **Speaker Script (Ayush):**
  > *"When microservices fail at 2:00 AM, you shouldn't have to panic through 14 tabs and risk your production data. With SurrealDB memory, Arize guardrails, Anchor recon, and Daytona's ephemeral compute, Aegis doesn't just manage incidents—it lets your team sleep through the outage. Thank you."*

---

## 🎨 Design & Aesthetic Guidelines for the Slide Designer
1. **Color Palette:**
   - Background: Dark Charcoal / Near Black (`#0f1117` or `#121316`)
   - Accent 1 (SurrealDB Purple): `#8b5cf6`
   - Accent 2 (Daytona Emerald Green): `#10b981`
   - Accent 3 (Arize Alert Red): `#ef4444`
   - Text: Pure White (`#ffffff`) for titles, Muted Slate (`#94a3b8`) for subtitles.
2. **Typography:** Clean monospace or modern sans-serif (Inter, JetBrains Mono, SF Pro).
3. **No Walls of Text:** Max 15 words per slide. Let the visuals, architecture diagram, and live demo do the talking!
4. **Sponsor Logos to Include on Slide 3:** Daytona, Arize AI, SurrealDB, ElevenLabs, Anchor Browser, AWS Bedrock.
