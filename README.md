# Macro War Room 🔴

Global macro hedge fund dashboard — React + FRED + Yahoo Finance.

## Setup

### 1. Install
```bash
npm create vite@latest macro-war-room -- --template react
cd macro-war-room
npm install recharts
cp src_App.jsx src/App.jsx
npm run dev
```

### 2. Live data (optional but recommended)
```bash
pip install requests yfinance
# Get free FRED key: https://fred.stlouisfed.org/docs/api/api_key.html
export FRED_API_KEY=your_key_here
python scripts/update_data.py
```

### 3. Deploy to Vercel
```bash
npm install -g vercel
vercel
```

### 4. Automate data updates
- Push to GitHub
- Add `FRED_API_KEY` in repo Settings → Secrets
- GitHub Actions runs every weekday morning automatically

## Data Sources
| Data | Source | Cost |
|------|---------|------|
| US yields, CPI, GDP, Fed Funds | FRED API | Free |
| FX rates (USDJPY, USDKRW, etc.) | Yahoo Finance | Free |
| Equity indices (S&P, Nikkei, KOSPI) | Yahoo Finance | Free |
| International yields | Yahoo Finance | Free |
| AI analysis | Anthropic API | Usage-based |

## Code Updates
Use Claude Code for AI-assisted iteration:
```bash
# Install
npm install -g @anthropic-ai/claude-code

# Update data
claude "KOSPI was revised to 8,600 today, update the dashboard"

# Add features
claude "Add Taiwan to the rates matrix"

# Fix issues
claude "The NFP chart isn't showing the Jun 2026 data point"
```

## Architecture
```
GitHub repo
├── src/App.jsx          ← React dashboard (edit here)
├── public/data.json     ← Auto-updated by GitHub Actions
├── scripts/update_data.py ← Data fetcher (FRED + Yahoo Finance)
└── .github/workflows/   ← Runs Mon-Fri 09:00 KST
```
