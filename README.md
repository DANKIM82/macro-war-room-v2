# Macro War Room 🔴

Global macro hedge fund dashboard — 빌드가 필요 없는 단일 HTML 페이지. 매일 GitHub Actions가 데이터를 갱신하고, GitHub Pages가 무료로 서빙합니다.

**🔗 Live: https://dankim82.github.io/macro-war-room-v2/**  · 매일 자동 갱신, 클릭만 하면 최신.

---

## ⚙️ 동작 방식 (How it works)

- 대시보드는 빌드가 필요 없는 단일 [`index.html`](index.html)입니다. React · Recharts · Babel을 CDN에서 불러오고, `./data.json` + `./analysis.json`을 **런타임에 fetch**해서 화면을 그립니다.
- GitHub Pages가 `main` 브랜치 루트의 `index.html`을 **그대로** 서빙합니다 (빌드 단계 없음).
- 매일(월~금) GitHub Actions가 데이터를 갱신해 루트의 `data.json` · `analysis.json`을 커밋 → Pages가 자동 반영. **그래서 보는 사람은 URL 새로고침만 하면 됩니다. `git pull` 불필요.**

---

## 🚀 로컬에서 보기 (Local preview)

Node/npm 빌드 도구 필요 없음. 정적 서버만 있으면 됩니다 (Python 내장 서버 사용).

```bash
git clone https://github.com/DANKIM82/macro-war-room-v2.git
cd macro-war-room-v2

# 정적 서버로 열기
python -m http.server 8000      # Windows: py -m http.server 8000
# → 브라우저에서 http://localhost:8000/ 접속
```

> ⚠️ `index.html`을 파일로 직접 더블클릭(`file://`)하면 브라우저 보안 정책 때문에 `data.json` fetch가 막힙니다. 반드시 위처럼 정적 서버로 여세요.

---

## 🎨 대시보드 UI 수정 (Editing the dashboard)

`index.html`은 **생성된 파일**입니다. 직접 고치지 말고, 소스를 수정한 뒤 다시 생성하세요.

```bash
# 1. 소스 수정
#    src/App.jsx    ← 컴포넌트 · 차트 · 정적 데이터 (UI 로직은 여기서)
#    src/index.css  ← 전역 스타일

# 2. index.html 재생성
python scripts/build_html.py    # Windows: py scripts/build_html.py

# 3. 커밋/푸시 → Pages가 자동 배포
git add index.html src/ && git commit -m "ui: ..." && git push
```

> 데이터(`*.json`)는 런타임에 fetch하므로, **데이터만 바뀔 때는 재생성이 필요 없습니다.** `build_html.py`는 UI를 바꿀 때만 돌리면 됩니다.

---

## 📈 데이터 자동화 (Data automation)

매일(월~금) 한국시간 오전 9시(00:00 UTC), GitHub Actions([`.github/workflows/update-data.yml`](.github/workflows/update-data.yml))가 실행됩니다:

1. `scripts/update_data.py` — FRED + Yahoo Finance에서 시장 숫자를 받아 루트 `data.json` 생성
2. `scripts/update_analysis.py` — Google News 헤드라인 + Claude(`claude-opus-4-8`) 분석으로 루트 `analysis.json` 생성 (레짐 배지 · 테마 · 시그널 코멘트)

그리고 두 파일을 저장소 루트에 커밋합니다.

저장소 **Settings → Secrets and variables → Actions** 에 시크릿 2개 등록:

- `FRED_API_KEY` — 미국 금리/CPI/GDP 라이브 데이터용 (무료 발급: https://fred.stlouisfed.org/docs/api/api_key.html)
- `ANTHROPIC_API_KEY` — 매일 뉴스 → AI 분석용

`ANTHROPIC_API_KEY`가 없으면 분석 단계는 건너뛰고(데이터 업데이트는 정상 동작), 앱은 내장 기본 내러티브로 표시됩니다. **Actions** 탭 → *Update macro data (daily)* → **Run workflow** 로 즉시 수동 실행도 가능합니다.

### 로컬에서 수동 데이터 갱신 (선택)

```bash
pip install requests yfinance anthropic

export FRED_API_KEY="your_key_here"        # Windows PowerShell: $env:FRED_API_KEY="your_key_here"
python scripts/update_data.py               # → data.json
python scripts/update_analysis.py           # → analysis.json (ANTHROPIC_API_KEY 필요)
```

**현재 자동 갱신되는 항목:** 미국 정책금리 · 2Y · 10Y · 2s10s · CPI · GDP, 전 지수(S&P · Nikkei · KOSPI · CSI300 · Euro Stoxx · FTSE), USD/KRW, Brent · Gold · VIX, 그리고 레짐 배지 · 테마 · 시그널 코멘트(AI). 그 외(레짐 레이더 점수, 트레이드 북, NFP 시계열, 타 국가 금리)는 아직 `src/App.jsx`에서 수동 관리합니다 — 더 많은 항목을 라이브로 연결하려면 `scripts/update_data.py`를 확장하세요.

### 일별 PDF 추적

헤더의 **⬇ PDF** 버튼 → 브라우저 인쇄 대화상자 → **PDF로 저장**. 파일명이 `MacroWarRoom_YYYY-MM-DD.pdf` 로 자동 지정되어 매일 한 장씩 스냅샷을 보관할 수 있습니다.

---

## ☁️ 배포 (GitHub Pages)

별도 배포 명령이 필요 없습니다. 아래 설정을 **한 번만** 하면, `main`에 push될 때마다 자동으로 서빙됩니다:

**Settings → Pages → Build and deployment → Source = `Deploy from a branch` → Branch `main` / `(root)`**

이후 매일의 자동 데이터 커밋과 직접 push 모두 그대로 라이브에 반영됩니다.

---

## 📊 Data Sources

| Data | Source | Cost |
| --- | --- | --- |
| US yields, CPI, GDP, Fed Funds | FRED API | Free |
| FX rates (USDJPY, USDKRW, etc.) | Yahoo Finance | Free |
| Equity indices (S&P, Nikkei, KOSPI, ...) | Yahoo Finance | Free |
| Commodities / vol (Brent, Gold, VIX) | Yahoo Finance | Free |
| Regime / themes / signal notes (AI) | Anthropic API | Usage-based |

---

## 🤖 Code Updates (with Claude)

Claude Code를 사용하여 AI의 지원을 받아 프로젝트를 빠르게 수정할 수 있습니다. (UI를 바꾸면 `index.html` 재생성까지 함께 처리하도록 요청하세요.)

```bash
# Claude Code 설치
npm install -g @anthropic-ai/claude-code

# 사용 예시
claude "KOSPI was revised to 8,600 today, update the dashboard and rebuild index.html"
claude "Add Taiwan to the rates matrix in src/App.jsx, then run build_html.py"
claude "The NFP chart isn't showing the Jun 2026 data point"
```

---

## 🏗️ Architecture

```text
macro-war-room-v2/
├── index.html                  ← 배포되는 단일 페이지 (생성물 — 직접 수정하지 말 것)
├── data.json                   ← 매일 자동 갱신되는 시장 데이터 (런타임 fetch)
├── analysis.json               ← 매일 자동 갱신되는 AI 분석 (레짐/테마/시그널)
├── favicon.svg
├── .nojekyll                   ← GitHub Pages Jekyll 비활성화
├── src/
│   ├── App.jsx                 ← 대시보드 소스 (UI 수정은 여기서)
│   └── index.css               ← 전역 스타일
├── scripts/
│   ├── build_html.py           ← src/App.jsx + index.css → index.html 생성기
│   ├── update_data.py          ← FRED + Yahoo Finance 데이터 수집
│   └── update_analysis.py      ← Google News + Claude 분석
└── .github/workflows/
    └── update-data.yml         ← 매일 오전 9시(KST) 자동 데이터 갱신 + 커밋
```

> 참고: 이 프로젝트는 원래 Vite/React 앱이었고, 빌드 없이 클릭만으로 보고 자동 갱신되도록 단일 HTML로 전환했습니다. `package.json` / `vite.config.js` 등 Vite 잔재는 더 이상 배포에 쓰이지 않습니다.
