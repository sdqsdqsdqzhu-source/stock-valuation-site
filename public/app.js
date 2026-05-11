const form = document.querySelector("#searchForm");
const input = document.querySelector("#tickerInput");
const statusBand = document.querySelector("#status");
const metricSelect = document.querySelector("#metricSelect");
const rangeSelect = document.querySelector("#rangeSelect");
let currentData = null;

const money = (value) => {
  if (!Number.isFinite(value)) return "--";
  if (Math.abs(value) >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toFixed(2)}`;
};

const pct = (value) => Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "N/A";
const signedPct = (value) => Number.isFinite(value) ? `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)}%` : "N/A";
const signedPpt = (value) => Number.isFinite(value) ? `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)}ppts` : "N/A";
const num = (value, digits = 1) => Number.isFinite(value) ? value.toFixed(digits) : "--";
const ratio = (value, digits = 1) => Number.isFinite(value) && value > 0 ? value.toFixed(digits) : "N/A";
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#039;",
})[char]);

const LABELS = {
  "当前价格": "当前价格 / Current price",
  "市值": "市值 / Market cap",
  "Market cap": "市值 / Market cap",
  "Forward PE": "预期市盈率 / Forward PE",
  "综合合理价": "综合合理价 / Composite fair value",
  "当前": "当前 / Current",
  "模型区间": "模型区间 / Model range",
  "Metric": "指标 / Metric",
  "Target": "目标 / Target",
  "Base FCF": "基础自由现金流 / Base FCF",
  "TTM Revenue": "TTM 营收 / TTM Revenue",
  "FCF Margin": "自由现金流率 / FCF Margin",
  "Y1-5 FCF Growth": "第1-5年FCF增长 / Y1-5 FCF Growth",
  "Y6-10 FCF Growth": "第6-10年FCF增长 / Y6-10 FCF Growth",
  "Terminal Growth": "永续增长率 / Terminal Growth",
  "Discount Rate": "折现率 / Discount Rate",
  "Cash & Investments": "现金及投资 / Cash & Investments",
  "Total Debt": "总债务 / Total Debt",
  "Diluted Shares": "摊薄股数 / Diluted Shares",
  "Beta": "贝塔值 / Beta",
  "Risk-free Rate": "无风险利率 / Risk-free Rate",
  "Market Return": "市场预期回报 / Market Return",
  "Cost of Debt": "债务成本 / Cost of Debt",
  "Tax Rate": "税率 / Tax Rate",
  "DCF fair price": "DCF合理价 / DCF fair price",
  "Enterprise value": "企业价值 / Enterprise value",
  "Equity value": "股权价值 / Equity value",
  "Auto WACC": "自动WACC / Auto WACC",
  "Year": "年份 / Year",
  "Growth": "增长率 / Growth",
  "FCF": "自由现金流 / FCF",
  "PV of FCF": "FCF现值 / PV of FCF",
  "Sensitivity: discount × terminal growth": "敏感性：折现率 × 永续增长 / Sensitivity: discount × terminal growth",
  "Financial quality score": "财务质量分 / Financial quality score",
  "Latest report": "最新财报 / Latest report",
  "Revenue": "营收 / Revenue",
  "Revenue & EPS Outlook": "营收与EPS展望 / Revenue & EPS Outlook",
  "Margin Guidance": "利润率指引 / Margin Guidance",
  "Capex Guidance": "资本开支指引 / Capex Guidance",
  "Buybacks & Dividends": "回购与分红 / Buybacks & Dividends",
  "Gross margin": "毛利率 / Gross margin",
  "Net margin": "净利率 / Net margin",
  "Debt / Assets": "负债/资产 / Debt / Assets",
  "ROE": "净资产收益率 / ROE",
  "FCF conversion": "自由现金流转换率 / FCF conversion",
  "Attention score": "市场热度分 / Attention score",
  "Reddit representative posts": "Reddit代表帖子 / Reddit representative posts",
  "Score": "分数 / Score",
  "Comments": "评论 / Comments",
  "Upvote": "赞同率 / Upvote",
  "Macro/policy fit": "宏观政策适配度 / Macro/policy fit",
  "Policy regime": "政策环境 / Policy regime",
  "Fed policy": "美联储政策 / Fed policy",
  "Tariff lens": "关税视角 / Tariff lens",
  "Risk control score": "风险控制分 / Risk control score",
  "Trailing PE": "滚动市盈率 / Trailing PE",
  "PEG Ratio": "PEG比率 / PEG Ratio",
  "Price / Sales": "市销率 / Price / Sales",
  "Price / Book": "市净率 / Price / Book",
  "Price / FCF": "市值/自由现金流 / Price / FCF",
  "EV / EBITDA": "企业价值/EBITDA / EV / EBITDA",
  "DCF": "DCF折现 / DCF",
  "Current PE": "当前PE / Current PE",
  "Target PE": "目标PE / Target PE",
  "Current Forward PE": "当前Forward PE / Current Forward PE",
  "Target Forward PE": "目标Forward PE / Target Forward PE",
  "Current PEG": "当前PEG / Current PEG",
  "Fair PEG": "合理PEG / Fair PEG",
  "Current P/S": "当前P/S / Current P/S",
  "Target P/S": "目标P/S / Target P/S",
  "Current P/B": "当前P/B / Current P/B",
  "Target P/B": "目标P/B / Target P/B",
  "Current P/FCF": "当前P/FCF / Current P/FCF",
  "Target P/FCF": "目标P/FCF / Target P/FCF",
  "Current EV/EBITDA": "当前EV/EBITDA / Current EV/EBITDA",
  "Target EV/EBITDA": "目标EV/EBITDA / Target EV/EBITDA",
  "Terminal growth": "永续增长率 / Terminal growth",
  "Discount rate": "折现率 / Discount rate",
  "Liquidity": "流动性 / Liquidity",
  "Volume ratio": "量比 / Volume ratio",
  "Order imbalance": "委买卖失衡 / Order imbalance",
  "Price/volume velocity": "价量动能 / Price/volume velocity",
  "Social/news baseline": "社媒/新闻基线 / Social/news baseline",
  "Reddit public search": "Reddit公开搜索 / Reddit public search",
  "X recent search": "X近期搜索 / X recent search",
  "Rate sensitivity": "利率敏感度 / Rate sensitivity",
  "Tariff sensitivity": "关税敏感度 / Tariff sensitivity",
  "Policy/fiscal catalyst": "政策/财政催化 / Policy/fiscal catalyst",
  "Geopolitical exposure": "地缘风险暴露 / Geopolitical exposure",
  "Commodity sensitivity": "商品周期敏感度 / Commodity sensitivity",
};

const TRAITS = {
  mega_cap: "超大市值 / Mega cap",
  cyclical: "周期性 / Cyclical",
  ai: "AI主题 / AI",
  export_control: "出口管制 / Export control",
  high_growth: "高成长 / High growth",
  turnaround: "转型修复 / Turnaround",
  policy_sensitive: "政策敏感 / Policy sensitive",
  geopolitical: "地缘风险 / Geopolitical",
  high_attention: "高关注度 / High attention",
  rate_sensitive: "利率敏感 / Rate sensitive",
  ecosystem: "生态系统 / Ecosystem",
  defensive: "防守型 / Defensive",
  cash_return: "现金回报 / Cash return",
  tariff_sensitive: "关税敏感 / Tariff sensitive",
  china_exposure: "中国敞口 / China exposure",
  commodity_sensitive: "商品周期敏感 / Commodity sensitive",
  scale: "规模优势 / Scale",
  low_margin: "低利润率 / Low margin",
  meme_sensitive: "散户热度敏感 / Meme sensitive",
  heavy_asset: "重资产 / Heavy asset",
  fiscal_spending_sensitive: "财政支出敏感 / Fiscal spending sensitive",
};

const STATUS = {
  High: "高 / High",
  Medium: "中 / Medium",
  Low: "低 / Low",
  Risk: "风险 / Risk",
  "N/A": "不适用 / N/A",
  "Very high": "非常高 / Very high",
  Moderate: "中等 / Moderate",
  connected: "已连接 / connected",
  planned: "计划中 / planned",
  limited: "受限 / limited",
  "needs key": "需要Key / needs key",
  "public limited": "公开接口受限 / public limited",
  high: "高 / high",
  medium: "中 / medium",
  watch: "观察 / watch",
};

const INPUT_ALIASES = {
  INTEL: "INTC",
  英特尔: "INTC",
  因特尔: "INTC",
  GOOGLE: "GOOG",
  谷歌: "GOOG",
  ALPHABET: "GOOG",
  APPLE: "AAPL",
  苹果: "AAPL",
  MICROSOFT: "MSFT",
  微软: "MSFT",
  NVIDIA: "NVDA",
  英伟达: "NVDA",
  TESLA: "TSLA",
  特斯拉: "TSLA",
  AMAZON: "AMZN",
  亚马逊: "AMZN",
  MICRON: "MU",
  美光: "MU",
  QUALCOMM: "QCOM",
  高通: "QCOM",
  FUTU: "FUTU",
  富途: "FUTU",
};

const SUMMARY = {
  "High quality / favorable setup": "高质量且环境有利 / High quality / favorable setup",
  "Constructive, but watch the flags": "结构尚可但需关注风险 / Constructive, but watch the flags",
  "Mixed setup": "多空混合 / Mixed setup",
  "High-risk or unattractive setup": "高风险或吸引力不足 / High-risk or unattractive setup",
  "顺风": "顺风 / Tailwind",
  "逆风": "逆风 / Headwind",
  "中性偏观察": "中性偏观察 / Neutral-watch",
};

const bi = (value) => LABELS[value] || STATUS[value] || SUMMARY[value] || value;
const traitLabel = (value) => TRAITS[value] || value.replaceAll("_", " ");
const statusLabel = (value) => STATUS[value] || value;
const normalizeInputTicker = (value) => INPUT_ALIASES[String(value || "").trim().toUpperCase()] || INPUT_ALIASES[String(value || "").trim()] || value;
const unitBi = (unit) => ({
  "B USD": "十亿美元 / B USD",
  "B": "十亿股 / B shares",
  "%": "%",
  "x": "倍 / x",
})[unit] || unit;
const noteBi = (note) => {
  const rules = [
    ["Futu OpenD snapshot connected.", "富途OpenD快照已连接 / Futu OpenD snapshot connected."],
    ["Futu historical K-line connected.", "富途历史K线已连接 / Futu historical K-line connected."],
    ["SEC companyfacts connected.", "SEC财报结构化数据已连接 / SEC companyfacts connected."],
    ["FRED macro data connected.", "FRED宏观数据已连接 / FRED macro data connected."],
    ["Reddit public search connected", "Reddit公开搜索已连接 / Reddit public search connected"],
    ["X recent search unavailable", "X近期搜索不可用 / X recent search unavailable"],
    ["FRED_API_KEY not set", "未设置FRED_API_KEY / FRED_API_KEY not set"],
    ["Using deterministic snapshot fallback.", "正在使用确定性行情备用数据 / Using deterministic snapshot fallback."],
    ["Using model fallback financials.", "正在使用模型备用财务数据 / Using model fallback financials."],
  ];
  const match = rules.find(([key]) => note.includes(key));
  return match ? note.replace(match[0], match[1]) : note;
};

function bar(label, value, detail = "") {
  const safe = Math.max(0, Math.min(100, Number(value) || 0));
  return `
    <div class="bar-row">
      <div class="bar-label"><span>${bi(label)}</span><strong>${Math.round(safe)}</strong></div>
      <div class="bar"><span style="width:${safe}%"></span></div>
      ${detail ? `<p>${detail}</p>` : ""}
    </div>
  `;
}

function stat(label, value, hint = "") {
  return `
    <div class="stat">
      <span>${bi(label)}</span>
      <strong>${value}</strong>
      ${hint ? `<small>${hint}</small>` : ""}
    </div>
  `;
}

function metricValue(value) {
  return Number.isFinite(value) ? value.toFixed(2) : "N/A";
}

function miniChange(label, value) {
  const cls = Number.isFinite(value) && value >= 0 ? "up" : "down";
  return `<span class="${cls}">${label} ${signedPct(value)}</span>`;
}

function renderOverview(data) {
  const profileTags = data.profile.traits.map((tag) => `<span class="chip">${traitLabel(tag)}</span>`).join("");
  const sourceText = String(data.snapshot.source || "");
  const sourceHint = sourceText.includes("fallback")
    ? `${sourceText} · 模拟兜底数据，请勿作为交易依据 / simulated fallback, not trading data`
    : sourceText;
  const priceHint = `
    <div class="price-changes">
      ${miniChange("日 / Day", data.price_context.day_change)}
      ${miniChange("周 / Week", data.price_context.week_change)}
      ${miniChange("月 / Month", data.price_context.month_change)}
      ${miniChange("季 / Quarter", data.price_context.quarter_change)}
    </div>
  `;
  document.querySelector("#overview").innerHTML = `
    <article class="hero-panel">
      <div>
        <p class="eyebrow">${data.code} · ${data.profile.size}</p>
        <div class="name-row">
          <span class="logo-wrap">
            <span class="logo-fallback">${data.ticker.slice(0, 3)}</span>
            <img class="logo" src="${data.profile.logo_url}" alt="${data.ticker} logo" onerror="if(this.dataset.fallback==='1'){this.style.display='none'}else{this.dataset.fallback='1';this.src='${data.profile.logo_fallback_url || ""}'}" />
          </span>
          <h2>${data.name}</h2>
        </div>
        <p>${data.profile.sector} / ${data.profile.industry}</p>
        <div class="chips">${profileTags}</div>
      </div>
      <div class="score-ring" style="--score:${data.summary.score}">
        <strong>${data.summary.score}</strong>
        <span>${bi(data.summary.label)}</span>
      </div>
    </article>
    ${stat("当前价格", money(data.snapshot.price), `${sourceHint}${priceHint}`)}
    ${stat("市值", money(data.snapshot.market_cap), "Market cap")}
    ${stat("Forward PE", ratio(data.valuation.forward_pe, 1), `模型预期估值 / Model forward estimate · Futu TTM/动态PE ${ratio(data.snapshot.pe_ttm || data.snapshot.pe, 1)}`)}
    ${stat("综合合理价", money(data.valuation.fair_value), `${data.valuation.upside}% vs current / 相对当前价格`)}
  `;
}

function renderValuation(data) {
  document.querySelector("#fairValueBadge").innerHTML = `
    <span>${money(data.valuation.range_low)} - ${money(data.valuation.range_high)}</span>
    <strong>${data.valuation.upside}%</strong>
  `;
  const current = data.valuation.current_price;
  const low = data.valuation.range_low;
  const high = data.valuation.range_high;
  const max = Math.max(current, high) * 1.18;
  const currentPos = Math.min(96, Math.max(3, (current / max) * 100));
  const lowPos = Math.min(96, Math.max(3, (low / max) * 100));
  const highPos = Math.min(96, Math.max(lowPos + 4, (high / max) * 100));
  document.querySelector("#valuationRange").innerHTML = `
    <div class="range-bg">
      <span class="range-fill" style="left:${lowPos}%; width:${highPos - lowPos}%"></span>
      <span class="current-dot" style="left:${currentPos}%"></span>
    </div>
    <div class="range-labels">
      <span>当前 / Current ${money(current)}</span>
      <span>模型区间 / Model range ${money(low)} - ${money(high)}</span>
    </div>
  `;
  document.querySelector("#methods").innerHTML = data.methods.map((method) => `
    <article class="method ${method.applicable ? "" : "disabled"} ${method.is_negative ? "negative" : ""}">
      <div>
        <div class="method-title">
          <h3>${bi(method.name)}</h3>
          <span>${statusLabel(method.confidence)}</span>
        </div>
        <p>${method.applicable ? method.why : method.invalid_reason}</p>
        <div class="method-metrics">
          <span>${bi(method.metric_label || "Metric")}: <strong>${metricValue(method.metric_value)}</strong></span>
          <span>${bi(method.target_label || "Target")}: <strong>${metricValue(method.target_value)}</strong></span>
        </div>
        <small>${method.applicable ? method.valuation_label : "保留展示 / Kept for explanation：说明为什么该方法现在不能用 / why this method is not usable now"}</small>
      </div>
      <div class="method-price">
        <strong>${method.applicable ? money(method.fair_value) : "N/A"}</strong>
        <span>${method.applicable ? `${money(method.low)} - ${money(method.high)}` : "不适用 / not applicable"}</span>
        <em>${Math.round((method.applicable ? method.weight : method.display_weight) * 100)}% 模型权重 / model weight</em>
      </div>
    </article>
  `).join("");
}

const dcfFields = [
  ["base_fcf_b", "Base FCF", "B USD", 0.1],
  ["revenue_b", "TTM Revenue", "B USD", 0.1],
  ["fcf_margin", "FCF Margin", "%", 0.1, 100],
  ["growth_stage_1", "Y1-5 FCF Growth", "%", 0.1, 100],
  ["growth_stage_2", "Y6-10 FCF Growth", "%", 0.1, 100],
  ["terminal_growth", "Terminal Growth", "%", 0.1, 100],
  ["discount_rate", "Discount Rate", "%", 0.1, 100],
  ["cash_b", "Cash & Investments", "B USD", 0.1],
  ["debt_b", "Total Debt", "B USD", 0.1],
  ["shares_b", "Diluted Shares", "B", 0.01],
  ["beta", "Beta", "x", 0.01],
  ["risk_free_rate", "Risk-free Rate", "%", 0.1, 100],
  ["market_return", "Market Return", "%", 0.1, 100],
  ["cost_of_debt", "Cost of Debt", "%", 0.1, 100],
  ["tax_rate", "Tax Rate", "%", 0.1, 100],
];

function dcfInput(field, label, unit, step, scale = 1) {
  const value = currentData.dcf_lab.inputs[field];
  const display = Number.isFinite(value) ? value * scale : 0;
  return `
    <label class="dcf-field">
      <span>${bi(label)}</span>
      <div>
        <input data-dcf="${field}" data-scale="${scale}" type="number" step="${step}" value="${display.toFixed(scale === 100 ? 2 : 3)}" />
        <em>${unitBi(unit)}</em>
      </div>
    </label>
  `;
}

function readDcfInputs() {
  const inputs = { ...currentData.dcf_lab.inputs };
  document.querySelectorAll("[data-dcf]").forEach((node) => {
    const scale = Number(node.dataset.scale || 1);
    inputs[node.dataset.dcf] = (Number(node.value) || 0) / scale;
  });
  inputs.years_stage_1 = 5;
  inputs.years_stage_2 = 5;
  return inputs;
}

function calculateDcf(inputs) {
  const fcf = inputs.base_fcf_b || (inputs.revenue_b * inputs.fcf_margin);
  const years = inputs.years_stage_1 + inputs.years_stage_2;
  const projections = [];
  let pvStage = 0;
  let currentFcf = fcf;
  for (let year = 1; year <= years; year += 1) {
    const growth = year <= inputs.years_stage_1 ? inputs.growth_stage_1 : inputs.growth_stage_2;
    currentFcf *= 1 + growth;
    const pv = currentFcf / ((1 + inputs.discount_rate) ** year);
    pvStage += pv;
    projections.push({ year, growth, fcf: currentFcf, pv });
  }
  const invalidTerminal = inputs.discount_rate <= inputs.terminal_growth;
  const terminalValue = invalidTerminal ? null : currentFcf * (1 + inputs.terminal_growth) / (inputs.discount_rate - inputs.terminal_growth);
  const terminalPv = invalidTerminal ? null : terminalValue / ((1 + inputs.discount_rate) ** years);
  const enterpriseValue = pvStage + (terminalPv || 0);
  const equityValue = enterpriseValue + inputs.cash_b - inputs.debt_b;
  const fairPrice = equityValue / Math.max(inputs.shares_b, 0.0001);
  const margin = inputs.current_price ? fairPrice / inputs.current_price - 1 : null;
  const debtWeight = inputs.debt_b / Math.max(inputs.market_cap_b + inputs.debt_b, 0.0001);
  const equityWeight = 1 - debtWeight;
  const costOfEquity = inputs.risk_free_rate + inputs.beta * (inputs.market_return - inputs.risk_free_rate);
  const wacc = debtWeight * inputs.cost_of_debt * (1 - inputs.tax_rate) + equityWeight * costOfEquity;
  return { projections, pvStage, terminalValue, terminalPv, enterpriseValue, equityValue, fairPrice, margin, debtWeight, equityWeight, costOfEquity, wacc, invalidTerminal };
}

function renderDcfLab(data) {
  const lab = data.dcf_lab;
  document.querySelector("#dcfLab").innerHTML = `
    <details class="collapsible-section" open>
      <summary>展开/收起 DCF 参数与结果 / Expand or collapse DCF inputs and results</summary>
      <div class="collapsible-body">
        <div class="dcf-layout">
          <div class="dcf-inputs">
            ${dcfFields.map((item) => dcfInput(...item)).join("")}
          </div>
          <div class="dcf-output">
            <div id="dcfSummary" class="dcf-summary"></div>
            <button id="useWaccBtn" class="secondary-button" type="button">用自动WACC作为折现率 / Use auto WACC as discount rate</button>
            <div id="dcfSensitivity" class="sensitivity"></div>
          </div>
        </div>
        <div class="dcf-table-wrap">
          <table class="dcf-table">
            <thead><tr><th>${bi("Year")}</th><th>${bi("Growth")}</th><th>${bi("FCF")}</th><th>${bi("PV of FCF")}</th></tr></thead>
            <tbody id="dcfProjectionRows"></tbody>
          </table>
        </div>
        <div class="dcf-notes">
          ${lab.notes.map((note) => `<span>${note}</span>`).join("")}
        </div>
      </div>
    </details>
  `;
  document.querySelectorAll("[data-dcf]").forEach((node) => {
    node.addEventListener("input", updateDcfLab);
  });
  document.querySelector("#useWaccBtn").addEventListener("click", () => {
    const result = calculateDcf(readDcfInputs());
    const discountInput = document.querySelector('[data-dcf="discount_rate"]');
    discountInput.value = (result.wacc * 100).toFixed(2);
    updateDcfLab();
  });
  updateDcfLab();
}

function updateDcfLab() {
  if (!currentData?.dcf_lab) return;
  const inputs = readDcfInputs();
  const result = calculateDcf(inputs);
  const marginClass = result.margin >= 0 ? "up" : "down";
  document.querySelector("#dcfBadge").innerHTML = `<span>${money(result.fairPrice)}</span><strong class="${marginClass}">${signedPct(result.margin)}</strong>`;
  document.querySelector("#dcfSummary").innerHTML = [
    stat("DCF fair price", money(result.fairPrice), `相对当前价 / vs current ${money(inputs.current_price)} · ${result.margin >= 0 ? "低估 / undervalued" : "高估 / overvalued"} ${signedPct(Math.abs(result.margin))}`),
    stat("Enterprise value", money(result.enterpriseValue * 1e9), `阶段现值 / PV stage ${money(result.pvStage * 1e9)} · 终值现值 / Terminal PV ${money((result.terminalPv || 0) * 1e9)}`),
    stat("Equity value", money(result.equityValue * 1e9), `现金 / Cash ${money(inputs.cash_b * 1e9)} · 债务 / Debt ${money(inputs.debt_b * 1e9)}`),
    stat("Auto WACC", pct(result.wacc), `股权成本 / CoE ${pct(result.costOfEquity)} · 债务权重 / Debt weight ${pct(result.debtWeight)} · 股权权重 / Equity weight ${pct(result.equityWeight)}`),
  ].join("") + (result.invalidTerminal ? `<p class="dcf-warning">折现率必须高于永续增长率，否则终值无效 / Discount rate must be above terminal growth, otherwise terminal value is invalid.</p>` : "");
  document.querySelector("#dcfProjectionRows").innerHTML = result.projections.map((row) => `
    <tr>
      <td>${row.year}</td>
      <td>${signedPct(row.growth)}</td>
      <td>${money(row.fcf * 1e9)}</td>
      <td>${money(row.pv * 1e9)}</td>
    </tr>
  `).join("");
  const discountCases = [inputs.discount_rate - 0.01, inputs.discount_rate, inputs.discount_rate + 0.01];
  const terminalCases = [inputs.terminal_growth - 0.005, inputs.terminal_growth, inputs.terminal_growth + 0.005];
  document.querySelector("#dcfSensitivity").innerHTML = `
    <strong>${bi("Sensitivity: discount × terminal growth")}</strong>
    <table>
      <thead><tr><th>r \\ g</th>${terminalCases.map((g) => `<th>${pct(g)}</th>`).join("")}</tr></thead>
      <tbody>
        ${discountCases.map((discount) => `
          <tr>
            <th>${pct(discount)}</th>
            ${terminalCases.map((terminal) => {
              const scenario = calculateDcf({ ...inputs, discount_rate: discount, terminal_growth: terminal });
              return `<td>${scenario.invalidTerminal ? "N/A" : money(scenario.fairPrice)}</td>`;
            }).join("")}
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function miniSparkline(points = []) {
  const clean = points.filter((p) => Number.isFinite(Number(p.value)));
  if (!clean.length) return `<p class="empty">暂无趋势数据 / No trend data</p>`;
  const values = clean.map((p) => Number(p.value));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const coords = clean.map((p, i) => {
    const x = 6 + (i / Math.max(clean.length - 1, 1)) * 188;
    const y = 62 - ((Number(p.value) - min) / span) * 52;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  return `
    <svg viewBox="0 0 200 72" role="img" aria-label="trend">
      <polyline points="${coords}" fill="none" stroke="#0f766e" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></polyline>
      ${clean.map((p, i) => {
        const [x, y] = coords.split(" ")[i].split(",");
        return `<circle cx="${x}" cy="${y}" r="3.2"></circle>`;
      }).join("")}
    </svg>
    <div class="turnaround-trend-values">
      ${clean.map((p) => `<span><em>${esc(p.date || "")}</em><strong>${esc(p.display || String(p.value))}</strong></span>`).join("")}
    </div>
  `;
}

function renderTurnaround(data) {
  const model = data.turnaround;
  if (!model) return;
  const scoreClass = model.score >= 75 ? "strong" : model.score >= 60 ? "watch" : model.score >= 45 ? "early" : "risk";
  document.querySelector("#turnaroundBadge").innerHTML = `<span>${esc(model.label)}</span><strong class="${scoreClass}">${model.score}</strong>`;
  document.querySelector("#turnaround").innerHTML = `
    <details class="collapsible-section" open>
      <summary>展开/收起拐点修复明细 / Expand or collapse turnaround details</summary>
      <div class="collapsible-body">
        <div class="turnaround-summary">
          ${bar("拐点修复总分 / Turnaround recovery score", model.score, esc(model.why_it_matters))}
        </div>
        <div class="turnaround-grid">
          ${model.dimensions.map((item) => `
            <article class="turnaround-card">
              <div class="turnaround-card-head">
                <div>
                  <h3>${esc(item.name)}</h3>
                  <span>权重 / Weight ${(item.weight * 100).toFixed(0)}%</span>
                </div>
                <strong>${item.score}</strong>
              </div>
              <p>${esc(item.explanation)}</p>
              <div class="turnaround-raw">
                ${item.raw.map((raw) => `<span><em>${esc(raw.label)}</em><b>${esc(raw.value)}</b></span>`).join("")}
              </div>
              <div class="turnaround-mini-trend">
                ${miniSparkline(item.trend || [])}
              </div>
            </article>
          `).join("")}
        </div>
      </div>
    </details>
  `;
}

function redditHistogram(reddit) {
  const daily = Array.isArray(reddit.daily) ? reddit.daily : [];
  if (!daily.length) return "";
  const maxValue = Math.max(...daily.map((d) => Number(d.posts) + Number(d.comments) / 10), 1);
  return `
    <div class="reddit-histogram">
      <strong>近7天Reddit抓取柱状图 / 7-day Reddit capture chart</strong>
      <div class="reddit-bars">
        ${daily.map((d) => {
          const value = Number(d.posts) + Number(d.comments) / 10;
          const height = Math.max(8, (value / maxValue) * 88);
          return `
            <div class="reddit-bar">
              <span style="height:${height}%"></span>
              <small>${esc(String(d.date || "").slice(5))}</small>
              <em>${Number(d.posts) || 0}帖 / posts<br>${Number(d.comments) || 0}评 / comments</em>
            </div>
          `;
        }).join("")}
      </div>
    </div>
  `;
}

function metricChange(item, field) {
  return item.change_type === "pp" ? signedPpt(item[field]) : signedPct(item[field]);
}

function renderFinancialMetricCard(item) {
  const points = item.points || [];
  return `
    <article class="financial-card">
      <div class="financial-card-head">
        <div>
          <h3>${esc(item.name)}</h3>
          <span>${esc(item.why || "")}</span>
        </div>
        <strong>${esc(item.display)}</strong>
      </div>
      <div class="financial-changes">
        <span class="${Number(item.yoy) >= 0 ? "up" : "down"}">同比 / YoY ${metricChange(item, "yoy")}</span>
        <span class="${Number(item.qoq) >= 0 ? "up" : "down"}">环比 / QoQ ${metricChange(item, "qoq")}</span>
      </div>
      <div class="financial-mini-trend">
        ${miniSparkline(points)}
      </div>
    </article>
  `;
}

function renderFinancials(data) {
  const report = data.financials.latest_report || {};
  const sourceLink = report.source_url ? ` · <a href="${esc(report.source_url)}" target="_blank" rel="noreferrer">${esc(report.source || "source")}</a>` : "";
  renderTrend();
  document.querySelector("#financialMetrics").innerHTML = [
    bar("Financial quality score", data.metrics.score, data.financials.source),
    stat("Latest report", report.filed || "N/A", `${report.form || "N/A"} · 报告期 / period ${report.period_end || "N/A"}${sourceLink}`),
    `<div class="financial-card-grid">${(data.financials.metric_history || []).map(renderFinancialMetricCard).join("")}</div>`,
  ].join("");
}

function renderTrend() {
  if (!currentData) return;
  const metric = metricSelect.value;
  const limit = Number(rangeSelect.value);
  const points = (currentData.financials.trends?.[metric] || []).slice(-limit);
  const target = document.querySelector("#financialTrend");
  if (!points.length) {
    target.innerHTML = `<p class="empty">暂无结构化趋势数据 / No structured trend data</p>`;
    return;
  }
  const values = points.map((p) => Number(p.value) || 0);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const coords = points.map((p, i) => {
    const x = 8 + (i / Math.max(points.length - 1, 1)) * 284;
    const y = 92 - ((Number(p.value) - min) / span) * 76;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  const latestDisplay = metric === "eps" ? num(values.at(-1), 2) : money(values.at(-1));
  target.innerHTML = `
    <svg viewBox="0 0 300 110" role="img">
      <polyline points="${coords}" fill="none" stroke="#0f766e" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></polyline>
      ${points.map((p, i) => {
        const [x, y] = coords.split(" ")[i].split(",");
        return `<circle cx="${x}" cy="${y}" r="3.5"></circle>`;
      }).join("")}
    </svg>
    <div class="trend-labels"><span>${points[0].date || ""}</span><strong>${latestDisplay}</strong><span>${points.at(-1).date || ""}</span></div>
  `;
}

function renderGuidance(data) {
  document.querySelector("#guidance").innerHTML = (data.financials.guidance || []).map((item) => `
    <article class="guidance-item">
      <div>
        <strong>${bi(item.name)}</strong>
        <span>${item.status}</span>
      </div>
      <p>${item.context}</p>
      <small>同比 / YoY ${signedPct(item.yoy)} · 环比 / QoQ ${signedPct(item.qoq)}</small>
      ${Number.isFinite(item.secondary_yoy) || Number.isFinite(item.secondary_qoq) ? `<small>EPS/净利润代理 / EPS or net income proxy: YoY ${signedPct(item.secondary_yoy)} · QoQ ${signedPct(item.secondary_qoq)}</small>` : ""}
      ${item.source_url ? `<a href="${esc(item.source_url)}" target="_blank" rel="noreferrer">${esc(item.source || "source")}</a>` : ""}
    </article>
  `).join("");
}

function renderAttention(data) {
  const reddit = data.attention.reddit_social || {};
  const redditPosts = Array.isArray(reddit.top_posts) ? reddit.top_posts : [];
  document.querySelector("#attention").innerHTML = `
    ${bar("Attention score", data.attention.score, data.attention.level)}
    ${data.attention.signals.map((item) => bar(item.name, item.value, item.detail)).join("")}
    ${redditHistogram(reddit)}
    ${redditPosts.length ? `
      <details class="reddit-posts">
        <summary>${bi("Reddit representative posts")} · ${redditPosts.length}</summary>
        ${redditPosts.map((post) => `
          <a href="${esc(post.url)}" target="_blank" rel="noreferrer">
            <span>${esc(post.subreddit)} · ${esc(post.created)}</span>
            <b>${esc(post.title)}</b>
            <small>${bi("Score")} ${post.score} · ${bi("Comments")} ${post.comments} · ${bi("Upvote")} ${pct(post.upvote_ratio)}</small>
          </a>
        `).join("")}
      </details>
    ` : ""}
    <div class="connector-list">
      ${data.attention.connectors.map((item) => `
        <div><strong>${item.name}</strong><span>${statusLabel(item.status)}</span><small>${item.needs}</small></div>
      `).join("")}
    </div>
  `;
}

function renderMacro(data) {
  document.querySelector("#macro").innerHTML = `
    ${bar("Macro/policy fit", data.macro.score, data.macro.interpretation)}
    ${data.macro.exposures.map((item) => bar(item.name, item.value)).join("")}
    ${stat("Policy regime", data.macro.regime.regime, data.macro.regime.source)}
    ${stat("Fed policy", data.macro.regime.fed_policy, data.macro.regime.yield_curve)}
    ${stat("Tariff lens", data.macro.regime.tariff_regime, "USTR/出口管制需实时接入 / USTR and export controls need live feed")}
  `;
}

function renderRisks(data) {
  document.querySelector("#risks").innerHTML = `
    ${bar("Risk control score", data.risk.score)}
    ${data.risk.flags.map((flag) => `
      <article class="risk ${flag.severity}">
        <span>${statusLabel(flag.severity)}</span>
        <h3>${flag.title}</h3>
        <p>${flag.detail}</p>
      </article>
    `).join("")}
  `;
}

function renderNotes(data) {
  const notes = data.data_notes.map((note) => `<span>${noteBi(note)}</span>`).join("");
  const links = (data.external_links || []).map((item) => `
    <a href="${item.url}" target="_blank" rel="noreferrer">
      <strong>${item.name}</strong>
      <small>${item.use}</small>
    </a>
  `).join("");
  document.querySelector("#notes").innerHTML = notes + links;
}

function render(data) {
  currentData = data;
  statusBand.textContent = `${data.ticker} 分析完成 / Analysis complete · ${data.updated_at}`;
  renderOverview(data);
  renderValuation(data);
  renderDcfLab(data);
  renderTurnaround(data);
  renderFinancials(data);
  renderGuidance(data);
  renderAttention(data);
  renderMacro(data);
  renderRisks(data);
  renderNotes(data);
}

async function analyze(ticker) {
  statusBand.textContent = `正在分析 / Analyzing ${ticker.toUpperCase()}...`;
  const response = await fetch(`/api/analyze?ticker=${encodeURIComponent(ticker)}`);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  render(await response.json());
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const normalized = normalizeInputTicker(input.value.trim() || "INTC");
  input.value = normalized;
  analyze(normalized).catch((error) => {
    statusBand.textContent = `分析失败 / Analysis failed：${error.message}`;
  });
});

metricSelect.addEventListener("change", renderTrend);
rangeSelect.addEventListener("change", renderTrend);

analyze(input.value);
