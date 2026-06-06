Please create a file named `README.md` in the root folder (or overwrite it if it already exists). Populate it with the EXACT markdown content provided below. Do not change the formatting, do not alter the Mermaid diagram, and do not add any conversational text to the file:

# ⚡ TrueSignal
**Adversarial HR Intelligence Engine | Hack2Skill & Redrob Submission**

> *Finding the right person, not just the right keywords.*

![TrueSignal UI](https://img.shields.io/badge/UI-Glassmorphism-black?style=flat-square)
![Powered By](https://img.shields.io/badge/Powered_By-Gemini_2.5_Flash-blue?style=flat-square)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square)

## 🧠 The Problem
Modern ATS systems rely on flat keyword matching (TF-IDF). They don't understand context, they reward title-inflators, and they are easily bypassed by fabricated timelines. Good candidates get lost in the noise.

## 🚀 The Solution: Adversarial Multi-Agent AI
TrueSignal abandons simple extraction. Instead, it uses a multi-agent debate framework powered by Google Gemini 2.5 Flash:
1. **The Advocate Agent:** Scans the candidate's history to highlight genuine business impact, quantifiable achievements, and core strengths.
2. **The Interrogator Agent:** Acts as a ruthless auditor. It probes for timeline inconsistencies, missing fundamental skills, and "Honeypot" logic flaws.

The engine synthesizes this debate to generate a strict, mathematically grounded score (0-100) and a concise decision ledger. 

## 🏗️ System Architecture

```mermaid
graph TD
    A[Recruiter / Judge] -->|Uploads .jsonl| B(FastAPI Backend)
    B --> C{XML Sanitization & Security}
    C -->|Clean Data| D[Google Gemini 2.5 Flash]
    
    subgraph Adversarial AI Engine
    D --> E[The Advocate: Highlights Impact]
    D --> F[The Interrogator: Hunts Flaws & Honeypots]
    E -.-> G((Debate Synthesis))
    F -.-> G
    end

    G --> H{Scoring Engine}
    H -->|Zero-Tolerance Math| I[Glassmorphism Dashboard]
    I -->|Ranked Leaderboard| A