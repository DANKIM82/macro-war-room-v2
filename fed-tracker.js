/* ════════════════════════════════════════════════════════════════════
   FED SPEAK TRACKER — standalone vanilla JS (no build, no libraries)
   Loaded by index.html via <script src="./fed-tracker.js" defer>.
   Mounts itself directly below the "Upcoming Catalysts" section.
   To refresh: edit FED_SNAPSHOT / FED_OFFICIALS below only.
   ════════════════════════════════════════════════════════════════════ */

// 데이터 기준일: 2026-09-08
// stance 척도: +2 강경매파 / +1 매파기울기 / 0 중립·데이터의존 / -1 비둘기기울기 / -2 강경비둘기

const FED_SNAPSHOT = {
  asOf: "2026-09-08",
  targetRange: "3.50–3.75%",
  nextFOMC: "2026-09-15~16",
  lastVote: "9–3 동결 (7/29)",
  marketOdds: "9월 25bp 인상 ~50% (CME FedWatch, 9/3 기준)"
};

const FED_OFFICIALS = [
  {
    name: "케빈 워시",
    nameEn: "Kevin Warsh",
    role: "의장 (2026.5.22 취임, 이사 임기 2040.1)",
    group: "board",
    isVoter2026: true,
    stance: 1,
    lastDate: "2026-08-28",
    remark: "잭슨홀 첫 기조연설. 기저 인플레가 목표를 향해 명확하고 충분한 속도로 움직인다는 확신이 없으면 '할 일이 남아 있다'고 표현. PCE 2%는 고정 목표이며 변경 의사 없음을 명확히 함. 금융여건이 경제를 제약하지 않고 있다고 평가하고 금리를 주된 정책수단으로 규정. 포워드가이던스 축소 기조, 연간 FOMC 8회를 6회로 줄이는 안도 위원회에 제기.",
    sourceUrl: "https://www.federalreserve.gov/newsevents/speech/warsh20260828a.htm"
  },
  {
    name: "필립 제퍼슨",
    nameEn: "Philip Jefferson",
    role: "부의장",
    group: "board",
    isVoter2026: true,
    stance: 0,
    lastDate: "2026-07-29",
    remark: "7월 FOMC 동결 찬성. 이후 개별 발언은 확인되지 않음 — 최신 연설 확인 필요.",
    sourceUrl: "https://www.federalreserve.gov/monetarypolicy/fomcminutes20260729.htm"
  },
  {
    name: "미셸 보우먼",
    nameEn: "Michelle Bowman",
    role: "감독담당 부의장",
    group: "board",
    isVoter2026: true,
    stance: -1,
    lastDate: "2026-07-29",
    remark: "7월 FOMC 동결 찬성. 1월 연설에서는 인플레가 목표에 근접하는 반면 노동시장이 취약해지고 있으며 그 취약성이 더 큰 리스크라고 평가. 최근 스탠스 재확인 필요.",
    sourceUrl: "https://www.federalreserve.gov/newsevents/speech/bowman20260116a.htm"
  },
  {
    name: "크리스토퍼 월러",
    nameEn: "Christopher Waller",
    role: "이사",
    group: "board",
    isVoter2026: true,
    stance: 0,
    lastDate: "2026-09-03",
    remark: "9/11 발표될 8월 CPI가 판단을 좌우한다고 명시. 인플레 둔화가 이어지면 동결 쪽으로 기울겠지만 뜨겁게 나오면 인상을 고려하겠다는 입장. 현재 차입비용이 수요를 '약간만' 제약하고 있어 인플레가 조금만 가속돼도 인상 지지로 돌아설 수 있다고 언급. 이 발언 직후 9월 인상 확률이 65%에서 50% 수준으로 하락.",
    sourceUrl: "https://www.pbs.org/newshour/economy/fed-governor-waller-muddies-outlook-on-possible-rate-hike-later-this-month"
  },
  {
    name: "마이클 바",
    nameEn: "Michael Barr",
    role: "이사",
    group: "board",
    isVoter2026: true,
    stance: 1,
    lastDate: "2026-09-01",
    remark: "워싱턴 은행 포럼 사전 원고에서 광범위한 가격압력이 고착되는 것을 우려한다고 밝힘. 인플레가 2%로 향한다는 확신이 생기면 정책기조 평가에 시간을 더 쓸 수 있으나, 충분히 완화되지 않는다면 단호하게 금리를 올려야 한다는 입장.",
    sourceUrl: "https://www.cnbc.com/2026/09/01/fed-governor-barr-says-hell-support-rate-hike-if-inflation-doesnt-ease.html"
  },
  {
    name: "리사 쿡",
    nameEn: "Lisa Cook",
    role: "이사",
    group: "board",
    isVoter2026: true,
    stance: -1,
    lastDate: "2026-07-29",
    remark: "7월 FOMC 동결 찬성으로 표결 참여. 이후 개별 발언은 확인되지 않음 — 최신 연설 확인 필요.",
    sourceUrl: "https://www.federalreserve.gov/monetarypolicy/fomcminutes20260729.htm"
  },
  {
    name: "제롬 파월",
    nameEn: "Jerome Powell",
    role: "이사 (전 의장, 이사 임기 2028.1)",
    group: "board",
    isVoter2026: true,
    stance: 0,
    lastDate: "2026-07-29",
    remark: "의장직 이임 후 이사로 잔류하며 FOMC 표결권 유지. 7월 동결 찬성. 이후 개별 발언은 확인되지 않음.",
    sourceUrl: "https://www.federalreserve.gov/monetarypolicy/fomcminutes20260729.htm"
  },
  {
    name: "존 윌리엄스",
    nameEn: "John Williams",
    role: "뉴욕 연은 총재 · FOMC 부의장 (상시 투표)",
    group: "bank",
    isVoter2026: true,
    stance: 0,
    lastDate: "2026-09-02",
    remark: "CNBC 인터뷰에서 최근 인플레 지표가 고무적이지만 하락 추세를 확인할 증거가 더 필요하다는 입장. 현 정책이 1~2년 내 목표 복귀를 담보할 만큼 충분한지 명확한 신호가 없다며 기다려 보자는 쪽. 사실상 9월 동결 지지로 해석됨.",
    sourceUrl: "https://www.pbs.org/newshour/economy/fed-governor-waller-muddies-outlook-on-possible-rate-hike-later-this-month"
  },
  {
    name: "베스 해맥",
    nameEn: "Beth Hammack",
    role: "클리블랜드 연은 총재",
    group: "bank",
    isVoter2026: true,
    stance: 2,
    lastDate: "2026-07-29",
    remark: "7월 FOMC에서 25bp 인상을 주장하며 반대표. 5년 넘게 목표를 상회한 인플레를 근거로 지금 긴축하지 않으면 기대가 고착될 수 있다는 논리. 회의 전부터 공개적으로 긴축을 주장해 온 인물.",
    sourceUrl: "https://www.cnbc.com/2026/07/29/fed-rate-decision-july-2026.html"
  },
  {
    name: "닐 카시카리",
    nameEn: "Neel Kashkari",
    role: "미니애폴리스 연은 총재",
    group: "bank",
    isVoter2026: true,
    stance: 2,
    lastDate: "2026-07-29",
    remark: "7월 FOMC에서 25bp 인상을 주장하며 반대표. 회의 수 주 전부터 공개적으로 추가 긴축 필요성을 언급.",
    sourceUrl: "https://www.cnbc.com/2026/07/29/fed-rate-decision-july-2026.html"
  },
  {
    name: "로리 로건",
    nameEn: "Lorie Logan",
    role: "댈러스 연은 총재",
    group: "bank",
    isVoter2026: true,
    stance: 2,
    lastDate: "2026-07-29",
    remark: "7월 FOMC에서 25bp 인상을 주장하며 반대표. 세 명의 반대표는 2016년 9월 이후 처음 나온 동일 방향 3인 반대로 기록됨.",
    sourceUrl: "https://www.cnbc.com/2026/07/29/fed-rate-decision-july-2026.html"
  },
  {
    name: "애나 폴슨",
    nameEn: "Anna Paulson",
    role: "필라델피아 연은 총재",
    group: "bank",
    isVoter2026: true,
    stance: -1,
    lastDate: "2026-07-29",
    remark: "7월 FOMC 동결 찬성. 연초에는 인플레 둔화와 노동시장 안정을 전제로 연내 소폭 추가 인하 여지를 언급했고 현 금리를 여전히 다소 긴축적이라고 평가. 인플레보다 고용 쪽 리스크에 무게를 두는 위원회 내 비둘기 축. 최근 발언 재확인 필요.",
    sourceUrl: "https://www.bloomberg.com/news/articles/2026-01-14/fed-s-paulson-repeats-she-sees-modest-rate-cuts-later-in-2026"
  },
  {
    name: "토머스 바킨",
    nameEn: "Thomas Barkin",
    role: "리치먼드 연은 총재 (2027 투표)",
    group: "bank",
    isVoter2026: false,
    stance: 0,
    lastDate: "2026-07-29",
    remark: "7월 FOMC 교체위원으로 참석. 최근 개별 발언 확인 필요.",
    sourceUrl: "https://www.federalreserve.gov/monetarypolicy/fomcminutes20260729.htm"
  },
  {
    name: "메리 데일리",
    nameEn: "Mary Daly",
    role: "샌프란시스코 연은 총재 (2027 투표)",
    group: "bank",
    isVoter2026: false,
    stance: 0,
    lastDate: "2026-07-29",
    remark: "7월 FOMC 교체위원으로 참석. 최근 개별 발언 확인 필요.",
    sourceUrl: "https://www.federalreserve.gov/monetarypolicy/fomcminutes20260729.htm"
  },
  {
    name: "오스탄 굴스비",
    nameEn: "Austan Goolsbee",
    role: "시카고 연은 총재 (2027 투표)",
    group: "bank",
    isVoter2026: false,
    stance: 1,
    lastDate: "2026-07-29",
    remark: "2025년 12월 인하에 반대표를 던진 이력. 당시 최근 6개월간 특히 서비스 부문에서 인플레 진전이 없었다고 지적하며 적어도 1분기까지는 기다렸어야 한다는 입장. 7월 FOMC 교체위원. 최근 발언 확인 필요.",
    sourceUrl: "https://www.federalreserve.gov/monetarypolicy/fomcminutes20260729.htm"
  },
  {
    name: "수전 콜린스",
    nameEn: "Susan Collins",
    role: "보스턴 연은 총재",
    group: "bank",
    isVoter2026: false,
    stance: 0,
    lastDate: "2026-07-29",
    remark: "7월 FOMC 참석(비투표). 최근 개별 발언 확인 필요.",
    sourceUrl: "https://www.federalreserve.gov/monetarypolicy/fomcminutes20260729.htm"
  },
  {
    name: "알베르토 무살렘",
    nameEn: "Alberto Musalem",
    role: "세인트루이스 연은 총재",
    group: "bank",
    isVoter2026: false,
    stance: 1,
    lastDate: "2026-07-29",
    remark: "인플레 상방 리스크와 기대 이탈 가능성을 반복 강조해 온 인물. 7월 FOMC 참석(비투표). 최근 발언 확인 필요.",
    sourceUrl: "https://www.federalreserve.gov/monetarypolicy/fomcminutes20260729.htm"
  },
  {
    name: "제프리 슈미드",
    nameEn: "Jeffrey Schmid",
    role: "캔자스시티 연은 총재",
    group: "bank",
    isVoter2026: false,
    stance: 1,
    lastDate: "2026-07-29",
    remark: "2025년 12월 인하에 반대표. 당시 현 정책이 겨우 긴축적인 수준이라고 평가. 7월 FOMC 참석(비투표). 최근 발언 확인 필요.",
    sourceUrl: "https://www.federalreserve.gov/monetarypolicy/fomcminutes20260729.htm"
  },
  {
    name: "애틀랜타 연은 (총재 공석)",
    nameEn: "Atlanta Fed",
    role: "총재직 공석 — 보스틱 2026.2.28 임기 종료",
    group: "bank",
    isVoter2026: false,
    stance: 0,
    lastDate: "2026-07-29",
    remark: "7월 FOMC 의사록에는 셰릴 베너블 수석부총재가 교체위원으로 기재됨. 후임 총재 선임 여부 확인 필요.",
    sourceUrl: "https://www.federalreserve.gov/monetarypolicy/fomcminutes20260729.htm"
  }
];

/* ════════════════════════════════════════════════════════════════════
   RENDERING — no need to touch below when updating remarks
   ════════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";

  var ANCHOR_TITLE = "Upcoming Catalysts";   // new section goes right under this section
  var SECTION_ID = "fed-tracker";

  var STANCES = [
    { v: 2,  label: "강경매파",       short: "+2" },
    { v: 1,  label: "매파기울기",     short: "+1" },
    { v: 0,  label: "중립·데이터의존", short: "0" },
    { v: -1, label: "비둘기기울기",   short: "−1" },
    { v: -2, label: "강경비둘기",     short: "−2" }
  ];
  var GROUP_FILTERS = [
    { k: "all",   label: "전체" },
    { k: "voter", label: "2026 투표권" },
    { k: "board", label: "이사회" },
    { k: "bank",  label: "지역연은" }
  ];
  var STANCE_FILTERS = [
    { k: "all",     label: "전체" },
    { k: "hawk",    label: "매파" },
    { k: "neutral", label: "중립" },
    { k: "dove",    label: "비둘기" }
  ];
  var state = { group: "all", stance: "all" };

  var CSS = [
    "#fed-tracker{text-align:left;margin-bottom:24px;color:var(--t,#2A2317);font-family:'Nunito Sans',system-ui,sans-serif}",
    ".fed-sec{font-family:'Bebas Neue',sans-serif;font-size:13px;letter-spacing:.22em;color:var(--dim,#9A8E74);margin:0 0 14px 1px;display:flex;align-items:center;gap:14px}",
    ".fed-sec:after{content:'';flex:1;height:1px;background:var(--b,rgba(60,48,24,.14))}",
    ".fed-panel{background:var(--p,#F7F1E3);border:1px solid var(--b,rgba(60,48,24,.14));border-radius:16px;padding:16px}",
    ".fed-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:14px}",
    ".fed-kpi{text-align:center;background:var(--p2,#EFE7D5);border:1px solid var(--b,rgba(60,48,24,.14));border-radius:12px;padding:10px 12px;min-width:0}",
    ".fed-kpi-k{font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--mt,#6E6450);margin-bottom:5px}",
    ".fed-kpi-v{font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:700;color:var(--t,#2A2317);line-height:1.35;word-break:keep-all;overflow-wrap:anywhere}",
    ".fed-asof{font-family:'JetBrains Mono',monospace;font-size:9.5px;color:var(--mt,#6E6450);margin:-6px 0 12px;text-align:right}",
    ".fed-spec{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:6px;margin-bottom:14px}",
    ".fed-col{border-radius:10px;padding:8px 6px 10px;min-height:92px;border:1px solid var(--b,rgba(60,48,24,.14));background:var(--p2,#EFE7D5)}",
    ".fed-col-h{font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;text-align:center;margin-bottom:2px}",
    ".fed-col-s{font-size:10px;text-align:center;color:var(--mt,#6E6450);margin-bottom:8px;line-height:1.2}",
    ".fed-col-b{display:flex;flex-wrap:wrap;gap:4px;justify-content:center}",
    ".fed-chip{font-family:'JetBrains Mono',monospace;font-size:10.5px;padding:3px 6px;border-radius:6px;border:1px solid transparent;cursor:default;line-height:1.2;font-weight:500}",
    ".fed-chip.fed-voter{font-weight:800;border-color:currentColor}",
    ".fed-s2{color:#A31227;background:rgba(214,42,66,.16)}",
    ".fed-s1{color:#9A3412;background:rgba(226,86,0,.13)}",
    ".fed-s0{color:#4B4535;background:rgba(110,100,80,.14)}",
    ".fed-sm1{color:#0B6E75;background:rgba(14,140,150,.14)}",
    ".fed-sm2{color:#095C47;background:rgba(14,158,120,.18)}",
    ".fed-filters{display:flex;flex-direction:column;gap:8px;margin-bottom:12px}",
    ".fed-frow{display:flex;flex-wrap:wrap;gap:6px;align-items:center}",
    ".fed-flabel{font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.14em;color:var(--mt,#6E6450);min-width:44px;text-transform:uppercase}",
    ".fed-btn{font-family:'Nunito Sans',sans-serif;font-size:12px;font-weight:600;padding:5px 11px;border-radius:999px;border:1px solid var(--b2,rgba(60,48,24,.24));background:transparent;color:var(--t,#2A2317);cursor:pointer}",
    ".fed-btn:hover{background:var(--p3,#E5DBC5)}",
    ".fed-btn[aria-pressed='true']{background:var(--t,#2A2317);color:var(--p,#F7F1E3);border-color:var(--t,#2A2317)}",
    ".fed-count{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--mt,#6E6450);margin-left:auto}",
    ".fed-cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}",
    ".fed-card{background:var(--p2,#EFE7D5);border:1px solid var(--b,rgba(60,48,24,.14));border-radius:12px;padding:12px 14px;display:flex;flex-direction:column;gap:6px;min-width:0}",
    ".fed-card-top{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}",
    ".fed-name{font-size:15px;font-weight:700;color:var(--t,#2A2317);line-height:1.25}",
    ".fed-en{font-family:'JetBrains Mono',monospace;font-size:10.5px;color:var(--mt,#6E6450);font-weight:400;margin-left:6px}",
    ".fed-role{font-size:11.5px;color:var(--mt,#6E6450);line-height:1.35}",
    ".fed-tags{display:flex;gap:5px;flex-wrap:wrap;flex:none;justify-content:flex-end}",
    ".fed-tag{font-family:'JetBrains Mono',monospace;font-size:10px;padding:2px 7px;border-radius:6px;white-space:nowrap;font-weight:700}",
    ".fed-tag-vote{color:var(--t,#2A2317);border:1px solid var(--t,#2A2317)}",
    ".fed-tag-novote{color:var(--mt,#6E6450);border:1px dashed var(--b2,rgba(60,48,24,.24));font-weight:500}",
    ".fed-remark{font-size:12.5px;line-height:1.55;color:var(--t,#2A2317)}",
    ".fed-meta{display:flex;justify-content:space-between;gap:8px;font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--mt,#6E6450);margin-top:auto;padding-top:4px}",
    ".fed-meta a{color:var(--orange,#E25600);text-decoration:none;font-weight:700}",
    ".fed-meta a:hover{text-decoration:underline}",
    ".fed-empty{grid-column:1/-1;text-align:center;padding:18px;font-size:12px;color:var(--mt,#6E6450)}",
    ".fed-legend{font-family:'JetBrains Mono',monospace;font-size:9.5px;color:var(--mt,#6E6450);margin:-4px 0 12px}",
    ".fed-legend b{color:var(--t,#2A2317)}",
    "@media(max-width:760px){.fed-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}",
    "@media(max-width:640px){.fed-cards{grid-template-columns:1fr}.fed-card-top{flex-direction:column}.fed-tags{justify-content:flex-start}.fed-spec{gap:4px}.fed-col{padding:6px 3px 8px}.fed-chip{font-size:9.5px;padding:2px 4px}.fed-col-s{font-size:9px}}",
    "@media print{#fed-tracker{break-inside:avoid-page}.fed-filters{display:none}}"
  ].join("\n");

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function stanceCls(v) { return v >= 0 ? "fed-s" + v : "fed-sm" + (-v); }
  function stanceInfo(v) {
    for (var i = 0; i < STANCES.length; i++) if (STANCES[i].v === v) return STANCES[i];
    return STANCES[2];
  }
  function safeUrl(u) { return /^https?:\/\//i.test(u || "") ? u : "#"; }

  // Initials from nameEn; if two people share initials, add the 2nd letter of the surname.
  var INITIALS = (function () {
    var base = FED_OFFICIALS.map(function (o) {
      var w = String(o.nameEn || o.name).split(/\s+/).filter(Boolean);
      return w.map(function (x) { return x.charAt(0).toUpperCase(); }).join("").slice(0, 3);
    });
    return base.map(function (b, i) {
      var dup = base.filter(function (x) { return x === b; }).length > 1;
      if (!dup) return b;
      var w = String(FED_OFFICIALS[i].nameEn).split(/\s+/);
      var last = w[w.length - 1] || "";
      return b + (last.charAt(1) || "").toLowerCase();
    });
  })();

  function matches(o) {
    if (state.group === "voter" && !o.isVoter2026) return false;
    if (state.group === "board" && o.group !== "board") return false;
    if (state.group === "bank" && o.group !== "bank") return false;
    if (state.stance === "hawk" && !(o.stance > 0)) return false;
    if (state.stance === "neutral" && o.stance !== 0) return false;
    if (state.stance === "dove" && !(o.stance < 0)) return false;
    return true;
  }

  function renderKPIs() {
    var s = FED_SNAPSHOT;
    var cells = [
      ["FF 목표범위", s.targetRange],
      ["다음 FOMC", s.nextFOMC],
      ["직전 표결", s.lastVote],
      ["시장 확률", s.marketOdds]
    ];
    return '<div class="fed-kpis">' + cells.map(function (c) {
      return '<div class="fed-kpi"><div class="fed-kpi-k">' + esc(c[0]) + '</div><div class="fed-kpi-v">' + esc(c[1]) + "</div></div>";
    }).join("") + "</div>" +
      '<div class="fed-asof">데이터 기준일 ' + esc(s.asOf) + "</div>";
  }

  function renderSpectrum() {
    return '<div class="fed-spec" role="list">' + STANCES.map(function (st) {
      var people = FED_OFFICIALS.map(function (o, i) { return { o: o, i: i }; })
        .filter(function (x) { return x.o.stance === st.v && matches(x.o); });
      var chips = people.map(function (x) {
        var o = x.o;
        var title = o.name + " (" + o.nameEn + ") · " + o.role + (o.isVoter2026 ? " · 2026 투표권" : "");
        return '<span class="fed-chip ' + stanceCls(st.v) + (o.isVoter2026 ? " fed-voter" : "") +
          '" title="' + esc(title) + '">' + esc(INITIALS[x.i]) + "</span>";
      }).join("");
      return '<div class="fed-col" role="listitem">' +
        '<div class="fed-col-h ' + stanceCls(st.v) + '" style="background:none">' + esc(st.short) + "</div>" +
        '<div class="fed-col-s">' + esc(st.label) + "</div>" +
        '<div class="fed-col-b">' + (chips || '<span class="fed-col-s">—</span>') + "</div></div>";
    }).join("") + "</div>" +
      '<div class="fed-legend"><b>굵은 테두리</b> = 2026 FOMC 투표권자 · 배지에 마우스를 올리면 이름 표시</div>';
  }

  function renderFilters(shown) {
    function row(label, items, key) {
      return '<div class="fed-frow"><span class="fed-flabel">' + esc(label) + "</span>" +
        items.map(function (f) {
          return '<button type="button" class="fed-btn" data-fed-key="' + key + '" data-fed-val="' + f.k +
            '" aria-pressed="' + (state[key] === f.k ? "true" : "false") + '">' + esc(f.label) + "</button>";
        }).join("") + (key === "stance" ? '<span class="fed-count">' + shown + " / " + FED_OFFICIALS.length + "명</span>" : "") +
        "</div>";
    }
    return '<div class="fed-filters">' + row("구분", GROUP_FILTERS, "group") + row("스탠스", STANCE_FILTERS, "stance") + "</div>";
  }

  function renderCards(list) {
    if (!list.length) return '<div class="fed-cards"><div class="fed-empty">조건에 맞는 인물이 없습니다.</div></div>';
    return '<div class="fed-cards">' + list.map(function (o) {
      var st = stanceInfo(o.stance);
      return '<article class="fed-card">' +
        '<div class="fed-card-top"><div><div class="fed-name">' + esc(o.name) +
        '<span class="fed-en">' + esc(o.nameEn) + "</span></div>" +
        '<div class="fed-role">' + esc(o.role) + "</div></div>" +
        '<div class="fed-tags"><span class="fed-tag ' + stanceCls(o.stance) + '">' + esc(st.short + " " + st.label) + "</span>" +
        (o.isVoter2026 ? '<span class="fed-tag fed-tag-vote">2026 투표</span>' : '<span class="fed-tag fed-tag-novote">비투표</span>') +
        "</div></div>" +
        '<div class="fed-remark">' + esc(o.remark) + "</div>" +
        '<div class="fed-meta"><span>발언일 ' + esc(o.lastDate) + "</span>" +
        '<a href="' + esc(safeUrl(o.sourceUrl)) + '" target="_blank" rel="noopener noreferrer">출처 ↗</a></div>' +
        "</article>";
    }).join("") + "</div>";
  }

  function sorted(list) {
    return list.slice().sort(function (a, b) {
      if (b.stance !== a.stance) return b.stance - a.stance;
      if (a.isVoter2026 !== b.isVoter2026) return a.isVoter2026 ? -1 : 1;
      if (a.group !== b.group) return a.group === "board" ? -1 : 1;
      return 0;
    });
  }

  function render(root) {
    var list = sorted(FED_OFFICIALS.filter(matches));
    root.querySelector(".fed-body").innerHTML =
      renderSpectrum() + renderFilters(list.length) + renderCards(list);
  }

  function build() {
    var root = document.createElement("section");
    root.id = SECTION_ID;
    root.setAttribute("aria-label", "Fed Speak Tracker");
    root.innerHTML = '<div class="fed-sec">Fed Speak Tracker</div>' +
      '<div class="fed-panel">' + renderKPIs() + '<div class="fed-body"></div></div>';
    root.addEventListener("click", function (e) {
      var btn = e.target.closest ? e.target.closest(".fed-btn") : null;
      if (!btn || !root.contains(btn)) return;
      state[btn.getAttribute("data-fed-key")] = btn.getAttribute("data-fed-val");
      render(root);
    });
    render(root);
    return root;
  }

  function injectCSS() {
    if (document.getElementById("fed-tracker-css")) return;
    var st = document.createElement("style");
    st.id = "fed-tracker-css";
    st.textContent = CSS;
    document.head.appendChild(st);
  }

  // Anchor = the section header whose text is ANCHOR_TITLE; insert before the next header.
  function findInsertPoint() {
    var heads = document.querySelectorAll("#root .sec");
    for (var i = 0; i < heads.length; i++) {
      if (heads[i].textContent.trim().toLowerCase() === ANCHOR_TITLE.toLowerCase()) {
        var parent = heads[i].parentNode, n = heads[i].nextElementSibling;
        while (n && !(n.classList.contains("sec") || n.id === SECTION_ID)) n = n.nextElementSibling;
        return { parent: parent, before: n };
      }
    }
    return null;
  }

  var section = null;
  function mount() {
    if (section && document.contains(section)) return true;
    var pt = findInsertPoint();
    if (!pt) return false;
    injectCSS();
    if (!section) section = build();
    pt.parent.insertBefore(section, pt.before);
    return true;
  }

  function start() {
    mount();
    // React renders asynchronously (and re-renders every second for the clock) —
    // keep the section in place if it isn't there yet or gets detached.
    var pending = false;
    new MutationObserver(function () {
      if (pending) return;
      pending = true;
      // setTimeout (not requestAnimationFrame) so it also mounts in background tabs
      setTimeout(function () { pending = false; mount(); }, 30);
    }).observe(document.getElementById("root") || document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
