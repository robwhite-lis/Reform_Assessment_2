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

## Tech
- Python + Streamlit. Run: `pip install -r requirements.txt` then `streamlit run app.py`.
- Owner is an experienced data/IT leader, strongest in Python, deliberately
  sharpening hands-on coding. Prefer **readable, well-commented** code over clever
  one-liners; explain non-obvious choices in comments so the code is defensible in
  an assessment. Keep dependencies minimal.

## Build plan (ordered — what's left)
1. **SQLite persistence** — replace session_state store with a local `braid.db`;
   posts and replies survive refresh. Enables the local-first argument.
2. **Live reply flow** — let users add responses (with register + disclosure), not
   just seed replies. This is where the netnography findings actually live.
3. **Trace seed data to `Netnography.xlsx`** — link each synthetic post to the
   coded row(s) it derives from, so the method→artefact chain is explicit.
4. **Portfolio framing** — screenshots + the 800-word text (build the app with the
   text in mind; two of the four marking criteria are the text and its coherence).

## Academic-integrity note
The core ideas, research and design are the student's own; AI assistance on the
build must be declared in the submission. Keep a light touch — assist, don't
author. Preserve the student's voice and choices.

## Traps to avoid
- Don't scale this into a "real platform" — scope is an MVP that makes an argument.
- Don't centralise storage or add cloud services.
- Don't auto-code posts with an LLM.
- Don't strip the disclosure dial, the lanes, or the braid — they ARE the thesis.
