# Braid — register-aware patient community (prototype)

M7004R Assessment 2 proof-of-concept.  A way of thinking about the "Anonymity Paradox",
from Assessment 1, giving users a way to have lived different personalities in different contexts.  Verification is separated from visibility (a disclosure slider), posts are made in the 
two register lanes (Clinical / Lived), and a post can be either or both (a braided posts that stitch a fact to an experience. 

All seeded content is synthetic, reconstructed from the netnography
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
- Drag the disclosure slider from Anonymous (Reddit-like) to Named (Facebook-like);
  the "You will appear as" preview updates live.
- Toggle "Researcher view" in the sidebar to overlay the codebook tags.

## Notes

- New posts are tagged "(awaiting coding)" rather than auto-coded — no fake AI.
