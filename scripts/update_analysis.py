"""
Macro War Room — Daily News + AI Analysis  (v2)

개선 내역:
  - 뉴스 쿼리: CB 인사 발언 / 핵심 지표 / 지정학 특화 키워드로 세분화
  - Fed 연설 캘린더(federalreserve.gov JSON) 자동 수집 → 당일·전날 연설자 파악
  - 이전 analysis.json 컨텍스트 주입 → 연속성 있는 레징 분석
  - Claude 프롬프트에 "오늘의 이벤트" 섹션 추가 → ECB 포럼 등 누락 방지
  - tool_use 방식으로 JSON 출력 강제 (파싱 오류 제거)

Run:  ANTHROPIC_API_KEY=... python scripts/update_analysis.py
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
TODAY    = datetime.now(timezone.utc).strftime("%Y-%m-%d")
TODAY_DT = datetime.now(timezone.utc)
OUTFILE  = "analysis.json"

# Signal names MUST match SIGNALS[].name in src/App.jsx so notes map cleanly.
SIGNAL_NAMES = ["US Real Rate", "2s10s Curve", "HY Credit Spread", "VIX",
                "Brent Crude", "Gold", "USD / KRW", "Semiconductor SOX"]

NEWS_QUERIES = [
    # 중앙은행 인사 발언 — 가장 중요한 카테고리
    "Federal Reserve Chair speech monetary policy rate hike",
    "Fed FOMC minutes statement interest rate decision",
    "ECB European Central Bank forum speech rate decision",
    "Bank of Korea BOK rate decision monetary policy",
    "BOJ Bank of Japan yield curve hike policy",
    # 핵심 지표 발표
    "US CPI inflation data release consumer price index",
    "nonfarm payrolls jobs report unemployment labor",
    "US GDP growth economic data quarterly",
    "core PCE deflator inflation Federal Reserve target",
    "US retail sales consumer spending",
    # 시장 / 원자재 / 지정학
    "Brent crude oil OPEC Iran production cut",
    "US Treasury yield 10 year bond selloff rally",
    "AI semiconductor chip Nvidia earnings capex",
    "Korea KOSPI won currency HBM SK Hynix Samsung",
    "geopolitical risk war ceasefire sanctions tariff",
]

# ── Fed 연설 캘린더 (federalreserve.gov 공개 JSON) ─────────────────────────
FED_CAL_URL = "https://www.federalreserve.gov/json/ne-isd-frb.json"

def fetch_fed_calendar():
    """당일 ±2일 이내 Fed 인사 연설/이벤트 목록을 반환."""
    try:
        req  = urllib.request.Request(FED_CAL_URL, headers={"User-Agent": "Mozilla/5.0"})
        raw  = urllib.request.urlopen(req, timeout=10).read()
        rows = json.loads(raw)
        events = []
        for r in rows:
            date_str = (r.get("EventDate") or r.get("StartDate") or "")[:10]
            try:
                ev_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            delta = (ev_dt - TODAY_DT).days
            if -2 <= delta <= 2:
                speaker  = r.get("Speaker") or r.get("Speakers") or "Unknown"
                title    = r.get("EventName") or r.get("Title") or ""
                location = r.get("Location") or ""
                events.append(f"  [{date_str}] {speaker} — {title} @ {location}".strip(" @"))
        print(f" [OK] Fed calendar: {len(events)} events near {TODAY}")
        return events
    except Exception as e:
        print(f" [WARN] Fed calendar: {e}")
        return []


# ── 이전 analysis.json 로드 (연속성 컨텍스트용) ────────────────────────────
def load_previous_analysis():
    try:
        with open(OUTFILE, encoding="utf-8") as f:
            prev = json.load(f)
        # 오늘 파일이 이미 있으면 건너뜀
        if prev.get("asOf") == TODAY:
            return None
        return {
            "regimeLabel": prev.get("regimeLabel", ""),
            "regimeSub":   prev.get("regimeSub", ""),
            "themes":      prev.get("themes", []),
            "asOf":        prev.get("asOf", "unknown"),
        }
    except Exception:
        return None


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

    # ── (a) Fed 연설 캘린더 ──────────────────────────────────────────────
    print("Fetching Fed speaker calendar...")
    fed_events = fetch_fed_calendar()
    fed_block  = (
        "\n".join(fed_events)
        if fed_events
        else "  (no Fed speeches scheduled within \u00b12 days)"
    )

    # ── (b) 뉴스 헤드라인 ────────────────────────────────────────────────
    print("Fetching news headlines...")
    blocks = []
    for q in NEWS_QUERIES:
        hs = fetch_news(q)
        if hs:
            blocks.append(f"## {q}\n" + "\n".join(hs))
    news_block = "\n\n".join(blocks) if blocks else "(no headlines fetched)"

    # ── (c) 시장 스냅샷 ──────────────────────────────────────────────────
    snapshot = "(no market data available)"
    try:
        with open("data.json", encoding="utf-8") as f:
            d = json.load(f)
        snapshot = json.dumps(
            {k: d.get(k) for k in ("date", "us", "equities", "fx", "commodities")},
            indent=2,
        )
    except Exception as e:
        print(f" [WARN] no market snapshot: {e}")

    # ── (d) 이전 레짐 (연속성 컨텍스트) ─────────────────────────────────
    prev = load_previous_analysis()
    prev_block = ""
    if prev:
        prev_block = (
            f"\nYESTERDAY'S REGIME (as of {prev['asOf']}):"
            f"\n  Label : {prev['regimeLabel']}"
            f"\n  Sub   : {prev['regimeSub']}"
            f"\n  Themes:\n"
            + "\n".join(f"    - {t}" for t in prev["themes"])
            + "\n"
        )

    # ── (e) 프롬프트 ─────────────────────────────────────────────────────
    prompt = f"""You are the chief macro strategist at a $50bn global macro hedge fund. Today is {TODAY}.

You receive: (1) live market data, (2) Fed speaker calendar \u00b12 days, (3) fresh news headlines across CB policy / key data releases / geopolitics, and (4) yesterday's regime for continuity.

RULES — read carefully:
\u2022 If a named CB official (Fed Chair, ECB president, BOK governor, etc.) spoke or published today or yesterday, name them explicitly and state what they signaled.
\u2022 If a key data print (CPI, NFP, FOMC, GDP) landed today, quote the actual vs. estimate.
\u2022 If a geopolitical event resolved (ceasefire, sanctions lifted, deal struck), update the regime — do NOT carry stale war narratives.
\u2022 The regimeLabel must change when macro facts change materially from yesterday.
\u2022 Each theme must name a specific person, data point, or event — no generic platitudes.

\u2501\u2501\u2501 MARKET DATA ({TODAY}):
{snapshot}

\u2501\u2501\u2501 FED SPEAKER CALENDAR (\u00b12 days of {TODAY}):
{fed_block}

\u2501\u2501\u2501 RECENT NEWS HEADLINES:
{news_block}
{prev_block}
\u2501\u2501\u2501

Produce the structured JSON using the write_analysis tool:
  regimeLabel : 2-4 word ALL-CAPS label (e.g. "HAWKISH RISK-ON MELT-UP")
  regimeSub   : ONE sentence <140 chars — today's dominant driver
  themes      : exactly 4 cause\u2192effect chains, each citing specific data/events/people
  signalNotes : one <120-char note per signal (use names verbatim): {", ".join(SIGNAL_NAMES)}
  headline    : one "state of the world" sentence as of {TODAY}

Millennium/Citadel PM style — blunt, specific, no filler."""

    import anthropic
    client = anthropic.Anthropic()

    print("Calling Claude (claude-opus-4-5)...")
    resp = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
        tools=[{
            "name": "write_analysis",
            "description": "Write the structured daily macro analysis output",
            "input_schema": SCHEMA,
        }],
        tool_choice={"type": "tool", "name": "write_analysis"},
    )

    tool_block = next((b for b in resp.content if b.type == "tool_use"), None)
    if tool_block is None:
        raise ValueError("Claude returned no tool_use block — check model/API version")
    data = tool_block.input

    data["generated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data["asOf"]      = TODAY

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
