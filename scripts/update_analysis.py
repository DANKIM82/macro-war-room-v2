"""
Macro War Room — Daily News + AI Analysis
Pulls recent macro headlines (Google News RSS, no key needed), sends them with the
latest market snapshot to Claude, and writes public/analysis.json — the regime
read / themes / signal notes the React app renders.

Run:  ANTHROPIC_API_KEY=... python scripts/update_analysis.py
Safe to run without a key (it just skips). Never fails the build on error.
"""

import os, sys, json, urllib.parse, urllib.request
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

# UTF-8 console so emoji/box chars don't crash on Windows (cp949)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TODAY   = datetime.now(timezone.utc).strftime("%Y-%m-%d")
OUTFILE = "public/analysis.json"

# Signal names MUST match SIGNALS[].name in src/App.jsx so notes map cleanly.
SIGNAL_NAMES = ["US Real Rate", "2s10s Curve", "HY Credit Spread", "VIX",
                "Brent Crude", "Gold", "USD / KRW", "Semiconductor SOX"]

NEWS_QUERIES = [
    "global macro markets",
    "Federal Reserve interest rate decision",
    "Brent crude oil price",
    "Middle East geopolitics war",
    "US inflation CPI",
    "stock market today",
]

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "regimeLabel": {"type": "string"},
        "regimeSub":   {"type": "string"},
        "themes":      {"type": "array", "items": {"type": "string"}},
        "signalNotes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["name", "note"],
            },
        },
        "headline": {"type": "string"},
    },
    "required": ["regimeLabel", "regimeSub", "themes", "signalNotes", "headline"],
}


def fetch_news(query, limit=6):
    url = ("https://news.google.com/rss/search?q="
           + urllib.parse.quote(query) + "&hl=en-US&gl=US&ceid=US:en")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        raw = urllib.request.urlopen(req, timeout=15).read()
        root = ET.fromstring(raw)
        out = []
        for it in root.findall(".//item")[:limit]:
            title = (it.findtext("title") or "").strip()
            pub   = (it.findtext("pubDate") or "").strip()
            if title:
                out.append(f"- {title}" + (f"  ({pub})" if pub else ""))
        print(f"  [OK]   news '{query}' → {len(out)} headlines")
        return out
    except Exception as e:
        print(f"  [ERR]  news '{query}': {e}")
        return []


def main():
    if not API_KEY:
        print("[SKIP] No ANTHROPIC_API_KEY — leaving analysis.json unchanged.")
        return

    print("Fetching news headlines...")
    blocks = []
    for q in NEWS_QUERIES:
        hs = fetch_news(q)
        if hs:
            blocks.append(f"## {q}\n" + "\n".join(hs))
    news_block = "\n\n".join(blocks) if blocks else "(no headlines fetched)"

    snapshot = "(no market data available)"
    try:
        with open("public/data.json", encoding="utf-8") as f:
            d = json.load(f)
        snapshot = json.dumps(
            {k: d.get(k) for k in ("date", "us", "equities", "fx", "commodities")},
            indent=2)
    except Exception as e:
        print(f"  [WARN] no market snapshot: {e}")

    prompt = f"""You are the chief macro strategist at a $50bn global macro hedge fund. Today is {TODAY}.

You are given (1) the latest market data and (2) recent news headlines. Produce a macro regime read that reflects TODAY's reality. Pay close attention to regime-CHANGING events in the news — wars starting or ending, central-bank pivots, oil shocks, elections. Do NOT repeat stale narratives if the news shows they have resolved.

MARKET DATA (as of {TODAY}):
{snapshot}

RECENT NEWS HEADLINES:
{news_block}

Produce:
- regimeLabel: a 2-4 word ALL-CAPS regime name (e.g. "STAGFLATION RISK", "SOFT LANDING", "RISK-ON REFLATION", "GEOPOLITICAL DE-ESCALATION")
- regimeSub: ONE sentence (<140 chars) naming the regime and its main driver, reflecting the latest news
- themes: exactly 4 punchy one-line macro themes as cause->effect chains, grounded in current events
- signalNotes: for EACH of these exact signal names, a <120 char note on what it means right now — use these names verbatim: {", ".join(SIGNAL_NAMES)}
- headline: a single "state of the world" sentence as of {TODAY}

Be specific, current, and blunt — Millennium/Citadel house style. No hedging fluff."""

    import anthropic
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    print("Calling Claude (claude-opus-4-8)...")
    resp = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=8000,
        thinking={"type": "adaptive"},
        output_config={"format": {"type": "json_schema", "schema": SCHEMA},
                       "effort": "medium"},
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    data = json.loads(text)
    data["generated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data["asOf"] = TODAY

    os.makedirs("public", exist_ok=True)
    with open(OUTFILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {OUTFILE} — regime: {data['regimeLabel']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Never fail the daily pipeline because of an LLM/news hiccup.
        print(f"[WARN] analysis step failed (keeping previous analysis.json): {e}")
        sys.exit(0)
