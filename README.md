# CampusSolve AI 🎓

A hackathon-ready Streamlit university information assistant built around:

- Python + Streamlit
- LangChain-compatible architecture
- Google Gemma via the Google GenAI API
- ElevenLabs Text-to-Speech
- Live university website search
- Official Facebook candidate search
- Notice/PDF extraction
- Source-priority verification
- Department + level context
- Add/select multiple universities

## Core flow

User question
→ selected university
→ official-domain live search
→ notice/PDF extraction
→ source ranking
→ Gemma grounded answer
→ source/date cards
→ optional ElevenLabs voice

## Important source rule

Priority 1: Official university website/domain  
Priority 2: Official Facebook page candidate  
Other sources are not treated as authoritative for deadlines, fees, exam dates, registration or administrative procedures.

If valid official evidence is unavailable, the assistant explicitly says that no valid official source was found rather than guessing.

## Setup

1. Create a virtual environment.

Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install packages:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and add your API keys.

4. Run:
```bash
streamlit run app.py
```

## Add a university

Use the sidebar:

- University name: required
- Official website: recommended
- Official Facebook: optional

If the website is left blank, CampusSolve attempts to discover a likely official website from the university name. For a hackathon demo, manually supplying the official domain is more reliable.

## Notes

The search layer uses DuckDuckGo search through the `ddgs` package because no separate search API key is required. Search-engine snippets are treated as discovery evidence; the app attempts to fetch the linked page/PDF before using it as evidence.

The Gemma model is configurable through `GEMMA_MODEL`. If your Google account exposes a different Gemma model name, change that value in `.env`.

Never commit `.env` to GitHub. The supplied API keys should be rotated because they were pasted into a chat.
"# AboutUniversityHackDay" 
