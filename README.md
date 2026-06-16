
# Macro War Room 🔴

Global macro hedge fund dashboard — React + FRED + Yahoo Finance.

## 🚀 Getting Started (Local Setup)

이 프로젝트를 로컬 컴퓨터에 다운로드하고 실행하는 방법입니다.

### 1. 프로젝트 다운로드 및 실행
작업할 폴더를 하나 만들고, 해당 경로에서 터미널(또는 파워쉘)을 열어 아래 명령어를 순서대로 실행하세요.

```bash
# 1. 깃허브에서 프로젝트 클론 (코드를 다운로드할 폴더에서 실행)
git clone [https://github.com/DANKIM82/macro-war-room-v2.git](https://github.com/DANKIM82/macro-war-room-v2.git)

# 2. 생성된 프로젝트 폴더로 이동
cd macro-war-room-v2

# 3. 필요 패키지 설치 (최초 1회만 실행)
npm install

# 4. 로컬 개발 서버 실행
npm run dev

```

> 서버가 실행되면 브라우저에서 `http://localhost:5173/` 로 접속하여 대시보드를 확인할 수 있습니다.

---

## 📈 Data Management

이 프로젝트는 Python 스크립트를 통해 최신 매크로 데이터를 가져옵니다.

### 2. Live Data Update (Optional but recommended)

로컬에서 최신 데이터를 수동으로 업데이트하고 싶을 때 사용합니다. Python 환경이 필요합니다.

```bash
# 필요한 파이썬 라이브러리 설치
pip install requests yfinance

# FRED API 키 설정 (무료 발급: [https://fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html))
# Mac/Linux:
export FRED_API_KEY="your_key_here"
# Windows PowerShell:
$env:FRED_API_KEY="your_key_here"

# 데이터 수집 스크립트 실행
python scripts/update_data.py

```

### 3. Automate Data Updates

데이터는 GitHub Actions를 통해 매일(월~금) 한국 시간(KST) 오전 9시에 자동으로 업데이트됩니다.

* GitHub 저장소 **Settings → Secrets and variables → Actions** 에 `FRED_API_KEY`를 등록해야 합니다.

---

## ☁️ Deployment

Vercel을 통해 쉽게 배포할 수 있습니다.

```bash
npm install -g vercel
vercel

```

---

## 📊 Data Sources

| Data | Source | Cost |
| --- | --- | --- |
| US yields, CPI, GDP, Fed Funds | FRED API | Free |
| FX rates (USDJPY, USDKRW, etc.) | Yahoo Finance | Free |
| Equity indices (S&P, Nikkei, KOSPI) | Yahoo Finance | Free |
| International yields | Yahoo Finance | Free |
| AI analysis | Anthropic API | Usage-based |

---

## 🤖 Code Updates (with Claude)

Claude Code를 사용하여 AI의 지원을 받아 프로젝트를 빠르게 수정할 수 있습니다.

```bash
# Claude Code 설치
npm install -g @anthropic-ai/claude-code

# 사용 예시 (터미널에 입력)
claude "KOSPI was revised to 8,600 today, update the dashboard"
claude "Add Taiwan to the rates matrix"
claude "The NFP chart isn't showing the Jun 2026 data point"

```

---

## 🏗️ Architecture

```text
macro-war-room-v2/
├── src/App.jsx            ← React dashboard (프론트엔드 UI 수정은 여기서 진행)
├── public/data.json       ← Python 스크립트 및 GitHub Actions에 의해 자동 업데이트되는 데이터
├── scripts/update_data.py ← Data fetcher (FRED + Yahoo Finance에서 데이터를 가져오는 로직)
└── .github/workflows/     ← 매일 오전 9시(KST) 자동 데이터 업데이트를 위한 설정

```
