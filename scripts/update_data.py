"""
Macro War Room — Automated Data Fetcher
Pulls live data from FRED (US macro) + Yahoo Finance (FX, equities, international yields)
Run: python update_data.py
Output: public/data.json  (loaded by the React app on startup)
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
TODAY    = datetime.today().strftime("%Y-%m-%d")
LOG      = []

# ─────────────────────────────────────────────────────────────────────────────
# FRED helper  (free API — register at fred.stlouisfed.org/docs/api/api_key.html)
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
        LOG.append(f"  [OK]   {series} → {vals[0]}")
        return vals
    except Exception as e:
        LOG.append(f"  [ERR]  {series}: {e}")
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
        if v != v:                              # NaN guard (NaN is truthy in Python!)
            LOG.append(f"  [SKIP] {ticker} — NaN")
            return None
        LOG.append(f"  [OK]   {ticker} → {v}")
        return v
    except Exception as e:
        LOG.append(f"  [ERR]  {ticker}: {e}")
        return None

# ─────────────────────────────────────────────────────────────────────────────
# FRED series reference card
# ─────────────────────────────────────────────────────────────────────────────
# US
#   Fed Funds Rate:          FEDFUNDS
#   2Y Treasury:             DGS2
#   10Y Treasury:            DGS10
#   CPI YoY (need to compute): CPIAUCSL
#   GDP YoY growth:          A191RL1Q225SBEA
#
# Yahoo Finance tickers
#   FX:  USDJPY=X  USDKRW=X  USDCNY=X  EURUSD=X  GBPUSD=X  DX-Y.NYB (DXY)
#   Equity: ^GSPC (S&P500)  ^N225 (Nikkei)  ^KS11 (KOSPI)  000300.SS (CSI300)
#             ^STOXX50E  ^FTSE
#   Yields (YF bonds): ^TNX (US 10Y)  ^FVX (US 5Y)  ^IRX (US 3M)
#            ^TNX for US 10Y  JGBS (JP 10Y)  TLT as proxy
#
# ─────────────────────────────────────────────────────────────────────────────
print("Fetching macro data...")
print("─" * 50)

# ── US ────────────────────────────────────────────────────────────────────────
print("US Rates (FRED):")
us_policy  = fred("FEDFUNDS")[0]
us_2y      = fred("DGS2")[0]
us_10y     = fred("DGS10")[0]
cpi_obs    = fred("CPIAUCSL", 14)        # 13 months to compute YoY
if cpi_obs[0] and cpi_obs[12]:
    us_cpi = round((cpi_obs[0] / cpi_obs[12] - 1) * 100, 1)
else:
    us_cpi = None
us_gdp     = fred("A191RL1Q225SBEA")[0]  # quarterly, real GDP growth

print("FX (Yahoo Finance):")
usdjpy  = yf_last("USDJPY=X")
usdkrw  = yf_last("USDKRW=X")
usdcny  = yf_last("USDCNY=X")
eurusd  = yf_last("EURUSD=X")
gbpusd  = yf_last("GBPUSD=X")
dxy     = yf_last("DX-Y.NYB")

print("Equities (Yahoo Finance):")
spx     = yf_last("^GSPC")
nikkei  = yf_last("^N225")
kospi   = yf_last("^KS11")
csi300  = yf_last("000300.SS")
eurostoxx = yf_last("^STOXX50E")
ftse    = yf_last("^FTSE")

# ── International yields via YF ───────────────────────────────────────────────
print("Bond yields (Yahoo Finance):")
us10y_yf    = yf_last("^TNX")            # US 10Y (%)
jp10y_yf    = yf_last("^JGBL")          # JP 10Y (may vary)
uk10y_yf    = yf_last("^TMBMKGB-10Y")   # UK Gilt 10Y

# ─────────────────────────────────────────────────────────────────────────────
# Assemble output JSON
# ─────────────────────────────────────────────────────────────────────────────
data = {
    "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "date":    TODAY,
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
        "SPX":       int(spx) if spx else None,
        "Nikkei":    int(nikkei) if nikkei else None,
        "KOSPI":     int(kospi) if kospi else None,
        "CSI300":    int(csi300) if csi300 else None,
        "EuroStoxx": int(eurostoxx) if eurostoxx else None,
        "FTSE":      int(ftse) if ftse else None,
    },
    "us": {
        "policyRate": us_policy,
        "y2":         us_2y,
        "y10":        us_10y or (round(us10y_yf, 4) if us10y_yf else None),
        "cpiYoY":     us_cpi,
        "gdpYoY":     us_gdp,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Save
# ─────────────────────────────────────────────────────────────────────────────
os.makedirs("public", exist_ok=True)
outfile = "public/data.json"
with open(outfile, "w") as f:
    json.dump(data, f, indent=2)

print("─" * 50)
print(f"Saved → {outfile}")
print(f"Updated: {data['updated']}")
if None in [us_policy, us_2y, us_10y]:
    print("\n⚠  FRED data unavailable — set FRED_API_KEY env variable")
    print("   Free key: https://fred.stlouisfed.org/docs/api/api_key.html")
else:
    print(f"\nUS: Policy {us_policy}% | 2Y {us_2y}% | 10Y {us_10y}% | CPI {us_cpi}%")
    print(f"FX: USDJPY {usdjpy} | USDKRW {usdkrw} | DXY {dxy}")
