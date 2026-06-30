"""
Macro War Room — Automated Data Fetcher
Pulls live data from FRED (US macro) + Yahoo Finance (FX, equities, international yields)
+ BOK ECOS API (South Korea: Policy Rate, 2Y/10Y Yield, CPI, GDP)
Run: python update_data.py
Output: data.json (loaded by index.html on startup)
"""

import json, os, sys
from datetime import datetime, timedelta, timezone

# Force UTF-8 console so emoji/box-drawing prints don't crash on Windows (cp949)
try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
        pass

try:
        import requests
        import yfinance as yf
except ImportError:
        print("Installing dependencies...")
        os.system("pip install requests yfinance --quiet")
        import requests
        import yfinance as yf

FRED_KEY = os.environ.get("FRED_API_KEY", "")   # free at fred.stlouisfed.org/docs/api
ECOS_KEY = os.environ.get("ECOS_API_KEY", "")   # free at ecos.bok.or.kr
TODAY    = datetime.today().strftime("%Y-%m-%d")
LOG      = []

# ─────────────────────────────────────────────────────────────────────────────
# FRED helper (free API — register at fred.stlouisfed.org/docs/api/api_key.html)
# ─────────────────────────────────────────────────────────────────────────────
def fred(series, obs=2):
        """Return last N observations for a FRED series."""
        if not FRED_KEY:
                    LOG.append(f"  [SKIP] {series} — no FRED_API_KEY")
                    return [None]
                try:
                            r = requests.get(
                                            "https://api.stlouisfed.org/fred/series/observations",
                                            params={"series_id": series, "api_key": FRED_KEY,
                                                                        "file_type": "json", "sort_order": "desc", "limit": obs},
                                            timeout=10
                            ).json()
                            vals = [float(o["value"]) if o["value"] != "." else None
                                    for o in r.get("observations", [])]
                            LOG.append(f"  [OK]  {series} → {vals[0]}")
                            return vals
except Exception as e:
        LOG.append(f"  [ERR] {series}: {e}")
        return [None]

# ─────────────────────────────────────────────────────────────────────────────
# Yahoo Finance helper
# ─────────────────────────────────────────────────────────────────────────────
def yf_last(ticker, period="5d"):
        """Return latest close price for a Yahoo Finance ticker (None if unavailable/NaN)."""
    try:
                df = yf.Ticker(ticker).history(period=period)
                if "Close" in df:
                                df = df.dropna(subset=["Close"])   # drop holidays / missing closes
            if df.empty:
                                LOG.append(f"  [SKIP] {ticker} — no data")
                                return None
                            v = round(float(df["Close"].iloc[-1]), 4)
            if v != v:   # NaN guard (NaN is truthy in Python!)
                                LOG.append(f"  [SKIP] {ticker} — NaN")
                                return None
                            LOG.append(f"  [OK]  {ticker} → {v}")
            return v
except Exception as e:
        LOG.append(f"  [ERR] {ticker}: {e}")
    return None

# ─────────────────────────────────────────────────────────────────────────────
# BOK ECOS API helper
# ECOS StatisticSearch endpoint:
#   /StatisticSearch/{apiKey}/json/kr/1/1/{statCode}/{cycle}/{startDate}/{endDate}/{itemCode}
#
# Key series used:
#   722Y001 / 0101000  — BOK Base Rate (monthly, %)
#   817Y002 / 010190000  — KTB 2Y yield (daily, %)
#   817Y002 / 010200000  — KTB 3Y yield (daily, %) — proxy for 2Y matrix row
#   817Y002 / 010500000  — KTB 10Y yield (daily, %)
#   901Y009 / 0            — CPI YoY (monthly, %)
#   111Y006 / C0           — GDP growth rate YoY (quarterly, %)
# ─────────────────────────────────────────────────────────────────────────────
def ecos(stat_code, item_code, cycle="M", n=14):
        """
            Fetch the latest N observations from BOK ECOS.
                cycle: D=daily, M=monthly, Q=quarterly, A=annual
                    Returns list of floats (most-recent first), or [None] on failure.
                        """
    if not ECOS_KEY:
                LOG.append(f"  [SKIP] ECOS {stat_code}/{item_code} — no ECOS_API_KEY")
                return [None] * n

    # Date window: go back far enough to always capture N obs
    days_back = {"D": 60, "M": 500, "Q": 1200, "A": 3650}.get(cycle, 500)
    start = (datetime.today() - timedelta(days=days_back)).strftime(
                "%Y%m%d" if cycle == "D" else ("%Y%m" if cycle == "M" else ("%Y%m" if cycle == "Q" else "%Y"))
    )
    end = datetime.today().strftime(
                "%Y%m%d" if cycle == "D" else ("%Y%m" if cycle == "M" else ("%Y%m" if cycle == "Q" else "%Y"))
    )

    url = (f"https://ecos.bok.or.kr/api/StatisticSearch/{ECOS_KEY}/json/kr"
                      f"/1/100/{stat_code}/{cycle}/{start}/{end}/{item_code}")
    try:
                r = requests.get(url, timeout=15).json()
                rows = r.get("StatisticSearch", {}).get("row", [])
                if not rows:
                                LOG.append(f"  [SKIP] ECOS {stat_code}/{item_code} — empty response")
                                return [None] * n
                            # Sort descending by TIME field so index 0 = most recent
                            rows.sort(key=lambda x: x.get("TIME", ""), reverse=True)
        vals = []
        for row in rows[:n]:
                        try:
                                            vals.append(round(float(row["DATA_VALUE"]), 4))
except (KeyError, ValueError):
                vals.append(None)
        while len(vals) < n:
                        vals.append(None)
                    LOG.append(f"  [OK]  ECOS {stat_code}/{item_code} → {vals[0]}")
        return vals
except Exception as e:
        LOG.append(f"  [ERR] ECOS {stat_code}/{item_code}: {e}")
        return [None] * n


def ecos_val(stat_code, item_code, cycle="M", n=14):
        """Return single latest value (float or None)."""
    return ecos(stat_code, item_code, cycle, n)[0]


# ─────────────────────────────────────────────────────────────────────────────
# Helper: pick index from list safely
# ─────────────────────────────────────────────────────────────────────────────
def idx(lst, i, fallback=None):
        try:
                    v = lst[i]
                    return v if v is not None else fallback
        except IndexError:
        return fallback


# ─────────────────────────────────────────────────────────────────────────────
# FETCH — US (FRED)
# ─────────────────────────────────────────────────────────────────────────────
print("Fetching macro data...")
print("─" * 50)

print("US Rates (FRED):")
us_policy = fred("FEDFUNDS")[0]
us_2y     = fred("DGS2")[0]
us_10y    = fred("DGS10")[0]
cpi_obs   = fred("CPIAUCSL", 14)   # 13 months to compute YoY
if cpi_obs[0] and cpi_obs[12]:
        us_cpi = round((cpi_obs[0] / cpi_obs[12] - 1) * 100, 1)
else:
    us_cpi = None
us_gdp = fred("A191RL1Q225SBEA")[0]   # quarterly, real GDP growth

# ─────────────────────────────────────────────────────────────────────────────
# FETCH — FX & Equities (Yahoo Finance)
# ─────────────────────────────────────────────────────────────────────────────
print("FX (Yahoo Finance):")
usdjpy  = yf_last("USDJPY=X")
usdkrw  = yf_last("USDKRW=X")
usdcny  = yf_last("USDCNY=X")
eurusd  = yf_last("EURUSD=X")
gbpusd  = yf_last("GBPUSD=X")
dxy     = yf_last("DX-Y.NYB")

print("Equities (Yahoo Finance):")
spx       = yf_last("^GSPC")
nikkei    = yf_last("^N225")
kospi     = yf_last("^KS11")
csi300    = yf_last("000300.SS")
eurostoxx = yf_last("^STOXX50E")
ftse      = yf_last("^FTSE")

# ── International yields via YF ───────────────────────────────────────────────
print("Bond yields (Yahoo Finance):")
us10y_yf = yf_last("^TNX")           # US 10Y (%)
jp10y_yf = yf_last("^JGBL")          # JP 10Y (may vary)
uk10y_yf = yf_last("^TMBMKGB-10Y")   # UK Gilt 10Y

print("Commodities / vol (Yahoo Finance):")
brent = yf_last("BZ=F")    # Brent crude
wti   = yf_last("CL=F")    # WTI crude
gold  = yf_last("GC=F")    # Gold
vix   = yf_last("^VIX")    # Volatility index

# ─────────────────────────────────────────────────────────────────────────────
# FETCH — South Korea (BOK ECOS API)
# ─────────────────────────────────────────────────────────────────────────────
print("South Korea (BOK ECOS API):")

# BOK Base Rate — 722Y001 / 0101000, monthly
kr_policy_obs = ecos("722Y001", "0101000", cycle="M", n=14)
kr_policy      = idx(kr_policy_obs, 0)    # now
kr_policy_m1   = idx(kr_policy_obs, 1)    # 1M ago
kr_policy_y1   = idx(kr_policy_obs, 12)   # 1Y ago

# KTB 3Y yield (daily) — proxy for "2Y Yield" row in the matrix
# 817Y002 / 010190000 = 국고채 2년, 010200000 = 국고채 3년
kr_2y_obs  = ecos("817Y002", "010190000", cycle="D", n=400)
kr_2y      = idx(kr_2y_obs, 0)
kr_2y_d1   = idx(kr_2y_obs, 1)
kr_2y_w1   = idx(kr_2y_obs, 5)
kr_2y_m1   = idx(kr_2y_obs, 22)
kr_2y_y1   = idx(kr_2y_obs, 250)

# KTB 10Y yield (daily) — 817Y002 / 010500000
kr_10y_obs = ecos("817Y002", "010500000", cycle="D", n=400)
kr_10y     = idx(kr_10y_obs, 0)
kr_10y_d1  = idx(kr_10y_obs, 1)
kr_10y_w1  = idx(kr_10y_obs, 5)
kr_10y_m1  = idx(kr_10y_obs, 22)
kr_10y_y1  = idx(kr_10y_obs, 250)

# 2s10s slope (bps) — computed from 2Y and 10Y
def slope_bps(y10, y2):
        if y10 is None or y2 is None:
                    return None
                return round((y10 - y2) * 100)

kr_slope     = slope_bps(kr_10y,    kr_2y)
kr_slope_d1  = slope_bps(kr_10y_d1, kr_2y_d1)
kr_slope_w1  = slope_bps(kr_10y_w1, kr_2y_w1)
kr_slope_m1  = slope_bps(kr_10y_m1, kr_2y_m1)
kr_slope_y1  = slope_bps(kr_10y_y1, kr_2y_y1)

# CPI YoY (monthly) — 901Y009 / 0
# DATA_VALUE is already a YoY % change from ECOS
kr_cpi_obs = ecos("901Y009", "0", cycle="M", n=14)
kr_cpi     = idx(kr_cpi_obs, 0)
kr_cpi_m1  = idx(kr_cpi_obs, 1)
kr_cpi_y1  = idx(kr_cpi_obs, 12)

# GDP YoY growth rate (quarterly) — 111Y006 / C0
kr_gdp_obs = ecos("111Y006", "C0", cycle="Q", n=6)
kr_gdp     = idx(kr_gdp_obs, 0)
kr_gdp_q1  = idx(kr_gdp_obs, 1)   # 1Q ago (≈ 1M ago proxy)
kr_gdp_y1  = idx(kr_gdp_obs, 4)   # ~1Y ago (4 quarters)

# ─────────────────────────────────────────────────────────────────────────────
# Assemble output JSON
# ─────────────────────────────────────────────────────────────────────────────
data = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "date": TODAY,
        "fx": {
                    "USDJPY":  usdjpy,
                    "USDKRW":  int(usdkrw) if usdkrw else None,
                    "USDCNY":  usdcny,
                    "EURUSD":  eurusd,
                    "GBPUSD":  gbpusd,
                    "DXY":     round(dxy, 2) if dxy else None,
                    "JPYKRW":  round(usdkrw / usdjpy, 2) if usdkrw and usdjpy else None,
        },
        "equities": {
                    "SPX":       int(spx)       if spx       else None,
                    "Nikkei":    int(nikkei)    if nikkei    else None,
                    "KOSPI":     int(kospi)     if kospi     else None,
                    "CSI300":    int(csi300)    if csi300    else None,
                    "EuroStoxx": int(eurostoxx) if eurostoxx else None,
                    "FTSE":      int(ftse)      if ftse      else None,
        },
        "commodities": {
                    "brent": round(brent, 2) if brent else None,
                    "wti":   round(wti,   2) if wti   else None,
                    "gold":  round(gold,  2) if gold  else None,
                    "vix":   round(vix,   2) if vix   else None,
        },
        "us": {
                    "policyRate": us_policy,
                    "y2":         us_2y,
                    "y10":        us_10y or (round(us10y_yf, 4) if us10y_yf else None),
                    "cpiYoY":     us_cpi,
                    "gdpYoY":     us_gdp,
        },
        # ── South Korea — live from BOK ECOS ─────────────────────────────────────
        "kr": {
                    "policyRate":  kr_policy,
                    "policyRate_m1": kr_policy_m1,
                    "policyRate_y1": kr_policy_y1,
                    "y2":    kr_2y,    "y2_d1":  kr_2y_d1,  "y2_w1":  kr_2y_w1,
                    "y2_m1": kr_2y_m1, "y2_y1":  kr_2y_y1,
                    "y10":    kr_10y,   "y10_d1": kr_10y_d1, "y10_w1": kr_10y_w1,
                    "y10_m1": kr_10y_m1,"y10_y1": kr_10y_y1,
                    "slope":    kr_slope,    "slope_d1": kr_slope_d1, "slope_w1": kr_slope_w1,
                    "slope_m1": kr_slope_m1, "slope_y1": kr_slope_y1,
                    "cpiYoY":    kr_cpi,   "cpiYoY_m1": kr_cpi_m1,  "cpiYoY_y1": kr_cpi_y1,
                    "gdpYoY":    kr_gdp,   "gdpYoY_q1": kr_gdp_q1,  "gdpYoY_y1": kr_gdp_y1,
        },
}

# ─────────────────────────────────────────────────────────────────────────────
# Save
# ─────────────────────────────────────────────────────────────────────────────
outfile = "data.json"
with open(outfile, "w") as f:
        json.dump(data, f, indent=2)

print("─" * 50)
print(f"Saved → {outfile}")
print(f"Updated: {data['updated']}")
if None in [us_policy, us_2y, us_10y]:
        print("\n⚠  FRED data unavailable — set FRED_API_KEY env variable")
    print("   Free key: https://fred.stlouisfed.org/docs/api/api_key.html")
else:
    print(f"\nUS:  Policy {us_policy}% | 2Y {us_2y}% | 10Y {us_10y}% | CPI {us_cpi}%")

if None in [kr_policy, kr_2y, kr_10y]:
        print("\n⚠  BOK ECOS data unavailable — set ECOS_API_KEY env variable")
    print("   Free key: https://ecos.bok.or.kr")
else:
    print(f"KR:  BOK {kr_policy}% | 2Y {kr_2y}% | 10Y {kr_10y}% | CPI {kr_cpi}%")

print(f"FX:  USDJPY {usdjpy} | USDKRW {usdkrw} | DXY {dxy}")
for msg in LOG:
        print(msg)
