// Data-driven paper comparison table.
// Fetches data/extracted-index.json (technical fingerprints) and
// data/papers-index.json (editorial metadata) and renders a merged view.
//
// Field rendering is declared per-column in COLUMNS so the future
// extract skill can mirror these requirements when producing
// content/extracted/<slug>.json.

const NOT_SPEC = "Not Specified";

// ── Column specs ──────────────────────────────────────────────────────────
// kind:
//   "idx"          row index (rendered after sort/filter)
//   "title"        paper title + optional deep-dive link
//   "venue"        single colored badge (uses venue_full as hover title)
//   "arxiv"        arxiv id rendered as link to arxiv.org/abs/<id>
//   "affiliations" comma-split into multiple colored badges
//   "link"         text + extracted URL rendered as link badge (open_source)
//   "tags"         comma/semicolon-split into colored pills
//   "text"         plain text fallback
const COLUMNS = [
  { key: "idx", label: "#", label_zh: "#", kind: "idx", width: 40 },
  { key: "title", label: "Title", label_zh: "標題", kind: "title", width: 260 },
  { key: "authors", label: "Authors", label_zh: "作者", kind: "text", width: 170 },
  { key: "year", label: "Year", label_zh: "年份", kind: "text", width: 55 },
  { key: "venue", label: "Venue", label_zh: "場域", kind: "venue", width: 110 },
  { key: "arxiv", label: "arXiv", label_zh: "arXiv", kind: "arxiv", width: 90 },
  { key: "affiliations", label: "Affiliations", label_zh: "單位", kind: "affiliations", width: 170 },
  { key: "problem_statement", label: "Problem", label_zh: "問題", kind: "text", group: "core_insights", width: 260 },
  { key: "key_innovation", label: "Innovation", label_zh: "創新", kind: "text", group: "core_insights", width: 260 },
  { key: "baselines_compared", label: "Baselines", label_zh: "比較對象", kind: "tags", group: "evaluation_and_results", width: 170 },
  { key: "key_improvements", label: "Improvements", label_zh: "改進", kind: "text", group: "evaluation_and_results", width: 220 },
  { key: "open_source", label: "Open Source", label_zh: "開源", kind: "link", group: "evaluation_and_results", width: 130 },
  { key: "evaluation_method", label: "Eval Method", label_zh: "評估方法", kind: "tags", group: "experimental_setup", width: 120 },
  { key: "software_simulator", label: "Simulator", label_zh: "模擬器", kind: "tags", group: "experimental_setup", width: 130 },
  { key: "network_topology", label: "Network Topology", label_zh: "網路拓樸", kind: "tags", group: "experimental_setup", width: 140 },
  { key: "ai_task", label: "AI Task", label_zh: "AI 任務", kind: "tags", group: "workload_and_traffic", width: 160 },
  { key: "traffic_pattern", label: "Traffic Pattern", label_zh: "流量模式", kind: "tags", group: "workload_and_traffic", width: 160 },
  { key: "compute_memory_hw", label: "Compute & Mem HW", label_zh: "運算/記憶體", kind: "tags", group: "hardware_infrastructure", width: 180 },
  { key: "network_hw", label: "Network HW", label_zh: "網路硬體", kind: "tags", group: "hardware_infrastructure", width: 160 },
  { key: "platform", label: "Platform", label_zh: "平台", kind: "tags", group: "hardware_infrastructure", width: 110 },
  { key: "transport_and_interconnect", label: "Transport", label_zh: "傳輸層", kind: "tags", group: "networking_stack", width: 150 },
  { key: "routing_and_congestion_control", label: "Routing & CC", label_zh: "路由/壅塞控制", kind: "tags", group: "networking_stack", width: 150 },
  { key: "comm_libraries", label: "Comm Libraries", label_zh: "通訊函式庫", kind: "tags", group: "networking_stack", width: 150 },
  { key: "gpu_count", label: "GPU Count", label_zh: "GPU 數", kind: "text", group: "scale", width: 110 },
  { key: "node_count", label: "Node Count", label_zh: "節點數", kind: "text", group: "scale", width: 90 },
];

// Filter panel groups — subset of `tags` columns we want as filter facets.
const FILTER_FIELDS = [
  "compute_memory_hw",
  "comm_libraries",
  "software_simulator",
  "baselines_compared",
  "traffic_pattern",
  "ai_task",
  "network_topology",
  "transport_and_interconnect",
  "routing_and_congestion_control",
];

// Deterministic tag-color palette — same vibe as the original lit-survey output.
const PALETTE = [
  ["#dbeafe", "#1e40af"], ["#dcfce7", "#166534"], ["#fef3c7", "#92400e"],
  ["#fce7f3", "#9d174d"], ["#e0e7ff", "#3730a3"], ["#f3e8ff", "#6b21a8"],
  ["#ccfbf1", "#115e59"], ["#fee2e2", "#991b1b"], ["#fef9c3", "#854d0e"],
  ["#cffafe", "#155e75"], ["#ede9fe", "#5b21b6"], ["#d1fae5", "#065f46"],
  ["#ffedd5", "#9a3412"], ["#f1f5f9", "#334155"], ["#ecfdf5", "#047857"],
  ["#fff7ed", "#c2410c"], ["#fdf4ff", "#86198f"], ["#f0fdfa", "#0f766e"],
  ["#fefce8", "#a16207"], ["#f0f9ff", "#0369a1"],
];

function tagColor(tag) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < tag.length; i++) {
    h = ((h ^ tag.charCodeAt(i)) * 16777619) >>> 0;
  }
  return PALETTE[h % PALETTE.length];
}

function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function isMeaningful(v) {
  return v && v !== NOT_SPEC && String(v).trim() !== "";
}

// Bilingual values may be either plain strings (legacy / EN-only fields) or
// {en, zh} objects (long-form prose). Resolve to a string given the current
// language, falling back to the other language if the preferred slot is empty.
function pickLang(value, lang = currentLang()) {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "object") {
    const primary = value[lang];
    if (isMeaningful(primary)) return primary;
    const other = lang === "zh" ? value.en : value.zh;
    if (isMeaningful(other)) return other;
    return "";
  }
  return String(value);
}

function isBilingualMissing(value) {
  return (
    typeof value === "object"
    && value !== null
    && !Array.isArray(value)
    && !isMeaningful(value[currentLang()])
    && isMeaningful(value[currentLang() === "zh" ? "en" : "zh"])
  );
}

function splitMulti(s, sep = /[,;]/) {
  const str = typeof s === "string" ? s : pickLang(s);
  if (!isMeaningful(str)) return [];
  return String(str).split(sep).map((t) => t.trim()).filter(Boolean);
}

function tagPill(tag, { title = "" } = {}) {
  const [bg, fg] = tagColor(tag);
  const t = title ? ` title="${escapeHTML(title)}"` : "";
  return `<span class="tag" style="background:${bg};color:${fg}"${t}>${escapeHTML(tag)}</span>`;
}

// ── Per-kind renderers ────────────────────────────────────────────────────

function renderText(value) {
  const resolved = pickLang(value);
  if (!isMeaningful(resolved)) {
    return `<span class="not-specified i18n" data-en="Not Specified" data-zh="未說明">${currentNotSpec()}</span>`;
  }
  const marker = isBilingualMissing(value)
    ? ` <span class="lang-fallback" title="${currentLang() === "zh" ? "尚無中文翻譯，顯示原文" : "no translation"}">${currentLang() === "zh" ? "EN" : "原文"}</span>`
    : "";
  return escapeHTML(resolved) + marker;
}

function renderTags(value) {
  const tags = splitMulti(value);
  if (tags.length === 0) return renderText(NOT_SPEC);
  return `<div class="tag-wrap">${tags.map((t) => tagPill(t)).join("")}</div>`;
}

function renderTitle(flat, editorial) {
  const arxivUrl = flat.arxiv ? `https://arxiv.org/abs/${flat.arxiv}` : (flat.url || "");
  const titleLink = arxivUrl
    ? `<a href="${escapeHTML(arxivUrl)}" target="_blank" rel="noopener">${escapeHTML(flat.title)}</a>`
    : escapeHTML(flat.title);
  if (!editorial) return titleLink;
  const ddLabel = `<span class="i18n" data-en="→ deep dive" data-zh="→ 深度頁面">→ deep dive</span>`;
  return `${titleLink}<br><a class="deep-dive-link" href="../papers/${escapeHTML(editorial.slug)}/">${ddLabel}</a>`;
}

function renderVenue(flat) {
  if (!isMeaningful(flat.venue)) return renderText(NOT_SPEC);
  return `<div class="tag-wrap">${tagPill(flat.venue, { title: flat.venue_full || "" })}</div>`;
}

function renderArxiv(value) {
  if (!isMeaningful(value)) return renderText(NOT_SPEC);
  const id = String(value).trim();
  return `<a class="arxiv-link" href="https://arxiv.org/abs/${encodeURIComponent(id)}" target="_blank" rel="noopener">${escapeHTML(id)}</a>`;
}

function renderAffiliations(value) {
  const items = splitMulti(value, /,/);
  if (items.length === 0) return renderText(NOT_SPEC);
  return `<div class="tag-wrap">${items.map((a) => tagPill(a)).join("")}</div>`;
}

// Extract a URL from a free-form open_source string like
//   "Yes (https://github.com/...)"  →  Yes [link]
//   "Yes"                            →  Yes
//   "No"                             →  No
//   "Partial (github.com/...)"       →  Partial [link]
function renderLink(value) {
  if (!isMeaningful(value)) return renderText(NOT_SPEC);
  const text = String(value);
  const m = text.match(/(https?:\/\/[^\s)]+|github\.com\/[^\s)]+)/i);
  // Take whatever sits before the URL (or the first word) as the verdict.
  let verdict = text.replace(m ? m[0] : "", "").replace(/[()\s]+$/, "").trim();
  if (!verdict) verdict = m ? "Yes" : text;
  const verdictNorm = verdict.toLowerCase();
  let verdictHTML;
  if (/^yes/.test(verdictNorm)) {
    verdictHTML = `<span class="link-verdict yes">${escapeHTML(verdict)}</span>`;
  } else if (/^partial/.test(verdictNorm)) {
    verdictHTML = `<span class="link-verdict partial">${escapeHTML(verdict)}</span>`;
  } else if (/^no/.test(verdictNorm)) {
    verdictHTML = `<span class="link-verdict no">${escapeHTML(verdict)}</span>`;
  } else {
    verdictHTML = `<span class="link-verdict other">${escapeHTML(verdict)}</span>`;
  }
  if (!m) return verdictHTML;
  let url = m[0];
  if (!/^https?:/i.test(url)) url = "https://" + url;
  const linkLabel = `<span class="i18n" data-en="link" data-zh="連結">link</span>`;
  return `${verdictHTML} <a class="repo-link" href="${escapeHTML(url)}" target="_blank" rel="noopener">${linkLabel} ↗</a>`;
}

function renderCell(col, flat, editorial) {
  switch (col.kind) {
    case "idx": return ""; // populated after sort/filter
    case "title": return renderTitle(flat, editorial);
    case "venue": return renderVenue(flat);
    case "arxiv": return renderArxiv(flat[col.key]);
    case "affiliations": return renderAffiliations(flat[col.key]);
    case "link": return renderLink(flat[col.key]);
    case "tags": return renderTags(flat[col.key]);
    case "text": return renderText(flat[col.key]);
    // (renderText handles both plain-string and {en, zh} object values)
    default: return escapeHTML(String(flat[col.key] ?? ""));
  }
}

// ── State + helpers ───────────────────────────────────────────────────────
const state = {
  records: [],
  flatRecords: [],
  editorialMap: {},
  checkedTags: {},
  sortCol: null,
  sortDir: 1,
};

function currentLang() {
  return (window.__getLang && window.__getLang()) || document.documentElement.lang || "en";
}

function currentNotSpec() {
  return currentLang() === "zh" ? "未說明" : "Not Specified";
}

function t(en, zh) {
  return currentLang() === "zh" ? zh : en;
}

function flatRecord(p) {
  const groups = [
    "core_insights",
    "evaluation_and_results",
    "experimental_setup",
    "workload_and_traffic",
    "hardware_infrastructure",
    "networking_stack",
    "scale",
  ];
  const out = { ...p };
  for (const g of groups) {
    if (p[g] && typeof p[g] === "object") Object.assign(out, p[g]);
  }
  return out;
}

function fieldTagsForRecord(flat, field) {
  return splitMulti(flat[field]);
}

// ── Rendering ─────────────────────────────────────────────────────────────

function buildFilterPanel() {
  const container = document.getElementById("filterGroups");
  container.innerHTML = "";
  for (const field of FILTER_FIELDS) {
    const col = COLUMNS.find((c) => c.key === field);
    if (!col) continue;
    const counts = new Map();
    for (const flat of state.flatRecords) {
      for (const tg of fieldTagsForRecord(flat, field)) {
        counts.set(tg, (counts.get(tg) || 0) + 1);
      }
    }
    const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    const group = document.createElement("div");
    group.className = "filter-group";
    group.dataset.field = field;
    const tagsHTML = sorted.map(([tag, n]) => `<label class="filter-tag">
        <input type="checkbox" data-field="${field}" data-tag="${escapeHTML(tag)}">
        ${tagPill(tag)}
        <span class="tag-count">${n}</span>
      </label>`).join("");
    group.innerHTML = `
      <div class="filter-group-title">
        ${escapeHTML(col.label)}
        <span class="filter-group-count">${sorted.length} tags</span>
      </div>
      <div class="filter-group-tags">${tagsHTML}</div>
    `;
    container.appendChild(group);
  }
  container.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
    cb.addEventListener("change", () => {
      const field = cb.dataset.field;
      const tag = cb.dataset.tag;
      if (!state.checkedTags[field]) state.checkedTags[field] = new Set();
      if (cb.checked) state.checkedTags[field].add(tag);
      else state.checkedTags[field].delete(tag);
      if (state.checkedTags[field].size === 0) delete state.checkedTags[field];
      applyFilters();
    });
  });
}

function buildTable() {
  const table = document.getElementById("paperTable");
  const oldColgroup = table.querySelector("colgroup");
  if (oldColgroup) oldColgroup.remove();
  const colgroup = document.createElement("colgroup");
  colgroup.innerHTML = COLUMNS.map((c) => `<col style="width:${c.width}px">`).join("");
  table.insertBefore(colgroup, table.firstChild);
  table.style.width = COLUMNS.reduce((s, c) => s + c.width, 0) + "px";

  const thead = document.getElementById("thead");
  const tbody = document.getElementById("tbody");
  thead.innerHTML = `<tr>${COLUMNS.map((c, i) =>
    `<th data-col="${i}">${escapeHTML(c.label)}</th>`
  ).join("")}</tr>`;
  thead.querySelectorAll("th").forEach((th) => {
    th.addEventListener("click", () => {
      const i = +th.dataset.col;
      if (state.sortCol === i) state.sortDir = -state.sortDir;
      else { state.sortCol = i; state.sortDir = 1; }
      applyFilters();
    });
  });

  tbody.innerHTML = "";
  for (let i = 0; i < state.flatRecords.length; i++) {
    const flat = state.flatRecords[i];
    const editorial = state.editorialMap[flat.slug];
    const tr = document.createElement("tr");
    tr.dataset.hasDetail = editorial ? "1" : "0";
    tr.innerHTML = COLUMNS.map((col) => {
      const cls = (col.kind === "tags" || col.kind === "venue" || col.kind === "affiliations")
        ? "tag-cell"
        : col.kind === "title" ? "title-cell"
        : col.kind === "idx" ? "idx-cell"
        : col.kind === "link" ? "link-cell"
        : "text-cell";
      return `<td class="${cls}" data-key="${col.key}">${renderCell(col, flat, editorial)}</td>`;
    }).join("");
    tbody.appendChild(tr);
  }
}

function rowMatchesTagFilters(flat) {
  for (const [field, required] of Object.entries(state.checkedTags)) {
    const rowTags = new Set(fieldTagsForRecord(flat, field));
    let any = false;
    for (const tg of required) {
      if (rowTags.has(tg)) { any = true; break; }
    }
    if (!any) return false;
  }
  return true;
}

function applyFilters() {
  const q = document.getElementById("search").value.toLowerCase();
  const detail = document.getElementById("detailFilter").value;
  const hasTagFilters = Object.keys(state.checkedTags).length > 0;
  const tbody = document.getElementById("tbody");
  const rows = Array.from(tbody.querySelectorAll("tr"));
  const flagged = [];
  let visible = 0;

  rows.forEach((tr, i) => {
    const flat = state.flatRecords[i];
    const text = tr.textContent.toLowerCase();
    const inText = !q || text.includes(q);
    const inDetail = !detail
      || (detail === "with" && tr.dataset.hasDetail === "1")
      || (detail === "without" && tr.dataset.hasDetail === "0");
    const inTags = !hasTagFilters || rowMatchesTagFilters(flat);
    const v = inText && inDetail && inTags;
    flagged.push(v);
    tr.classList.toggle("hidden", !v);
    if (v) visible++;
  });

  if (state.sortCol != null) {
    const col = COLUMNS[state.sortCol];
    const sorted = rows.map((tr, i) => ({ tr, flat: state.flatRecords[i] }))
      .sort((a, b) => {
        const av = String(a.flat[col.key] ?? "");
        const bv = String(b.flat[col.key] ?? "");
        return state.sortDir * av.localeCompare(bv, undefined, { numeric: true });
      });
    sorted.forEach(({ tr }) => tbody.appendChild(tr));
    document.querySelectorAll("thead th").forEach((th, i) => {
      th.classList.toggle("sort-asc", i === state.sortCol && state.sortDir === 1);
      th.classList.toggle("sort-desc", i === state.sortCol && state.sortDir === -1);
    });
  }

  let n = 1;
  tbody.querySelectorAll("tr:not(.hidden) td.idx-cell").forEach((td) => { td.textContent = n++; });

  document.getElementById("visibleCount").textContent =
    t(`Showing ${visible} of ${state.records.length} papers`,
      `顯示 ${visible} 篇，共 ${state.records.length} 篇`);
  document.getElementById("clearFiltersBtn").style.display =
    hasTagFilters ? "inline-block" : "none";

  const ddCount = state.records.filter((p) => state.editorialMap[p.slug]).length;
  document.getElementById("stats").innerHTML =
    `<span>` + t(`<strong>${visible}</strong> visible / <strong>${state.records.length}</strong> total`,
                 `<strong>${visible}</strong> 顯示 / <strong>${state.records.length}</strong> 總計`) + `</span>` +
    `<span>` + t(`Deep-dive pages: <strong>${ddCount}</strong>`,
                 `深度頁面：<strong>${ddCount}</strong>`) + `</span>`;
}

async function init() {
  const [extracted, editorial] = await Promise.all([
    fetch("../data/extracted-index.json").then((r) => r.json()),
    fetch("../data/papers-index.json").then((r) => r.json()),
  ]);
  state.records = extracted;
  state.flatRecords = extracted.map(flatRecord);
  state.editorialMap = Object.fromEntries(editorial.map((p) => [p.slug, p]));

  buildFilterPanel();
  buildTable();
  applyFilters();

  document.getElementById("search").addEventListener("input", applyFilters);
  document.getElementById("detailFilter").addEventListener("change", applyFilters);
  document.getElementById("filterPanelToggle").addEventListener("click", () => {
    const content = document.getElementById("filterPanelContent");
    const toggle = document.querySelector(".filter-panel-toggle");
    const hidden = content.style.display === "none";
    content.style.display = hidden ? "block" : "none";
    toggle.classList.toggle("open", hidden);
  });
  document.getElementById("clearFiltersBtn").addEventListener("click", () => {
    state.checkedTags = {};
    document.querySelectorAll('#filterGroups input[type="checkbox"]').forEach((cb) => { cb.checked = false; });
    applyFilters();
  });

  // Re-render dynamic DOM on language change, then re-apply .i18n swap to the
  // freshly built nodes (avoids recursing through setLang's dispatchEvent).
  document.addEventListener("langchange", (ev) => {
    const l = ev.detail.lang;
    buildTable();
    applyFilters();
    document.querySelectorAll(".i18n").forEach((e) => {
      if (e.dataset[l]) e.innerHTML = e.dataset[l];
    });
  });

  document.getElementById("footer").innerHTML =
    `<span class="i18n" data-en="Built from content/extracted/ — one paper per JSON file. Future updates: prompt-driven via skill." data-zh="資料來自 content/extracted/ — 每篇論文一個 JSON。未來更新將透過 skill 以 prompt 觸發。">` +
    `Built from content/extracted/ — one paper per JSON file. Future updates: prompt-driven via skill.</span>`;

  // If a lang preference was already set before script.js loaded, the inline
  // bootstrap at the bottom of the HTML will trigger setLang after this init.
}

init().catch((e) => {
  document.getElementById("stats").textContent = `Failed to load data: ${e.message}`;
  console.error(e);
});
