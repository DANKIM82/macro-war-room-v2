"""
Fed Speak Tracker - daily market odds for the next FOMC meeting.

Runs after update_data.py and adds a "fed" block to data.json.
fed-tracker.js reads that block and overrides the hardcoded FED_SNAPSHOT
fields (targetRange, nextFOMC, marketOdds, oddsAsOf).

Method (same idea as CME FedWatch, computed from 30-day fed funds futures):
  r_month  = 100 - price of the ZQ contract for a month (average EFFR in that month)
  r0       = EFFR in force now (FRED DFF; if the last meeting's decision is not
             yet in FRED, it is backed out of that meeting month's contract)
  r_after  = expected EFFR after the next meeting
             meeting late in month and next month has no meeting -> 100 - P(next month)
             otherwise -> (N*r_month - d*r0) / (N - d), d = days before effective date
  x        = (r_after - r0) / 0.25  -> probability of a 25bp move (and 50bp if |x| > 1)
Futures: Yahoo Finance tickers like ZQV26.CBT. Rates: FRED.
"""

import calendar, json, math, os, sys
from datetime import date, datetime, timedelta, timezone

import requests
import yfinance as yf

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FRED_KEY = os.environ.get("FRED_API_KEY", "")
DATA_FILE = "data.json"

# Statement (second) day of each meeting. Source: federalreserve.gov FOMC calendar.
# 2027 dates are tentative per the Fed. Extend this list each year.
FOMC = [
    ("2026-01-27", "2026-01-28"), ("2026-03-17", "2026-03-18"), ("2026-04-28", "2026-04-29"),
    ("2026-06-16", "2026-06-17"), ("2026-07-28", "2026-07-29"), ("2026-09-15", "2026-09-16"),
    ("2026-10-27", "2026-10-28"), ("2026-12-08", "2026-12-09"),
    ("2027-01-26", "2027-01-27"), ("2027-03-16", "2027-03-17"), ("2027-04-27", "2027-04-28"),
    ("2027-06-08", "2027-06-09"), ("2027-07-27", "2027-07-28"), ("2027-09-14", "2027-09-15"),
    ("2027-10-26", "2027-10-27"), ("2027-12-07", "2027-12-08"),
]
FOMC = [(date.fromisoformat(a), date.fromisoformat(b)) for a, b in FOMC]
MONTH_CODE = "FGHJKMNQUVXZ"


def ym_add(y, m, k):
    t = y * 12 + (m - 1) + k
    return t // 12, t % 12 + 1


def zq_rate(y, m):
    """Implied average EFFR for month (y, m) from the latest ZQ close, with price date."""
    t = f"ZQ{MONTH_CODE[m - 1]}{str(y)[-2:]}.CBT"
    df = yf.Ticker(t).history(period="10d").dropna(subset=["Close"])
    if df.empty:
        raise RuntimeError(f"no data for {t}")
    px = float(df["Close"].iloc[-1])
    print(f" [OK] {t} -> {px}")
    return 100 - px, df.index[-1].date()


def fred_obs(series, start):
    r = requests.get("https://api.stlouisfed.org/fred/series/observations", params={
        "series_id": series, "api_key": FRED_KEY, "file_type": "json",
        "observation_start": start.isoformat(), "sort_order": "asc"}, timeout=15).json()
    return [(date.fromisoformat(o["date"]), float(o["value"]))
            for o in r.get("observations", []) if o["value"] != "."]


def meeting_in_month(y, m):
    return next((b for a, b in FOMC if b.year == y and b.month == m), None)


def main():
    today_us = (datetime.now(timezone.utc) - timedelta(hours=4)).date()  # ET-ish
    # a meeting counts as "done" the day after its statement day (ET)
    upcoming = [b for a, b in FOMC if b >= today_us]
    past = [b for a, b in FOMC if b < today_us]
    if not upcoming:
        raise RuntimeError("FOMC calendar exhausted - extend FOMC list")
    nxt, last = upcoming[0], past[-1] if past else None

    # ── current EFFR (r0) ──────────────────────────────────────────────
    dff = fred_obs("DFF", today_us - timedelta(days=70))
    upper = fred_obs("DFEDTARU", today_us - timedelta(days=70))
    lower = fred_obs("DFEDTARL", today_us - timedelta(days=70))
    if not dff:
        raise RuntimeError("DFF unavailable (FRED_API_KEY?)")
    r0, r0_date = dff[-1][1], dff[-1][0]
    rng = (lower[-1][1], upper[-1][1]) if lower and upper else None

    if last and r0_date <= last:
        # decision not yet reflected in FRED -> back it out of that month's contract
        y, m = last.year, last.month
        N, d = calendar.monthrange(y, m)[1], last.day
        r_m, _ = zq_rate(y, m)
        pre = [v for dt, v in dff if dt.year == y and dt.month == m and dt.day <= d]
        pre_avg = sum(pre) / len(pre) if pre else r0
        r0 = (N * r_m - d * pre_avg) / (N - d)
        if rng:
            shift = round((r0 - pre_avg) / 0.25) * 0.25
            rng = (rng[0] + shift, rng[1] + shift)
        print(f" [INFO] last meeting {last} not in FRED yet -> r0 from futures {r0:.4f}")

    # ── expected EFFR after the next meeting ───────────────────────────
    y, m = nxt.year, nxt.month
    N, d = calendar.monthrange(y, m)[1], nxt.day
    ny, nm = ym_add(y, m, 1)
    if N - d < 10 and meeting_in_month(ny, nm) is None:
        r_after, px_date = zq_rate(ny, nm)
    else:
        r_m, px_date = zq_rate(y, m)
        r_after = (N * r_m - d * r0) / (N - d)

    x = (r_after - r0) / 0.25
    a = abs(x)
    big, small = max(0.0, min(a - 1, 1.0)), None
    small = min(a, 1.0) - big if a <= 1 else 1.0 - big
    hold = max(0.0, 1 - min(a, 1.0))
    move_ko, move_en = ("인상", "hike") if x >= 0 else ("인하", "cut")
    pct = lambda v: int(round(v * 100))
    mo = f"{m}월"
    mo_en = nxt.strftime("%b")
    pxd = f"{px_date.month}/{px_date.day}"

    if a < 0.01:
        ko, en = f"{mo} 동결 ~100%", f"{mo_en} hold ~100%"
    elif big >= 0.005:
        ko = f"{mo} 50bp {move_ko} {pct(big)}% · 25bp {move_ko} {pct(small)}%"
        en = f"{mo_en} 50bp {move_en} {pct(big)}% · 25bp {move_en} {pct(small)}%"
    else:
        ko = f"{mo} 25bp {move_ko} {pct(small)}% · 동결 {pct(hold)}%"
        en = f"{mo_en} 25bp {move_en} {pct(small)}% · hold {pct(hold)}%"
    ko += f" (연방기금선물 내재, {pxd} 종가)"
    en += f" (fed funds futures implied, {pxd} close)"

    meet = next(p for p in FOMC if p[1] == nxt)
    fmt = lambda v: f"{v:.2f}"
    fed = {
        "asOf": px_date.isoformat(),
        "nextFOMC": f"{meet[0].isoformat()}~{meet[1].day:02d}",
        "targetRange": f"{fmt(rng[0])}–{fmt(rng[1])}%" if rng else None,
        "marketOdds": ko,
        "marketOddsEn": en,
        "effr": round(r0, 4),
        "impliedAfter": round(r_after, 4),
        "impliedMoveBp": round(x * 25, 1),
    }
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    data["fed"] = fed
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print("FED:", json.dumps(fed, ensure_ascii=False))


if __name__ == "__main__":
    main()
