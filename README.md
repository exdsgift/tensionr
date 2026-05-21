# ⚡️ tensionr
> **Real-time Global Intelligence & Narrative Resonance Engine.**

[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](https://opensource.org/licenses/MIT)
[![Status: Live](https://img.shields.io/badge/Status-Live-00ff41.svg?style=flat-square)](#)
[![Engine: Python/JS](https://img.shields.io/badge/Engine-Python%20%7C%20JS-blue.svg)](#)

**tensionr** is a high-fidelity intelligence dashboard designed to monitor global instability, narrative shifts, and strategic asset movements in real-time. By synthesizing multi-domain signals (from GDELT news flows to ADS-B aerial telemetry) tensionr provides a unified "Geopolitical Tactical Picture" for rapid situational awareness.

![tensionr Dashboard](images/dashboard1.png)

## 🛰️ Core Capabilities

- **LLM-Powered SITREP:** Real-time tactical bulletins synthesized via **Mistral-7B**, providing a concise "Situation Report" of global alerts and anomalies.
- **Geopolitical Time Machine:** A "Static Data Lake" of daily archives, allowing users to select past dates and visualize historical geopolitical shifts.
- **Narrative Resonance Mapping:** Uses NLP (GoEmotions) to extract granular emotional undertones (Fear, Anger, Sadness, etc.) from global news nodes.
- **Strategic Aerial Telemetry:** Real-time tracking of military assets with automated anomaly detection for strategic airframes.
- **Multi-Domain GTI:** A composite algorithmic score quantifying global instability based on news sentiment, market volatility (VIX, Gold), and tactical telemetry.
- **Resilient Data Pipeline:** Parallelized RSS fetching and smart API fallbacks ensuring continuous intelligence even under rate-limiting.

## 🎯 Who is it for?

- **OSINT Analysts:** Rapidly aggregate and filter unverified raw chatter and verified news nodes.
- **Risk Managers:** Monitor the GTI to assess corporate or asset exposure in volatile regions.
- **Geopolitical Researchers:** Visualize how narratives evolve and spread across different domains and languages.
- **Data Enthusiasts:** A showcase of real-time data orchestration using Python, JS, and automated CI/CD pipelines.

## 🛠️ Tech Stack

- **Backend:** Python (Data harvesting, GDELT integration, NLP sentiment analysis).
- **Frontend:** Vanilla JS / Bootstrap 5 / Leaflet.js (Tactical mapping and hardware-accelerated UI).
- **Orchestration:** GitHub Actions (Automated telemetry sync every 40 minutes).
- **Virtualization:** Managed via `uv` for ultra-fast, reproducible environments.

## 🚀 Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/exdsgift/tensionr.git
   cd tensionr
   ```

2. **Setup environment:**
   ```bash
   uv venv
   source .venv/bin/activate # or .venv\Scripts\activate on Windows
   uv pip install -r requirements.txt
   ```

3. **Launch the Engine:**
   Run the data harvester to populate the dashboard:
   ```bash
   python src/fetch_gdelt.py
   ```
   Then simply open `index.html` in your browser.

---

*tensionr © 2026 // Engineered for the next generation of global observers.*
