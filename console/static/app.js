/* Register console front end. State comes from /api/state; every write is one POST that appends a change set block. */
let S = null, view = "outstanding", open = null, form = null;
const $ = (s, el = document) => el.querySelector(s);
const KINDS = ["REQ", "DEC", "LIM", "RSK", "OI", "CR"];
const COLOR = k => `--c:var(--${k.toLowerCase()});--cb:var(--${k.toLowerCase()}-bg)`;
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const madeBy = () => $("#made-by").value.trim();
const toast = m => { const t = $("#toast"); t.textContent = m; t.hidden = false; setTimeout(() => t.hidden = true, 2600); };

async function load(retries = 20) {
  try {
    return await loadOnce();
  } catch (e) {
    // the server is restarting, or briefly unreachable; keep the page alive and come back
    banner(retries > 0 ? "Reconnecting to the console…" : "Console unreachable. Start it with 'make up', then reload.");
    if (retries > 0) { await new Promise(r => setTimeout(r, 700)); return load(retries - 1); }
    throw e;
  }
}
function banner(msg) {
  let b = document.getElementById("conn-banner");
  if (!msg) { if (b) b.remove(); return; }
  if (!b) { b = document.createElement("div"); b.id = "conn-banner"; document.body.prepend(b); }
  b.textContent = msg;
}
/* Baselining until the freeze; live once the registers hold items. */
function stage() { return S.baseline?.present && !S.baseline.frozen && !S.items.length ? "baseline" : "live"; }
let viewChosen = false;
async function loadOnce() {
  S = await (await fetch("/api/state")).json();
  S.byId = Object.fromEntries(S.items.map(i => [i.id, i]));
  S.baseline = await (await fetch("/api/baseline")).json();
  $("#eng-name").textContent = S.engagement.name + (S.engagement.current ? " · " + S.engagement.current : "");
  const st = stage();
  $("#stage").textContent = st === "baseline" ? "Baselining" : S.baseline?.frozen ? `Live · baseline frozen ${S.baseline.frozen.on}` : "Live";
  $("#stage").className = "stage " + st;
  $("#banner").innerHTML = st === "baseline"
    ? "<strong>Baselining.</strong> The pulled pages are candidates and nothing is written to the registers until you freeze. Verdicts and edits are kept in the baseline folder and can be changed until then."
    : S.engagement.writes === "direct"
    ? "This view is the registers <strong>as they stand</strong>: every move, edit or new item writes the item file, and git holds the history."
    : "This view is the registers <strong>as proposed</strong>: the item files plus every change set not yet applied. Every move, edit or new item appends a block to your session's change set, which the ingester applies.";
  const direct = S.engagement.writes === "direct";
  $("#close-session").hidden = direct;
  if (!viewChosen) { view = st === "baseline" ? "baseline" : "outstanding"; viewChosen = true; }
  const mine = S.change_sets.filter(c => !c.closed && !c.applied && c.header["Made by"] === madeBy());
  $("#session-info").textContent = direct ? "writes in place" : mine.length ? `${mine[0].id}, ${mine[0].blocks.length} block(s) this session` : "no open change set";
  banner("");
  render();
}
const said = r => r.changeSet ? `${r.changeSet} item ${r.item}` : `${r.item} written`;
async function post(url, body) {
  const r = await fetch(url, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({...body, madeBy: madeBy()})});
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || "failed");
  return j;
}

/* ---------- navigation ---------- */
function render() {
  const counts = k => S.items.filter(i => i.kind === k).length;
  const pendingN = S.change_sets.filter(c => !c.applied).reduce((n, c) => n + c.blocks.length, 0);
  const st = stage(), B = S.baseline;
  const link = (v, label, n, style = "") => `<a href="#" data-v="${v}" style="${style}" class="${view === v ? "on" : ""}">${label}${n !== undefined ? ` <span class="n">${n}</span>` : ""}</a>`;
  const group = (label, links) => `<div class="grp"><span class="grp-l">${label}</span>${links.join("")}</div>`;
  $("#nav").innerHTML = [
    B?.present ? group("Source", [link("baseline", "Baseline", B.frozen ? "frozen" : B.candidates.filter(c => !c.verdict).length, "--c:var(--cs)")]) : "",
    group("Meeting", [link("outstanding", "Outstanding"), link("triage", "Work through", queue().length), link("report", "Meeting report"), link("slt", "Weekly SLT report")]),
    group("Registers", KINDS.map(k => link(k, S.model.names[k] + "s", counts(k), COLOR(k)))),
    S.engagement.writes === "direct" && !S.change_sets.length ? "" : group("Changes", [link("cs", "Change sets", pendingN, "--c:var(--cs)")]),
    `<div class="grp"><a href="guide.html" data-ext="1">Guide</a></div>`,
  ].join("");
  if (st === "baseline") $("#nav").querySelectorAll(".grp").forEach((g, n) => { if (n === 1) g.classList.add("dim"); });
  $("#nav").querySelectorAll("a:not([data-ext])").forEach(a => a.onclick = e => { e.preventDefault(); view = a.dataset.v; open = null; form = null; render(); });
  const m = $("#main");
  document.body.classList.toggle("print-mode", view === "report" || view === "slt");
  if (view === "outstanding") m.innerHTML = outstanding();
  else if (view === "triage") { m.innerHTML = triage(); wire(m); }
  else if (view === "report") m.innerHTML = report();
  else if (view === "slt") m.innerHTML = slt();
  else if (view === "baseline") { m.innerHTML = baselineView(); wireBaseline(m); }
  else if (view === "cs") m.innerHTML = changeSets();
  else m.innerHTML = register(view);
  m.querySelectorAll("[data-open]").forEach(el => el.onclick = e => { e.preventDefault(); openItem(el.dataset.open); });
  m.querySelectorAll("[data-new]").forEach(el => el.onclick = () => { open = null; form = {mode: "create", kind: el.dataset.new, fields: {}, links: []}; renderDetail(); });
  $("#copy-md", m)?.addEventListener("click", () => { navigator.clipboard.writeText(view === "slt" ? sltMarkdown() : reportMarkdown()).then(() => toast("Report copied as markdown")); });
  $("#print", m)?.addEventListener("click", () => window.print());
  m.querySelectorAll("[data-tq]").forEach(el => el.onclick = () => { triageMove(el.dataset.tq); });
  m.querySelectorAll("[data-rk]").forEach(el => el.onclick = () => { riskKind = el.dataset.rk; render(); });
  $("#flt-scope", m)?.addEventListener("change", e => { scopeFilter = e.target.value; render(); });
  m.querySelectorAll("[data-raw]").forEach(el => el.onclick = async e => { e.preventDefault(); const t = await (await fetch("/api/change-set/" + el.dataset.raw)).text(); $("#raw-" + el.dataset.raw).innerHTML = `<pre>${esc(t)}</pre>`; });
  // Work through carries the open item in the queue panel itself, so the drawer stays hidden there.
  // Calling renderDetail() in that view would call back into render() and recurse.
  if (view === "triage") { const d = $("#detail"); if (d) d.hidden = true; }
  else renderDetail();
}
const head = (title, sub = "", actions = "") => `<div class="toolbar"><div><h2>${title}</h2>${sub ? `<div class="small muted">${sub}</div>` : ""}</div>${actions ? `<div class="actions">${actions}</div>` : ""}</div>`;
const idTag = i => `<a href="#" data-open="${i.id}" class="id" style="${COLOR(i.kind)}">${i.id}</a>${i.provisional ? '<span class="tag new">pending id</span>' : ""}`;
const pendTag = i => i.pending.length && !i.provisional ? `<span class="tag">${i.pending.length} pending</span>` : "";
const row = (i, cols) => `<tr class="row ${i.pending.length ? "pending" : ""}" data-open="${i.id}"><td>${idTag(i)}</td><td class="t">${esc(i.title)}${pendTag(i)}</td>${cols.map(c => `<td class="${c === "status" ? "st" : ""}">${esc(Array.isArray(i[c]) ? i[c].join("; ") : i[c])}</td>`).join("")}</tr>`;
const table = (items, cols) => `<div style="overflow-x:auto"><table><tr><th>ID</th><th>Title</th>${cols.map(c => `<th>${esc(S.model.labels[c] || c)}</th>`).join("")}</tr>${items.map(i => row(i, cols)).join("") || `<tr><td colspan="${cols.length + 2}" class="muted">none</td></tr>`}</table></div>`;

let riskKind = "";
let scopeFilter = "";
function register(k) {
  let items = S.items.filter(i => i.kind === k);
  const scopes = S.engagement.scopes || [];
  let chips = "";
  if (k === "RSK") {
    if (riskKind) items = items.filter(i => i["risk-kind"] === riskKind);
    chips = `<div class="moves" style="--c:var(--rsk)">${["", "Risk", "Assumption", "Dependency"].map(v => `<button data-rk="${v}" class="${riskKind === v ? "on" : ""}">${v || "All"}</button>`).join("")}</div>`;
  }
  if (scopes.length) {
    if (scopeFilter) items = items.filter(i => i.scope === scopeFilter);
    chips += `<select id="flt-scope"><option value="">All scopes</option>${scopes.map(s => `<option ${s === scopeFilter ? "selected" : ""}>${esc(s)}</option>`).join("")}</select>`;
  }
  const cols = ["status", ...S.model.short[k].filter(f => f !== "owner" && (f !== "scope" || scopes.length)), "owner", "raised-on", "closed-on"];
  return head(`${S.model.names[k]}s`, `${items.length} item${items.length === 1 ? "" : "s"}. Click a row to open it.`, `${chips}<button class="primary" data-new="${k}">New ${S.model.names[k].toLowerCase()}</button>`) + table(items, cols);
}

function outstanding() {
  const it = S.items, term = k => S.model.terminal[k];
  const old14 = i => { const d = parseDate(i["raised-on"]); return d && (new Date() - d) / 864e5 > 14; };
  const later = i => i.phase && S.engagement.current && S.engagement.phases.indexOf(i.phase) > S.engagement.phases.indexOf(S.engagement.current);
  const defect = i => !i.owner || (i.kind === "OI" && !i["next action"]);
  const sec = (t, items, cols, note = "") => `<div class="section"><h3>${t}</h3>${note ? `<p class="small muted">${note}</p>` : ""}${table(items, cols)}</div>`;
  const oi = it.filter(i => i.kind === "OI" && i.status !== "Closed").sort((a, b) => (a.owner || "").localeCompare(b.owner || "") || (a.due || "z").localeCompare(b.due || "z"));
  const lim = it.filter(i => i.kind === "LIM" && ["Identified", "Under assessment"].includes(i.status));
  const rsk = it.filter(i => i.kind === "RSK" && ["Identified", "Mitigating"].includes(i.status) && (i.impact === "H" || (parseDate(i.due) && parseDate(i.due) < new Date())));
  const cr = it.filter(i => i.kind === "CR" && ["For approval", "Proposed", "Submitted"].includes(i.status)).sort((a, b) => (a.status === "For approval" ? 0 : 1) - (b.status === "For approval" ? 0 : 1));
  const dec = it.filter(i => i.kind === "DEC" && i.status === "Proposed" && old14(i));
  const req = it.filter(i => i.kind === "REQ" && i.status === "Draft" && old14(i) && !later(i));
  const defects = it.filter(i => !term(i.kind).includes(i.status) && defect(i));
  const deferred = it.filter(i => (i.kind === "CR" && i.status === "Deferred") || (i.kind === "REQ" && later(i)));
  const missing = (S.integrity?.suggestions || []).filter(s => s.level === "fail"), bad = S.integrity?.failures || [];
  const gaps = missing.length || bad.length
    ? `<div class="note">Register gaps: ${missing.length} missing support${missing.length === 1 ? "" : "s"}, ${bad.length} integrity failure${bad.length === 1 ? "" : "s"}. ${[...new Set(missing.map(s => s.id))].slice(0, 12).map(id => `<a href="#" data-open="${esc(id)}" class="id" style="${COLOR(S.byId[id]?.kind || "cs")}">${esc(id)}</a>`).join(" ")}</div>`
    : "";
  return head("Outstanding", "Model section 8, in order. Amber marks an item with a pending change in an unapplied change set.") + gaps + `
    <div class="stat"><div><b>${oi.length}</b><span>open items</span></div><div><b>${lim.length}</b><span>limitations to disposition</span></div><div><b>${cr.filter(c => c.status === "For approval").length}</b><span>CRs with the business</span></div><div><b class="${defects.length ? "req" : ""}">${defects.length}</b><span>register defects</span></div></div>
    ${sec("1. Open items not Closed", oi, ["status", "owner", "next action", "due"])}
    ${sec("2. Limitations in Identified or Under assessment", lim, ["status", "owner", "raised-on"])}
    ${sec("3. Risks with Impact H or past review", rsk, ["status", "likelihood", "impact", "due"])}
    ${sec("4. Change requests: For approval first", cr, ["status", "estimate", "approved-by", "owner"])}
    ${sec("5. Decisions in Proposed older than 14 days", dec, ["status", "owner", "raised-on"])}
    ${sec("6. Requirements in Draft older than 14 days", req, ["status", "moscow", "owner", "raised-on"])}
    ${sec("Register defects", defects, ["status", "owner", "next action"], "Non-terminal items with no owner, or open items with no next action. A defect in the register, not a discussion point.")}
    ${sec("Later-phase view", deferred, ["status", "phase", "owner"], "Reviewed at phase planning, not in the weekly meeting.")}`;
}

function changeSets() {
  const cs = [...S.change_sets].reverse();
  return head("Change sets", "One file per session under <code>change-sets/</code>. The ingester applies them; the console only appends.") +
    (cs.map(c => `<div class="cs"><div class="hd"><div><span class="id" style="--c:var(--cs);--cb:var(--cs-bg)">${c.id}</span> &nbsp;${esc(c.header["Made by"] || "")} · ${esc(c.header["Session date"] || "")}
      ${c.applied ? '<span class="tag new">applied</span>' : c.closed ? '<span class="tag">closed, awaiting ingester</span>' : '<span class="tag">open</span>'}</div>
      <a href="#" data-raw="${c.id}" class="small">show file</a></div>
      ${c.blocks.map(b => `<div class="blk"><b>Item ${b.n}</b> · ${b.kind} · target <code>${esc(b.fields.Target)}</code> ${b.fields.From ? `· <span class="st">${esc(b.fields.From)} → ${esc(b.fields.Status)}</span>` : b.fields.Status ? `· <span class="st">${esc(b.fields.Status)}</span>` : ""}
        <div class="f">${Object.entries(b.fields).filter(([k]) => !["Target", "Grade", "Verdict", "From", "Based on", "Gist", "Status"].includes(k)).map(([k, v]) => `${esc(k)}: ${esc(v)}`).join(" · ")}${b.links.length ? " · links: " + esc(b.links.join("; ")) : ""}</div>
        <div class="small muted">${esc(b.fields.Gist || "")} · ${esc(b.evidence.join("; "))}</div></div>`).join("") || '<div class="blk muted">no blocks yet</div>'}
      <div id="raw-${c.id}"></div></div>`).join("") || '<p class="muted">No change sets yet. Open an item and make a move.</p>');
}

/* ---------- detail drawer ---------- */
function openItem(id) { open = id; form = null; if (view === "triage") { const q = queue(); const at = q.findIndex(e => e.item.id === id); if (at >= 0) { setPos(at); render(); return; } view = S.byId[id]?.kind || "outstanding"; render(); return; } renderDetail(); }
function renderDetail() {
  const d = $("#detail");
  if (!open && !form) { d.hidden = true; return; }
  d.hidden = false;
  if (form && form.mode === "create") { d.innerHTML = createForm(); wire(d); return; }
  const i = S.byId[open]; if (!i) { d.hidden = true; return; }
  if (view === "triage") { d.hidden = true; render(); return; }
  d.innerHTML = itemPanel(i, true);
  wire(d);
}
function itemPanel(i, closable) {
  const k = i.kind, changed = new Set();
  i.pending.forEach(p => { const b = S.change_sets.find(c => c.id === p.cs)?.blocks.find(b => b.n === p.n); if (b) Object.keys(b.fields).forEach(f => changed.add(f.toLowerCase())); });
  const fld = (key, v) => `<div class="field ${changed.has(key) ? "changed" : ""}"><label>${esc(S.model.labels[key] || key)}</label><div class="v">${esc(v) || '<span class="muted">—</span>'}</div></div>`;
  const moves = (S.model.transitions[k] || {})[i.status] || [];
  return `${closable ? '<button class="ghost close" id="close-detail">×</button>' : ""}
    <span class="eyebrow">${S.model.names[k]}</span>
    <h2>${idTag(i)} ${esc(i.title)}</h2>
    <div class="st">${esc(i.status)}${S.model.terminal[k].includes(i.status) ? " (terminal)" : ""}</div>
    ${i.pending.map(p => `<div class="pend"><b>${p.cs} item ${p.n}</b>${p.from ? ` · ${esc(p.from)} → ${esc(p.status)}` : ""}<br>${esc(p.gist)}</div>`).join("")}
    ${supportsPanel(i)}
    ${moves.length ? `<h3>Move to</h3><div class="moves" style="${COLOR(k)}">${moves.map(m => `<button data-move="${m}" class="${form?.to === m ? "on" : ""}">${m}</button>`).join("")}</div>` : ""}
    ${form && form.mode === "move" ? moveForm(i) : ""}
    ${S.model.short[k].filter(f => f !== "scope" || (S.engagement.scopes || []).length).map(f => fld(f, i[f])).join("")}
    <div class="field ${changed.has("links") ? "changed" : ""}"><label>Links</label><ul class="links">${i.links.map(l => { const m = l.match(/([A-Z]+-\d{4}(?:\.\d+)?)/); return `<li>${m && S.byId[m[1]] ? esc(l.replace(m[1], "")) + `<a href="#" data-open="${m[1]}">${m[1]}</a>` : esc(l)}</li>`; }).join("") || '<li class="muted">none</li>'}</ul></div>
    ${S.model.long[k].map(f => fld(f, i[f])).join("")}
    ${fld("raised-on", i["raised-on"])}${fld("closed-on", i["closed-on"])}
    ${i.history?.length ? `<div class="field"><label>History</label><ul class="small muted hist">${i.history.map(h => `<li>${esc(h)}</li>`).join("")}</ul></div>` : ""}
    <div class="small muted">updated ${esc(i.updated || "")}</div>
    ${form && form.mode === "edit" ? editForm(i) : `<div class="form"><button id="edit-btn">Edit fields</button></div>`}`;
}
/* What section 9 and the SUPPORTS table say this item still needs. Accepting writes the offer as a new
   provisional item and links the two; dismissing keeps the reason beside the register. */
/* Link existing: the records of the offered type the trigger could point at instead of creating one.
   Ranked matches share a title word; the datalist holds every record of that type for the rest. */
function linkRow(s, all, attr) {
  const opt = c => `<option value="${esc(c.id)}">${esc(c.title)}</option>`;
  return `<div class="small muted" style="margin:6px 0 2px">Or link an existing <span class="id" style="${COLOR(s.kind)}">${s.kind}</span>:</div>
    <div class="moves" style="${COLOR(s.kind)}">${s.matches.map(m => `<button ${attr}="${esc(s.key)}" data-target="${esc(m.id)}" title="${esc(m.id)} · ${esc(m.status)}${m.page ? " · " + esc(m.page) : ""}">${esc(m.title)}</button>`).join("")}
    <input list="lk-${esc(s.key)}" data-lkin="${esc(s.key)}" placeholder="${s.matches.length ? "or another id" : "id or title"}" style="width:220px"><datalist id="lk-${esc(s.key)}">${all.map(opt).join("")}</datalist><button class="ghost" ${attr}="${esc(s.key)}">Link</button></div>`;
}
function supportsPanel(i) {
  const R = S.integrity || {suggestions: [], prompts: [], failures: []};
  const mine = R.suggestions.filter(s => s.id === i.id), prompts = R.prompts.filter(p => p.id === i.id);
  if (!mine.length && !prompts.length) return "";
  return `<div class="supports"><h3>Supports needed</h3>
    ${mine.map(s => `<div class="blk"><span class="id" style="${COLOR(s.kind)}">${s.kind}</span> ${esc(s.fields.title || "untitled")} <span class="small muted">${esc(s.rule)} · ${s.level === "fail" ? "needed" : "suggested"}${s.needsOwner ? " · owner needed" : ""}</span>
      <div class="moves" style="${COLOR(s.kind)}"><button data-sacc="${esc(s.key)}">Accept</button> <button class="ghost" data-sdis="${esc(s.key)}" data-rule="${esc(s.rule)}">Dismiss</button></div>
      ${linkRow(s, S.items.filter(x => x.kind === s.kind && x.id !== i.id), "data-slink")}
      ${form?.mode === "support" && form.key === s.key ? supportForm(s) : ""}</div>`).join("")}
    ${prompts.map(p => `<div class="blk small muted">${esc(p.rule)}: ${esc(p.text)}</div>`).join("")}</div>`;
}
function supportForm(s) {
  if (form.dismiss) return `<div class="form"><h3>Dismiss ${esc(s.rule)}</h3>
    <div class="field"><label>Reason to dismiss</label><input data-f="__reason" value="${esc(form.fields.__reason || "")}"></div>${tail()}</div>`;
  const keys = Object.keys(s.fields); if (!keys.includes("title")) keys.unshift("title");
  if (s.needsOwner && !keys.includes("owner")) keys.splice(1, 0, "owner");
  return `<div class="form"><h3>Accept the implied ${esc(S.model.names[s.kind] || s.kind)}</h3>
    ${keys.map(k => input(k, form.fields[k] ?? s.fields[k] ?? "", k === "title" || (k === "owner" && s.needsOwner), s.kind)).join("")}
    <p class="small muted">It is written in ${esc(s.status)} and linked: this item gets <code>${esc(s.link)}&lt;new&gt;</code>${s.reverse ? `, the new one gets <code>${esc(s.reverse)}</code>` : ""}.</p>${tail()}</div>`;
}
function wire(d) {
  $("#close-detail", d)?.addEventListener("click", () => { open = null; form = null; renderDetail(); });
  d.querySelectorAll("[data-sacc]").forEach(el => el.onclick = () => { form = {mode: "support", key: el.dataset.sacc, fields: {}, links: []}; renderDetail(); });
  d.querySelectorAll("[data-slink]").forEach(el => el.onclick = async () => {
    const key = el.dataset.slink, target = el.dataset.target || d.querySelector(`[data-lkin="${key}"]`)?.value.trim();
    if (!target) return toast("Pick the record to link");
    try { const r = await post("/api/support/link", {id: open, key, target, evidence: ""}); toast(`${said(r)}: linked to ${target}`); await load(); renderDetail(); } catch (e) { toast(e.message); }
  });
  d.querySelectorAll("[data-sdis]").forEach(el => el.onclick = () => { form = {mode: "support", key: el.dataset.sdis, rule: el.dataset.rule, dismiss: true, fields: {}, links: []}; renderDetail(); });
  d.querySelectorAll("[data-son]").forEach(el => el.onchange = () => { const s = form.supports[+el.dataset.son]; s.pick = el.checked; s.on = sOn(s); renderDetail(); });
  d.querySelectorAll("[data-sedit]").forEach(el => el.oninput = () => { const n = +el.dataset.sedit, s = form.supports[n]; s.edits[el.dataset.sk] = el.value; s.on = sOn(s); const cb = d.querySelector(`[data-son="${n}"]`); if (cb) cb.checked = s.on; });
  d.querySelectorAll("[data-open]").forEach(el => el.onclick = e => { e.preventDefault(); openItem(el.dataset.open); });
  d.querySelectorAll("[data-move]").forEach(el => el.onclick = () => { form = {mode: "move", to: el.dataset.move, fields: {}, links: [], supports: null}; renderDetail(); refreshSupports(true); });
  $("#edit-btn", d)?.addEventListener("click", () => { form = {mode: "edit", fields: {}, links: []}; renderDetail(); });
  $("#cancel", d)?.addEventListener("click", () => { form = null; renderDetail(); });
  $("#submit", d)?.addEventListener("click", submit);
  d.querySelectorAll("[data-tq]").forEach(el => el.onclick = () => triageMove(el.dataset.tq));
  d.querySelectorAll("[data-f]").forEach(el => el.oninput = () => form.fields[el.dataset.f] = el.value);
  $("#new-link", d)?.addEventListener("input", e => form.linkText = e.target.value);
  $("#new-link-word", d)?.addEventListener("change", e => form.linkWord = e.target.value);
  $("#evidence", d)?.addEventListener("input", e => form.evidence = e.target.value);
  $("#gist", d)?.addEventListener("input", e => form.gist = e.target.value);
  // last, so the handlers above have already written the field, the link word and the link text
  if (form?.mode === "move") {
    d.querySelectorAll("[data-f]").forEach(el => el.addEventListener("change", () => refreshSupports()));
    $("#new-link", d)?.addEventListener("change", () => refreshSupports());
    $("#new-link-word", d)?.addEventListener("change", () => refreshSupports());
  }
}
const stkList = (id = "stk") => `<datalist id="${id}">${S.stakeholders.map(s => `<option value="${esc(s.name)}">${esc(s.role)}</option>`).join("")}<option value="Joint"><option value="Vendor: "></datalist>`;
/* The link the reviewer has half typed counts as part of the move: the preview and the submit both read it. */
const pendingLinks = () => {
  const links = [...(form.links || [])];
  if (form.linkText && form.linkText.trim()) links.push(`${form.linkWord || Object.keys(S.model.linkWords[form.kind || S.byId[open].kind])[0]} ${form.linkText.trim()}`);
  return links;
};
const input = (key, val = "", req = false, kind = null) => {
  const c = (key === "impact" && kind !== "RSK") ? null : S.model.choices[key];
  const lab = `<label>${esc(S.model.labels[key] || key)}${req ? ' <span class="req">required</span>' : ""}</label>`;
  if (c) return `<div class="field">${lab}<select data-f="${key}"><option value="">—</option>${c.map(o => `<option ${o === val ? "selected" : ""}>${o}</option>`).join("")}</select></div>`;
  if (key === "owner" || key === "approved-by") return `<div class="field">${lab}<input data-f="${key}" list="stk" value="${esc(val)}">${stkList()}</div>`;
  if (key === "scope") return (S.engagement.scopes || []).length ? `<div class="field">${lab}<select data-f="scope"><option value="">—</option>${(S.engagement.scopes || []).map(s => `<option ${s === val ? "selected" : ""}>${esc(s)}</option>`).join("")}</select></div>` : "";
  if (key === "phase") return `<div class="field">${lab}<select data-f="phase"><option value="">—</option>${S.engagement.phases.map(p => `<option ${p === val ? "selected" : ""}>${p}</option>`).join("")}</select></div>`;
  if (S.model.long.REQ.concat(S.model.long.DEC, S.model.long.LIM, S.model.long.RSK, S.model.long.OI, S.model.long.CR).includes(key)) return `<div class="field">${lab}<textarea data-f="${key}">${esc(val)}</textarea></div>`;
  return `<div class="field">${lab}<input data-f="${key}" value="${esc(val)}"></div>`;
};
const linkAdder = (k) => { const words = Object.keys(S.model.linkWords[k] || {}); return `<div class="field"><label>Add link</label><div style="display:flex;gap:6px"><select id="new-link-word" style="width:45%">${words.map(w => `<option ${form.linkWord === w ? "selected" : ""}>${w}</option>`).join("")}</select><input id="new-link" placeholder="${S.engagement.writes === "direct" ? "REQ-0014" : "REQ-0014, or item 2 for a block in this session's change set"}" value="${esc(form.linkText || "")}"></div></div>`; };
const tail = () => `<div class="field"><label>Evidence (meeting, document or note)</label><input id="evidence" value="${esc(form.evidence || "")}" placeholder="e.g. stakeholder forum 11 Sep"></div>
  <div class="field"><label>Why, in one sentence (Gist)</label><input id="gist" value="${esc(form.gist || "")}"></div>
  <div class="err" id="err"></div><div class="actions"><button class="primary" id="submit">${form.mode === "support" && form.dismiss ? "Dismiss" : (S.engagement.writes === "direct" ? "Write" : "Append to change set")}</button><button id="cancel">Cancel</button></div>`;

function moveForm(i) {
  const k = i.kind, req = (S.model.required[k] || {})[form.to] || [];
  const fields = req.filter(r => !r.startsWith("link:")).map(r => r === "options" ? "options" : r);
  const links = req.filter(r => r.startsWith("link:")).map(r => r.slice(5));
  if (!form.linkWord && links.length) form.linkWord = links.find(w => !i.links.some(l => l.toLowerCase().startsWith(w))) || links[0];
  const ticked = (form.supports || []).some(s => s.on);
  const held = i.links.some(l => links.some(w => l.toLowerCase().startsWith(w)));
  return `<div class="form"><h3>${esc(i.status)} → ${esc(form.to)}</h3>
    ${fields.map(f => input(f, form.fields[f] ?? i[f] ?? "", true, k)).join("")}
    ${links.length ? `<p class="small muted">This move needs a link: ${links.map(esc).join(", ")}. ${held ? "Already present, or add another below." : ticked ? "Already present, or provided by a ticked support below, or add another." : "Add it below, or create the record first from its register and link <code>item n</code>."}</p>` : ""}
    ${supportsChooser()}
    ${linkAdder(k)}${tail()}</div>`;
}
/* What the chosen move implies, previewed by the server. Ticked offers are written to the change set
   before the move and linked to it; one that needs an owner stays unticked until an owner is typed. */
function supportsChooser() {
  if (form.supports === null) return '<p class="small muted">Checking what this move implies…</p>';
  if (!form.supports.length) return "";
  const names = form.supports.some(s => s.needsOwner) ? stkList("stk-s") : "";
  const one = (s, n) => {
    const gaps = sGaps(s), hint = sReady(s) ? "" : ` · fill the ${gaps.filter(g => !sVal(s, g)).map(g => (S.model.labels[g] || g).toLowerCase()).join(" and ")} to include`;
    return `<label class="dup" title="${esc(s.check)} · ${esc(sVal(s, "source"))}"><input type="checkbox" data-son="${n}" ${s.on ? "checked" : ""}> <span class="id" style="${COLOR(s.kind)}">${s.kind}</span> ${esc(sVal(s, "title") || "untitled")} <span class="small muted">${esc(s.rule)} · ${s.level === "fail" ? "needed" : "suggested"}${hint}</span></label>
      ${gaps.map(g => `<input data-sedit="${n}" data-sk="${g}" ${g === "owner" ? 'list="stk-s"' : ""} placeholder="${esc(S.model.labels[g] || g)}" value="${esc(s.edits[g] || "")}">`).join("")}`;
  };
  return `<div class="supports">${names}<h3>This move implies</h3>${form.supports.map(one).join("")}
    <p class="small muted">Ticked items are written to the change set before the move and linked to it.</p></div>`;
}
/* An offer is only worth writing once every field it carries has a value. The engine leaves a field
   the model requires on create in the offer with an empty value, so each gap gets its own box here.
   A fail-level offer is ticked as soon as it is ready, unless the reviewer has said otherwise. */
const sVal = (s, k) => String(s.edits[k] ?? s.fields[k] ?? "").trim();
const sGaps = s => {
  const keys = Object.keys(s.fields);
  if (!keys.includes("title")) keys.unshift("title");
  if (s.needsOwner && !keys.includes("owner")) keys.splice(1, 0, "owner");
  return keys.filter(k => !sVal(s, k));
};
const sReady = s => !sGaps(s).some(g => !sVal(s, g));
const sOn = s => (s.pick === undefined ? s.level === "fail" : s.pick) && sReady(s);
/* The offers depend on the fields and links being typed into the move, so ask the server again as they
   change. Replies can land out of order, so only the latest request may install a list: every ask takes
   the next number on this form and a reply whose number has been overtaken is dropped. The reviewer's
   own ticks and edits survive; the panel is only redrawn when the implication moved. */
async function refreshSupports(first) {
  if (!form || form.mode !== "move") return;
  const f = form, to = f.to, on = open, was = f.supports, prev = Object.fromEntries((was || []).map(s => [s.key, s]));
  const seq = f.seq = (f.seq || 0) + 1;
  const current = () => form === f && form.mode === "move" && form.to === to && open === on && f.seq === seq;
  const sig = list => (list || []).map(s => `${s.key}|${sVal(s, "title")}|${s.on}`).join("~");
  let r;
  try { r = await post("/api/supports", {id: on, to, fields: f.fields, links: pendingLinks()}); }
  catch (e) { if (first && current()) { f.supports = []; renderDetail(); } toast(e.message); return; }
  if (!current()) return;
  const next = r.suggestions.map(s => { const p = prev[s.key], e = {...s, edits: p ? p.edits : {}, pick: p ? p.pick : undefined}; e.on = sOn(e); return e; });
  if (was && sig(was) === sig(next)) { f.supports = next; return; }
  const a = document.activeElement, key = a && a.dataset ? a.dataset.f : null, at = a && a.selectionStart;
  f.supports = next;
  renderDetail();
  if (key) { const el = $(`#detail [data-f="${CSS.escape(key)}"]`); if (el) { el.focus(); try { el.setSelectionRange(at, at); } catch {} } }
}
function editForm(i) {
  const k = i.kind;
  return `<div class="form"><h3>Edit fields</h3>${["title", ...S.model.short[k], ...S.model.long[k]].map(f => input(f, form.fields[f] ?? i[f] ?? "", false, k)).join("")}${linkAdder(k)}${tail()}</div>`;
}
function createForm() {
  const k = form.kind, req = S.model.create[k];
  if (!form.linkWord) form.linkWord = (req.find(r => r.startsWith("link:")) || "link:").slice(5) || Object.keys(S.model.linkWords[k])[0];
  return `<button class="ghost close" id="close-detail">×</button><span class="eyebrow">New</span><h2>${S.model.names[k]}</h2>
    <div class="field"><label>Starts in</label><select data-f="__status">${[S.model.first[k], ...((S.model.transitions[k] || {})[S.model.first[k]] || [])].map(st => `<option ${form.fields.__status === st ? "selected" : ""}>${st}</option>`).join("")}</select></div><div class="form">
    ${["title", ...S.model.short[k], ...S.model.long[k]].filter(f => f !== "notes").map(f => input(f, form.fields[f] ?? "", req.includes(f), k)).join("")}
    ${req.some(r => r.startsWith("link:")) ? `<p class="small muted">Needs a link: ${req.filter(r => r.startsWith("link:")).map(r => esc(r.slice(5))).join(", ")}.</p>` : ""}
    ${linkAdder(k)}${tail()}</div>`;
}
async function submit() {
  const err = $("#err");
  try {
    if (!madeBy()) throw new Error("Type your name in Made by first.");
    const body = {fields: form.fields, links: pendingLinks(), evidence: form.evidence || "", gist: form.gist || ""};
    let r;
    if (form.mode === "support") {
      if (form.dismiss) { if (!form.fields.__reason) throw new Error("Give a reason to dismiss."); r = await post("/api/support/dismiss", {id: open, key: form.key, rule: form.rule, reason: form.fields.__reason}); toast("Dismissed; kept in supports-dismissed.json"); }
      else {
        const {__reason, ...fields} = form.fields, s = (S.integrity?.suggestions || []).find(x => x.key === form.key);
        if (!String(fields.title ?? s?.fields.title ?? "").trim()) throw new Error("Give the implied item a title.");
        r = await post("/api/support/accept", {id: open, key: form.key, fields, evidence: form.evidence || ""}); toast(`${said(r)}${r.changeSet ? " appended" : ""} and linked`);
      }
      form = null; await load(); return;
    }
    if (form.mode === "create") { const {__status, ...rest} = form.fields; r = await post("/api/create", {...body, fields: rest, kind: form.kind, status: __status || ""}); }
    else if (form.mode === "move") {
      const chosen = (form.supports || []).filter(s => s.on);
      if (chosen.some(s => !sReady(s))) throw new Error("Fill the missing field on every ticked support, or untick it.");
      r = await post("/api/transition", {...body, id: open, to: form.to, supports: chosen.map(s => ({key: s.key, fields: s.edits}))});
    }
    else r = await post("/api/edit", {...body, id: open});
    toast(r.changeSet ? `${said(r)} appended` : said(r));
    form = null; await load();
    if (view === "triage") { const q = queue(); if (!q.some(e => e.item.id === open)) { open = null; } render(); }
  } catch (e) { err.textContent = e.message; }
}
function parseDate(s) { const m = /^(\d{1,2}) (\w+) (\d{4})/.exec(s || ""); if (!m) return null; const mi = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"].indexOf(m[2]); return mi < 0 ? null : new Date(+m[3], mi, +m[1]); }

/* ---------- boot ---------- */
function setTheme(t) {
  try { t === "system" ? localStorage.removeItem("theme") : localStorage.setItem("theme", t); } catch {}
  if (t === "system") delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = t;
  document.querySelectorAll("#theme button").forEach(b => b.classList.toggle("on", b.dataset.theme === t));
}
document.querySelectorAll("#theme button").forEach(b => b.onclick = () => setTheme(b.dataset.theme));
setTheme((() => { try { return localStorage.getItem("theme") || "system"; } catch { return "system"; } })());
try { $("#made-by").value = localStorage.getItem("madeBy") || ""; } catch {}
$("#made-by").addEventListener("change", () => { try { localStorage.setItem("madeBy", madeBy()); } catch {} load(); });
$("#close-session").addEventListener("click", async () => { try { const r = await post("/api/close-session", {}); toast(`${r.changeSet} closed for the ingester`); load(); } catch (e) { toast(e.message); } });
load();


/* ---------- workflow mode: the triage queue ---------- */
function queue() {
  const it = S.items, term = k => S.model.terminal[k];
  const dt = s => parseDate(s), now = new Date(), old14 = i => dt(i["raised-on"]) && (now - dt(i["raised-on"])) / 864e5 > 14;
  const later = i => i.phase && S.engagement.current && S.engagement.phases.indexOf(i.phase) > S.engagement.phases.indexOf(S.engagement.current);
  let parked = []; try { parked = JSON.parse(localStorage.getItem("parked") || "[]"); } catch {}
  const q = [];
  const add = (i, why, rank) => { if (!q.some(e => e.item.id === i.id)) q.push({item: i, why, rank}); };
  it.filter(i => !term(i.kind).includes(i.status) && !i.provisional).forEach(i => {
    if (!i.owner) add(i, "No owner. Every live item needs one person who answers for it.", 0);
    else if (i.kind === "OI" && !i["next action"]) add(i, "Open item with no next action.", 0);
  });
  it.filter(i => i.kind === "LIM" && i.status === "Identified").forEach(i => add(i, "Limitation not yet under assessment. Raise the assessing open item, or withdraw it.", 1));
  it.filter(i => i.kind === "LIM" && i.status === "Under assessment" && old14(i)).forEach(i => add(i, "Under assessment for more than 14 days. Choose an option or give the open item a new due date.", 1));
  it.filter(i => i.kind === "OI" && i.status !== "Closed").sort((a, b) => (dt(a.due) || 9e15) - (dt(b.due) || 9e15)).forEach(i => add(i, dt(i.due) && dt(i.due) < now ? "Open item past its due date." : "Open item. Set the next action and due, or close it into a record.", 2));
  it.filter(i => i.kind === "RSK" && ["Identified", "Mitigating"].includes(i.status) && (!dt(i.due) || dt(i.due) < now)).forEach(i => { const w = (i["risk-kind"] || "Risk").toLowerCase(); add(i, i.due ? `${i["risk-kind"] || "Risk"} past its review date. ${w === "assumption" ? "Verify it, or retire it as confirmed." : w === "dependency" ? "Chase it, or retire it as delivered." : "Update likelihood, impact and mitigation, or retire it."}` : `${i["risk-kind"] || "Risk"} with no review date.`, 3); });
  it.filter(i => i.kind === "CR" && i.status === "For approval").forEach(i => add(i, "Change request with the business. Record the decision when it comes.", 4));
  it.filter(i => i.kind === "CR" && i.status === "Proposed").forEach(i => add(i, "Change request being shaped. Reason, chosen option and estimate get it to the board.", 4));
  it.filter(i => i.kind === "DEC" && i.status === "Proposed" && old14(i)).forEach(i => add(i, "Decision proposed more than 14 days ago. Accept, reject, or give it an open item.", 5));
  it.filter(i => i.kind === "REQ" && i.status === "Draft" && old14(i) && !later(i)).forEach(i => add(i, "Requirement in Draft for more than 14 days. Agree it with its owner, or withdraw it.", 6));
  it.filter(i => i.kind === "REQ" && i.status === "Agreed" && !later(i)).forEach(i => add(i, "Agreed but not yet designed. Does a design section cover it?", 7));
  q.sort((a, b) => a.rank - b.rank);
  return q.filter(e => !parked.includes(e.item.id)).concat(q.filter(e => parked.includes(e.item.id)).map(e => ({...e, parked: true})));
}
function getPos() { try { return +(localStorage.getItem("triagePos") || 0); } catch { return 0; } }
function setPos(n) { try { localStorage.setItem("triagePos", n); } catch {} }
function triageMove(what) {
  const q = queue(); let p = getPos();
  if (what === "next") p = Math.min(q.length - 1, p + 1);
  if (what === "prev") p = Math.max(0, p - 1);
  if (what === "park" || what === "unpark") { let parked = []; try { parked = JSON.parse(localStorage.getItem("parked") || "[]"); } catch {}
    const id = q[p]?.item.id; if (id) { parked = what === "park" ? [...new Set([...parked, id])] : parked.filter(x => x !== id); try { localStorage.setItem("parked", JSON.stringify(parked)); } catch {} } }
  if (what === "reset") p = 0;
  setPos(p); form = null; render();
}
function triage() {
  const q = queue();
  if (!q.length) return head("Work through", "Nothing needs a hand. The register is clean.");
  let p = Math.min(getPos(), q.length - 1); setPos(p);
  const e = q[p], i = e.item; open = i.id;
  const related = i.links.map(l => l.match(/([A-Z]+-\d{4}(?:\.\d+)?)/)?.[1]).filter(id => id && S.byId[id]).map(id => S.byId[id]);
  const back = S.items.filter(o => o.id !== i.id && o.links.some(l => l.includes(i.id)));
  const ctx = [...related, ...back.filter(b => !related.includes(b))];
  const done = q.filter((x, n) => n < p).length;
  return `<div class="toolbar"><div><h2>Work through</h2><div class="small muted">${p + 1} of ${q.length}${e.parked ? " · parked" : ""} · one item per screen with its context and only its legal moves</div></div>
    <div class="moves"><button data-tq="prev" title="k">← Previous</button><button data-tq="next" title="j">Next →</button>${e.parked ? '<button data-tq="unpark">Unpark</button>' : '<button data-tq="park" title="p">Park for later</button>'}<button class="ghost" data-tq="reset">Start over</button></div></div>
    <div class="progress"><div style="width:${Math.round(100 * p / q.length)}%"></div></div>
    <div class="triage">
      <div class="tq-main"><div class="why">${esc(e.why)}</div>${itemPanel(i, false)}</div>
      <div class="tq-side"><h3>Around it</h3>${ctx.length ? ctx.map(c => `<div class="ctx"><a href="#" data-open="${c.id}" class="id" style="${COLOR(c.kind)}">${c.id}</a> <span class="st">${esc(c.status)}</span><div>${esc(c.title)}</div>${c.kind === "OI" && c["next action"] ? `<div class="small muted">${esc(c["next action"])}</div>` : ""}</div>`).join("") : '<p class="small muted">No linked items.</p>'}
      <p class="small muted" style="margin-top:14px">Keys: j next, k previous, p park.</p></div>
    </div>`;
}
document.addEventListener("keydown", e => {
  if (view !== "triage" || ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) return;
  if (e.key === "j") triageMove("next"); if (e.key === "k") triageMove("prev"); if (e.key === "p") triageMove("park");
});

/* ---------- report mode ---------- */
function reportData() {
  const it = S.items, dt = parseDate, now = new Date();
  const later = i => i.phase && S.engagement.current && S.engagement.phases.indexOf(i.phase) > S.engagement.phases.indexOf(S.engagement.current);
  const byOwner = {};
  it.filter(i => i.kind === "OI" && i.status !== "Closed").forEach(i => (byOwner[i.owner || "Unowned"] ||= []).push(i));
  return {
    decisions: it.filter(i => (i.kind === "DEC" && i.status === "Proposed") || (i.kind === "LIM" && i.status === "Under assessment")),
    crs: it.filter(i => i.kind === "CR" && ["For approval", "Proposed", "Submitted"].includes(i.status)),
    risks: it.filter(i => i.kind === "RSK" && ["Identified", "Mitigating"].includes(i.status) && (i.impact === "H" || (dt(i.due) && dt(i.due) < now))),
    assumptions: it.filter(i => i.kind === "RSK" && i["risk-kind"] === "Assumption" && ["Identified", "Mitigating"].includes(i.status)),
    dependencies: it.filter(i => i.kind === "RSK" && i["risk-kind"] === "Dependency" && ["Identified", "Mitigating"].includes(i.status)),
    byOwner, blocked: it.filter(i => i.kind === "OI" && i.status === "Blocked"),
    newLims: it.filter(i => i.kind === "LIM" && i.status === "Identified"),
    drafts: it.filter(i => i.kind === "REQ" && i.status === "Draft" && !later(i)),
    pending: S.change_sets.filter(c => !c.applied).flatMap(c => c.blocks.map(b => ({cs: c.id, by: c.header["Made by"], b}))),
    defects: it.filter(i => !S.model.terminal[i.kind].includes(i.status) && (!i.owner || (i.kind === "OI" && !i["next action"]))),
  };
}
function report() {
  const r = reportData();
  const li = (i, extra = "") => `<li><span class="id" style="${COLOR(i.kind)}">${i.id}</span> ${esc(i.title)} <span class="st">${esc(i.status)}</span>${extra}</li>`;
  return `<div class="toolbar no-print"><div><h2>Meeting report</h2><div class="small muted">One printable page for the weekly meeting.</div></div><div class="actions"><button id="copy-md">Copy as markdown</button><button id="print">Print</button></div></div>
    <div class="report">
    <div class="rhead"><span class="eyebrow">${esc(S.engagement.name)} · ${esc(S.engagement.current)}</span><h1>Register report, ${esc(S.today)}</h1><p class="small muted">Registers as proposed, including ${r.pending.length} pending change(s) not yet applied by the ingester.</p></div>
    <div class="stat"><div><b>${r.decisions.length}</b><span>calls needed</span></div><div><b>${r.crs.filter(c => c.status === "For approval").length}</b><span>CRs awaiting approval</span></div><div><b>${Object.values(r.byOwner).flat().length}</b><span>open items</span></div><div><b>${r.risks.length}</b><span>risks to review</span></div><div><b class="${r.defects.length ? "req" : ""}">${r.defects.length}</b><span>register defects</span></div></div>
    <h3>Calls needed at this meeting</h3><ul class="rl">${r.decisions.map(i => li(i, i.kind === "LIM" && i.options ? `<div class="small">${esc(i.options).replace(/\n/g, "<br>")}</div>` : i.rationale ? `<div class="small muted">${esc(i.rationale)}</div>` : "")).join("") || "<li class='muted'>none</li>"}</ul>
    <h3>Change requests</h3><ul class="rl">${r.crs.map(i => li(i, `<div class="small">${esc(i.reason || "")}</div><div class="small muted">${i.estimate ? "Estimate: " + esc(i.estimate) : "No estimate yet"}${i["approved-by"] ? " · approved by " + esc(i["approved-by"]) : ""}</div>`)).join("") || "<li class='muted'>none</li>"}</ul>
    <h3>Risks to review</h3><ul class="rl">${r.risks.map(i => li(i, ` <span class="small">L ${esc(i.likelihood)} · I ${esc(i.impact)} · review ${esc(i.due || "unset")}</span>`)).join("") || "<li class='muted'>none</li>"}</ul>
    <h3>Dependencies</h3><ul class="rl">${r.dependencies.map(i => li(i, `<div class="small">${esc(i.trigger || "")}</div><div class="small muted">${esc(i.owner)}${i.due ? " · review " + esc(i.due) : ""}</div>`)).join("") || "<li class='muted'>none</li>"}</ul>
    <h3>Assumptions</h3><ul class="rl">${r.assumptions.map(i => li(i, `<div class="small">${i.mitigation ? "Verify: " + esc(i.mitigation) : "Not yet being verified"}</div><div class="small muted">${esc(i.owner)}${i.due ? " · review " + esc(i.due) : ""}</div>`)).join("") || "<li class='muted'>none</li>"}</ul>
    <h3>New limitations</h3><ul class="rl">${r.newLims.map(i => li(i, `<div class="small muted">${esc(i.impact || "")}</div>`)).join("") || "<li class='muted'>none</li>"}</ul>
    <h3>Actions by owner</h3>${Object.entries(r.byOwner).sort().map(([o, items]) => `<h4>${esc(o)}</h4><ul class="rl">${items.map(i => li(i, `<div class="small">${esc(i["next action"] || "no next action")}${i.due ? " · due " + esc(i.due) : ""}</div>`)).join("")}</ul>`).join("")}
    <h3>Requirements still in Draft</h3><ul class="rl">${r.drafts.map(i => li(i, ` <span class="small muted">${esc(i.moscow)} · ${esc(i.owner)}</span>`)).join("") || "<li class='muted'>none</li>"}</ul>
    <h3>Pending changes since last ingestion</h3><ul class="rl">${r.pending.map(p => `<li><span class="small">${p.cs} · ${esc(p.by)}</span> ${esc(p.b.kind)} ${esc(p.b.fields.Target)}${p.b.fields.From ? ` ${esc(p.b.fields.From)} → ${esc(p.b.fields.Status)}` : p.b.fields.Title ? ": " + esc(p.b.fields.Title) : ""} <span class="small muted">${esc(p.b.fields.Gist || "")}</span></li>`).join("") || "<li class='muted'>none</li>"}</ul>
    ${r.defects.length ? `<h3>Register defects</h3><ul class="rl">${r.defects.map(i => li(i, ` <span class="small req">${!i.owner ? "no owner" : "no next action"}</span>`)).join("")}</ul>` : ""}
    </div>`;
}
function reportMarkdown() {
  const r = reportData(), L = [];
  const line = (i, extra = "") => `- **${i.id}** ${i.title} _(${i.status})_${extra}`;
  L.push(`# Register report, ${S.today}`, ``, `${S.engagement.name} · ${S.engagement.current}. Registers as proposed, ${r.pending.length} pending change(s).`, ``);
  L.push(`## Calls needed`, ...(r.decisions.map(i => line(i, i.kind === "LIM" && i.options ? "\n" + i.options.split("\n").map(o => "    " + o).join("\n") : "")) || []), ``);
  L.push(`## Change requests`, ...r.crs.map(i => line(i, `\n    ${i.reason || ""}\n    ${i.estimate ? "Estimate: " + i.estimate : "No estimate yet"}`)), ``);
  L.push(`## Risks to review`, ...r.risks.map(i => line(i, ` L ${i.likelihood} I ${i.impact}, review ${i.due || "unset"}`)), ``);
  L.push(`## Dependencies`, ...r.dependencies.map(i => line(i, ` ${i.trigger || ""} (${i.owner})`)), ``);
  L.push(`## Assumptions`, ...r.assumptions.map(i => line(i, i.mitigation ? ` verify: ${i.mitigation}` : " not yet being verified")), ``);
  L.push(`## New limitations`, ...r.newLims.map(i => line(i, i.impact ? `\n    ${i.impact}` : "")), ``);
  L.push(`## Actions by owner`); Object.entries(r.byOwner).sort().forEach(([o, items]) => { L.push(`### ${o}`, ...items.map(i => line(i, ` ${i["next action"] || "no next action"}${i.due ? ", due " + i.due : ""}`)), ``); });
  L.push(`## Requirements still in Draft`, ...r.drafts.map(i => line(i, ` ${i.moscow}, ${i.owner}`)), ``);
  L.push(`## Pending changes`, ...r.pending.map(p => `- ${p.cs} (${p.by}): ${p.b.kind} ${p.b.fields.Target}${p.b.fields.From ? ` ${p.b.fields.From} → ${p.b.fields.Status}` : p.b.fields.Title ? ": " + p.b.fields.Title : ""}. ${p.b.fields.Gist || ""}`), ``);
  if (r.defects.length) L.push(`## Register defects`, ...r.defects.map(i => line(i, !i.owner ? " no owner" : " no next action")));
  return L.join("\n");
}


/* ---------- weekly SLT report ----------
   Progress for senior leadership: where the requirements stand, what moved this week, what needs their
   call, and what is at risk. Built from the item dates (raised-on, closed-on, updated) over a seven-day
   window, so it needs no history beyond the files. */
function sltData() {
  const it = S.items, now = new Date(), dt = parseDate, term = k => S.model.terminal[k];
  const week = new Date(now - 7 * 864e5);
  const inWeek = d => d && d >= week && d <= now;
  const later = i => i.phase && S.engagement.current && S.engagement.phases.indexOf(i.phase) > S.engagement.phases.indexOf(S.engagement.current);
  const byState = k => { const o = {}; S.model.states[k].forEach(st => o[st] = 0); it.filter(i => i.kind === k).forEach(i => { o[i.status] = (o[i.status] || 0) + 1; }); return o; };
  const rows = KINDS.map(k => { const all = it.filter(i => i.kind === k); return {k, name: S.model.names[k] + "s", total: all.length,
    open: all.filter(i => !term(k).includes(i.status)).length, raised: all.filter(i => inWeek(dt(i["raised-on"]))).length,
    closed: all.filter(i => inWeek(dt(i["closed-on"]))).length, moved: all.filter(i => inWeek(dt(i.updated)) && !inWeek(dt(i["raised-on"]))).length}; });
  const req = it.filter(i => i.kind === "REQ" && !later(i));
  const reqStates = byState("REQ");
  const delivered = req.filter(i => ["Delivered", "Verified"].includes(i.status)).length, designed = req.filter(i => ["Designed", "Delivered", "Verified"].includes(i.status)).length;
  return {
    weekEnding: S.today, rows, reqStates, reqTotal: req.length, delivered, designed,
    calls: it.filter(i => i.kind === "CR" && i.status === "For approval"),
    shaping: it.filter(i => i.kind === "CR" && ["Proposed", "Submitted"].includes(i.status)),
    decisionsOverdue: it.filter(i => i.kind === "DEC" && i.status === "Proposed" && dt(i["raised-on"]) && (now - dt(i["raised-on"])) / 864e5 > 14),
    limsOpen: it.filter(i => i.kind === "LIM" && ["Identified", "Under assessment"].includes(i.status)),
    risksHigh: it.filter(i => i.kind === "RSK" && ["Identified", "Mitigating"].includes(i.status) && i.impact === "H"),
    realised: it.filter(i => i.kind === "RSK" && i.status === "Realised" && inWeek(dt(i["closed-on"]) || dt(i.updated))),
    depsLate: it.filter(i => i.kind === "RSK" && i["risk-kind"] === "Dependency" && ["Identified", "Mitigating"].includes(i.status) && dt(i.due) && dt(i.due) < now),
    blocked: it.filter(i => i.kind === "OI" && i.status === "Blocked"),
    oiOpen: it.filter(i => i.kind === "OI" && i.status !== "Closed").length,
    oiLate: it.filter(i => i.kind === "OI" && i.status !== "Closed" && dt(i.due) && dt(i.due) < now).length,
    movedItems: it.filter(i => inWeek(dt(i.updated)) || inWeek(dt(i["raised-on"])) || inWeek(dt(i["closed-on"]))).sort((a, b) => a.kind.localeCompare(b.kind) || a.id.localeCompare(b.id)),
    pending: S.change_sets.filter(c => !c.applied).reduce((n, c) => n + c.blocks.length, 0),
    unowned: it.filter(i => !term(i.kind).includes(i.status) && !i.owner).length,
    gaps: (() => { const o = {}; (S.integrity?.suggestions || []).filter(s => s.level === "fail").forEach(s => o[s.rule] = (o[s.rule] || 0) + 1); (S.integrity?.failures || []).forEach(f => o[f.rule] = (o[f.rule] || 0) + 1); return o; })(),
  };
}
function slt() {
  const r = sltData();
  const more = arr => arr.length > 10 ? `<li class="muted small">and ${arr.length - 10} more in the register</li>` : "";
  const li = (i, extra = "") => `<li><span class="id" style="${COLOR(i.kind)}">${i.id}</span> ${esc(i.title)} <span class="st">${esc(i.status)}</span>${extra}</li>`;
  const bar = Object.entries(r.reqStates).filter(([st]) => st !== "Withdrawn").map(([st, n]) => n ? `<div class="seg" style="flex:${n}" title="${st}: ${n}"><span>${st} ${n}</span></div>` : "").join("");
  return `<div class="toolbar no-print"><div><h2>Weekly SLT report</h2><div class="small muted">Progress and calls needed, for the leadership team. Seven-day window ending today.</div></div><div class="actions"><button id="copy-md">Copy as markdown</button><button id="print">Print</button></div></div>
    <div class="report">
    <div class="rhead"><span class="eyebrow">${esc(S.engagement.name)} · ${esc(S.engagement.current)}</span><h1>Weekly report, week ending ${esc(r.weekEnding)}</h1></div>
    <div class="stat"><div><b>${r.delivered}/${r.reqTotal}</b><span>requirements delivered</span></div><div><b>${r.designed}/${r.reqTotal}</b><span>requirements designed</span></div><div><b class="${r.calls.length ? "req" : ""}">${r.calls.length}</b><span>change requests awaiting approval</span></div><div><b class="${r.risksHigh.length ? "req" : ""}">${r.risksHigh.length}</b><span>high-impact risks open</span></div><div><b>${r.oiOpen}</b><span>open items${r.oiLate ? `, ${r.oiLate} past due` : ""}</span></div></div>
    <h3>Requirement progress</h3><div class="pbar">${bar || '<div class="muted small">no requirements in this phase</div>'}</div>
    <h3>Movement this week</h3>
    <div style="overflow-x:auto"><table><tr><th>Register</th><th>Total</th><th>Open</th><th>Raised this week</th><th>Moved this week</th><th>Closed this week</th></tr>
    ${r.rows.map(x => `<tr><td>${x.name}</td><td>${x.total}</td><td>${x.open}</td><td>${x.raised || ""}</td><td>${x.moved || ""}</td><td>${x.closed || ""}</td></tr>`).join("")}</table></div>
    <h3>Calls needed from leadership</h3><ul class="rl">${r.calls.map(i => li(i, `<div class="small">${esc(i.reason || "")}</div><div class="small muted">${i.estimate ? "Estimate: " + esc(i.estimate) : "No estimate yet"}${i.owner ? " · " + esc(i.owner) : ""}</div>`)).join("") || "<li class='muted'>none</li>"}</ul>
    ${r.decisionsOverdue.length ? `<h4>Decisions waiting more than two weeks</h4><ul class="rl">${r.decisionsOverdue.map(i => li(i, `<div class="small muted">${esc(i.owner)} · raised ${esc(i["raised-on"])}</div>`)).join("")}</ul>` : ""}
    <h3>Risks and dependencies</h3>
    ${r.realised.length ? `<h4>Realised this week</h4><ul class="rl">${r.realised.map(i => li(i, `<div class="small">${esc(i.impact ? "Impact " + i.impact : "")}${i.mitigation ? " · " + esc(i.mitigation) : ""}</div>`)).join("")}</ul>` : ""}
    <h4>High impact, open</h4><ul class="rl">${r.risksHigh.map(i => li(i, ` <span class="small">${esc(i["risk-kind"] || "Risk")} · L ${esc(i.likelihood)} · ${esc(i.owner)}${i.due ? " · review " + esc(i.due) : ""}</span>${i.mitigation ? `<div class="small muted">${esc(i.mitigation)}</div>` : ""}`)).join("") || "<li class='muted'>none</li>"}</ul>
    ${r.depsLate.length ? `<h4>Dependencies past their date</h4><ul class="rl">${r.depsLate.map(i => li(i, ` <span class="small muted">${esc(i.owner)} · due ${esc(i.due)}</span>`)).join("")}</ul>` : ""}
    <h3>Change requests being shaped <span class="small muted">${r.shaping.length}</span></h3><ul class="rl">${r.shaping.slice(0, 10).map(i => li(i, ` <span class="small muted">${i.estimate ? esc(i.estimate) : "no estimate yet"}${i["implemented-by"] ? " · " + esc(i["implemented-by"]) : ""}</span>`)).join("") || "<li class='muted'>none</li>"}${more(r.shaping)}</ul>
    <h3>Limitations still open <span class="small muted">${r.limsOpen.length}</span></h3><ul class="rl">${r.limsOpen.slice(0, 10).map(i => li(i, i.options ? `<div class="small">${esc(i.options).replace(/\n/g, "<br>")}</div>` : i.impact ? `<div class="small muted">${esc(i.impact)}</div>` : "")).join("") || "<li class='muted'>none</li>"}${more(r.limsOpen)}</ul>
    ${r.blocked.length ? `<h3>Blocked</h3><ul class="rl">${r.blocked.map(i => li(i, `<div class="small">${esc(i["next action"] || "")}</div><div class="small muted">${esc(i.owner)}</div>`)).join("")}</ul>` : ""}
    <h3>What changed this week</h3><ul class="rl">${r.movedItems.map(i => li(i, ` <span class="small muted">${parseDate(i["closed-on"]) && parseDate(i["closed-on"]) >= new Date(Date.now() - 7 * 864e5) ? "closed" : parseDate(i["raised-on"]) && parseDate(i["raised-on"]) >= new Date(Date.now() - 7 * 864e5) ? "new" : "updated"} ${esc(i.updated || i["raised-on"] || "")}</span>`)).join("") || "<li class='muted'>nothing recorded in the last seven days</li>"}</ul>
    ${Object.keys(r.gaps).length ? `<h3>Register gaps</h3><p class="small">${Object.entries(r.gaps).map(([k, n]) => `${esc(k)}: ${n}`).join(" · ")}</p><p class="small muted">Supports the model expects and the registers do not yet hold, plus integrity failures. Each one is a record to write.</p>` : ""}
    <p class="small muted">Registers as proposed, including ${r.pending} pending change(s) not yet applied by the ingester.${r.unowned ? ` ${r.unowned} live item(s) have no owner.` : ""}</p>
    </div>`;
}
function sltMarkdown() {
  const r = sltData(), L = [];
  const line = (i, extra = "") => `- **${i.id}** ${i.title} _(${i.status})_${extra}`;
  L.push(`# Weekly report, week ending ${r.weekEnding}`, ``, `${S.engagement.name} · ${S.engagement.current}`, ``);
  L.push(`Requirements delivered ${r.delivered}/${r.reqTotal}, designed ${r.designed}/${r.reqTotal}. Change requests awaiting approval: ${r.calls.length}. High-impact risks open: ${r.risksHigh.length}. Open items: ${r.oiOpen}${r.oiLate ? `, ${r.oiLate} past due` : ""}.`, ``);
  L.push(`## Requirement progress`, ...Object.entries(r.reqStates).map(([st, n]) => `- ${st}: ${n}`), ``);
  L.push(`## Movement this week`, ``, `| Register | Total | Open | Raised | Moved | Closed |`, `|---|---|---|---|---|---|`, ...r.rows.map(x => `| ${x.name} | ${x.total} | ${x.open} | ${x.raised} | ${x.moved} | ${x.closed} |`), ``);
  L.push(`## Calls needed from leadership`, ...(r.calls.map(i => line(i, `\n    ${i.reason || ""}\n    ${i.estimate ? "Estimate: " + i.estimate : "No estimate yet"}`)).length ? r.calls.map(i => line(i, `\n    ${i.reason || ""}\n    ${i.estimate ? "Estimate: " + i.estimate : "No estimate yet"}`)) : ["- none"]), ``);
  if (r.decisionsOverdue.length) L.push(`### Decisions waiting more than two weeks`, ...r.decisionsOverdue.map(i => line(i, ` ${i.owner}, raised ${i["raised-on"]}`)), ``);
  L.push(`## Risks and dependencies`);
  if (r.realised.length) L.push(`### Realised this week`, ...r.realised.map(i => line(i)));
  L.push(`### High impact, open`, ...(r.risksHigh.length ? r.risksHigh.map(i => line(i, ` ${i["risk-kind"] || "Risk"}, L ${i.likelihood}, ${i.owner}${i.mitigation ? ". " + i.mitigation : ""}`)) : ["- none"]));
  if (r.depsLate.length) L.push(`### Dependencies past their date`, ...r.depsLate.map(i => line(i, ` ${i.owner}, due ${i.due}`)));
  const cap = arr => arr.length > 10 ? [`- and ${arr.length - 10} more in the register`] : [];
  L.push(``, `## Change requests being shaped (${r.shaping.length})`, ...(r.shaping.length ? r.shaping.slice(0, 10).map(i => line(i, ` ${i.estimate || "no estimate yet"}`)) : ["- none"]), ...cap(r.shaping), ``);
  L.push(`## Limitations still open (${r.limsOpen.length})`, ...(r.limsOpen.length ? r.limsOpen.slice(0, 10).map(i => line(i, i.options ? "\n" + i.options.split("\n").map(o => "    " + o).join("\n") : "")) : ["- none"]), ...cap(r.limsOpen), ``);
  if (r.blocked.length) L.push(`## Blocked`, ...r.blocked.map(i => line(i, ` ${i["next action"] || ""} (${i.owner})`)), ``);
  L.push(`## What changed this week`, ...(r.movedItems.length ? r.movedItems.map(i => line(i, ` ${i.updated || i["raised-on"] || ""}`)) : ["- nothing recorded in the last seven days"]), ``);
  if (Object.keys(r.gaps).length) L.push(`## Register gaps`, Object.entries(r.gaps).map(([k, n]) => `${k}: ${n}`).join(" · "), ``);
  L.push(`_Registers as proposed, ${r.pending} pending change(s) not yet applied._`);
  return L.join("\n");
}

/* ---------- baseline mode ---------- */
let BF = {kind: "", page: "", verdict: "", q: "", sel: new Set(), reason: "", tab: "rows", edit: null, confirmFreeze: false, pos: 0, help: false, sedit: null, sfields: {}};
function baselineView() {
  const B = S.baseline, cs = B.candidates;
  const hasScopes = (S.engagement.scopes || []).length > 0;
  const f = cs.filter(c => (!BF.kind || c.kind === BF.kind) && (!BF.page || c.page === BF.page) && (BF.verdict === "" ? true : BF.verdict === "none" ? !c.verdict : c.verdict === BF.verdict) && (!BF.q || (c.title + " " + c.description).toLowerCase().includes(BF.q.toLowerCase())));
  f.sort((a, b) => (a.verdict ? 1 : 0) - (b.verdict ? 1 : 0) || (b.inferred ? 1 : 0) - (a.inferred ? 1 : 0));
  const n = v => cs.filter(c => c.verdict === v).length;
  const byId = Object.fromEntries(cs.map(c => [c.id, c]));
  // a group with one undecided row left holds no duplicate decision; only suggest where two or more remain
  const clusters = B.clusters.filter(g => { const und = g.filter(id => !byId[id]?.verdict).length; return und > 1 || (und === 1 && g.some(id => byId[id]?.verdict === "Accept")); });
  const opt = (arr, cur, blank) => `<option value="">${blank}</option>` + arr.map(x => `<option ${x === cur ? "selected" : ""}>${esc(x)}</option>`).join("");
  const todo = cs.filter(c => !c.verdict).length;
  return `<div class="toolbar"><div><h2>Baseline</h2><div class="small muted">${cs.length} candidates from ${B.pages.length} page(s) · ${n("Accept")} accepted · ${n("Merge")} merged · ${n("Reject")} rejected · ${n("Discard")} discarded · <b>${todo} to go</b>${B.dismissed ? ` · ${B.dismissed} group(s) called not duplicates` : ""}</div></div>
    <div class="actions">${B.frozen ? `<span class="small muted">Frozen ${esc(B.frozen.on)} by ${esc(B.frozen.by)}</span>` : BF.confirmFreeze ? `<span class="small muted">Writes ${n("Accept")} items into the registers and ends baselining. </span><button id="bl-freeze-go" class="primary">Yes, freeze</button> <button id="bl-freeze-no" class="ghost">Not yet</button>` : `<button id="bl-freeze" class="primary" title="Write the accepted set as the registers' first items. Runs once, only into empty registers.">Freeze baseline</button>`}</div></div>
    ${B.skipped?.length ? `<div class="small muted" style="margin:-6px 0 10px">${B.skipped.length} page(s) treated as views and producing no candidates: ${B.skipped.map(p => `${esc(p)} <a href="#" data-unskip="${esc(p)}" class="muted">restore</a>`).join(" · ")}</div>` : ""}
    ${B.frozen ? "" : `<details class="how" ${BF.help ? "open" : ""}><summary>How to work through this</summary><ol>
      <li><b>Drop the pages that are views.</b> Filter by page. A summary, outstanding or conventions page restates rows that are already on a register page. Choose it and press <i>Treat as a view</i>; it produces no candidates from then on, on every pull.</li>
      <li><b>Resolve the duplicates tab.</b> Untick any row that is not the same item, then <i>This one leads</i> on the one to keep. The rest fold into it. Wrong group: <i>Not duplicates</i>.</li>
      <li><b>Pass through each register page</b> on the Row by row tab: one row at a time, keys <kbd>a</kbd> accept, <kbd>r</kbd> reject with the chosen reason, <kbd>x</kbd> discard, <kbd>e</kbd> edit, <kbd>j</kbd>/<kbd>k</kbd> next and previous.</li>
      <li><b>Fill the missing supports.</b> Every accepted row whose state implies another record, a decision behind an accepted limitation, a change request behind one marked Change requested, the open item that carries a draft, is offered here prefilled. Accept, edit then accept, link a record already in the set, or dismiss with a reason. A limitation the source calls Accepted with nothing behind it can instead be sent back to Under assessment. The freeze waits until this list is empty of failures.</li>
      <li><b>Fix fields in bulk</b> on the Candidates tab where a page has a pattern: no owner, wrong MoSCoW, wrong type.</li>
      <li><b>Freeze</b> when nothing is left to decide.</li></ol></details>`}
    ${B.frozen ? `<div class="note">The baseline is frozen. ${Object.entries(B.frozen.counts).map(([k, v]) => `${v} ${S.model.names[k].toLowerCase()}${v === 1 ? "" : "s"}`).join(", ")} were written to the registers; the id map is in <code>baseline/frozen.md</code>. Verdicts here are read only now; every change from here is a change set.</div>` : ""}
    <div class="progress"><div style="width:${Math.round(100 * cs.filter(c => c.verdict).length / Math.max(1, cs.length))}%"></div></div>
    ${B.frozen ? "" : `<div class="tabs"><button data-bltab="rows" class="${BF.tab === "rows" ? "on" : ""}">Candidates <span class="n">${cs.length}</span></button><button data-bltab="dups" class="${BF.tab === "dups" ? "on" : ""}">Suggested duplicates <span class="n">${clusters.length}</span></button><button data-bltab="pass" class="${BF.tab === "pass" ? "on" : ""}">Row by row <span class="n">${todo}</span></button><button data-bltab="supports" class="${BF.tab === "supports" ? "on" : ""}">Missing supports <span class="n">${B.suggestions.suggestions.filter(s => s.level === "fail").length}</span></button></div>`}
    ${BF.tab === "pass" && !B.frozen ? blPass(cs, byId) : ""}
    ${BF.tab === "dups" && !B.frozen ? (clusters.length ? `<div class="section"><p class="small muted">Groups whose titles overlap or that share a source id. Suggestions only${clusters.length > 25 ? `; showing the first 25 of ${clusters.length}` : ""}.</p>
      ${clusters.slice(0, 25).map(g => `<div class="cs"><div class="small muted">${g.filter(id => !byId[id]?.verdict).length} still to decide. Tick the rows that are the same item, then choose which one leads; the rest fold into it, keeping their sources and anything it does not already hold. Unticked rows stay undecided. <button class="ghost" data-notdup="${g.join(",")}">Not duplicates</button> <button class="ghost" data-discgroup="1" title="Not register rows: drop the ticked ones without a rejection reason">Discard ticked</button>${(() => { const done = g.filter(id => byId[id]?.verdict); if (!done.length) return ""; const t = {}; done.forEach(id => { const v = byId[id].verdict; t[v] = (t[v] || 0) + 1; }); return `<br><span class="small muted">Already decided here: ${Object.entries(t).map(([v, n]) => `${n} ${v.toLowerCase()}`).join(", ")}.</span>`; })()}</div>${g.map(id => { const c = byId[id]; const done = !!c.verdict; return `<div class="blk ${done ? "done" : ""}">${done ? `<span class="vd">${esc(c.verdict)}</span>` : `<label class="dup"><input type="checkbox" data-dup="${id}" checked> same</label>`} ${!done || c.verdict === "Accept" ? `<button class="ghost" data-survivor="${id}">This one leads</button>` : ""} <span class="id" style="${COLOR(c.kind)}">${c.kind}</span> ${esc(c.title)} <span class="small muted">${esc(c.page)}${c.ref ? " · " + esc(c.ref) : ""}</span></div>`; }).join("")}</div>`).join("")}</div>` : `<p class="muted">No duplicate groups left to decide.</p>`) : ""}
    ${BF.tab === "supports" && !B.frozen ? blSupports() : ""}
    ${BF.tab !== "rows" && !B.frozen ? "" : `<div class="toolbar bl-filters">
      <select id="bf-kind">${opt(KINDS, BF.kind, "all types")}</select>
      <select id="bf-page">${opt(B.pages, BF.page, "all pages")}</select>${BF.page ? `<button class="ghost" id="bf-skip" title="A page that restates rows already on a register page. It stays pulled but produces no candidates.">Treat as a view</button>` : ""}
      <select id="bf-verdict"><option value="">any verdict</option><option value="none" ${BF.verdict === "none" ? "selected" : ""}>undecided</option>${["Accept", "Merge", "Reject", "Discard"].map(v => `<option ${BF.verdict === v ? "selected" : ""}>${v}</option>`).join("")}</select>
      <input id="bf-q" placeholder="search titles" value="${esc(BF.q)}" style="width:220px">
      <span class="small muted">${f.length} shown · ${BF.sel.size} selected</span>
    </div>
    ${B.frozen ? "" : `<div class="bulk"><label><input type="checkbox" id="bf-all"> select shown</label>
      <button data-bulk="Accept">Accept</button>
      <select id="bf-reason">${B.reasons.map(r => `<option ${BF.reason === r ? "selected" : ""}>${r}</option>`).join("")}</select><button data-bulk="Reject">Reject</button><button data-bulk="Discard" title="Not a register row: drop it without a rejection reason and keep it out of the change set and rejections.md">Discard</button>
      <select id="bf-kindset"><option value="">retype as…</option>${KINDS.map(k => `<option value="${k}">${S.model.names[k]}</option>`).join("")}</select>
      <span class="sep"></span><input id="bf-owner" placeholder="new owner" list="stk" style="width:170px"><datalist id="stk">${S.stakeholders.map(s => `<option value="${esc(s.name)}">`).join("")}<option value="Joint"><option value="Vendor: "></datalist><button data-bulk="owner">Reassign owner</button><span class="sep"></span>
      <select id="bf-moscow"><option value="">set MoSCoW…</option>${S.model.choices.moscow.map(m => `<option>${m}</option>`).join("")}</select>
      ${hasScopes ? `<select id="bf-scope"><option value="">set Scope…</option>${S.engagement.scopes.map(s => `<option>${esc(s)}</option>`).join("")}</select>` : ""}
      <select id="bf-impl"><option value="">set implemented by…</option>${S.model.choices["implemented-by"].map(m => `<option>${m}</option>`).join("")}</select>
      <button data-bulk="fields">Apply fields</button><button data-bulk="clear" class="ghost">Clear verdict</button></div>`}
    <div style="overflow-x:auto"><table><tr><th></th><th>Type</th><th>Title</th><th>Page · source id</th><th>Owner</th>${hasScopes ? "<th>Scope</th>" : ""}<th>MoSCoW</th><th>Confidence</th><th>Verdict</th></tr>
    ${f.map(c => `<tr class="row ${c.verdict ? "decided" : ""}"><td>${B.frozen ? "" : `<input type="checkbox" data-sel="${c.id}" ${BF.sel.has(c.id) ? "checked" : ""}>`}</td>
      <td><span class="id" style="${COLOR(c.kind)}">${c.kind}</span></td>
      <td class="t"><div>${B.frozen ? esc(c.title) : `<a href="#" data-edit="${c.id}" title="Edit before the freeze">${esc(c.title)}</a>`}${c.inferred ? '<span class="tag">inferred</span>' : ""}${c.status ? `<span class="tag">${esc(c.status)}</span>` : ""}</div>${c.description ? `<div class="small muted">${esc(c.description.slice(0, 160))}</div>` : ""}</td>
      <td class="small">${esc(c.page)}${c.ref ? `<br><code>${esc(c.ref)}</code>` : ""}${c.source_status ? `<br><span class="muted">was ${esc(c.source_status)}</span>` : ""}</td>
      <td>${esc(c.owner)}</td>${hasScopes ? `<td>${esc(c.scope)}</td>` : ""}<td>${esc(c.moscow)}</td><td class="small">${esc(c.confidence)}</td>
      <td class="st">${c.frozenAs ? `<span class="id" style="${COLOR(c.kind)}">${esc(c.frozenAs)}</span><br>` : c.exported ? `<span class="small muted">in ${esc(c.exported)}</span><br>` : ""}${c.verdict === "Reject" ? `Reject<br><span class="small muted">${esc(c.reason)}</span>` : c.verdict === "Merge" ? `Merge → ${esc(byId[c.mergedInto]?.title?.slice(0, 40) || "?")}` : esc(c.verdict)}</td></tr>`).join("") || `<tr><td colspan="${hasScopes ? 9 : 8}" class="muted">nothing matches</td></tr>`}
    </table></div>`}${BF.edit && byId[BF.edit] && !B.frozen ? blEditor(byId[BF.edit]) : ""}`;
}
/* Row by row: one undecided candidate at a time, in page order, with the verdicts on keys. */
function blPass(cs, byId) {
  const B = S.baseline;
  const pages = BF.page ? [BF.page] : B.pages;
  const q = cs.filter(c => pages.includes(c.page) && !c.verdict && (!BF.kind || c.kind === BF.kind));
  const opt = (arr, cur, blank) => `<option value="">${blank}</option>` + arr.map(x => `<option ${x === cur ? "selected" : ""}>${esc(x)}</option>`).join("");
  const bar = `<div class="toolbar bl-filters"><select id="bf-page">${opt(B.pages, BF.page, "all pages")}</select><select id="bf-kind">${opt(KINDS, BF.kind, "all types")}</select>
    <span class="small muted">${q.length} undecided${BF.page ? " on this page" : ""}</span></div>`;
  if (!q.length) return bar + `<p class="muted">Nothing undecided here.</p>`;
  BF.pos = Math.min(BF.pos, q.length - 1);
  const c = q[BF.pos];
  const f = (lab, v) => v ? `<div class="field"><label>${lab}</label><div class="v">${esc(v)}</div></div>` : "";
  const dup = B.clusters.find(g => g.includes(c.id));
  const near = dup ? dup.filter(id => id !== c.id).map(id => byId[id]).filter(Boolean) : [];
  return bar + `<div class="progress"><div style="width:${Math.round(100 * BF.pos / q.length)}%"></div></div>
    <div class="triage"><div class="tq-main">
      <div class="toolbar"><div><span class="id" style="${COLOR(c.kind)}">${c.kind}</span> <span class="small muted">${esc(c.page)}${c.table ? " · " + esc(c.table) : ""}${c.ref ? " · " + esc(c.ref) : ""}${c.source_status ? " · was " + esc(c.source_status) : ""}</span></div><span class="small muted">${BF.pos + 1} of ${q.length}</span></div>
      <h2 style="margin:4px 0 10px">${esc(c.title)}${c.inferred ? '<span class="tag">inferred</span>' : ""}</h2>
      ${f("Description", c.description)}${f("Scope", c.scope)}${f("Owner", c.owner)}${f("MoSCoW", c.moscow)}${f("Phase", c.phase)}${f("Rationale", c.rationale)}${f("Impact", c.impact)}${f("Next action", c["next action"])}${f("Source", c.source)}${f("Notes", c.notes)}
      <div class="moves" style="--c:var(--cs)">
        <button data-pv="Accept" title="a">Accept <kbd>a</kbd></button>
        <select id="pv-reason">${B.reasons.map(r => `<option ${BF.reason === r ? "selected" : ""}>${r}</option>`).join("")}</select><button data-pv="Reject" title="r">Reject <kbd>r</kbd></button>
        <button data-pv="Discard" title="x">Discard <kbd>x</kbd></button>
        <button data-pv="edit" title="e">Edit <kbd>e</kbd></button>
        <span class="sep"></span><button class="ghost" data-pv="prev" title="k">← <kbd>k</kbd></button><button class="ghost" data-pv="next" title="j">Skip <kbd>j</kbd> →</button>
      </div></div>
      <div class="tq-side"><h3>Looks like</h3>${near.length ? near.map(n => `<div class="ctx"><span class="id" style="${COLOR(n.kind)}">${n.kind}</span> ${n.verdict ? `<span class="vd">${esc(n.verdict)}</span>` : ""}<div>${esc(n.title)}</div><div class="small muted">${esc(n.page)}${n.ref ? " · " + esc(n.ref) : ""}</div></div>`).join("") : '<p class="small muted">No suggested duplicate.</p>'}
      <p class="small muted" style="margin-top:14px">A verdict moves to the next row. Reject uses the reason in the box.</p></div></div>`;
}
/* Missing supports: what the accepted rows' states imply and the set does not yet hold. Each offer is
   prefilled from its trigger; accepting adds an implied candidate, linked both ways, already accepted. */
function blSupports() {
  const B = S.baseline, R = B.suggestions, byId = Object.fromEntries(B.candidates.map(c => [c.id, c]));
  const fails = R.suggestions.filter(s => s.level === "fail"), warnsS = R.suggestions.filter(s => s.level === "warn");
  const one = s => {
    const editing = BF.sedit === s.key, f = editing ? {...s.fields, ...BF.sfields} : s.fields;
    const fld = (k, v) => `<div class="field"><label>${esc(S.model.labels[k] || k)}</label>${editing ? (["rationale", "reason", "impact", "next action", "source"].includes(k) ? `<textarea data-sf="${k}">${esc(v)}</textarea>` : k === "owner" ? `<input data-sf="owner" list="stk" value="${esc(v)}">` : `<input data-sf="${k}" value="${esc(v)}">`) : `<div class="v">${esc(v) || '<span class="muted">—</span>'}</div>`}</div>`;
    const keys = Object.keys(f); if (s.needsOwner && !keys.includes("owner")) keys.splice(1, 0, "owner");
    return `<div class="cs blk-support"><div class="small muted"><b>${esc(s.rule)}</b> (${esc(s.check)}) · ${esc(S.model.names[byId[s.id]?.kind] || "")} <i>${esc(s.triggerTitle)}</i> on ${esc(s.triggerPage)} is ${esc(byId[s.id] ? (byId[s.id].status || byId[s.id].source_status || S.model.first[byId[s.id].kind]) : "")} and needs a <span class="id" style="${COLOR(s.kind)}">${s.kind}</span>${s.needsOwner ? ' <span class="tag">owner needed</span>' : ""}</div>
      ${keys.map(k => fld(k, f[k] ?? "")).join("")}
      <div class="small muted">Links: trigger gets <code>${esc(s.link)}&lt;new id&gt;</code>${s.reverse ? `; new item gets <code>${esc(s.reverse)}</code>` : ""}</div>
      <div class="moves" style="--c:var(--cs)">
        ${s.recommend === "Reassess" ? `<button class="primary" data-sv="Reassess" data-key="${s.key}" title="Send the limitation back to Under assessment; its open item is offered next">Reassess (recommended)</button> <button data-sv="Accept" data-key="${s.key}">Reconstruct</button>` : `<button class="primary" data-sv="Accept" data-key="${s.key}">${s.recommend === "Reconstruct" ? "Reconstruct (recommended)" : "Accept"}</button>${s.recommend ? ` <button data-sv="Reassess" data-key="${s.key}">Reassess</button>` : ""}`}
        <button data-sv="edit" data-key="${s.key}">${editing ? "Stop editing" : "Edit"}</button>
        <input data-sreason="${s.key}" placeholder="reason to dismiss" style="width:220px"><button class="ghost" data-sv="Dismiss" data-key="${s.key}">Dismiss</button>
      </div>${linkRow(s, B.candidates.filter(c => c.kind === s.kind && c.verdict === "Accept" && c.id !== s.id), "data-blink")}</div>`;
  };
  const prompts = R.prompts.filter(p => byId[p.id]);
  // the stakeholder list lives in the bulk toolbar, which this tab does not render; the owner boxes need it here
  const names = fails.concat(warnsS).some(s => s.needsOwner) ? `<datalist id="stk">${S.stakeholders.map(p => `<option value="${esc(p.name)}">`).join("")}<option value="Joint"><option value="Vendor: "></datalist>` : "";
  return `<div class="section">${names}<p class="small muted">${fails.length} needed before the freeze · ${warnsS.length} suggested · ${prompts.length} field prompt(s) · ${R.dismissed} dismissed. Offers are drafted in their first state; nothing here fills Approved by.</p>
    ${fails.map(one).join("") || '<p class="muted">Nothing missing among the accepted rows.</p>'}
    ${warnsS.length ? `<h3>Suggested, not required</h3>${warnsS.map(one).join("")}` : ""}
    ${prompts.length ? `<h3>Fix by hand in the editor</h3>${prompts.map(p => `<div class="blk"><span class="id" style="${COLOR(byId[p.id].kind)}">${byId[p.id].kind}</span> <a href="#" data-edit="${p.id}">${esc(byId[p.id].title)}</a> <span class="small muted">${esc(p.rule)}: ${esc(p.text)}</span></div>`).join("")}` : ""}</div>`;
}
/* The editor: a fixed panel for one candidate. Fields follow the model for its type; what you save is a
   verdict override, so nothing touches the source page and Clear verdict does not undo it. */
const BL_LONG = {description: "Description", rationale: "Rationale", trigger: "Trigger", mitigation: "Mitigation", options: "Options", "next action": "Next action", notes: "Notes"};
function blEditor(c) {
  const B = S.baseline, fld = (k, lab, inner) => `<div class="field"><label>${lab}</label>${inner}</div>`;
  const text = k => fld(k, S.model.labels[k] || k, `<input data-f="${k}" value="${esc(c[k] || "")}">`);
  const choice = (k, arr) => fld(k, S.model.labels[k] || k, `<select data-f="${k}"><option value=""></option>${arr.map(x => `<option ${c[k] === x ? "selected" : ""}>${esc(x)}</option>`).join("")}</select>`);
  const scopes = S.engagement.scopes || [];
  const scopeArr = c.scope && !scopes.includes(c.scope) ? scopes.concat(c.scope) : scopes;
  const short = S.model.short[c.kind].filter(k => !["chosen-option", "estimate"].includes(k) && (k !== "scope" || scopes.length));
  const status = c.status || B.states[c.kind].find(x => x.toLowerCase() === (c.source_status || "").toLowerCase()) || S.model.first[c.kind];
  return `<div class="bl-edit" style="--c:var(--cs);--cb:var(--cs-bg)"><button class="close ghost" id="ble-close">Close</button><h3><span class="id" style="${COLOR(c.kind)}">${c.kind}</span> Edit candidate <span class="small muted">${esc(c.page)}${c.ref ? " · " + esc(c.ref) : ""}</span></h3>
    ${fld("title", "Title", `<input data-f="title" value="${esc(c.title)}">`)}
    <div class="cols">${fld("kind", "Type", `<select id="ble-kind">${KINDS.map(k => `<option value="${k}" ${c.kind === k ? "selected" : ""}>${S.model.names[k]}</option>`).join("")}</select>`)}
    ${fld("status", "Status at freeze", `<select data-f="status">${B.states[c.kind].map(x => `<option ${status === x ? "selected" : ""}>${x}</option>`).join("")}</select>`)}
    ${short.map(k => k === "scope" ? choice(k, scopeArr) : S.model.choices[k] ? choice(k, S.model.choices[k]) : text(k)).join("")}${text("raised-on")}</div>
    ${Object.entries(BL_LONG).filter(([k]) => k === "description" || k === "notes" || S.model.long[c.kind].includes(k) || (c.kind === "CR" && k === "rationale")).map(([k, lab]) => fld(k, c.kind === "CR" && k === "rationale" ? "Reason" : lab, `<textarea data-f="${k}">${esc(c[k] || "")}</textarea>`)).join("")}
    <div class="moves"><button class="primary" id="ble-save">Save</button> <button id="ble-save-accept">Save and accept</button> <span class="small muted">Changing the type re-reads the fields for the new type after saving.</span></div></div>`;
}
async function passVerdict(what) {
  const B = S.baseline, pages = BF.page ? [BF.page] : B.pages;
  const q = B.candidates.filter(c => pages.includes(c.page) && !c.verdict && (!BF.kind || c.kind === BF.kind));
  const c = q[Math.min(BF.pos, q.length - 1)]; if (!c) return;
  if (what === "next") { BF.pos = Math.min(q.length - 1, BF.pos + 1); render(); return; }
  if (what === "prev") { BF.pos = Math.max(0, BF.pos - 1); render(); return; }
  if (what === "edit") { BF.edit = c.id; render(); return; }
  try { await blPost({ids: [c.id], verdict: what, reason: what === "Reject" ? ($("#pv-reason")?.value || BF.reason || "other") : ""}); } catch (e) { toast(e.message); }
}
document.addEventListener("keydown", e => {
  if (view !== "baseline" || BF.tab !== "pass" || BF.edit || ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) return;
  const k = {a: "Accept", r: "Reject", x: "Discard", e: "edit", j: "next", k: "prev"}[e.key]; if (k) { e.preventDefault(); passVerdict(k); }
});
async function blPost(body) { const y = window.scrollY; await post("/api/baseline/verdict", body); await load(); window.scrollTo(0, y); }
function wireBaseline(m) {
  const re = () => { render(); };
  m.querySelectorAll("[data-bltab]").forEach(el => el.onclick = () => { BF.tab = el.dataset.bltab; BF.pos = 0; re(); });
  const skipBtn = $("#bf-skip", m); if (skipBtn) skipBtn.onclick = async () => { const pg = BF.page; try { await post("/api/baseline/skip-page", {page: pg}); BF.page = ""; toast(`${pg} treated as a view`); await load(); } catch (e) { toast(e.message); } };
  m.querySelectorAll("[data-unskip]").forEach(el => el.onclick = async e => { e.preventDefault(); try { await post("/api/baseline/skip-page", {page: el.dataset.unskip, undo: true}); await load(); } catch (e2) { toast(e2.message); } });
  m.querySelectorAll("details.how").forEach(d => d.ontoggle = () => { BF.help = d.open; });
  m.querySelectorAll("[data-pv]").forEach(el => el.onclick = () => passVerdict(el.dataset.pv));
  const pr = $("#pv-reason", m); if (pr) pr.onchange = e => BF.reason = e.target.value;
  const on = (sel, ev, fn) => { const el = $(sel, m); if (el) el[ev] = fn; };
  on("#bf-kind", "onchange", e => { BF.kind = e.target.value; re(); });
  on("#bf-page", "onchange", e => { BF.page = e.target.value; re(); });
  on("#bf-verdict", "onchange", e => { BF.verdict = e.target.value; re(); });
  on("#bf-q", "oninput", e => { BF.q = e.target.value; clearTimeout(BF.t); BF.t = setTimeout(re, 250); });
  on("#bf-reason", "onchange", e => BF.reason = e.target.value);
  m.querySelectorAll("[data-sel]").forEach(el => el.onchange = () => { el.checked ? BF.sel.add(el.dataset.sel) : BF.sel.delete(el.dataset.sel); });
  if ($("#bf-all", m)) $("#bf-all", m).onchange = e => { m.querySelectorAll("[data-sel]").forEach(el => { el.checked = e.target.checked; e.target.checked ? BF.sel.add(el.dataset.sel) : BF.sel.delete(el.dataset.sel); }); re(); };
  m.querySelectorAll("[data-bulk]").forEach(el => el.onclick = async () => {
    const ids = [...BF.sel]; if (!ids.length) return toast("Select some candidates first");
    try {
      const w = el.dataset.bulk;
      if (w === "Accept") await blPost({ids, verdict: "Accept"});
      else if (w === "Reject") await blPost({ids, verdict: "Reject", reason: $("#bf-reason", m).value});
      else if (w === "Discard") await blPost({ids, verdict: "Discard"});
      else if (w === "clear") await blPost({ids, verdict: ""});
      else if (w === "owner") { const o = $("#bf-owner", m).value.trim(); if (!o) return toast("Type the new owner first"); await blPost({ids, fields: {owner: o}}); }
      else if (w === "fields") { const kind = $("#bf-kindset", m).value || null, fields = {}; const o = $("#bf-owner", m).value.trim(), mo = $("#bf-moscow", m).value, im = $("#bf-impl", m).value; if (o) fields.owner = o; if (mo) fields.moscow = mo; if (im) fields["implemented-by"] = im; const sc = ($("#bf-scope", m) || {}).value || ""; if (sc) fields.scope = sc; BF.sel.clear(); await blPost({ids, kind, fields}); }
      BF.sel.clear(); render(); toast(`${ids.length} updated`);
    } catch (e) { toast(e.message); }
  });
  m.querySelectorAll("[data-discgroup]").forEach(el => el.onclick = async () => {
    const ticked = [...el.closest(".cs").querySelectorAll("[data-dup]")].filter(x => x.checked).map(x => x.dataset.dup);
    if (!ticked.length) { toast("Nothing ticked to discard"); return; }
    try { await blPost({ids: ticked, verdict: "Discard"}); toast(`Discarded ${ticked.length}`); } catch (e) { toast(e.message); }
  });
  m.querySelectorAll("[data-notdup]").forEach(el => el.onclick = async () => {
    try { await post("/api/baseline/not-duplicates", {ids: el.dataset.notdup.split(",")}); toast("Group set aside; the rows stay undecided"); await load(); } catch (e) { toast(e.message); }
  });
  m.querySelectorAll("[data-survivor]").forEach(el => el.onclick = async () => {
    const keep = el.dataset.survivor;
    const group = el.closest(".cs");
    const others = [...group.querySelectorAll("[data-dup]")].filter(x => x.checked && x.dataset.dup !== keep).map(x => x.dataset.dup);
    if (!others.length) { toast("Tick the rows that are the same item first"); return; }
    try { await post("/api/baseline/verdict", {ids: [keep], verdict: "Accept"}); await blPost({ids: others, verdict: "Merge", mergedInto: keep}); toast(`Folded ${others.length} into it`); } catch (e) { toast(e.message); }
  });
  m.querySelectorAll("[data-sf]").forEach(el => el.oninput = () => { BF.sfields[el.dataset.sf] = el.value; });
  m.querySelectorAll("[data-blink]").forEach(el => el.onclick = async () => {
    const key = el.dataset.blink, target = el.dataset.target || m.querySelector(`[data-lkin="${key}"]`)?.value.trim();
    if (!target) return toast("Pick the record to link");
    try { const y = window.scrollY; await post("/api/baseline/support", {key, verdict: "Link", target}); await load(); window.scrollTo(0, y); toast(`Linked to ${target}; nothing created`); } catch (e) { toast(e.message); }
  });
  m.querySelectorAll("[data-sv]").forEach(el => el.onclick = async () => {
    const key = el.dataset.key, what = el.dataset.sv;
    if (what === "edit") { if (BF.sedit === key) { BF.sedit = null; BF.sfields = {}; } else { BF.sedit = key; BF.sfields = {}; } render(); return; }
    const body = {key, verdict: what};
    if (what === "Dismiss") { body.reason = m.querySelector(`[data-sreason="${key}"]`)?.value.trim() || ""; if (!body.reason) return toast("Give a reason to dismiss"); }
    if (what === "Accept" && BF.sedit === key) body.fields = BF.sfields;
    try { const y = window.scrollY; await post("/api/baseline/support", body); BF.sedit = null; BF.sfields = {}; await load(); window.scrollTo(0, y); toast(what === "Accept" ? "Added as an accepted candidate" : what === "Reassess" ? "Sent back to Under assessment" : "Dismissed"); } catch (e) { toast(e.message); }
  });
  m.querySelectorAll("[data-edit]").forEach(el => el.onclick = e => { e.preventDefault(); BF.edit = el.dataset.edit; render(); });
  const ed = $("#ble-close", m);
  if (ed) {
    ed.onclick = () => { BF.edit = null; render(); };
    const save = async accept => {
      const fields = {}; m.querySelectorAll("[data-f]").forEach(x => { fields[x.dataset.f] = x.value; });
      const kind = $("#ble-kind", m).value;
      try { await blPost({ids: [BF.edit], kind, fields, ...(accept ? {verdict: "Accept"} : {})}); if (BF.tab === "pass") { BF.edit = null; render(); } toast(accept ? "Saved and accepted" : "Saved"); } catch (e) { toast(e.message); }
    };
    $("#ble-save", m).onclick = () => save(false);
    $("#ble-save-accept", m).onclick = () => save(true);
  }
  const fz = $("#bl-freeze", m); if (fz) fz.onclick = () => { if (!madeBy()) return toast("Say who you are first (Made by)"); BF.confirmFreeze = true; render(); };
  const fno = $("#bl-freeze-no", m); if (fno) fno.onclick = () => { BF.confirmFreeze = false; render(); };
  const fgo = $("#bl-freeze-go", m); if (fgo) fgo.onclick = async () => { try { const r = await post("/api/baseline/freeze", {}); BF.confirmFreeze = false; toast(`Frozen: ${r.written} items written, ${r.rejected} rejected`); await load(); } catch (e) { BF.confirmFreeze = false; toast(e.message); render(); } };
}
