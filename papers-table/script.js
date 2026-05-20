// Schema-driven paper comparison table.
//
// Columns + canonical tag values + bilingual labels all come from
// schemas/<domain>.yaml. Each subtable tab loads its own schema and
// shows records whose `domains` array contains that domain.
//
// To add a new subtable: drop a new YAML at schemas/<name>.yaml and add
// the name to AVAILABLE_DOMAINS below.

const NOT_SPEC = "Not Specified";

// Known subtables — add an entry here when you add a new schema YAML.
const AVAILABLE_DOMAINS = ["ai-networking", "inference-modeling"];

// Deterministic tag-color palette.
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

// ── Bilingual helpers ────────────────────────────────────────────────────
function currentLang() {
  return (window.__getLang && window.__getLang()) || document.documentElement.lang || "en";
}
function t(en, zh) { return currentLang() === "zh" ? zh : en; }
function currentNotSpec() { return currentLang() === "zh" ? "未說明" : "Not Specified"; }

function isMeaningful(v) {
  return v && v !== NOT_SPEC && String(v).trim() !== "";
}

function pickLang(value, lang = currentLang()) {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "object" && !Array.isArray(value)) {
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
    typeof value === "object" && value !== null && !Array.isArray(value)
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
  const ti = title ? ` title="${escapeHTML(title)}"` : "";
  return `<span class="tag" style="background:${bg};color:${fg}"${ti}>${escapeHTML(tag)}</span>`;
}

// ── Per-kind renderers ───────────────────────────────────────────────────
function renderText(value) {
  const resolved = pickLang(value);
  if (!isMeaningful(resolved)) {
    return `<span class="not-specified">${currentNotSpec()}</span>`;
  }
  const marker = isBilingualMissing(value)
    ? ` <span class="lang-fallback" title="${currentLang() === "zh" ? "尚無中文翻譯，顯示原文" : "no translation"}">${currentLang() === "zh" ? "EN" : "原文"}</span>`
    : "";
  return escapeHTML(resolved) + marker;
}

function renderTags(value) {
  const tags = splitMulti(value);
  if (tags.length === 0) return renderText(NOT_SPEC);
  return `<div class="tag-wrap">${tags.map((tg) => tagPill(tg)).join("")}</div>`;
}

function renderTitle(record, editorial) {
  const title = pickLang(record.title) || record.title || "";
  const arxivUrl = record.arxiv ? `https://arxiv.org/abs/${record.arxiv}` : (record.url || "");
  const titleLink = arxivUrl
    ? `<a href="${escapeHTML(arxivUrl)}" target="_blank" rel="noopener">${escapeHTML(title)}</a>`
    : escapeHTML(title);
  if (!editorial) return titleLink;
  const ddLabel = t("→ deep dive", "→ 深度頁面");
  return `${titleLink}<br><a class="deep-dive-link" href="../papers/${escapeHTML(editorial.slug)}/">${ddLabel}</a>`;
}

function renderVenue(record) {
  if (!isMeaningful(record.venue)) return renderText(NOT_SPEC);
  return `<div class="tag-wrap">${tagPill(record.venue, { title: record.venue_full || "" })}</div>`;
}

function renderArxiv(value) {
  if (!isMeaningful(value)) return renderText(NOT_SPEC);
  const id = String(value).trim();
  return `<a class="arxiv-link" style="white-space:nowrap" href="https://arxiv.org/abs/${encodeURIComponent(id)}" target="_blank" rel="noopener">${escapeHTML(id)}</a>`;
}

function renderAffiliations(value) {
  const items = splitMulti(value, /,/);
  if (items.length === 0) return renderText(NOT_SPEC);
  return `<div class="tag-wrap">${items.map((a) => tagPill(a)).join("")}</div>`;
}

function linkLabelFromUrl(url) {
  try {
    const u = new URL(url);
    const host = u.hostname.toLowerCase();
    if (host.endsWith("github.com")) return "GitHub";
    if (host.endsWith("huggingface.co")) return "HuggingFace";
    if (host.endsWith("anonymous.4open.science")) return "Anonymous";
    if (host.endsWith("zenodo.org")) return "Zenodo";
    if (host.endsWith("gitlab.com")) return "GitLab";
    if (host.endsWith("bitbucket.org")) return "Bitbucket";
    return host.replace(/^www\./, "");
  } catch (_) {
    return "Link";
  }
}

function renderLink(value) {
  if (!isMeaningful(value)) return renderText(NOT_SPEC);
  const text = String(value).trim();
  const urls = text.match(/https?:\/\/[^\s,;)]+/gi) || [];
  const verdictRaw = text.replace(/https?:\/\/[^\s,;)]+/gi, "").replace(/[()\s,;]+/g, " ").trim();
  const verdictNorm = verdictRaw.toLowerCase();
  let cls = "other";
  if (/^yes/.test(verdictNorm) || urls.length) cls = "yes";
  else if (/^partial/.test(verdictNorm)) cls = "partial";
  else if (/^no\b/.test(verdictNorm)) cls = "no";
  if (urls.length === 0) {
    const fallback = verdictRaw || text;
    return `<span class="link-verdict ${cls}">${escapeHTML(fallback)}</span>`;
  }
  const verdictLabel = /^partial/.test(verdictNorm) ? "Partial" : "";
  const links = urls.map((u) => {
    const safeUrl = /^https?:/i.test(u) ? u : "https://" + u;
    const label = linkLabelFromUrl(safeUrl);
    return `<a class="repo-link" href="${escapeHTML(safeUrl)}" target="_blank" rel="noopener">${escapeHTML(label)} ↗</a>`;
  }).join(" ");
  const verdictHTML = verdictLabel
    ? `<span class="link-verdict ${cls}">${escapeHTML(verdictLabel)}</span> `
    : "";
  return `${verdictHTML}${links}`;
}

function renderList(value) {
  if (Array.isArray(value)) {
    if (!value.length) return renderText(NOT_SPEC);
    return `<div class="tag-wrap">${value.map((tg) => tagPill(String(tg))).join("")}</div>`;
  }
  return renderTags(value);
}

function renderDomains(value) {
  if (!Array.isArray(value) || !value.length) return renderText(NOT_SPEC);
  return `<div class="tag-wrap">${value.map((d) => tagPill(d)).join("")}</div>`;
}

function renderCell(field, record, editorial) {
  const value = record[field.key];
  switch (field.kind) {
    case "title": return renderTitle(record, editorial);
    case "venue": return renderVenue(record);
    case "arxiv": return renderArxiv(value);
    case "affiliations": return renderAffiliations(value);
    case "link": return renderLink(value);
    case "tags": return renderTags(value);
    case "list": return renderList(value);
    case "domains": return renderDomains(value);
    case "text": return renderText(value);
    default: return escapeHTML(String(value ?? ""));
  }
}

// ── Schema loading ───────────────────────────────────────────────────────
const schemaCache = new Map();

async function fetchYamlText(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`Failed to load ${url}: ${r.status}`);
  return r.text();
}

async function loadSchema(name) {
  if (schemaCache.has(name)) return schemaCache.get(name);
  const yamlText = await fetchYamlText(`../schemas/${name}.yaml`);
  const raw = jsyaml.load(yamlText);
  // Resolve inheritance: parent fields first (in their order), then child fields.
  // Child entries with the same key override parent entries.
  let mergedFields = {};
  if (Array.isArray(raw.inherits)) {
    for (const parentName of raw.inherits) {
      const parent = await loadSchema(parentName);
      mergedFields = { ...mergedFields, ...parent.fields };
    }
  }
  mergedFields = { ...mergedFields, ...(raw.fields || {}) };
  // Attach the field key (object key) onto each field as `.key` for downstream use.
  const fieldsWithKey = {};
  for (const [k, v] of Object.entries(mergedFields)) {
    fieldsWithKey[k] = { key: k, ...v };
  }
  const resolved = { ...raw, fields: fieldsWithKey };
  schemaCache.set(name, resolved);
  return resolved;
}

function getLabel(obj, fallback = "") {
  if (!obj) return fallback;
  if (typeof obj === "string") return obj;
  return obj[currentLang()] || obj.en || obj.zh || fallback;
}

// ── State ────────────────────────────────────────────────────────────────
const state = {
  domain: "ai-networking",
  schemas: {},        // name → resolved schema
  records: [],        // all records
  editorialMap: {},   // slug → editorial paper
  visibleRecords: [], // records matching state.domain
  checkedTags: {},
  sortCol: null,
  sortDir: 1,
};

// ── UI build ─────────────────────────────────────────────────────────────
function buildSubtableTabs() {
  const c = document.getElementById("subtableTabs");
  c.innerHTML = AVAILABLE_DOMAINS.map((d) => {
    const sch = state.schemas[d];
    const lbl = getLabel(sch && sch.label, d);
    const cls = d === state.domain ? "subtable-tab active" : "subtable-tab";
    return `<button class="${cls}" data-domain="${escapeHTML(d)}">${escapeHTML(lbl)}</button>`;
  }).join("");
  c.querySelectorAll(".subtable-tab").forEach((btn) => {
    btn.addEventListener("click", () => switchDomain(btn.dataset.domain));
  });
}

function switchDomain(domain) {
  if (!state.schemas[domain]) {
    console.warn("Unknown domain", domain);
    return;
  }
  state.domain = domain;
  state.checkedTags = {};
  state.sortCol = null;
  state.sortDir = 1;
  // Update URL without reloading
  const url = new URL(location.href);
  url.searchParams.set("domain", domain);
  history.replaceState(null, "", url);
  // Update active tab
  document.querySelectorAll(".subtable-tab").forEach((b) => {
    b.classList.toggle("active", b.dataset.domain === domain);
  });
  // Filter records
  state.visibleRecords = state.records.filter((r) => (r.domains || []).includes(domain));
  buildFilterPanel();
  buildTable();
  applyFilters();
}

function fieldsForCurrentDomain() {
  const sch = state.schemas[state.domain];
  // Build column order: title first, then everything else (respecting YAML key order)
  const all = Object.values(sch.fields);
  const titleField = all.find((f) => f.kind === "title");
  const rest = all.filter((f) => f.kind !== "title" && f.kind !== "domains");
  // Domains column intentionally hidden in the comparison table — it's filter-state.
  return titleField ? [titleField, ...rest] : rest;
}

function filterableFields() {
  // Any field with kind "tags" or "list" becomes a filter facet.
  return fieldsForCurrentDomain().filter((f) => f.kind === "tags" || f.kind === "list");
}

function buildFilterPanel() {
  const c = document.getElementById("filterGroups");
  c.innerHTML = "";
  for (const field of filterableFields()) {
    const counts = new Map();
    for (const r of state.visibleRecords) {
      const v = r[field.key];
      const tags = Array.isArray(v) ? v.map(String) : splitMulti(v);
      for (const tag of tags) counts.set(tag, (counts.get(tag) || 0) + 1);
    }
    const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    const grp = document.createElement("div");
    grp.className = "filter-group";
    grp.dataset.field = field.key;
    const tagsHTML = sorted.map(([tag, n]) => `<label class="filter-tag">
      <input type="checkbox" data-field="${field.key}" data-tag="${escapeHTML(tag)}">
      ${tagPill(tag)}
      <span class="tag-count">${n}</span>
    </label>`).join("");
    const lbl = escapeHTML(getLabel(field.label, field.key));
    grp.innerHTML = `
      <div class="filter-group-title">
        ${lbl}
        <span class="filter-group-count">${sorted.length} tags</span>
      </div>
      <div class="filter-group-tags">${tagsHTML}</div>
    `;
    c.appendChild(grp);
  }
  c.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
    cb.addEventListener("change", () => {
      const f = cb.dataset.field;
      const tag = cb.dataset.tag;
      if (!state.checkedTags[f]) state.checkedTags[f] = new Set();
      if (cb.checked) state.checkedTags[f].add(tag);
      else state.checkedTags[f].delete(tag);
      if (state.checkedTags[f].size === 0) delete state.checkedTags[f];
      applyFilters();
    });
  });
}

function buildTable() {
  const table = document.getElementById("paperTable");
  const old = table.querySelector("colgroup");
  if (old) old.remove();
  const cols = fieldsForCurrentDomain();
  // Insert an index column up front.
  const colgroup = document.createElement("colgroup");
  colgroup.innerHTML = `<col style="width:40px">` + cols.map(
    (c) => `<col style="width:${c.width || 150}px">`
  ).join("");
  table.insertBefore(colgroup, table.firstChild);
  table.style.width = (40 + cols.reduce((s, c) => s + (c.width || 150), 0)) + "px";

  const thead = document.getElementById("thead");
  thead.innerHTML = `<tr><th data-col="-1">#</th>` + cols.map(
    (c, i) => `<th data-col="${i}">${escapeHTML(getLabel(c.label, c.key))}</th>`
  ).join("") + `</tr>`;
  thead.querySelectorAll("th").forEach((th) => {
    th.addEventListener("click", () => {
      const i = +th.dataset.col;
      if (i < 0) return; // # column not sortable
      if (state.sortCol === i) state.sortDir = -state.sortDir;
      else { state.sortCol = i; state.sortDir = 1; }
      applyFilters();
    });
  });

  const tbody = document.getElementById("tbody");
  tbody.innerHTML = "";
  state.visibleRecords.forEach((record, idx) => {
    const editorial = state.editorialMap[record.slug];
    const tr = document.createElement("tr");
    tr.dataset.hasDetail = editorial ? "1" : "0";
    tr.dataset.recordIdx = String(idx);
    tr.innerHTML = `<td class="idx-cell"></td>` + cols.map((field) => {
      const cls = (field.kind === "tags" || field.kind === "venue"
                  || field.kind === "affiliations" || field.kind === "list"
                  || field.kind === "domains") ? "tag-cell"
        : field.kind === "title" ? "title-cell"
        : field.kind === "link" ? "link-cell"
        : "text-cell";
      return `<td class="${cls}" data-key="${field.key}">${renderCell(field, record, editorial)}</td>`;
    }).join("");
    tbody.appendChild(tr);
  });
}

function rowMatchesTagFilters(record) {
  for (const [field, required] of Object.entries(state.checkedTags)) {
    const v = record[field];
    const rowTags = new Set(Array.isArray(v) ? v.map(String) : splitMulti(v));
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
  let visible = 0;

  rows.forEach((tr) => {
    const idx = +tr.dataset.recordIdx;
    const record = state.visibleRecords[idx];
    const text = tr.textContent.toLowerCase();
    const inText = !q || text.includes(q);
    const inDetail = !detail
      || (detail === "with" && tr.dataset.hasDetail === "1")
      || (detail === "without" && tr.dataset.hasDetail === "0");
    const inTags = !hasTagFilters || rowMatchesTagFilters(record);
    const v = inText && inDetail && inTags;
    tr.classList.toggle("hidden", !v);
    if (v) visible++;
  });

  if (state.sortCol != null) {
    const cols = fieldsForCurrentDomain();
    const field = cols[state.sortCol];
    if (field) {
      const sorted = rows.map((tr) => {
        const idx = +tr.dataset.recordIdx;
        return { tr, record: state.visibleRecords[idx] };
      }).sort((a, b) => {
        const av = String(pickLang(a.record[field.key]) ?? "");
        const bv = String(pickLang(b.record[field.key]) ?? "");
        const aMeaningful = av && av !== "Not Specified" && av !== "未說明";
        const bMeaningful = bv && bv !== "Not Specified" && bv !== "未說明";
        if (!aMeaningful && bMeaningful) return 1;
        if (aMeaningful && !bMeaningful) return -1;
        if (!aMeaningful && !bMeaningful) return 0;
        return state.sortDir * av.localeCompare(bv, undefined, { numeric: true });
      });
      sorted.forEach(({ tr }) => tbody.appendChild(tr));
      document.querySelectorAll("thead th").forEach((th) => {
        const colIdx = +th.dataset.col;
        th.classList.toggle("sort-asc", colIdx === state.sortCol && state.sortDir === 1);
        th.classList.toggle("sort-desc", colIdx === state.sortCol && state.sortDir === -1);
      });
    }
  }

  let n = 1;
  tbody.querySelectorAll("tr:not(.hidden) td.idx-cell").forEach((td) => { td.textContent = n++; });

  document.getElementById("visibleCount").textContent =
    t(`Showing ${visible} of ${state.visibleRecords.length} papers`,
      `顯示 ${visible} 篇，共 ${state.visibleRecords.length} 篇`);
  document.getElementById("clearFiltersBtn").style.display = hasTagFilters ? "inline-block" : "none";

  const ddCount = state.visibleRecords.filter((p) => state.editorialMap[p.slug]).length;
  document.getElementById("stats").innerHTML =
    `<span>` + t(`<strong>${visible}</strong> visible / <strong>${state.visibleRecords.length}</strong> in subtable`,
                 `<strong>${visible}</strong> 顯示 / <strong>${state.visibleRecords.length}</strong> 此分表`) + `</span>` +
    `<span>` + t(`Deep-dive pages: <strong>${ddCount}</strong>`,
                 `深度頁面：<strong>${ddCount}</strong>`) + `</span>` +
    `<span>` + t(`(${state.records.length} total records)`,
                 `（共 ${state.records.length} 筆記錄）`) + `</span>`;
}

async function init() {
  // Load all known schemas in parallel.
  await Promise.all(AVAILABLE_DOMAINS.map(async (d) => {
    state.schemas[d] = await loadSchema(d);
  }));

  const [extracted, editorial] = await Promise.all([
    fetch("../data/extracted-index.json").then((r) => r.json()),
    fetch("../data/papers-index.json").then((r) => r.json()).catch(() => []),
  ]);
  state.records = extracted;
  state.editorialMap = Object.fromEntries(editorial.map((p) => [p.slug, p]));

  // Pick initial domain from URL or default to first available.
  const urlDomain = new URLSearchParams(location.search).get("domain");
  state.domain = (urlDomain && AVAILABLE_DOMAINS.includes(urlDomain))
    ? urlDomain
    : AVAILABLE_DOMAINS[0];

  buildSubtableTabs();
  state.visibleRecords = state.records.filter((r) => (r.domains || []).includes(state.domain));
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

  document.addEventListener("langchange", (ev) => {
    const l = ev.detail.lang;
    buildSubtableTabs();
    buildFilterPanel();
    buildTable();
    applyFilters();
    document.querySelectorAll(".i18n").forEach((e) => {
      if (e.dataset[l]) e.innerHTML = e.dataset[l];
    });
  });

  document.getElementById("footer").innerHTML =
    `<span class="i18n" data-en="Schema-driven: edit schemas/&lt;domain&gt;.yaml to change columns or canonical tag values. Records at content/extracted/&lt;slug&gt;.json, one paper per file." data-zh="Schema-driven：編輯 schemas/&lt;domain&gt;.yaml 即可變更欄位或 canonical tag 值。記錄位於 content/extracted/&lt;slug&gt;.json，每篇論文一個檔。">Schema-driven: edit schemas/&lt;domain&gt;.yaml to change columns or canonical tag values.</span>`;
}

init().catch((e) => {
  document.getElementById("stats").textContent = `Failed to load: ${e.message}`;
  console.error(e);
});
