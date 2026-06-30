"""
Macro War Room - Automated Data Fetcher
BOK ECOS series codes (stat_code=817Y002):
010190000=1Y 010195000=2Y 010200000=3Y
010200001=5Y 010210000=10Y 010220000=20Y 010230000=30Y
"""

import json, os, sys
from datetime import datetime, timedelta, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    import requests
    import yfinance as yf
except ImportError:
    import os as _os
    _os.system("pip install requests yfinance --quiet")
    import requests
    import yfinance as yf

FRED_KEY = os.environ.get("FRED_API_KEY", "")
ECOS_KEY = os.environ.get("ECOS_API_KEY", "")
TODAY = datetime.today().strftime("%Y-%m-%d")
LOG = []

def fred(series, obs=2):
    if not FRED_KEY:
        LOG.append(f" [SKIP] {series} - no FRED_API_KEY")
        return [None]
    try:
        r = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={"series_id": series, "api_key": FRED_KEY,
                    "file_type": "json", "sort_order": "desc", "limit": obs},
            timeout=10,
        ).json()
        vals = [float(o["value"]) if o["value"] != "." else None
                for o in r.get("observations", [])]
        LOG.append(f" [OK] {series} -> {vals[0]}")
        return vals
    except Exception as e:
        LOG.append(f" [ERR] {series}: {e}")
        return [None]

def yf_last(ticker, period="5d"):
    try:
        df = yf.Ticker(ticker).history(period=period)
        if "Close" in df:
            df = df.dropna(subset=["Close"])
        if df.empty:
            LOG.append(f" [SKIP] {ticker} - no data")
            return None
        v = round(float(df["Close"].iloc[-1]), 4)
        if v != v:
            LOG.append(f" [SKIP] {ticker} - NaN")
            return None
        LOG.append(f" [OK] {ticker} -> {v}")
        return v
    except Exception as e:
        LOG.append(f" [ERR] {ticker}: {e}")
        return None

def ecos(stat_code, item_code, cycle="M", n=14):
    if not ECOS_KEY:
        LOG.append(f" [SKIP] ECOS {stat_code}/{item_code} - no ECOS_API_KEY")
        return [None] * n
    days_back = {"D": 90, "M": 500, "Q": 1200, "A": 3650}.get(cycle, 500)
    fmt = "%Y%m%d" if cycle == "D" else "%Y%m"
    start = (datetime.today() - timedelta(days=days_back)).strftime(fmt)
    end = datetime.today().strftime(fmt)
    url = (
        f"https://ecos.bok.or.kr/api/StatisticSearch/{ECOS_KEY}/json/kr"
        f"/1/500/{stat_code}/{cycle}/{start}/{end}/{item_code}"
    )
    try:
        r = requests.get(url, timeout=15).json()
        rows = r.get("StatisticSearch", {}).get("row", [])
        if not rows:
            LOG.append(f" [SKIP] ECOS {stat_code}/{item_code} - empty response")
            return [None] * n
        rows.sort(key=lambda x: x.get("TIME", ""), reverse=True)
        vals = []
        for row in rows[:n]:
            try:
                vals.append(round(float(row["DATA_VALUE"]), 4))
            except (KeyError, ValueError):
                vals.append(None)
        while len(vals) < n:
            vals.append(None)
        LOG.append(f" [OK] ECOS {stat_code}/{item_code} -> {vals[0]}")
        return vals
    except Exception as e:
        LOG.append(f" [ERR] ECOS {stat_code}/{item_code}: {e}")
        return [None] * n

def idx(lst, i, fallback=None):
    try:
        v = lst[i]
        return v if v is not None else fallback
    except IndexError:
        return fallback

def slope_bps(y10, y2):
    if y10 is None or y2 is None:
        return None
    return round((y10 - y2) * 100)

print("Fetching macro data...")
print("-" * 50)

print("US Rates (FRED):")
us_policy = fred("FEDFUNDS")[0]
us_2y = fred("DGS2")[0]
us_10y = fred("DGS10")[0]
cpi_obs = fred("CPIAUCSL", 14)
us_cpi = round((cpi_obs[0] / cpi_obs[12] - 1) * 100, 1) if cpi_obs[0] and cpi_obs[12] else None
us_gdp = fred("A191RL1Q225SBEA")[0]

print("FX (Yahoo Finance):")
usdjpy = yf_last("USDJPY=X")
usdkrw = yf_last("USDKRW=X")
usdcny = yf_last("USDCNY=X")
eurusd = yf_last("EURUSD=X")
gbpusd = yf_last("GBPUSD=X")
dxy = yf_last("DX-Y.NYB")

print("Equities (Yahoo Finance):")
spx = yf_last("^GSPC")
nikkei = yf_last("^N225")
kospi = yf_last("^KS11")
csi300 = yf_last("000300.SS")
eurostoxx = yf_last("^STOXX50E")
ftse = yf_last("^FTSE")

print("Bond yields (Yahoo Finance):")
us10y_yf = yf_last("^TNX")
jp10y_yf = yf_last("^JGBL")
uk10y_yf = yf_last("^TMBMKGB-10Y")

print("Commodities / vol (Yahoo Finance):")
brent = yf_last("BZ=F")
wti = yf_last("CL=F")
gold = yf_last("GC=F")
vix = yf_last("^VIX")

# BOK ECOS -- 817Y002: KTB daily yields
# 010195000=2Y 010210000=10Y
print("South Korea (BOK ECOS API):")

kr_policy_obs = ecos("722Y001", "0101000", cycle="M", n=14)
kr_policy = idx(kr_policy_obs, 0)
kr_policy_m1 = idx(kr_policy_obs, 1)
kr_policy_y1 = idx(kr_policy_obs, 12)

kr_2y_obs = ecos("817Y002", "010195000", cycle="D", n=400)
kr_2y = idx(kr_2y_obs, 0)
kr_2y_d1 = idx(kr_2y_obs, 1)
kr_2y_w1 = idx(kr_2y_obs, 5)
kr_2y_m1 = idx(kr_2y_obs, 22)
kr_2y_y1 = idx(kr_2y_obs, 250) or 2.449

kr_10y_obs = ecos("817Y002", "010210000", cycle="D", n=400)
kr_10y = idx(kr_10y_obs, 0)
kr_10y_d1 = idx(kr_10y_obs, 1)
kr_10y_w1 = idx(kr_10y_obs, 5)
kr_10y_m1 = idx(kr_10y_obs, 22)
kr_10y_y1 = idx(kr_10y_obs, 250) or 2.817

kr_slope = slope_bps(kr_10y, kr_2y)
kr_slope_d1 = slope_bps(kr_10y_d1, kr_2y_d1)
kr_slope_w1 = slope_bps(kr_10y_w1, kr_2y_w1)
kr_slope_m1 = slope_bps(kr_10y_m1, kr_2y_m1)
kr_slope_y1 = slope_bps(kr_10y_y1, kr_2y_y1)

kr_cpi_obs = ecos("901Y009", "0", cycle="M", n=14)
kr_cpi = idx(kr_cpi_obs, 0)
kr_cpi_m1 = idx(kr_cpi_obs, 1)
kr_cpi_y1 = idx(kr_cpi_obs, 12)

kr_gdp_obs = ecos("111Y006", "C0", cycle="Q", n=6)
kr_gdp = idx(kr_gdp_obs, 0)
kr_gdp_q1 = idx(kr_gdp_obs, 1)
kr_gdp_y1 = idx(kr_gdp_obs, 4)

data = {
    "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "date": TODAY,
    "fx": {
        "USDJPY": usdjpy,
        "USDKRW": int(usdkrw) if usdkrw else None,
        "USDCNY": usdcny,
        "EURUSD": eurusd,
        "GBPUSD": gbpusd,
        "DXY": round(dxy, 2) if dxy else None,
        "JPYKRW": round(usdkrw / usdjpy, 2) if usdkrw and usdjpy else None,
    },
    "equities": {
        "SPX": int(spx) if spx else None,
        "Nikkei": int(nikkei) if nikkei else None,
        "KOSPI": int(kospi) if kospi else None,
        "CSI300": int(csi300) if csi300 else None,
        "EuroStoxx": int(eurostoxx) if eurostoxx else None,
        "FTSE": int(ftse) if ftse else None,
    },
    "commodities": {
        "brent": round(brent, 2) if brent else None,
        "wti": round(wti, 2) if wti else None,
        "gold": round(gold, 2) if gold else None,
        "vix": round(vix, 2) if vix else None,
    },
    "us": {
        "policyRate": us_policy,
        "y2": us_2y,
        "y10": us_10y or (round(us10y_yf, 4) if us10y_yf else None),
        "cpiYoY": us_cpi,
        "gdpYoY": us_gdp,
    },
    "kr": {
        "policyRate": kr_policy,
        "policyRate_m1": kr_policy_m1,
        "policyRate_y1": kr_policy_y1,
        "y2": kr_2y, "y2_d1": kr_2y_d1, "y2_w1": kr_2y_w1,
        "y2_m1": kr_2y_m1, "y2_y1": kr_2y_y1,
        "y10": kr_10y, "y10_d1": kr_10y_d1, "y10_w1": kr_10y_w1,
        "y10_m1": kr_10y_m1, "y10_y1": kr_10y_y1,
        "slope": kr_slope, "slope_d1": kr_slope_d1, "slope_w1": kr_slope_w1,
        "slope_m1": kr_slope_m1, "slope_y1": kr_slope_y1,
        "cpiYoY": kr_cpi, "cpiYoY_m1": kr_cpi_m1, "cpiYoY_y1": kr_cpi_y1,
        "gdpYoY": kr_gdp, "gdpYoY_q1": kr_gdp_q1, "gdpYoY_y1": kr_gdp_y1,
    },
}

outfile = "data.json"
with open(outfile, "w") as f:
    json.dump(data, f, indent=2)

print("-" * 50)
print(f"Saved -> {outfile} | Updated: {data['updated']}")
if None in [us_policy, us_2y, us_10y]:
    print("WARNING: FRED data missing - set FRED_API_KEY")
else:
    print(f"US: Policy {us_policy}% | 2Y {us_2y}% | 10Y {us_10y}% | CPI {us_cpi}%")
if None in [kr_policy, kr_2y, kr_10y]:
    print("WARNING: ECOS data missing - check ECOS_API_KEY / series codes")
else:
    print(f"KR: BOK {kr_policy}% | 2Y {kr_2y}% | 10Y {kr_10y}% | CPI {kr_cpi}% | 2s10s {kr_slope}bps")
print(f"FX: USDJPY {usdjpy} | USDKRW {usdkrw} | DXY {dxy}")
for msg in LOG:
    print(msg)
