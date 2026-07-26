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

import json
import pathlib
import sqlite3

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

# Synthetic community members — verified names linked to the aliases that
# appear in the seeded posts, showing the mapping the moderator view exposes.
SEED_USERS = [
    {"verified_name": "Sarah Chen",   "aliases": ["MorningTide", "TealWing"]},
    {"verified_name": "James Okafor", "aliases": ["SlateGrey"]},
    {"verified_name": "Priya Nair",   "aliases": ["Fjord_49",    "NorthLight"]},
    {"verified_name": "Helen Marsh",  "aliases": ["HeatherM",    "RiverStone"]},
    {"verified_name": "Tom Bradley",  "aliases": ["PineMarten",  "SeaGlass"]},
    {"verified_name": "Diane Reeves", "aliases": ["GreyHeron"]},
]


# --------------------------------------------------------------------------
# SQLite persistence — local-first; data never leaves this machine.
# This honours the data-dignity argument the artefact makes.
# --------------------------------------------------------------------------
DB_PATH = pathlib.Path(__file__).parent / "braid.db"


def _init_db():
    """
    Create all tables on first run and seed synthetic data.
    Every CREATE is IF NOT EXISTS — idempotent and safe to call on every startup.
    Tables:
      posts / responses — community feed content
      users / aliases   — identity layer (verification separated from visibility)
      config            — key/value store for onboarding flag and local_user_id
    """
    with sqlite3.connect(DB_PATH) as conn:
        # ── feed tables ───────────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id         INTEGER PRIMARY KEY,
                author     TEXT    NOT NULL,
                disclosure INTEGER NOT NULL DEFAULT 1,
                up         INTEGER NOT NULL DEFAULT 0,
                lived      TEXT    NOT NULL DEFAULT '',
                clinical   TEXT    NOT NULL DEFAULT '',
                codes      TEXT    NOT NULL DEFAULT '[]'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id         INTEGER PRIMARY KEY,
                post_id    INTEGER NOT NULL REFERENCES posts(id),
                author     TEXT    NOT NULL,
                disclosure INTEGER NOT NULL DEFAULT 1,
                lived      TEXT    NOT NULL DEFAULT '',
                clinical   TEXT    NOT NULL DEFAULT '',
                codes      TEXT    NOT NULL DEFAULT '[]'
            )
        """)
        # ── identity tables ───────────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY,
                verified_name TEXT    NOT NULL,
                is_local      INTEGER NOT NULL DEFAULT 0,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # sort_order 0 = first/default alias (used as Lived-lane default)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS aliases (
                id         INTEGER PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                alias      TEXT    NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0
            )
        """)
        # key/value config: onboarding_complete, local_user_id
        conn.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        # ── seed posts (first run only) ───────────────────────────────
        if conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0] == 0:
            for p in SEED:
                conn.execute(
                    "INSERT INTO posts (id, author, disclosure, up, lived, clinical, codes)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (p["id"], p["author"], p["disclosure"], p["up"],
                     p["lived"], p["clinical"], json.dumps(p["codes"]))
                )
                for r in p.get("responses", []):
                    conn.execute(
                        "INSERT INTO responses (post_id, author, disclosure, lived, clinical, codes)"
                        " VALUES (?,?,?,?,?,?)",
                        (p["id"], r["author"], r["disclosure"],
                         r["lived"], r["clinical"], json.dumps(r["codes"]))
                    )
        # ── seed example community members (first run only) ───────────
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            for su in SEED_USERS:
                cur = conn.execute(
                    "INSERT INTO users (verified_name, is_local) VALUES (?,0)",
                    (su["verified_name"],)
                )
                uid = cur.lastrowid
                for i, alias in enumerate(su["aliases"]):
                    conn.execute(
                        "INSERT INTO aliases (user_id, alias, sort_order) VALUES (?,?,?)",
                        (uid, alias, i)
                    )


def _load_posts():
    """Return all posts with nested responses, newest first."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, author, disclosure, up, lived, clinical, codes"
            " FROM posts ORDER BY id DESC"
        ).fetchall()
        posts = []
        for pid, author, disc, up, lived, clinical, codes in rows:
            resp_rows = conn.execute(
                "SELECT author, disclosure, lived, clinical, codes"
                " FROM responses WHERE post_id=? ORDER BY id",
                (pid,)
            ).fetchall()
            posts.append({
                "id": pid,
                "author": author,
                "disclosure": disc,
                "up": up,
                "lived": lived,
                "clinical": clinical,
                "codes": json.loads(codes),
                "responses": [
                    {"author": ra, "disclosure": rd,
                     "lived": rl, "clinical": rc,
                     "codes": json.loads(rco)}
                    for ra, rd, rl, rc, rco in resp_rows
                ],
            })
        return posts


def _insert_post(author, disclosure, lived, clinical, codes):
    """Write a new post to the database; return its auto-assigned id."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO posts (author, disclosure, up, lived, clinical, codes)"
            " VALUES (?,?,0,?,?,?)",
            (author, disclosure, lived, clinical, json.dumps(codes))
        )
        return cur.lastrowid


# ── Identity helpers ──────────────────────────────────────────────────────

def _onboarding_complete():
    """True if the local user has finished the onboarding flow."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT value FROM config WHERE key='onboarding_complete'"
        ).fetchone()
        return row is not None and row[0] == "1"


def _get_local_user():
    """
    Return the local user record (id, verified_name, aliases list) or None.
    None means onboarding has not been completed yet.
    """
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT id, verified_name FROM users WHERE is_local=1"
        ).fetchone()
        if row is None:
            return None
        uid, vname = row
        alias_rows = conn.execute(
            "SELECT id, alias, sort_order FROM aliases"
            " WHERE user_id=? ORDER BY sort_order, id",
            (uid,)
        ).fetchall()
        return {
            "id": uid,
            "verified_name": vname,
            "aliases": [
                {"id": aid, "alias": a, "sort_order": s}
                for aid, a, s in alias_rows
            ],
        }


def _create_local_user(verified_name, alias_list):
    """
    Persist the local user's verified name and initial aliases.
    Sets onboarding_complete = 1 and records local_user_id in config.
    Called once from the onboarding screen.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO users (verified_name, is_local) VALUES (?,1)",
            (verified_name.strip(),)
        )
        uid = cur.lastrowid
        for i, alias in enumerate(alias_list):
            if alias.strip():
                conn.execute(
                    "INSERT INTO aliases (user_id, alias, sort_order) VALUES (?,?,?)",
                    (uid, alias.strip(), i)
                )
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('onboarding_complete','1')"
        )
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('local_user_id',?)",
            (str(uid),)
        )


def _update_verified_name(user_id, name):
    """Update a user's verified display name in the DB."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE users SET verified_name=? WHERE id=?", (name.strip(), user_id)
        )


def _add_alias(user_id, alias):
    """Add a new alias for user_id. Returns False if already at the 3-alias cap."""
    with sqlite3.connect(DB_PATH) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM aliases WHERE user_id=?", (user_id,)
        ).fetchone()[0]
        if count >= 3:
            return False
        conn.execute(
            "INSERT INTO aliases (user_id, alias, sort_order) VALUES (?,?,?)",
            (user_id, alias.strip(), count)
        )
        return True


def _remove_alias(alias_id):
    """Delete a specific alias row by its id."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM aliases WHERE id=?", (alias_id,))


def _get_all_users():
    """
    Return all users with their aliases — local user first, then seeded members.
    Used by the admin panel to show the moderator-perspective overview.
    """
    with sqlite3.connect(DB_PATH) as conn:
        user_rows = conn.execute(
            "SELECT id, verified_name, is_local FROM users ORDER BY is_local DESC, id"
        ).fetchall()
        result = []
        for uid, vname, is_local in user_rows:
            alias_rows = conn.execute(
                "SELECT id, alias, sort_order FROM aliases"
                " WHERE user_id=? ORDER BY sort_order, id",
                (uid,)
            ).fetchall()
            result.append({
                "id": uid,
                "verified_name": vname,
                "is_local": bool(is_local),
                "aliases": [
                    {"id": aid, "alias": a, "sort_order": s}
                    for aid, a, s in alias_rows
                ],
            })
        return result


# Initialise (or verify) the database at import time — runs once per process.
_init_db()


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


def _build_disc_options(local_user):
    """
    Build the personalised disclosure-dial options for the compose panel.
    Each entry is a dict: {label, author, level}.

    Mapping:
      level 0 → Anonymous        (no alias, no verification)
      level 1 → each alias       (verified but pseudonymous — Lived default)
      level 2 → Known to mods    (verified, name held by moderation team)
      level 3 → verified name    (fully named — Clinical default)

    The select_slider uses 'label' as its option string; submit_post
    looks up the chosen label in this list to get author and disc level.
    """
    opts = [{"label": "Anonymous", "author": "Anonymous", "level": 0}]
    if local_user:
        for rec in local_user["aliases"]:
            opts.append({
                "label": f"As {rec['alias']}",
                "author": rec["alias"],
                "level": 1,
            })
        opts.append({
            "label": "Known to moderators",
            "author": local_user["verified_name"],
            "level": 2,
        })
        opts.append({
            "label": f"As {local_user['verified_name']}",
            "author": local_user["verified_name"],
            "level": 3,
        })
    else:
        # Fallback: generic labels (shouldn't reach here post-onboarding)
        for i, d in enumerate(DISCLOSURE[1:], 1):
            opts.append({"label": d["label"], "author": "You", "level": i})
    return opts


# --------------------------------------------------------------------------
# Onboarding screen — shown once on first run
# --------------------------------------------------------------------------
def _show_onboarding():
    """
    Full-page identity setup, shown before the user can access the feed.
    Operationalises 'verification ≠ visibility': the real name and the
    alias(es) are collected together but stored and used separately.
    """
    st.markdown(
        f'<div style="background:{C["navy"]};color:#F4F7F5;border-radius:14px;'
        f'padding:20px 24px;margin-bottom:20px;">'
        f'<span style="font-family:Georgia,serif;font-size:28px;font-weight:700;">'
        f'Braid</span>'
        f'<div style="font-size:13px;color:{C["sage"]};margin-top:6px;">'
        f'Welcome — set up your identity before you join the conversation.'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "Braid separates **verification** from **visibility**. You give a real "
        "name so the community knows everyone here is a genuine patient or "
        "advocate — but your real name is never shown in the feed. What the "
        "community sees is your chosen alias. You decide which alias to use, "
        "post by post."
    )
    st.caption(
        "Everything you enter is stored in a local SQLite file on this device. "
        "Nothing is sent to any server."
    )

    st.divider()

    # ── Section 1: verified identity (clinical register colours) ──────
    st.markdown(
        f'<div style="background:{C["clinicalBg"]};border-left:3px solid {C["clinical"]};'
        f'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:6px;">'
        f'<div style="font-size:9.5px;text-transform:uppercase;letter-spacing:0.08em;'
        f'font-weight:700;color:{C["clinical"]};">Your verified identity</div>'
        f'<div style="font-size:13px;color:{C["muted"]};margin-top:3px;">'
        f'Stored locally and visible to moderators only — never shown in the feed.'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    verified_name = st.text_input(
        "Your full name",
        placeholder="e.g. Sarah Chen",
        help="Only you and moderators will ever see this.",
        key="ob_vname",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section 2: aliases (lived register colours) ────────────────────
    st.markdown(
        f'<div style="background:{C["livedBg"]};border-left:3px solid {C["lived"]};'
        f'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:6px;">'
        f'<div style="font-size:9.5px;text-transform:uppercase;letter-spacing:0.08em;'
        f'font-weight:700;color:{C["lived"]};">Your aliases</div>'
        f'<div style="font-size:13px;color:{C["muted"]};margin-top:3px;">'
        f'Choose 1–3 pseudonyms. You pick which one appears on each post. '
        f'Nobody else can link them to your name.'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    alias1 = st.text_input("Alias 1 — required", placeholder="e.g. MorningTide",
                           key="ob_a1")
    alias2 = st.text_input("Alias 2 — optional", placeholder="e.g. TealWing",
                           key="ob_a2")
    alias3 = st.text_input("Alias 3 — optional", placeholder="e.g. NorthLight",
                           key="ob_a3")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Get started →", type="primary", use_container_width=True):
        errors = []
        if not verified_name.strip():
            errors.append("Please enter your verified display name.")
        if not alias1.strip():
            errors.append("Please enter at least one alias.")
        aliases = [a for a in [alias1, alias2, alias3] if a.strip()]
        if len(aliases) != len({a.lower() for a in aliases}):
            errors.append("Each alias must be unique.")
        if errors:
            for e in errors:
                st.error(e)
        else:
            _create_local_user(verified_name, aliases)
            st.success("Identity saved. Loading Braid…")
            st.rerun()


# --------------------------------------------------------------------------
# Admin / identity management panel
# --------------------------------------------------------------------------
def _show_admin():
    """
    Identity management view — navy-accented, three sections:
      1. Edit your own verified name and aliases.
      2. Register-linked disclosure preview (the central design argument).
      3. Community overview showing all members' verified→alias mapping,
         as a moderator would see it.
    """
    local = _get_local_user()
    if local is None:
        st.warning("No local identity found. Please restart the app.")
        return

    # ── Header ────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="background:{C["navy"]};color:#F4F7F5;border-radius:14px;'
        f'padding:18px 20px;margin-bottom:16px;">'
        f'<span style="font-family:Georgia,serif;font-size:24px;font-weight:700;">'
        f'Identity Management</span>'
        f'<div style="font-size:12px;color:{C["sage"]};margin-top:4px;">'
        f'Verification is separated from visibility — this is where that '
        f'separation lives.'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # ── 1. Your verified name ─────────────────────────────────────────
    st.markdown(
        f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.08em;color:{C["navy"]};margin-bottom:8px;">'
        f'Your verified identity</div>',
        unsafe_allow_html=True,
    )
    with st.form("form_vname"):
        new_vname = st.text_input(
            "Verified display name",
            value=local["verified_name"],
            help="Held locally. Seen by moderators only — never in the feed.",
        )
        if st.form_submit_button("Save name"):
            if new_vname.strip():
                _update_verified_name(local["id"], new_vname)
                # Bust the session-state cache so the panel re-reads from DB.
                st.session_state.pop("local_user", None)
                st.success("Verified name updated.")
                st.rerun()
            else:
                st.error("Name cannot be empty.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 2. Your aliases ────────────────────────────────────────────────
    st.markdown(
        f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.08em;color:{C["lived"]};margin-bottom:6px;">'
        f'Your aliases <span style="font-size:10px;font-weight:400;color:{C["muted"]};">'
        f'(max 3 — first is the Lived-lane default)</span></div>',
        unsafe_allow_html=True,
    )

    aliases = local["aliases"]
    for idx, rec in enumerate(aliases):
        col_name, col_btn = st.columns([6, 1])
        with col_name:
            default_note = "  ·  default for Lived lane" if idx == 0 else ""
            st.markdown(
                f'<div style="padding:7px 11px;background:{C["livedBg"]};'
                f'border:1px solid {C["livedLine"]};border-radius:7px;'
                f'font-size:14px;color:{C["ink"]};">'
                f'<strong>{rec["alias"]}</strong>'
                f'<span style="font-size:11px;color:{C["muted"]};">'
                f'{default_note}</span></div>',
                unsafe_allow_html=True,
            )
        with col_btn:
            # Always keep at least one alias
            if len(aliases) > 1:
                if st.button("✕", key=f"rm_{rec['id']}",
                             help=f"Remove alias '{rec['alias']}'"):
                    _remove_alias(rec["id"])
                    st.session_state.pop("local_user", None)
                    st.rerun()

    if len(aliases) < 3:
        with st.form("form_add_alias", clear_on_submit=True):
            new_alias = st.text_input(
                "New alias",
                placeholder="e.g. NorthLight",
            )
            if st.form_submit_button("+ Add alias"):
                if new_alias.strip():
                    ok = _add_alias(local["id"], new_alias.strip())
                    if ok:
                        st.session_state.pop("local_user", None)
                        st.rerun()
                    else:
                        st.error("You already have 3 aliases.")
                else:
                    st.error("Alias cannot be empty.")

    st.divider()

    # ── 3. Register-linked disclosure preview ─────────────────────────
    # This is the core design argument: the same verified person uses their
    # real name in the Clinical lane and their alias in the Lived lane,
    # without having to think about it.
    st.markdown(
        f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.08em;color:{C["navy"]};margin-bottom:8px;">'
        f'How register-linked disclosure works for you</div>',
        unsafe_allow_html=True,
    )

    first_alias = aliases[0]["alias"] if aliases else "your alias"
    col_c, col_l = st.columns(2)
    with col_c:
        st.markdown(
            f'<div style="background:{C["clinicalBg"]};border-left:3px solid {C["clinical"]};'
            f'border-radius:0 8px 8px 0;padding:11px 13px;">'
            f'<div style="font-size:9.5px;text-transform:uppercase;letter-spacing:0.08em;'
            f'font-weight:700;color:{C["clinical"]};">Clinical lane</div>'
            f'<div style="font-size:14px;color:{C["ink"]};margin-top:5px;">'
            f'Posts appear as <strong>{local["verified_name"]}</strong></div>'
            f'<div style="font-size:11px;color:{C["muted"]};margin-top:3px;">'
            f'Named · authoritative register</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_l:
        st.markdown(
            f'<div style="background:{C["livedBg"]};border-left:3px solid {C["lived"]};'
            f'border-radius:0 8px 8px 0;padding:11px 13px;">'
            f'<div style="font-size:9.5px;text-transform:uppercase;letter-spacing:0.08em;'
            f'font-weight:700;color:{C["lived"]};">Lived lane</div>'
            f'<div style="font-size:14px;color:{C["ink"]};margin-top:5px;">'
            f'Posts appear as <strong>{first_alias}</strong></div>'
            f'<div style="font-size:11px;color:{C["muted"]};margin-top:3px;">'
            f'Aliased · experiential register</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.caption(
        "Both identities belong to the same verified person. The link is held "
        "locally here — never exposed to the community. This is Braid's direct "
        "response to context collapse (Marwick and boyd, 2011)."
    )

    st.divider()

    # ── 4. Community overview (moderator perspective) ──────────────────
    st.markdown(
        f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.08em;color:{C["navy"]};margin-bottom:4px;">'
        f'Community overview — moderator perspective</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "In a deployed Braid, moderators could consult this mapping to maintain "
        "safety while the community feed only ever shows aliases."
    )

    all_users = _get_all_users()

    # Table header
    st.markdown(
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;'
        f'padding:6px 12px;background:{C["navy"]}18;border-radius:6px 6px 0 0;'
        f'margin-bottom:2px;">'
        f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.06em;color:{C["navy"]};">Verified name</div>'
        f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.06em;color:{C["navy"]};">Aliases</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    for u in all_users:
        alias_text = ", ".join(a["alias"] for a in u["aliases"]) or "—"
        bg     = "#EEF1F8" if u["is_local"] else C["card"]
        border = C["navy"] if u["is_local"] else C["line"]
        you_badge = (
            f' <span style="font-size:10px;background:{C["navy"]};color:#F4F7F5;'
            f'border-radius:4px;padding:1px 6px;">You</span>'
            if u["is_local"] else ""
        )
        st.markdown(
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;'
            f'background:{bg};border:1px solid {border};'
            f'border-radius:7px;padding:9px 12px;margin-bottom:5px;">'
            f'<div style="font-size:14px;font-weight:600;color:{C["ink"]};">'
            f'{u["verified_name"]}{you_badge}</div>'
            f'<div style="font-size:14px;color:{C["muted"]};">{alias_text}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.caption("Braid · M7004R Assessment 2 · identity management")


# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------
st.set_page_config(page_title="Braid — prototype", page_icon="🧵", layout="centered")

# ── Onboarding gate ────────────────────────────────────────────────────────
# If the user hasn't completed onboarding, show that screen and stop here.
if not _onboarding_complete():
    _show_onboarding()
    st.stop()

# ── Local user — cache in session_state for the duration of this session ──
if "local_user" not in st.session_state:
    st.session_state.local_user = _get_local_user()

# ── Post session state ─────────────────────────────────────────────────────
if "posts" not in st.session_state:
    st.session_state.posts = _load_posts()
for k, v in {"c_lived": "", "c_clinical": ""}.items():
    st.session_state.setdefault(k, v)


def submit_post():
    lived = st.session_state.c_lived.strip()
    clinical = st.session_state.c_clinical.strip()
    if not lived and not clinical:
        return
    # Resolve author name and disc level from the personalised options list.
    selected_label = st.session_state.get("c_disc", "")
    opts = st.session_state.get("disc_opts", [])
    match = next((o for o in opts if o["label"] == selected_label), None)
    author = match["author"] if match else "You"
    disc   = match["level"]  if match else 1
    _insert_post(author, disc, lived, clinical, ["(awaiting coding)"])
    st.session_state.posts = _load_posts()
    st.session_state.c_lived = ""
    st.session_state.c_clinical = ""
    # Clear c_disc so the lane-switcher block resets to the lane default on next render.
    st.session_state.pop("c_disc", None)


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    # Navy header — matches the method/analytical register colour from Assessment 1.
    st.markdown(
        f'<div style="background:{C["navy"]};color:#F4F7F5;border-radius:10px;'
        f'padding:12px 14px;margin-bottom:12px;">'
        f'<span style="font-family:Georgia,serif;font-size:20px;font-weight:700;">'
        f'Braid</span>'
        f'<div style="font-size:10px;color:{C["sage"]};margin-top:3px;">'
        f'M7004R Assessment 2 · prototype</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Page navigation
    page = st.radio(
        "Navigate",
        ["Community feed", "My identity"],
        label_visibility="collapsed",
        key="page",
    )

    st.divider()

    if page == "Community feed":
        researcher = st.toggle(
            "Researcher view", value=False,
            help="Overlay the netnography codebook tags on every post.",
        )
        st.divider()
    else:
        researcher = False  # not applicable on admin page

    local = st.session_state.local_user
    if local:
        st.markdown(
            f'<div style="font-size:12px;color:{C["muted"]};">'
            f'Signed in as<br>'
            f'<span style="font-weight:600;color:{C["ink"]};">'
            f'{local["aliases"][0]["alias"] if local["aliases"] else "—"}'
            f'</span></div>',
            unsafe_allow_html=True,
        )
        st.divider()

    st.markdown("**Why this design**")
    st.markdown(
        "- **Verification ≠ visibility.** Everyone is a verified patient; the "
        "disclosure dial sets how much identity to reveal, per post.\n"
        "- **Two register lanes.** A cool Clinical lane and a warm Lived lane.\n"
        "- **Braided posts.** Stitch a fact to an experience — the dual-layered "
        "pattern that worked best in the Reddit data."
    )


# ── Page routing ──────────────────────────────────────────────────────────
if page == "My identity":
    _show_admin()
    st.stop()

# ── Community feed ────────────────────────────────────────────────────────

# Header
st.markdown(
    f'<div style="background:{C["navy"]};color:#F4F7F5;border-radius:14px;'
    f'padding:18px 20px;margin-bottom:6px;">'
    f'<span style="font-family:Georgia,serif;font-size:30px;font-weight:700;">'
    f'Braid</span>'
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

# Lane switcher
lane = st.radio("View", ["Whole space", "Clinical lane", "Lived lane"],
                horizontal=True, label_visibility="collapsed")
lane_key = {"Whole space": "all", "Clinical lane": "clinical",
            "Lived lane": "lived"}[lane]
lane_accent = {"all": C["pine"], "clinical": C["clinical"],
               "lived": C["lived"]}[lane_key]
st.markdown(
    f'<div style="height:4px;background:{lane_accent};border-radius:999px;'
    f'margin:2px 0 14px;"></div>', unsafe_allow_html=True)

# Build personalised disclosure options and store in session_state so
# submit_post can resolve author name + level without re-building them.
_local = st.session_state.local_user
disc_opts = _build_disc_options(_local)
disc_labels_p = [o["label"] for o in disc_opts]
st.session_state["disc_opts"] = disc_opts

# Register-linked disclosure default — now using the user's real alias and name:
# Clinical lane  → "As [verified name]"  (named, authoritative self)
# Lived / whole  → "As [first alias]"    (aliased, vulnerable self)
if _local and _local["aliases"]:
    _default_clinical = f"As {_local['verified_name']}"
    _default_lived    = f"As {_local['aliases'][0]['alias']}"
else:
    _default_clinical = disc_labels_p[-1]   # last option = most named
    _default_lived    = disc_labels_p[1] if len(disc_labels_p) > 1 else disc_labels_p[0]

default_disc = _default_clinical if lane_key == "clinical" else _default_lived
if "c_disc" not in st.session_state:
    st.session_state.c_disc = default_disc
# Reset dial whenever the user switches lanes
if st.session_state.get("last_lane") != lane_key:
    st.session_state.c_disc = default_disc
    st.session_state.last_lane = lane_key

# Compose panel
with st.expander("➕ Share something", expanded=False):
    st.caption("Fill one box, or both to braid a fact and an experience together.")
    st.text_area("Lived — how it felt", key="c_lived",
                 placeholder="What was it actually like? Fears, wins, the human side…",
                 height=80)
    st.text_area("Clinical — the facts", key="c_clinical",
                 placeholder="Trial data, drug details, a resource, a factual question…",
                 height=80)

    st.select_slider("Post as", options=disc_labels_p, key="c_disc")

    # Look up the currently selected option to drive the preview and safeguard note.
    sel_label = st.session_state.c_disc
    sel_opt   = next((o for o in disc_opts if o["label"] == sel_label), disc_opts[1])

    # Preview: show how the post author will appear in the feed.
    st.markdown(
        "You will appear as: " +
        author_row({"author": sel_opt["author"], "disclosure": sel_opt["level"]}),
        unsafe_allow_html=True,
    )

    # Safeguard note — shown whenever posting under an alias (level 1).
    # Per CLAUDE.md: "Posted under alias · not linked to your clinical identity in this space."
    if sel_opt["level"] == 1:
        st.markdown(
            f'<div style="margin-top:6px;font-size:11.5px;color:{C["lived"]};'
            f'background:{C["livedBg"]};border-left:3px solid {C["lived"]};'
            f'border-radius:0 6px 6px 0;padding:5px 10px;">'
            f'Posted under alias · not linked to your clinical identity in this space.'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.button("Post", type="primary", on_click=submit_post)

# Feed
visible = [p for p in st.session_state.posts
           if lane_key == "all" or register_of(p) in (lane_key, "braided")]
st.markdown("".join(post_html(p, researcher) for p in visible),
            unsafe_allow_html=True)

st.caption("Braid · proof-of-concept · design encodes the Anonymity Paradox finding")
