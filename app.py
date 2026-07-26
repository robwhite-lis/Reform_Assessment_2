"""
Braid — a register-aware patient community (prototype)
M7004R Assessment 2 · Streamlit port

Operationalises the "Anonymity Paradox" from Assessment 1:
  1. Verification is separated from visibility (a disclosure dial).
  2. Two register lanes — Clinical (cool) and Lived (warm).
  3. Braided posts stitch both registers together, mirroring the
     dual-layered responses that dominated the Reddit corpus.

All seeded content is SYNTHETIC, reconstructed from the netnography
codebook — no real patient posts are reproduced.

Run:  streamlit run app.py
"""

import streamlit as st

# --------------------------------------------------------------------------
# Palette — the two register "temperatures" carry the argument:
# cool = clinical, warm = lived.
# --------------------------------------------------------------------------
C = {
    "pine": "#153F3B",
    "pineDeep": "#0E2E2B",
    "navy": "#1E2B4A",      # method accent — sidebar header, researcher/analytical UI
    "sage": "#8DB3A6",
    "paper": "#EEF1F0",
    "card": "#FFFFFF",
    "ink": "#1D2B29",
    "muted": "#5E6E6B",
    "line": "#DFE4E2",
    "clinical": "#2C6E7F",
    "clinicalBg": "#E7F0F1",
    "clinicalLine": "#BFD8DC",
    "lived": "#BE6A38",
    "livedBg": "#F7EBE1",
    "livedLine": "#E7CBB2",
}

# disclosure spectrum: Reddit-like (anonymous) -> Facebook-like (named)
DISCLOSURE = [
    {"label": "Anonymous",
     "sub": "No verification. Maximum privacy, minimum trust.",
     "anchor": "Reddit-like"},
    {"label": "Verified · pseudonym",
     "sub": "Proven to be a genuine patient or advocate, shown under a chosen name.",
     "anchor": "Proposed default"},
    {"label": "Known to moderators",
     "sub": "Verified and identifiable to the moderation team only.",
     "anchor": ""},
    {"label": "Named to community",
     "sub": "Full identity shown to everyone, as in the Facebook group.",
     "anchor": "Facebook-like"},
]
DISC_LABELS = [d["label"] for d in DISCLOSURE]

# --------------------------------------------------------------------------
# Seed data — synthetic, reconstructed from the codebook
# --------------------------------------------------------------------------
SEED = [
    {
        "id": 1, "author": "MorningTide", "disclosure": 1, "up": 47,
        "lived": ("Three-monthly scan tomorrow and I'm wide awake at 2am again. "
                  "I know the drill by now but the fear never really files itself "
                  "away. Anyone else still get this after years?"),
        "clinical": "",
        "codes": ["Emotional support-seeking", "Venting/catharsis"],
        "responses": [
            {"author": "SlateGrey", "disclosure": 1,
             "lived": ("Four years out and yes, every single time. You're not being "
                       "dramatic — scanxiety is real and it doesn't mean anything's wrong."),
             "clinical": "",
             "codes": ["Emotional reassurance", "Validation/agreement"]},
            {"author": "Fjord_49", "disclosure": 1,
             "lived": "The night before is always the worst for me too.",
             "clinical": ("One thing that helped: I asked my team to book scans for a "
                          "Monday so I'm not waiting over a weekend for results."),
             "codes": ["Experiential anecdote", "Practical suggestion"]},
        ],
    },
    {
        "id": 2, "author": "GreyHeron", "disclosure": 1, "up": 63,
        "lived": ("Not what the leaflet says — what was it actually like starting "
                  "immunotherapy? I want the real version."),
        "clinical": "",
        "codes": ["Experiential knowledge-seeking", "Emotional support-seeking"],
        "responses": [
            {"author": "MorningTide", "disclosure": 1,
             "lived": ("Honestly the first cycle floored me with fatigue and I cried "
                       "more than I expected."),
             "clinical": ("But my bloods stayed fine throughout and the tiredness eased "
                          "by cycle three — here's the side-effect tracker I used so you "
                          "can show your nurse."),
             "codes": ["Experiential anecdote", "Emotional reassurance", "Practical suggestion"]},
        ],
    },
    {
        "id": 3, "author": "PineMarten", "disclosure": 1, "up": 12,
        "lived": "",
        "clinical": ("Looking for the progression-free survival figures from the latest "
                     "BRAF/MEK combination trial vs immunotherapy first-line. Does anyone "
                     "have the actual numbers rather than the press summary?"),
        "codes": ["Factual/clinical information-seeking"],
        "responses": [
            {"author": "HeatherM", "disclosure": 2,
             "lived": "",
             "clinical": ("The ASCO 2026 update has the head-to-head data — I'll drop the "
                          "abstract in the resources thread. Short version: the sequencing "
                          "question is still open, so it's worth raising with your oncologist."),
             "codes": ["Factual/clinical information", "Redirect to professional"]},
        ],
    },
    {
        "id": 4, "author": "SeaGlass", "disclosure": 1, "up": 8,
        "lived": "",
        "clinical": ("Sharing a summary I made of the off-label options being discussed "
                     "at the moment — happy to be corrected."),
        "codes": ["Factual/clinical information-sharing"],
        "responses": [
            {"author": "PineMarten", "disclosure": 1,
             "lived": "",
             "clinical": ("Useful, thanks — one flag though: point 3 mixes up neoadjuvant "
                          "and adjuvant timing. Worth fixing before others rely on it."),
             "codes": ["Thanks for factual sharing", "Correction (blunt)"]},
        ],
    },
    {
        "id": 5, "author": "Anonymous", "disclosure": 0, "up": 34,
        "lived": ("I've decided to take a break from treatment for the summer, against "
                  "advice. I just need to feel like a person again. Tell me I'm not making "
                  "a terrible mistake."),
        "clinical": "",
        "codes": ["Validation-seeking", "Emotional support-seeking"],
        "responses": [
            {"author": "SlateGrey", "disclosure": 1,
             "lived": ("You're not. Quality of life is a legitimate part of this decision "
                       "and you're allowed to weigh it."),
             "clinical": ("Just keep the conversation open with your team so it stays a "
                          "pause, not a door closing."),
             "codes": ["Validation/agreement", "Redirect to professional"]},
        ],
    },
]


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def register_of(item):
    has_c = bool(item.get("clinical", "").strip())
    has_l = bool(item.get("lived", "").strip())
    if has_c and has_l:
        return "braided"
    return "clinical" if has_c else "lived"


def disclosure_chip(level):
    d = DISCLOSURE[level]
    verified = 1 <= level <= 2
    fg = C["pine"] if verified else C["muted"]
    bg = "#E4EEEA" if verified else "#EFEFEC"
    bd = "#CADED7" if verified else C["line"]
    return (f'<span style="display:inline-flex;align-items:center;gap:4px;'
            f'font-size:11px;color:{fg};background:{bg};border:1px solid {bd};'
            f'border-radius:999px;padding:2px 8px;white-space:nowrap;">'
            f'{d["label"]}</span>')


def author_row(item):
    tick = ""
    if 1 <= item["disclosure"] <= 2:
        tick = (f'<span style="color:{C["clinical"]};font-weight:700;'
                f'font-size:12px;">✓</span>')
    return (f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">'
            f'<span style="font-weight:650;font-size:14px;color:{C["ink"]};">'
            f'{item["author"]}</span>{tick}{disclosure_chip(item["disclosure"])}</div>')


def register_block(kind, text):
    cool = kind == "clinical"
    col = C["clinical"] if cool else C["lived"]
    bg = C["clinicalBg"] if cool else C["livedBg"]
    label = "Clinical" if cool else "Lived"
    return (f'<div style="background:{bg};border-left:3px solid {col};'
            f'border-radius:0 8px 8px 0;padding:9px 12px;margin-top:6px;">'
            f'<div style="font-size:9.5px;text-transform:uppercase;'
            f'letter-spacing:0.08em;font-weight:700;color:{col};margin-bottom:2px;">'
            f'{label}</div>'
            f'<div style="font-size:14.5px;line-height:1.5;color:{C["ink"]};">'
            f'{text}</div></div>')


def code_tags(codes):
    # Navy used here as the researcher/analytical UI colour, per the Assessment 1 palette.
    pills = "".join(
        f'<span style="font-family:ui-monospace,Menlo,monospace;font-size:10.5px;'
        f'color:{C["navy"]};background:#EEF0F6;border:1px dashed {C["navy"]}44;'
        f'border-radius:4px;padding:1px 6px;margin:2px 4px 0 0;'
        f'display:inline-block;">{c}</span>'
        for c in codes
    )
    return (f'<div style="margin-top:8px;padding:6px 8px;background:#F2F4F9;'
            f'border-left:3px solid {C["navy"]};border-radius:0 6px 6px 0;">'
            f'<div style="font-size:9px;text-transform:uppercase;letter-spacing:0.08em;'
            f'font-weight:700;color:{C["navy"]};margin-bottom:4px;">Researcher view</div>'
            f'{pills}</div>')


def body_html(item, researcher):
    parts = []
    reg = register_of(item)
    if reg == "braided":
        parts.append(
            f'<div style="font-size:10px;font-weight:700;letter-spacing:0.06em;'
            f'text-transform:uppercase;color:{C["pine"]};margin-bottom:2px;">'
            f'<span style="color:{C["clinical"]};">◗</span>'
            f'<span style="color:{C["lived"]};">◖</span> Braided</div>'
        )
    if item.get("lived", "").strip():
        parts.append(register_block("lived", item["lived"]))
    if item.get("clinical", "").strip():
        parts.append(register_block("clinical", item["clinical"]))
    if researcher:
        parts.append(code_tags(item["codes"]))
    return "".join(parts)


def post_html(p, researcher):
    reg = register_of(p)
    accent = {"clinical": C["clinical"], "lived": C["lived"], "braided": C["pine"]}[reg]

    responses = ""
    if p["responses"]:
        blocks = "".join(
            f'<div style="margin-bottom:10px;">{author_row(r)}{body_html(r, researcher)}</div>'
            for r in p["responses"]
        )
        responses = (f'<div style="margin-top:12px;padding-left:12px;'
                     f'border-left:2px solid {C["line"]};">{blocks}</div>')

    engage = (f'<div style="display:flex;gap:16px;margin-top:10px;font-size:12px;'
              f'color:{C["muted"]};"><span>▲ {p["up"]}</span>'
              f'<span>💬 {len(p["responses"])}</span></div>')

    return (f'<div style="background:{C["card"]};border:1px solid {C["line"]};'
            f'border-top:3px solid {accent};border-radius:12px;padding:14px 16px;'
            f'margin-bottom:14px;">'
            f'{author_row(p)}{body_html(p, researcher)}{engage}{responses}</div>')


# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------
st.set_page_config(page_title="Braid — prototype", page_icon="🧵", layout="centered")

# session state
if "posts" not in st.session_state:
    st.session_state.posts = [dict(p) for p in SEED]
for k, v in {"c_lived": "", "c_clinical": "", "c_disc": DISC_LABELS[1]}.items():
    st.session_state.setdefault(k, v)


def submit_post():
    lived = st.session_state.c_lived.strip()
    clinical = st.session_state.c_clinical.strip()
    if not lived and not clinical:
        return
    disc = DISC_LABELS.index(st.session_state.c_disc)
    st.session_state.posts.insert(0, {
        "id": len(st.session_state.posts) + 1000,
        "author": "Anonymous" if disc == 0 else "You",
        "disclosure": disc, "up": 0,
        "lived": lived, "clinical": clinical,
        "codes": ["(awaiting coding)"], "responses": [],
    })
    st.session_state.c_lived = ""
    st.session_state.c_clinical = ""
    st.session_state.c_disc = DISC_LABELS[1]


# --- sidebar: researcher view + about -------------------------------------
with st.sidebar:
    # Navy header block — matches the method/analytical register of the Assessment 1 slides.
    st.markdown(
        f'<div style="background:{C["navy"]};color:#F4F7F5;border-radius:10px;'
        f'padding:12px 14px;margin-bottom:10px;">'
        f'<span style="font-family:Georgia,serif;font-size:20px;font-weight:700;">Braid</span>'
        f'<div style="font-size:10px;color:{C["sage"]};margin-top:3px;">'
        f'M7004R Assessment 2 · prototype</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    researcher = st.toggle("Researcher view", value=False,
                           help="Overlay the netnography codebook tags on every post.")
    st.divider()
    st.markdown("**Why this design**")
    st.markdown(
        "- **Verification ≠ visibility.** Everyone is a verified patient; the "
        "disclosure dial sets how much identity to reveal, per post.\n"
        "- **Two register lanes.** A cool Clinical lane and a warm Lived lane.\n"
        "- **Braided posts.** Stitch a fact to an experience — the dual-layered "
        "pattern that worked best in the Reddit data."
    )

# --- header ---------------------------------------------------------------
st.markdown(
    f'<div style="background:{C["navy"]};color:#F4F7F5;border-radius:14px;'
    f'padding:18px 20px;margin-bottom:6px;">'
    f'<span style="font-family:Georgia,serif;font-size:30px;font-weight:700;">Braid</span>'
    f'<span style="font-size:10px;font-weight:700;letter-spacing:0.1em;'
    f'text-transform:uppercase;color:{C["navy"]};background:{C["sage"]};'
    f'border-radius:4px;padding:3px 7px;margin-left:10px;">Prototype</span>'
    f'<div style="font-size:12.5px;color:{C["sage"]};margin-top:6px;">'
    f'Clinical facts and lived experience, side by side — you choose what to show.'
    f'</div></div>',
    unsafe_allow_html=True,
)
st.caption("ℹ️ Synthetic content, reconstructed from the netnography codebook. "
           "No real patient posts are shown.")

# --- lane switcher --------------------------------------------------------
lane = st.radio("View", ["Whole space", "Clinical lane", "Lived lane"],
                horizontal=True, label_visibility="collapsed")

lane_key = {"Whole space": "all", "Clinical lane": "clinical", "Lived lane": "lived"}[lane]
lane_accent = {"all": C["pine"], "clinical": C["clinical"], "lived": C["lived"]}[lane_key]
st.markdown(
    f'<div style="height:4px;background:{lane_accent};border-radius:999px;'
    f'margin:2px 0 14px;"></div>', unsafe_allow_html=True)

# --- compose --------------------------------------------------------------
with st.expander("➕ Share something", expanded=False):
    st.caption("Fill one box, or both to braid a fact and an experience together.")
    st.text_area("Lived — how it felt", key="c_lived",
                 placeholder="What was it actually like? Fears, wins, the human side…",
                 height=80)
    st.text_area("Clinical — the facts", key="c_clinical",
                 placeholder="Trial data, drug details, a resource, a factual question…",
                 height=80)
    st.select_slider("How much do you want to show?", options=DISC_LABELS, key="c_disc")
    sel = DISC_LABELS.index(st.session_state.c_disc)
    st.caption(f"↔ more private (Reddit-like) … more open (Facebook-like) — "
               f"**{DISCLOSURE[sel]['sub']}**")
    st.markdown("You will appear as: " +
                author_row({"author": "Anonymous" if sel == 0 else "You",
                            "disclosure": sel}), unsafe_allow_html=True)
    st.button("Post", type="primary", on_click=submit_post)

# --- feed -----------------------------------------------------------------
visible = [p for p in st.session_state.posts
           if lane_key == "all" or register_of(p) in (lane_key, "braided")]

feed = "".join(post_html(p, researcher) for p in visible)
st.markdown(feed, unsafe_allow_html=True)

st.caption("Braid · proof-of-concept · design encodes the Anonymity Paradox finding")
