# Braid — register-aware patient community (prototype)

M7004R Assessment 2 proof-of-concept. Operationalises the "Anonymity Paradox"
from Assessment 1: verification is separated from visibility (a disclosure dial),
two register lanes (Clinical / Lived), and braided posts that stitch a fact to an
experience. All seeded content is synthetic, reconstructed from the netnography
codebook.

## Run it

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Opens at http://localhost:8501

## What to try

- Switch the lane (Whole space / Clinical lane / Lived lane) — the feed filters.
- Open "Share something", fill both boxes, and post a *braided* card.
- Drag the disclosure dial from Anonymous (Reddit-like) to Named (Facebook-like);
  the "You will appear as" preview updates live.
- Toggle "Researcher view" in the sidebar to overlay the codebook tags.

## Notes

- State lives in `st.session_state`, so a refresh resets it. Persistence (SQLite,
  which ships with Python) is the natural next step and lets the write-up make the
  local-first / data-dignity argument concretely.
- New posts are tagged "(awaiting coding)" rather than auto-coded — no fake AI.
