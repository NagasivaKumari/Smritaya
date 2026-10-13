"""Smritaya — landing content served to the frontend.

Single source of truth for the marketing page. Edit copy here (or swap for a
CMS/DB) without touching the frontend. `/content` merges this with live stats.
"""

LANDING: dict = {
    "hero": {
        "eyebrow": "Smritaya · the witness for the verbal economy",
        "title": "The word is the contract.",
        "title_em": "We make it stick.",
        "lede": "A billion people run on spoken promises. Smritaya is an ambient AI "
                "witness that hears every deal, remembers the exact words, and stands "
                "beside you when a word is broken.",
        "primary_cta": "Enter the witness",
        "secondary_cta": "See how it works",
        "secondary_href": "#how",
    },
    "stats_eyebrow": "The record, right now",
    "stats_title": "Live from your chambers.",
    "stats_title_em": "Not a demo number.",
    "sections": [
        {
            "id": "why",
            "kind": "cards",
            "eyebrow": "The verbal economy",
            "title": "The law was never the problem.",
            "title_em": "Nothing could hear.",
            "cards": [
                {"big": "1.4B", "k": "people.",
                 "d": "Most of India works on spoken promises — no paper, no witness, no proof."},
                {"big": "₹0", "k": "recovered.",
                 "d": "When a word breaks, the injured party has nothing to stand on. Not because "
                      "the law ignores verbal contracts, but because nothing ever heard them."},
                {"big": "Every day", "k": "it happens.",
                 "d": "The carpenter. The landlord. The friend who said “next month, no tension.”"},
            ],
        },
        {
            "id": "how",
            "kind": "loop",
            "eyebrow": "One connected loop",
            "title": "Voice in. Memory kept.",
            "title_em": "Answers out.",
            "steps": [
                {"n": "01 · Omi", "t": "It listens",
                 "d": "Ambient speech from the Omi app or wearable streams in through "
                      "developer-mode webhooks — memory-creation and real-time."},
                {"n": "02 · Extractor", "t": "It remembers",
                 "d": "The Extractor agent turns raw speech into deeds: who, the exact words, "
                      "the amount, the due date, the topic."},
                {"n": "03 · Qdrant", "t": "It stores",
                 "d": "Each deed becomes a vector with structured facts, held in private per-user "
                      "memory — searchable by meaning and by filter in one query."},
                {"n": "04 · Advisor", "t": "It argues",
                 "d": "When a word breaks, the Drafter convenes a Hearing and drafts the "
                      "escalation ladder — gentle, then firm, then formal."},
            ],
        },
        {
            "id": "stack",
            "kind": "stack",
            "eyebrow": "The stack · all three, genuinely",
            "title": "Remove any one —",
            "title_em": "and there is no product.",
            "cards": [
                {"name": "Omi", "role": "The ears",
                 "d": "Developer-mode webhooks ingest ambient speech; notifications close the "
                      "loop back to your phone."},
                {"name": "Qdrant", "role": "The memory",
                 "d": "The testament collection stores every verbatim quote with structured "
                      "payload — semantic and filtered retrieval, answered only from what was sworn."},
                {"name": "Lyzr", "role": "The mind",
                 "d": "Three specialized agents — Extractor, Advisor, Drafter — reason over the "
                      "record. Remove any one and there is no product."},
            ],
        },
        {
            "id": "trust",
            "kind": "trust",
            "eyebrow": "Privacy-first knowledge",
            "title": "Secure, local memory —",
            "title_em": "yours alone.",
            "pillars": [
                {"seal": "intact", "t": "Per-person chambers",
                 "d": "Every relationship gets its own chamber, its trust rendered as a wax seal "
                      "— intact, cracked, or broken."},
                {"seal": "broken", "t": "Strike from the record",
                 "d": "Privacy as a legal right. Deletion is real: one deed, or an entire "
                      "chamber, gone from the memory."},
                {"seal": "pending", "t": "Answers, not dashboards",
                 "d": "Ask in plain words. The witness answers only from the record and cites "
                      "its snippets."},
            ],
        },
    ],
    "final": {
        "title": "Every word,",
        "title_em": "witnessed.",
        "lede": "Speak as you always have. The witness does the remembering.",
        "cta": "Enter the witness",
    },
    "nav": [
        {"label": "The problem", "href": "#why"},
        {"label": "How it works", "href": "#how"},
        {"label": "The stack", "href": "#stack"},
        {"label": "Privacy", "href": "#trust"},
    ],
    "nav_cta": "Enter",
    # No customer logo wall yet — Smritaya has no customers, so the
    # same slot carries an honest capability strip instead — no invented logos.
    "marquee": [
        "Omi · ambient capture",
        "Extractor · who said what",
        "Qdrant · private memory",
        "Lyzr · the mind",
        "Per-person chambers",
        "Verbatim quotes",
        "Strike from the record",
        "Dispute hearings",
        "Escalation ladders",
    ],
    "footer": {
        "wordmark_pre": "SMRI", "wordmark_em": "T", "wordmark_post": "AYA",
        "tagline": "The witness for the verbal economy. Every spoken promise, remembered — and defended.",
        "columns": [
            {"h": "Product", "links": [
                {"label": "The problem", "href": "#why"},
                {"label": "How it works", "href": "#how"},
                {"label": "The stack", "href": "#stack"},
                {"label": "Enter the witness", "action": "enter"},
            ]},
            {"h": "Trust", "links": [
                {"label": "Privacy by design", "href": "#trust"},
                {"label": "Per-person chambers", "href": "#trust"},
                {"label": "Strike from the record", "href": "#trust"},
            ]},
            {"h": "Built on", "links": [
                {"label": "Omi"}, {"label": "Qdrant"}, {"label": "Lyzr"},
            ]},
        ],
        "copyright": "© 2026 Smritaya",
        "note": "the witness for the verbal economy",
    },
}


# The in-app interface copy. `/copy` serves this so no string is hardcoded in JSX.
APP: dict = {
    "brand": {
        "wordmark_pre": "SMRI", "wordmark_em": "T", "wordmark_post": "AYA",
        "sub": "the witness for the verbal economy",
    },
    "nav": [
        {"id": "stand", "label": "The Stand"},
        {"id": "ledger", "label": "The Ledger"},
        {"id": "chambers", "label": "The Chambers"},
        {"id": "vault", "label": "The Vault"},
    ],
    "nav_hint": "/ to question",
    "auth": {
        "signin_title": "Sign in to the witness",
        "signup_title": "Open a chamber",
        "reset_title": "Reset your password",
        "email": "Email address",
        "password": "Password",
        "confirm": "Confirm password",
        "email_ph": "name@firm.com",
        "password_ph": "at least 8 characters",
        "show": "Show password",
        "hide": "Hide password",
        "forgot": "Forgot password?",
        "signin_btn": "Enter the workspace",
        "signup_btn": "Create account",
        "send_btn": "Send reset link",
        "set_btn": "Set new password",
        "to_signin": "Already have an account? Sign in",
        "to_signup": "New here? Create an account",
        "reset_sent": "Reset link sent",
        "reset_hint": "No email service in this build — the reset link is shown here.",
        "reset_link_label": "Open the reset link",
        "reset_no_account": "No account found for that email.",
        "reset_done": "Password reset. Sign in with your new password.",
        "signed_out": "You have left the stand. Your record stays sealed.",
        "welcome": "Welcome to Smritaya Workspace",
        "strength": ["too short", "weak", "okay", "strong"],
    },
    "labels": {
        "kept": "kept", "broken": "broken", "pending": "pending",
        "contested": "contested", "untested": "untested", "at_stake": "at stake",
    },
    "palette": {
        "placeholder": "Question the witness…",
        "hint": "the witness answers only from what was sworn",
        "loading": "Consulting the record…",
        "cited": "cited from the record",
        "silent": "The witness is silent",
        "suggestions": [
            "What is overdue?", "What did Ramesh promise?",
            "Who owes me the most?", "What has Aditi kept?",
        ],
    },
    "toasts": {
        "reminder": "Reminder drafted — the witness nudges, you stay gracious.",
        "kept": "The word is kept. The seal is pressed.",
        "struck": "Struck from the record: “{text}”",
        "chamber_emptied": "The chamber of {name} is emptied.",
        "omi_linked": "Omi linked — nudges will reach {id}",
    },
    "stand": {
        "eyebrow": "Smritaya · the witness for the verbal economy",
        "title": "Every word,", "title_em": "witnessed.",
        "lede": "Speak your agreements as you always have — with the carpenter, the landlord, "
                "the friend. The witness hears, remembers the exact words, and stands beside "
                "you when a word is broken.",
        "doors": [
            {"num": "speak or type", "name": "Witness a verbal promise", "action": "witness"},
            {"num": "press /", "name": "Question the witness", "action": "palette"},
            {"num": "the ledger", "name": "Read the record", "action": "ledger"},
        ],
        "latest": "Latest words sworn",
        "stats": [
            {"key": "pending", "label": "words pending"},
            {"key": "overdue", "label": "overdue", "tone": "broken"},
            {"key": "stake", "label": "at stake", "tone": "gold", "format": "money"},
            {"key": "chambers", "label": "chambers"},
        ],
    },
    "ledger": {
        "eyebrow": "The Ledger", "title": "The record, ", "title_em": "as spoken.",
        "empty": "Nothing stands in the record here.",
        "filters": [
            {"id": "all", "label": "all"}, {"id": "overdue", "label": "overdue"},
            {"id": "pending", "label": "pending"}, {"id": "broken", "label": "broken"},
            {"id": "contested", "label": "contested"}, {"id": "kept", "label": "kept"},
        ],
    },
    "chambers": {
        "eyebrow": "The Chambers", "title": "Every soul has ", "title_em": "a seal.",
        "lede": "Trust, pressed in wax. One chamber for every person whose word touched yours.",
    },
    "chamber": {
        "back": "← back to the record",
        "opening": "Opening the chamber…",
        "sealed": "The chamber is sealed: {error}",
        "empty": "Nothing stands in the record here.",
        "eyebrow": "Everything sworn",
        "tags": {
            "intact": "their word holds", "cracked": "their word has fissures",
            "broken": "their word has been broken", "untested": "their word is untested",
        },
    },
    "hearing": {
        "back": "← return to the record",
        "loading": "Convening the hearing…",
        "error": "The hearing cannot be convened: {error}",
        "eyebrow": "The hearing · convened by the witness",
        "title": "is called to answer.",
        "acts": [
            {"num": "I", "title": "The Summons"},
            {"num": "II", "title": "The Evidence — verbatim, cited"},
            {"num": "III", "title": "The Pattern of their word"},
            {"num": "IV", "title": "The Memo — choose your words"},
        ],
        "exhibit": "Exhibit",
        "act_word": "Act",
        "pattern_fallback": "The record speaks for itself.",
        "memo_labels": {
            "gentle": "First word · gentle", "firm": "Second word · firm",
            "formal": "Last resort · formal notice",
        },
        "copy": "copy", "copied": "copied", "due": "due",
    },
    "deed": {
        "who": "who", "sum": "sum", "due": "due", "sworn": "sworn", "overdue": "overdue",
        "you_swore": "you swore", "they_swore": "they swore",
        "send_reminder": "Send reminder", "drafting": "drafting…",
        "convene": "Convene hearing", "word_kept": "Word kept",
        "reminder_label": "Reminder, drafted", "overdue_stamp": "Overdue",
    },
    "vault": {
        "eyebrow": "The Vault",
        "title": "Your memory is ", "title_em": "yours.",
        "articles": [
            [{"t": "Article I — "}, {"em": "Nothing leaves without command."},
             {"t": " Every deed lives in a vector store on hardware you control. "
                   "No cloud holds your words unless you choose it."}],
            [{"t": "Article II — "}, {"em": "The right to be forgotten is a button."},
             {"t": " Any word, or an entire chamber, can be struck from the record. "
                   "Striking is real deletion — the points are removed from the index, not hidden."}],
            [{"t": "Article III — "}, {"em": "You hold the seal."},
             {"t": " Retrieval is filtered per person; no other user's record can ever "
                   "surface in your answers."}],
        ],
        "where": "Where your words live",
        "witness_id": "Your witness id — point Omi here",
        "omi_connect": "Connect your Omi",
        "omi_lede": "Point Omi's webhooks at this app's /omi/conversation — Omi adds your own id to every call. Paste that id here and the witness maps it to this account: your words land in this ledger and nudges reach your Omi.",
        "omi_ph": "your Omi id",
        "omi_save": "link", "omi_saving": "linking…",
        "omi_linked": "linked — nudges reach this Omi", "omi_unlinked": "not linked yet",
        "rows": [
            {"key": "memory", "label": "memory"},
            {"key": "embedder", "label": "embedder"},
            {"key": "reasoning", "label": "reasoning"},
            {"key": "omi", "label": "notifications"},
            {"key": "points", "label": "deeds on record"},
        ],
        "strike": "Strike from the record",
        "confirm": "confirm strike", "spare": "spare", "strike_btn": "strike",
        "strike_chamber": "strike an entire chamber", "forget": "forget {name}",
    },
}

