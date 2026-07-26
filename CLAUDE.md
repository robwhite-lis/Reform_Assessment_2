# CLAUDE.md — project brief for Braid

Standing context for Claude Code. Read before making changes.

## What this is
Braid is a **prototype patient community app** built as the artefact for an
assessed Master's submission (London Interdisciplinary School, module M7004R
"Re:Form", Assessment 2 — a product prototype + 800-word contextualising text).
It is **not** a production system and should not be built like one.

It is the visual/interactive output of a netnography study of melanoma patient
communities. The study compared a private, identity-disclosed Facebook group
with public, pseudonymous Reddit (r/melanoma) and found the **Anonymity Paradox**:
the pseudonymous space drew out *more* emotional and experiential disclosure than
the identity-disclosed one. Braid is the design response to that finding.

## The thesis the code must preserve
Three design moves carry the argument. Do not remove or dilute them without asking:
1. **Verification is separated from visibility.** Every user is a verified patient
   or advocate; a *disclosure dial* then lets them choose how much identity to
   reveal, per post. The dial runs Anonymous (Reddit-like) → Named (Facebook-like),
   with "Verified · pseudonym" as the proposed default. This is the core idea.
2. **Two register lanes** — Clinical (cool teal) and Lived (warm amber). The
   temperature coding is meaningful, not decoration.
3. **Braided posts** stitch a clinical fact to a lived experience in one post,
   mirroring the dual-layered responses that worked best in the Reddit data.

## Hard rules (ethics — non-negotiable)
- **Synthetic data only.** All seeded posts are reconstructed from the codebook
  and must stay clearly labelled synthetic. Never introduce real patient content.
- **No fake AI.** New posts are tagged `(awaiting coding)`, NOT auto-classified by
  an LLM. The coding in the study was interpretive human work; do not fake it. If
  we ever add AI assistance it must be optional, on-device/local, and declared —
  because the project itself critiques careless AI use on patient data.
- **Local-first / data-dignity.** Persistence must keep data on the user's side
  (local SQLite), never a cloud service. This is an argument the artefact makes,
  so the architecture must honour it.

## Design decisions with reasons (don't "fix" these)
- State currently lives in `st.session_state` (resets on refresh). Intentional for
  the PoC; SQLite is the planned next step.
- Palette continues the Assessment 1 portfolio (deep pine, sage, cool/warm
  register accents). Keep visual continuity.
- Copy is plain, patient-facing, UK spelling. Name things by what people do.

## Exact colour palette (Assessment 1 portfolio — maintain continuity)
These hex values are taken directly from the Assessment 1 submission and must
be used consistently. Do not substitute approximations.

| Role | Hex | Usage |
|---|---|---|
| Pine (primary dark) | `#153F3B` | Header backgrounds, primary buttons |
| Pine deep | `#0E2E2B` | Header border, hover states |
| Navy (method accent) | `#1E2B4A` | Secondary headers, analytical UI elements |
| Sage | `#8DB3A6` | Subtitles, secondary accents, toggle active |
| Paper | `#EEF1F0` | Page background |
| Card white | `#FFFFFF` | Post card backgrounds |
| Ink | `#1D2B29` | Body text |
| Muted | `#5E6E6B` | Secondary text, metadata |
| Line | `#DFE4E2` | Borders, dividers |
| Clinical (cool) | `#2C6E7F` | Clinical lane accent, Stethoscope icon |
| Clinical bg | `#E7F0F1` | Clinical register block background |
| Clinical border | `#BFD8DC` | Clinical register block border |
| Lived (warm) | `#BE6A38` | Lived lane accent, Heart icon |
| Lived bg | `#F7EBE1` | Lived register block background |
| Lived border | `#E7CBB2` | Lived register block border |

The navy (`#1E2B4A`) is currently absent from the app — it should be introduced
as the colour for the sidebar header and any secondary analytical UI elements
(e.g. the researcher view panel) to match the Assessment 1 method slides.

## Tech
- Python + Streamlit. Run: `pip install -r requirements.txt` then `streamlit run app.py`.
- Owner is an experienced data/IT leader, strongest in Python, deliberately
  sharpening hands-on coding. Prefer **readable, well-commented** code over clever
  one-liners; explain non-obvious choices in comments so the code is defensible in
  an assessment. Keep dependencies minimal.

## Build plan (ordered — what's left)

### 1. Colour scheme alignment
Update `app.py` to use the exact hex values in the palette table above.
Specifically: introduce `#1E2B4A` navy for sidebar header and researcher-view
elements. Verify all existing values match the table exactly.

### 2. Identity management (PRIORITY — central to Assessment 2 argument)
This is the feature that operationalises the thesis most directly.

**What to build:**
- An onboarding screen shown on first run (detected via SQLite flag).
- User enters a **verified display name** (seen only by moderators — stored
  locally, never shown in the feed).
- User creates **1–3 aliases** (pseudonyms they choose; only they know which
  is theirs). Stored in SQLite against a local session token.
- When composing a post, the disclosure dial shows the user's *actual aliases*
  rather than abstract labels. E.g. "Post as MorningTide" or "Post as yourself."
- The Lived lane defaults the dial to the user's first alias (pseudonym).
  The Clinical lane defaults to their verified display name. This is
  **register-linked disclosure** — the central design argument.
- A visible safeguard note appears on Lived-lane posts:
  "Posted under alias · not linked to your clinical identity in this space."

**What NOT to build:**
- Do not attempt cross-platform identity (e.g. injecting aliases into Facebook).
  That is architecturally impossible and not what is claimed. The Assessment 2
  text handles this as a design argument and policy aspiration, not a feature.
- Do not build login, authentication, or any server-side identity layer.
  A local SQLite token is sufficient for a prototype.

**Why this matters for the argument:**
The assessment text cites Marwick and boyd (2011) on "context collapse" — the
way platforms like Facebook flatten multiple audience contexts into one identity,
silencing the vulnerable self. The identity management feature is Braid's direct
design response: verification is separated from visibility, and register-linked
defaults mean a patient naturally uses their real name for clinical questions and
an alias for emotional disclosure — without having to think about it.

### 3. SQLite persistence
Replace `st.session_state` post store with a local `braid.db`. Posts, replies,
and user identity (verified name + aliases) all survive refresh. This enables
the local-first / data-dignity argument in the 800-word text.

### 4. Live reply flow
Let users add responses to any post, with full register + disclosure choice.
Currently only seeded replies exist. This is where the netnography findings
live — a Lived post drawing a braided reply should be demonstrable live.

### 5. Trace seed data to Netnography.xlsx
Add a small metadata field to each seeded post linking it to the coded row
it derives from (e.g. "Derived from RED#6 · Primary code: Venting/catharsis").
Visible in researcher view only. Makes the method→artefact chain explicit.

## Data files in this repo

### Netnography.xlsx
The actual coded dataset from the Assessment 1 netnography study.
- Sheet: `Data` — 20 rows (10 Facebook, 10 Reddit), one per post
- Key columns: Post ID (FBG#1–10, RED#1–10), Platform, Primary Post Sentiment
  Code, Secondary Post Sentiment Code, Primary Response Sentiment Code,
  Secondary Response Sentiment Code
- Post IDs follow the pattern FBG#N (Facebook group) and RED#N (Reddit)
- Coding uses the 23-code taxonomy (11 post codes, 12 response codes) from
  the Assessment 1 codebook
- This file is the evidential basis for the seeded synthetic posts in app.py.
  Each seeded post should be traceable to a specific row in this file.
- Use openpyxl to read it. Do not modify it — it is the primary research record.
- In researcher view, display the source row reference alongside the codebook
  tags so the method→artefact link is visible to the marker.

## Theoretical framing (for any explanatory text in the app)
The About panel and any in-app explanatory copy should reflect this framing:

- **The Anonymity Paradox**: pseudonymous Reddit produced more emotional and
  experiential disclosure than the identity-disclosed private Facebook group.
  Platform architecture shapes which registers of knowledge patients feel able
  to produce — not just what they share, but what they treat as legitimate.

- **Context collapse** (Marwick and boyd, 2011): social media technologies
  flatten multiple audience contexts into one, making it structurally difficult
  to vary self-presentation. Facebook forces patients to perform a single
  identity to moderators, acquaintances, and close peers simultaneously.
  The vulnerable, back-stage self goes quiet.
  Full reference: Marwick, A.E. and boyd, d. (2011) 'I tweet honestly, I tweet
  passionately: Twitter users, context collapse, and the imagined audience',
  *New Media & Society*, 13(1), pp. 114–133. DOI: 10.1177/1461444810365313.

- **Braid's response**: verification is separated from visibility. Register-linked
  disclosure defaults mean the Clinical lane surfaces the named, authoritative
  self; the Lived lane surfaces the aliased, vulnerable self. Both are the same
  verified person — the link is held locally, not exposed to the community.

## Academic-integrity note
The core ideas, research and design are the student's own; AI assistance on the
build must be declared in the submission. Keep a light touch — assist, don't
author. Preserve the student's voice and choices.

## Traps to avoid
- Don't scale this into a "real platform" — scope is an MVP that makes an argument.
- Don't centralise storage or add cloud services.
- Don't auto-code posts with an LLM.
- Don't strip the disclosure dial, the lanes, or the braid — they ARE the thesis.
