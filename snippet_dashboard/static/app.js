"use strict";

/** Dashboard state and DOM interactions for the Snippet Atlas. */
const state = { folder: "./sample_notes", language: "", query: "", grouped: false, snippets: [] };
const elements = {
  folder: document.querySelector("#folder-input"), scan: document.querySelector("#scan-button"),
  search: document.querySelector("#search-input"), list: document.querySelector("#snippet-list"),
  loading: document.querySelector("#loading-state"), empty: document.querySelector("#empty-state"),
  error: document.querySelector("#error-banner"), count: document.querySelector("#result-count"),
  group: document.querySelector("#group-toggle"), theme: document.querySelector("#theme-toggle")
};

function setLoading(visible) {
  elements.loading.hidden = !visible;
  if (visible) { elements.empty.hidden = true; elements.list.replaceChildren(); }
}

function showError(message) { elements.error.textContent = message; elements.error.hidden = false; }
function clearError() { elements.error.hidden = true; elements.error.textContent = ""; }

async function loadDashboard() {
  clearError(); setLoading(true); state.folder = elements.folder.value.trim() || "./sample_notes";
  const params = new URLSearchParams({ folder: state.folder });
  if (state.language) params.set("language", state.language);
  if (state.query) params.set("q", state.query);
  try {
    const [snippetResponse, statsResponse] = await Promise.all([
      fetch(`/api/snippets?${params}`), fetch(`/api/stats?folder=${encodeURIComponent(state.folder)}`)
    ]);
    const snippetData = await snippetResponse.json(); const statsData = await statsResponse.json();
    if (!snippetResponse.ok) throw new Error(snippetData.error || "Could not scan snippets.");
    if (!statsResponse.ok) throw new Error(statsData.error || "Could not load scan stats.");
    state.snippets = snippetData; updateStats(statsData); renderSnippets();
  } catch (error) { elements.list.replaceChildren(); showError(error.message || "Something went wrong."); elements.empty.hidden = true; }
  finally { setLoading(false); if (!elements.error.hidden) elements.loading.hidden = true; }
}

function updateStats(stats) {
  document.querySelector("#stat-files").textContent = stats.files;
  document.querySelector("#stat-snippets").textContent = stats.snippets;
  document.querySelector("#stat-python").textContent = stats.python;
  document.querySelector("#stat-javascript").textContent = stats.javascript;
}

function renderSnippets() {
  elements.list.replaceChildren(); elements.count.textContent = `${state.snippets.length} ${state.snippets.length === 1 ? "snippet" : "snippets"}`;
  elements.empty.hidden = state.snippets.length !== 0;
  if (state.grouped) {
    const files = new Map(); state.snippets.forEach((snippet) => { if (!files.has(snippet.file)) files.set(snippet.file, []); files.get(snippet.file).push(snippet); });
    files.forEach((snippets) => snippets.forEach((snippet, index) => elements.list.append(createCard(snippet, index === 0))));
  } else state.snippets.forEach((snippet, index) => elements.list.append(createCard(snippet, false, index)));
}

function createCard(snippet, grouped, index = 0) {
  const card = document.createElement("article"); card.className = `snippet-card${grouped ? " grouped" : ""}`; card.style.animationDelay = `${Math.min(index, 8) * 35}ms`;
  const header = document.createElement("div"); header.className = "card-header";
  const file = document.createElement("div"); file.className = "file-name"; file.textContent = snippet.file;
  const lines = document.createElement("span"); lines.className = "line-range"; lines.textContent = `Lines ${snippet.start_line}-${snippet.end_line}`; file.append(lines);
  const badge = document.createElement("span"); badge.className = `language-badge ${snippet.language}`; badge.textContent = snippet.language; header.append(file, badge); card.append(header);
  if (snippet.nearest_heading) { const heading = document.createElement("div"); heading.className = "heading-label"; heading.textContent = `↳ ${snippet.nearest_heading}`; card.append(heading); }
  const codeWrap = document.createElement("pre"); codeWrap.className = "code-wrap"; const code = document.createElement("code"); highlightCode(code, snippet.code, snippet.language); codeWrap.append(code); card.append(codeWrap);
  const actions = document.createElement("div"); actions.className = "card-actions"; const status = document.createElement("span"); status.className = "copy-status"; status.setAttribute("aria-live", "polite");
  const copy = document.createElement("button"); copy.className = "card-button"; copy.type = "button"; copy.textContent = "Copy"; copy.addEventListener("click", () => copySnippet(snippet.code, copy, status));
  const run = document.createElement("button"); run.className = "card-button run-button"; run.type = "button"; run.textContent = "Run (mock)"; run.addEventListener("click", () => runSnippet(snippet, card, run)); actions.append(status, copy, run); card.append(actions); return card;
}

function highlightCode(container, source, language) {
  const tokenPattern = language === "python" ? /(#[^\n]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b(?:def|return|if|else|elif|for|in|import|from|class|True|False|None|and|or|not|print)\b)/g : /(\/\/[^\n]*|`(?:\\.|[^`\\])*`|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b(?:const|let|var|function|return|if|else|for|while|true|false|new|await|async)\b)/g;
  let position = 0;
  for (const match of source.matchAll(tokenPattern)) { if (match.index > position) container.append(document.createTextNode(source.slice(position, match.index))); const token = document.createElement("span"); token.className = match[0].startsWith("#") || match[0].startsWith("//") ? "token-comment" : /^["'`]/.test(match[0]) ? "token-string" : "token-keyword"; token.textContent = match[0]; container.append(token); position = match.index + match[0].length; }
  if (position < source.length) container.append(document.createTextNode(source.slice(position)));
}

async function copySnippet(source, button, status) { try { await navigator.clipboard.writeText(source); status.textContent = "Copied!"; button.textContent = "Copied"; setTimeout(() => { status.textContent = ""; button.textContent = "Copy"; }, 1600); } catch { status.textContent = "Copy unavailable"; } }

async function runSnippet(snippet, card, button) {
  button.disabled = true; button.textContent = "Checking..."; const oldTerminal = card.querySelector(".terminal"); if (oldTerminal) oldTerminal.remove();
  const terminal = document.createElement("pre"); terminal.className = "terminal"; terminal.textContent = "MOCK OUTPUT: checking syntax..."; card.append(terminal);
  try { const response = await fetch("/api/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ snippet_id: snippet.id, folder: state.folder }) }); const result = await response.json(); if (!response.ok) throw new Error(result.error || "Mock run failed."); terminal.className = `terminal ${result.syntax_ok ? "ok" : "bad"}`; terminal.textContent = `${result.syntax_ok ? "SYNTAX OK" : `SYNTAX ERROR${result.line ? ` · line ${result.line}` : ""}`}\n${result.error || "No syntax errors found."}\n\n${result.warnings.join("\n")}\n${result.stdout.length ? `\n${result.stdout.join("\n")}` : "\n<no simulated output>"}`; } catch (error) { terminal.className = "terminal bad"; terminal.textContent = error.message || "Mock run failed."; } finally { button.disabled = false; button.textContent = "Run (mock)"; }
}

function setTheme(light) { document.body.classList.toggle("light", light); elements.theme.textContent = light ? "☾" : "☼"; elements.theme.setAttribute("aria-label", light ? "Switch to dark theme" : "Switch to light theme"); try { localStorage.setItem("snippet-theme", light ? "light" : "dark"); } catch { /* Storage can be unavailable in privacy modes. */ } }

elements.scan.addEventListener("click", loadDashboard); elements.folder.addEventListener("keydown", (event) => { if (event.key === "Enter") loadDashboard(); });
let searchTimer; elements.search.addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => { state.query = elements.search.value.trim(); loadDashboard(); }, 280); });
document.querySelectorAll(".filter-chip").forEach((chip) => chip.addEventListener("click", () => { document.querySelectorAll(".filter-chip").forEach((item) => item.classList.remove("active")); chip.classList.add("active"); state.language = chip.dataset.language; loadDashboard(); }));
elements.group.addEventListener("change", () => { state.grouped = elements.group.checked; renderSnippets(); }); elements.theme.addEventListener("click", () => setTheme(!document.body.classList.contains("light")));
try { setTheme(localStorage.getItem("snippet-theme") === "light"); } catch { setTheme(false); } loadDashboard();