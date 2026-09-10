"""
Macro War Room - Automated Data Fetcher
BOK ECOS series codes (stat_code=817Y002):
010190000=1Y 010195000=2Y 010200000=3Y
010200001=5Y 010210000=10Y 010220000=20Y 010230000=30Yh

NFP fetching:
- PAYEMS  : Total Nonfarm Payrolls (monthly, thousands, seasonally adjusted)
- MoM change is derived as (current_level - prior_level), stored in THOUSANDS
  (e.g. 162 = +162K jobs) — same unit as the consensus `estimate` field.
- `actual`   = FIRST PRINT (set once when the month first appears, never
               overwritten, so surprise = first print - consensus is apples to apples)
- `revised`  = latest FRED value (updated every run)
- `release`  = BLS release date (from FRED PAYEMS vintage dates)
- `spx`      = S&P 500 % change on the release day, auto-filled from Yahoo
               (null if the cash market was closed, e.g. Good Friday)
- `estimate` = Dow Jones consensus in thousands — patch manually after each
               release (no free consensus API); `note` is optional.
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

def fred(series, obs=2, units=None):
    """
    units=None   -> raw level (default)
    units="pch"  -> percent change from preceding period (e.g. Retail Sales m/m)
    units="pc1"  -> percent change from year ago (e.g. Core PCE y/y)
    """
    if not FRED_KEY:
        LOG.append(f" [SKIP] {series} - no FRED_API_KEY")
        return [None]
    try:
        params = {"series_id": series, "api_key": FRED_KEY,
                  "file_type": "json", "sort_order": "desc", "limit": obs}
        if units:
            params["units"] = units
        r = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params=params,
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

def fred_obs(series, obs=400):
    """FRED observations as [(date 'YYYY-MM-DD', float), ...] newest first, '.' skipped."""
    if not FRED_KEY:
        LOG.append(f" [SKIP] {series} - no FRED_API_KEY")
        return []
    try:
        r = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={"series_id": series, "api_key": FRED_KEY, "file_type": "json",
                    "sort_order": "desc", "limit": obs},
            timeout=15,
        ).json()
        out = [(o["date"], float(o["value"])) for o in r.get("observations", [])
               if o.get("value") not in (".", "", None)]
        LOG.append(f" [OK] {series} -> {out[0] if out else 'empty'}")
        return out
    except Exception as e:
        LOG.append(f" [ERR] {series}: {e}")
        return []

def hist_points(obs, dp=2):
    """From newest-first [(date, v)] daily obs -> now / 1D / 1W / 1M / 1Y ago values."""
    if not obs:
        return {}
    d0 = datetime.strptime(obs[0][0], "%Y-%m-%d")
    def on_or_before(days):
        cutoff = (d0 - timedelta(days=days)).strftime("%Y-%m-%d")
        for d, v in obs:
            if d <= cutoff:
                return round(v, dp)
        return None
    return {
        "now": round(obs[0][1], dp),
        "d1":  round(obs[1][1], dp) if len(obs) > 1 else None,
        "w1":  on_or_before(7),
        "m1":  on_or_before(30),
        "y1":  on_or_before(365),
    }

def yf_hist_points(ticker):
    """Yahoo daily closes -> now / 1D / 1W / 1M / 1Y ago (for equity index rows)."""
    try:
        df = yf.Ticker(ticker).history(period="13mo").dropna(subset=["Close"])
        obs = [(i.strftime("%Y-%m-%d"), float(c)) for i, c in zip(df.index, df["Close"])]
        obs.reverse()
        return hist_points(obs, dp=0)
    except Exception as e:
        LOG.append(f" [ERR] {ticker} history: {e}")
        return {}

def yoy_series(obs, lag=12):
    """Index-level obs (newest first) -> list of y/y % changes, newest first."""
    out = []
    for i in range(len(obs) - lag):
        try:
            out.append(round((obs[i][1] / obs[i + lag][1] - 1) * 100, 1))
        except (ZeroDivisionError, TypeError):
            out.append(None)
    return out

def month_label(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%b %Y")
    except Exception:
        return None

def quarter_label(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return f"Q{(dt.month - 1)//3 + 1} {dt.year}"
    except Exception:
        return None

def slope_bps(y10, y2):
    if y10 is None or y2 is None:
        return None
    return round((y10 - y2) * 100)

# ── NFP helpers ──────────────────────────────────────────────────────────────

def fred_nfp_history(n_months=48):
    """
    Fetch the last n_months of PAYEMS (Total Nonfarm Payrolls, level in thousands SA).
    Derives month-over-month job change in THOUSANDS: (curr_level - prev_level).
    Returns list of {"date": "YYYY-MM-01", "actual": int} oldest first.
    Falls back to [] when FRED key is missing.
    """
    if not FRED_KEY:
        LOG.append(" [SKIP] NFP history - no FRED_API_KEY")
        return []
    try:
        r = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={
                "series_id": "PAYEMS",
                "api_key": FRED_KEY,
                "file_type": "json",
                "sort_order": "desc",
                "limit": n_months + 1,   # +1 so we can compute MoM change for the latest month
            },
            timeout=10,
        ).json()
        obs = r.get("observations", [])
        result = []
        for i in range(len(obs) - 1):
            curr = obs[i]
            prev = obs[i + 1]
            try:
                curr_v = float(curr["value"])
                prev_v = float(prev["value"])
                # PAYEMS level is in thousands -> MoM change in thousands (162 = +162K)
                mom_k = int(round(curr_v - prev_v))
                result.append({"date": curr["date"], "actual": mom_k})
            except (ValueError, TypeError):
                pass
        result.reverse()   # oldest first
        latest = result[-1] if result else "n/a"
        LOG.append(f" [OK] NFP history -> {len(result)} months, latest={latest}")
        return result
    except Exception as e:
        LOG.append(f" [ERR] NFP history: {e}")
        return []


def load_existing_nfp(data_file="data.json"):
    """Load existing NFP entries from data.json so we preserve estimate/spx/note."""
    try:
        with open(data_file, encoding="utf-8") as f:
            d = json.load(f)
        return d.get("nfp", [])
    except Exception:
        return []


def _date_to_mo(date_str):
    """'2026-06-01' -> "Jun'26" """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        yr = str(dt.year)[2:]
        return dt.strftime(f"%b'{yr}")
    except Exception:
        return date_str[:7]


def _norm_k(v):
    """Legacy rows stored raw job counts (162000); normalise to thousands (162)."""
    if v is None:
        return None
    return int(round(v / 1000)) if abs(v) >= 5000 else v


def merge_nfp(existing, fresh_actuals):
    """
    Merge freshly-fetched FRED values into the existing NFP list.

    Rules:
      - `actual` is the FIRST PRINT: set when a month first appears, never overwritten.
      - `revised` tracks the latest FRED value every run.
      - estimate / spx / note / release are preserved untouched.
      - Brand-new months are added with estimate/spx/note = null.
    Returns merged list sorted oldest -> newest.
    """
    by_date = {}
    for e in existing:
        e = dict(e)
        e["actual"] = _norm_k(e.get("actual"))
        if "revised" in e:
            e["revised"] = _norm_k(e.get("revised"))
        by_date[e["date"]] = e
    for fa in fresh_actuals:
        d = fa["date"]
        if d in by_date:
            by_date[d]["revised"] = fa["actual"]
            if by_date[d].get("actual") is None:
                by_date[d]["actual"] = fa["actual"]
        else:
            by_date[d] = {
                "date":     d,
                "mo":       _date_to_mo(d),
                "actual":   fa["actual"],
                "revised":  fa["actual"],
                "estimate": None,
                "spx":      None,
                "note":     None,
            }
    return sorted(by_date.values(), key=lambda x: x["date"])


def fred_payems_release_dates():
    """BLS release dates = PAYEMS vintage dates (newest last)."""
    if not FRED_KEY:
        return []
    try:
        r = requests.get(
            "https://api.stlouisfed.org/fred/series/vintagedates",
            params={"series_id": "PAYEMS", "api_key": FRED_KEY, "file_type": "json",
                    "sort_order": "desc", "limit": 60},
            timeout=10,
        ).json()
        return sorted(r.get("vintage_dates", []))
    except Exception as e:
        LOG.append(f" [ERR] PAYEMS vintage dates: {e}")
        return []


def fill_nfp_release_and_spx(rows):
    """
    For rows missing `release` / `spx`: release = first PAYEMS vintage after the
    reference month ends; spx = S&P 500 close-to-close % change on that date.
    Leaves spx null when the cash market was closed on release day.
    """
    todo = [r for r in rows if r.get("spx") is None and not r.get("spx_closed")]
    if not todo:
        return rows
    vint = fred_payems_release_dates()
    try:
        df = yf.Ticker("^GSPC").history(period="2y").dropna(subset=["Close"])
        closes = {i.strftime("%Y-%m-%d"): float(c) for i, c in zip(df.index, df["Close"])}
        days = sorted(closes)
    except Exception as e:
        LOG.append(f" [ERR] ^GSPC history for NFP day-of: {e}")
        closes, days = {}, []
    for r in todo:
        if not r.get("release") and vint:
            ref = datetime.strptime(r["date"], "%Y-%m-%d")
            month_end = (ref.replace(day=28) + timedelta(days=4)).replace(day=1)
            limit = (month_end + timedelta(days=70)).strftime("%Y-%m-%d")
            nxt = [v for v in vint if month_end.strftime("%Y-%m-%d") <= v <= limit]
            if nxt:
                r["release"] = nxt[0]
        rel = r.get("release")
        if rel and days and rel <= days[-1]:
            if rel in closes:
                i = days.index(rel)
                if i > 0:
                    r["spx"] = round((closes[rel] / closes[days[i - 1]] - 1) * 100, 1)
                    LOG.append(f" [OK] NFP {r['mo']} SPX day-of ({rel}) -> {r['spx']}%")
            else:
                r["spx_closed"] = True   # e.g. Good Friday — cash market shut
                LOG.append(f" [OK] NFP {r['mo']} released {rel}: US cash market closed")
    return rows

# ── main fetch ───────────────────────────────────────────────────────────────

print("Fetching macro data...")
print("-" * 50)

print("US Rates (FRED):")
us_pol_obs = fred_obs("DFEDTARU", 400)            # Fed funds target, upper bound
us_pol    = hist_points(us_pol_obs)
us_policy = us_pol.get("now") if us_pol else fred("FEDFUNDS")[0]
us_2y_h  = hist_points(fred_obs("DGS2", 400))
us_10y_h = hist_points(fred_obs("DGS10", 400))
us_2y  = us_2y_h.get("now")
us_10y = us_10y_h.get("now")
cpi_obs  = fred_obs("CPIAUCSL", 26)
cpi_yoy  = yoy_series(cpi_obs)
us_cpi   = idx(cpi_yoy, 0)
us_cpi_asof = month_label(cpi_obs[0][0]) if cpi_obs else None
gdp_obs  = fred_obs("A191RL1Q225SBEA", 6)
us_gdp   = gdp_obs[0][1] if gdp_obs else None
us_gdp_asof = quarter_label(gdp_obs[0][0]) if gdp_obs else None
us_retail_sales = fred("RSAFS", 2, units="pch")[0]
us_core_pce = fred("PCEPILFE", 2, units="pc1")[0]

print("FX (Yahoo Finance):")
usdjpy = yf_last("USDJPY=X")
usdkrw = yf_last("USDKRW=X")
usdcny = yf_last("USDCNY=X")
eurusd = yf_last("EURUSD=X")
gbpusd = yf_last("GBPUSD=X")
dxy    = yf_last("DX-Y.NYB")

print("Equities (Yahoo Finance):")
spx       = yf_last("^GSPC")
spx_h     = yf_hist_points("^GSPC")
nikkei    = yf_last("^N225")
kospi     = yf_last("^KS11")
csi300    = yf_last("000300.SS")
eurostoxx = yf_last("^STOXX50E")
ftse      = yf_last("^FTSE")

print("Bond yields (Yahoo Finance):")
us10y_yf = yf_last("^TNX")
jp10y_yf = yf_last("^JGBL")
uk10y_yf = yf_last("^TMBMKGB-10Y")

print("Commodities / vol (Yahoo Finance):")
brent = yf_last("BZ=F")
wti   = yf_last("CL=F")
gold  = yf_last("GC=F")
vix   = yf_last("^VIX")

# BOK ECOS -- 817Y002: KTB daily yields
# 010195000=2Y 010210000=10Y
print("South Korea (BOK ECOS API):")

kr_policy_obs = ecos("722Y001", "0101000", cycle="M", n=14)
kr_policy     = idx(kr_policy_obs, 0)
kr_policy_m1  = idx(kr_policy_obs, 1)
kr_policy_y1  = idx(kr_policy_obs, 12)

kr_2y_obs   = ecos("817Y002", "010195000", cycle="D", n=1000)
kr_2y       = idx(kr_2y_obs, 0)
kr_2y_d1    = idx(kr_2y_obs, 1)
kr_2y_w1    = idx(kr_2y_obs, 5)
kr_2y_obs_m = ecos("721Y001", "5090000", cycle="M", n=24)
kr_2y_m1    = idx(kr_2y_obs_m, 1)
kr_2y_y1    = idx(kr_2y_obs_m, 12)

kr_10y_obs   = ecos("817Y002", "010210000", cycle="D", n=1000)
kr_10y       = idx(kr_10y_obs, 0)
kr_10y_d1    = idx(kr_10y_obs, 1)
kr_10y_w1    = idx(kr_10y_obs, 5)
kr_10y_obs_m = ecos("721Y001", "5050000", cycle="M", n=24)
kr_10y_m1    = idx(kr_10y_obs_m, 1)
kr_10y_y1    = idx(kr_10y_obs_m, 12)

kr_slope    = slope_bps(kr_10y,    kr_2y)
kr_slope_d1 = slope_bps(kr_10y_d1, kr_2y_d1)
kr_slope_w1 = slope_bps(kr_10y_w1, kr_2y_w1)
kr_slope_m1 = slope_bps(kr_10y_m1, kr_2y_m1)
kr_slope_y1 = slope_bps(kr_10y_y1, kr_2y_y1)

# 901Y009 returns the CPI INDEX LEVEL (2020=100) -> convert to y/y %
kr_cpi_obs = ecos("901Y009", "0", cycle="M", n=26)
def _kr_yoy(i):
    a, b = idx(kr_cpi_obs, i), idx(kr_cpi_obs, i + 12)
    return round((a / b - 1) * 100, 1) if a and b else None
kr_cpi     = _kr_yoy(0)
kr_cpi_m1  = _kr_yoy(1)
kr_cpi_y1  = _kr_yoy(12)

kr_gdp_obs = ecos("111Y006", "C0", cycle="Q", n=6)
kr_gdp     = idx(kr_gdp_obs, 0)
kr_gdp_q1  = idx(kr_gdp_obs, 1)
kr_gdp_y1  = idx(kr_gdp_obs, 4)

# ── NFP history (FRED PAYEMS) ────────────────────────────────────────────────
print("NFP history (FRED PAYEMS):")
fresh_actuals = fred_nfp_history(n_months=48)
existing_nfp  = load_existing_nfp("data.json")
merged_nfp    = merge_nfp(existing_nfp, fresh_actuals)
merged_nfp    = merged_nfp[-48:]  # keep last 48 months to avoid bloat
merged_nfp    = fill_nfp_release_and_spx(merged_nfp)

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
        "cpiAsOf":    us_cpi_asof,
        "gdpAsOf":    us_gdp_asof,
        "policyRate_d1": us_pol.get("d1"), "policyRate_w1": us_pol.get("w1"),
        "policyRate_m1": us_pol.get("m1"), "policyRate_y1": us_pol.get("y1"),
        "y2_d1":  us_2y_h.get("d1"),  "y2_w1":  us_2y_h.get("w1"),
        "y2_m1":  us_2y_h.get("m1"),  "y2_y1":  us_2y_h.get("y1"),
        "y10_d1": us_10y_h.get("d1"), "y10_w1": us_10y_h.get("w1"),
        "y10_m1": us_10y_h.get("m1"), "y10_y1": us_10y_h.get("y1"),
        "cpiYoY_m1": idx(cpi_yoy, 1), "cpiYoY_y1": idx(cpi_yoy, 12),
        "gdpYoY_q1": gdp_obs[1][1] if len(gdp_obs) > 1 else None,
        "gdpYoY_y1": gdp_obs[4][1] if len(gdp_obs) > 4 else None,
        "spx_d1": spx_h.get("d1"), "spx_w1": spx_h.get("w1"),
        "spx_m1": spx_h.get("m1"), "spx_y1": spx_h.get("y1"),
        "retailSalesMoM": round(us_retail_sales, 1) if us_retail_sales is not None else None,
        "corePCEYoY":     round(us_core_pce, 1) if us_core_pce is not None else None,
    },
    "kr": {
        "policyRate":    kr_policy,
        "policyRate_m1": kr_policy_m1,
        "policyRate_y1": kr_policy_y1,
        "y2":     kr_2y,    "y2_d1":  kr_2y_d1,  "y2_w1":  kr_2y_w1,
        "y2_m1":  kr_2y_m1, "y2_y1":  kr_2y_y1,
        "y10":    kr_10y,   "y10_d1": kr_10y_d1, "y10_w1": kr_10y_w1,
        "y10_m1": kr_10y_m1,"y10_y1": kr_10y_y1,
        "slope":    kr_slope,    "slope_d1": kr_slope_d1,
        "slope_w1": kr_slope_w1, "slope_m1": kr_slope_m1, "slope_y1": kr_slope_y1,
        "cpiYoY":   kr_cpi,  "cpiYoY_m1": kr_cpi_m1, "cpiYoY_y1": kr_cpi_y1,
        "gdpYoY":   kr_gdp,  "gdpYoY_q1": kr_gdp_q1, "gdpYoY_y1": kr_gdp_y1,
    },
    # NFP history — [{date, mo, actual, revised, estimate, spx, release, note}] oldest first,
    # all job figures in THOUSANDS.
    # actual   : first print (auto from FRED PAYEMS the first time a month appears).
    # revised  : latest FRED value (auto, every run).
    # estimate : Dow Jones consensus — patch manually after each release.
    # spx      : S&P 500 % on release day — auto-filled from Yahoo.
    # note     : optional annotation, preserved from prior data.json.
    "nfp": merged_nfp,
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
print(f"NFP: {len(merged_nfp)} months stored | latest={merged_nfp[-1] if merged_nfp else 'n/a'}")
for msg in LOG:
    print(msg)
