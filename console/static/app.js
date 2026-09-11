/* Register console front end. State comes from /api/state; every write is one POST that appends a change set block. */
let S = null, view = "outstanding", open = null, form = null;
const $ = (s, el = document) => el.querySelector(s);
const KINDS = ["REQ", "DEC", "LIM", "RSK", "OI", "CR"];
const COLOR = k => `--c:var(--${k.toLowerCase()});--cb:var(--${k.toLowerCase()}-bg)`;
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const madeBy = () => $("#made-by").value.trim();
const toast = m => { const t = $("#toast"); t.textContent = m; t.hidden = false; setTimeout(() => t.hidden = true, 2600); };

async function load() {
  S = await (await fetch("/api/state")).json();
  S.byId = Object.fromEntries(S.items.map(i => [i.id, i]));
  S.baseline = await (await fetch("/api/baseline")).json();
  $("#eng-name").textContent = S.engagement.name + (S.engagement.current ? " · " + S.engagement.current : "");
  const mine = S.change_sets.filter(c => !c.closed && !c.applied && c.header["Made by"] === madeBy());
  $("#session-info").textContent = mine.length ? `${mine[0].id}, ${mine[0].blocks.length} block(s) this session` : "no open change set";
  render();
}
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
  $("#nav").innerHTML = [
    `<a href="#" data-v="outstanding" class="${view === "outstanding" ? "on" : ""}">Outstanding</a>`,
    `<a href="#" data-v="triage" class="${view === "triage" ? "on" : ""}">Work through <span class="n">${queue().length}</span></a>`,
    `<a href="#" data-v="report" class="${view === "report" ? "on" : ""}">Meeting report</a>`,
    ...(S.baseline?.present ? [`<a href="#" data-v="baseline" style="--c:var(--cs)" class="${view === "baseline" ? "on" : ""}">Baseline <span class="n">${S.baseline.candidates.filter(c => !c.verdict).length}</span></a>`] : []),
    `<div class="gap"></div>`,
    ...KINDS.map(k => `<a href="#" data-v="${k}" style="${COLOR(k)}" class="${view === k ? "on" : ""}">${S.model.names[k]}s <span class="n">${counts(k)}</span></a>`),
    `<div class="gap"></div>`,
    `<a href="#" data-v="cs" style="--c:var(--cs)" class="${view === "cs" ? "on" : ""}">Change sets <span class="n">${pendingN}</span></a>`,
  ].join("");
  $("#nav").querySelectorAll("a").forEach(a => a.onclick = e => { e.preventDefault(); view = a.dataset.v; open = null; form = null; render(); });
  const m = $("#main");
  document.body.classList.toggle("print-mode", view === "report");
  if (view === "outstanding") m.innerHTML = outstanding();
  else if (view === "triage") { m.innerHTML = triage(); wire(m); }
  else if (view === "report") m.innerHTML = report();
  else if (view === "baseline") { m.innerHTML = baselineView(); wireBaseline(m); }
  else if (view === "cs") m.innerHTML = changeSets();
  else m.innerHTML = register(view);
  m.querySelectorAll("[data-open]").forEach(el => el.onclick = e => { e.preventDefault(); openItem(el.dataset.open); });
  m.querySelectorAll("[data-new]").forEach(el => el.onclick = () => { open = null; form = {mode: "create", kind: el.dataset.new, fields: {}, links: []}; renderDetail(); });
  $("#copy-md", m)?.addEventListener("click", () => { navigator.clipboard.writeText(reportMarkdown()).then(() => toast("Report copied as markdown")); });
  $("#print", m)?.addEventListener("click", () => window.print());
  m.querySelectorAll("[data-tq]").forEach(el => el.onclick = () => { triageMove(el.dataset.tq); });
  m.querySelectorAll("[data-raw]").forEach(el => el.onclick = async e => { e.preventDefault(); const t = await (await fetch("/api/change-set/" + el.dataset.raw)).text(); $("#raw-" + el.dataset.raw).innerHTML = `<pre>${esc(t)}</pre>`; });
  renderDetail();
}
const idTag = i => `<a href="#" data-open="${i.id}" class="id" style="${COLOR(i.kind)}">${i.id}</a>${i.provisional ? '<span class="tag new">pending id</span>' : ""}`;
const pendTag = i => i.pending.length && !i.provisional ? `<span class="tag">${i.pending.length} pending</span>` : "";
const row = (i, cols) => `<tr class="row ${i.pending.length ? "pending" : ""}" data-open="${i.id}"><td>${idTag(i)}</td><td class="t">${esc(i.title)}${pendTag(i)}</td>${cols.map(c => `<td class="${c === "status" ? "st" : ""}">${esc(Array.isArray(i[c]) ? i[c].join("; ") : i[c])}</td>`).join("")}</tr>`;
const table = (items, cols) => `<div style="overflow-x:auto"><table><tr><th>ID</th><th>Title</th>${cols.map(c => `<th>${esc(S.model.labels[c] || c)}</th>`).join("")}</tr>${items.map(i => row(i, cols)).join("") || `<tr><td colspan="${cols.length + 2}" class="muted">none</td></tr>`}</table></div>`;

function register(k) {
  const items = S.items.filter(i => i.kind === k);
  const cols = ["status", ...S.model.short[k].filter(f => f !== "owner"), "owner", "raised-on", "closed-on"];
  return `<div class="toolbar"><h2>${S.model.names[k]}s</h2><button class="primary" data-new="${k}">New ${S.model.names[k].toLowerCase()}</button></div>${table(items, cols)}`;
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
  return `<h2>Outstanding</h2><p class="small muted">Model section 8, in order. Amber marks an item with a pending change in an unapplied change set.</p>
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
  return `<h2>Change sets</h2><p class="small muted">One file per session under <code>change-sets/</code>. The ingester applies them; the console only appends.</p>` +
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
    ${moves.length ? `<h3>Move to</h3><div class="moves" style="${COLOR(k)}">${moves.map(m => `<button data-move="${m}" class="${form?.to === m ? "on" : ""}">${m}</button>`).join("")}</div>` : ""}
    ${form && form.mode === "move" ? moveForm(i) : ""}
    ${S.model.short[k].map(f => fld(f, i[f])).join("")}
    <div class="field ${changed.has("links") ? "changed" : ""}"><label>Links</label><ul class="links">${i.links.map(l => { const m = l.match(/([A-Z]+-\d{4}(?:\.\d+)?)/); return `<li>${m && S.byId[m[1]] ? esc(l.replace(m[1], "")) + `<a href="#" data-open="${m[1]}">${m[1]}</a>` : esc(l)}</li>`; }).join("") || '<li class="muted">none</li>'}</ul></div>
    ${S.model.long[k].map(f => fld(f, i[f])).join("")}
    ${fld("raised-on", i["raised-on"])}${fld("closed-on", i["closed-on"])}
    <div class="small muted">updated ${esc(i.updated || "")}</div>
    ${form && form.mode === "edit" ? editForm(i) : `<div class="form"><button id="edit-btn">Edit fields</button></div>`}`;
}
function wire(d) {
  $("#close-detail", d)?.addEventListener("click", () => { open = null; form = null; renderDetail(); });
  d.querySelectorAll("[data-open]").forEach(el => el.onclick = e => { e.preventDefault(); openItem(el.dataset.open); });
  d.querySelectorAll("[data-move]").forEach(el => el.onclick = () => { form = {mode: "move", to: el.dataset.move, fields: {}, links: []}; renderDetail(); });
  $("#edit-btn", d)?.addEventListener("click", () => { form = {mode: "edit", fields: {}, links: []}; renderDetail(); });
  $("#cancel", d)?.addEventListener("click", () => { form = null; renderDetail(); });
  $("#submit", d)?.addEventListener("click", submit);
  d.querySelectorAll("[data-tq]").forEach(el => el.onclick = () => triageMove(el.dataset.tq));
  d.querySelectorAll("[data-f]").forEach(el => el.oninput = () => form.fields[el.dataset.f] = el.value);
  $("#new-link", d)?.addEventListener("input", e => form.linkText = e.target.value);
  $("#new-link-word", d)?.addEventListener("change", e => form.linkWord = e.target.value);
  $("#evidence", d)?.addEventListener("input", e => form.evidence = e.target.value);
  $("#gist", d)?.addEventListener("input", e => form.gist = e.target.value);
}
const input = (key, val = "", req = false, kind = null) => {
  const c = (key === "impact" && kind !== "RSK") ? null : S.model.choices[key];
  const lab = `<label>${esc(S.model.labels[key] || key)}${req ? ' <span class="req">required</span>' : ""}</label>`;
  if (c) return `<div class="field">${lab}<select data-f="${key}"><option value="">—</option>${c.map(o => `<option ${o === val ? "selected" : ""}>${o}</option>`).join("")}</select></div>`;
  if (key === "owner" || key === "approved-by") return `<div class="field">${lab}<input data-f="${key}" list="stk" value="${esc(val)}"><datalist id="stk">${S.stakeholders.map(s => `<option value="${esc(s.name)}">${esc(s.role)}</option>`).join("")}<option value="Joint"><option value="Vendor: "></datalist></div>`;
  if (key === "phase") return `<div class="field">${lab}<select data-f="phase"><option value="">—</option>${S.engagement.phases.map(p => `<option ${p === val ? "selected" : ""}>${p}</option>`).join("")}</select></div>`;
  if (S.model.long.REQ.concat(S.model.long.DEC, S.model.long.LIM, S.model.long.RSK, S.model.long.OI, S.model.long.CR).includes(key)) return `<div class="field">${lab}<textarea data-f="${key}">${esc(val)}</textarea></div>`;
  return `<div class="field">${lab}<input data-f="${key}" value="${esc(val)}"></div>`;
};
const linkAdder = (k) => { const words = Object.keys(S.model.linkWords[k] || {}); return `<div class="field"><label>Add link</label><div style="display:flex;gap:6px"><select id="new-link-word" style="width:45%">${words.map(w => `<option ${form.linkWord === w ? "selected" : ""}>${w}</option>`).join("")}</select><input id="new-link" placeholder="REQ-0014, or item 2 for a block in this session" value="${esc(form.linkText || "")}"></div></div>`; };
const tail = () => `<div class="field"><label>Evidence (meeting, document or note)</label><input id="evidence" value="${esc(form.evidence || "")}" placeholder="e.g. stakeholder forum 11 Sep"></div>
  <div class="field"><label>Why, in one sentence (Gist)</label><input id="gist" value="${esc(form.gist || "")}"></div>
  <div class="err" id="err"></div><div class="actions"><button class="primary" id="submit">Append to change set</button><button id="cancel">Cancel</button></div>`;

function moveForm(i) {
  const k = i.kind, req = (S.model.required[k] || {})[form.to] || [];
  const fields = req.filter(r => !r.startsWith("link:")).map(r => r === "options" ? "options" : r);
  const links = req.filter(r => r.startsWith("link:")).map(r => r.slice(5));
  if (!form.linkWord && links.length) form.linkWord = links.find(w => !i.links.some(l => l.toLowerCase().startsWith(w))) || links[0];
  return `<div class="form"><h3>${esc(i.status)} → ${esc(form.to)}</h3>
    ${fields.map(f => input(f, form.fields[f] ?? i[f] ?? "", true, k)).join("")}
    ${links.length ? `<p class="small muted">This move needs a link: ${links.map(esc).join(", ")}. ${i.links.some(l => links.some(w => l.toLowerCase().startsWith(w))) ? "Already present, or add another below." : "Add it below, or create the record first from its register and link <code>item n</code>."}</p>` : ""}
    ${linkAdder(k)}${tail()}</div>`;
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
    const links = [...form.links];
    if (form.linkText) links.push(`${form.linkWord || Object.keys(S.model.linkWords[form.kind || S.byId[open].kind])[0]} ${form.linkText.trim()}`);
    const body = {fields: form.fields, links, evidence: form.evidence || "", gist: form.gist || ""};
    let r;
    if (form.mode === "create") { const {__status, ...rest} = form.fields; r = await post("/api/create", {...body, fields: rest, kind: form.kind, status: __status || ""}); }
    else if (form.mode === "move") r = await post("/api/transition", {...body, id: open, to: form.to});
    else r = await post("/api/edit", {...body, id: open});
    toast(`${r.changeSet} item ${r.item} appended`);
    form = null; await load();
    if (view === "triage") { const q = queue(); if (!q.some(e => e.item.id === open)) { open = null; } render(); }
  } catch (e) { err.textContent = e.message; }
}
function parseDate(s) { const m = /^(\d{1,2}) (\w+) (\d{4})/.exec(s || ""); if (!m) return null; const mi = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"].indexOf(m[2]); return mi < 0 ? null : new Date(+m[3], mi, +m[1]); }

/* ---------- boot ---------- */
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
  it.filter(i => i.kind === "RSK" && ["Identified", "Mitigating"].includes(i.status) && (!dt(i.due) || dt(i.due) < now)).forEach(i => add(i, i.due ? "Risk past its review date. Update likelihood, impact and mitigation, or retire it." : "Risk with no review date.", 3));
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
  if (!q.length) return `<h2>Work through</h2><p class="muted">Nothing needs a hand. The register is clean.</p>`;
  let p = Math.min(getPos(), q.length - 1); setPos(p);
  const e = q[p], i = e.item; open = i.id;
  const related = i.links.map(l => l.match(/([A-Z]+-\d{4}(?:\.\d+)?)/)?.[1]).filter(id => id && S.byId[id]).map(id => S.byId[id]);
  const back = S.items.filter(o => o.id !== i.id && o.links.some(l => l.includes(i.id)));
  const ctx = [...related, ...back.filter(b => !related.includes(b))];
  const done = q.filter((x, n) => n < p).length;
  return `<div class="toolbar"><div><h2>Work through</h2><span class="small muted">${p + 1} of ${q.length}${e.parked ? " · parked" : ""}</span></div>
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
  return `<div class="toolbar no-print"><h2>Meeting report</h2><div style="display:flex;gap:6px"><button id="copy-md">Copy as markdown</button><button id="print">Print</button></div></div>
    <div class="report">
    <div class="rhead"><span class="eyebrow">${esc(S.engagement.name)} · ${esc(S.engagement.current)}</span><h1>Register report, ${esc(S.today)}</h1><p class="small muted">Registers as proposed, including ${r.pending.length} pending change(s) not yet applied by the ingester.</p></div>
    <div class="stat"><div><b>${r.decisions.length}</b><span>calls needed</span></div><div><b>${r.crs.filter(c => c.status === "For approval").length}</b><span>CRs awaiting approval</span></div><div><b>${Object.values(r.byOwner).flat().length}</b><span>open items</span></div><div><b>${r.risks.length}</b><span>risks to review</span></div><div><b class="${r.defects.length ? "req" : ""}">${r.defects.length}</b><span>register defects</span></div></div>
    <h3>Calls needed at this meeting</h3><ul class="rl">${r.decisions.map(i => li(i, i.kind === "LIM" && i.options ? `<div class="small">${esc(i.options).replace(/\n/g, "<br>")}</div>` : i.rationale ? `<div class="small muted">${esc(i.rationale)}</div>` : "")).join("") || "<li class='muted'>none</li>"}</ul>
    <h3>Change requests</h3><ul class="rl">${r.crs.map(i => li(i, `<div class="small">${esc(i.reason || "")}</div><div class="small muted">${i.estimate ? "Estimate: " + esc(i.estimate) : "No estimate yet"}${i["approved-by"] ? " · approved by " + esc(i["approved-by"]) : ""}</div>`)).join("") || "<li class='muted'>none</li>"}</ul>
    <h3>Risks to review</h3><ul class="rl">${r.risks.map(i => li(i, ` <span class="small">L ${esc(i.likelihood)} · I ${esc(i.impact)} · review ${esc(i.due || "unset")}</span>`)).join("") || "<li class='muted'>none</li>"}</ul>
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
  L.push(`## New limitations`, ...r.newLims.map(i => line(i, i.impact ? `\n    ${i.impact}` : "")), ``);
  L.push(`## Actions by owner`); Object.entries(r.byOwner).sort().forEach(([o, items]) => { L.push(`### ${o}`, ...items.map(i => line(i, ` ${i["next action"] || "no next action"}${i.due ? ", due " + i.due : ""}`)), ``); });
  L.push(`## Requirements still in Draft`, ...r.drafts.map(i => line(i, ` ${i.moscow}, ${i.owner}`)), ``);
  L.push(`## Pending changes`, ...r.pending.map(p => `- ${p.cs} (${p.by}): ${p.b.kind} ${p.b.fields.Target}${p.b.fields.From ? ` ${p.b.fields.From} → ${p.b.fields.Status}` : p.b.fields.Title ? ": " + p.b.fields.Title : ""}. ${p.b.fields.Gist || ""}`), ``);
  if (r.defects.length) L.push(`## Register defects`, ...r.defects.map(i => line(i, !i.owner ? " no owner" : " no next action")));
  return L.join("\n");
}


/* ---------- baseline mode ---------- */
let BF = {kind: "", page: "", verdict: "", q: "", sel: new Set(), reason: "", showClusters: true};
function baselineView() {
  const B = S.baseline, cs = B.candidates;
  const f = cs.filter(c => (!BF.kind || c.kind === BF.kind) && (!BF.page || c.page === BF.page) && (BF.verdict === "" ? true : BF.verdict === "none" ? !c.verdict : c.verdict === BF.verdict) && (!BF.q || (c.title + " " + c.description).toLowerCase().includes(BF.q.toLowerCase())));
  f.sort((a, b) => (a.verdict ? 1 : 0) - (b.verdict ? 1 : 0) || (b.inferred ? 1 : 0) - (a.inferred ? 1 : 0));
  const n = v => cs.filter(c => c.verdict === v).length;
  const byId = Object.fromEntries(cs.map(c => [c.id, c]));
  const clusters = B.clusters.filter(g => g.some(id => !byId[id]?.verdict));
  const opt = (arr, cur, blank) => `<option value="">${blank}</option>` + arr.map(x => `<option ${x === cur ? "selected" : ""}>${esc(x)}</option>`).join("");
  return `<div class="toolbar"><div><h2>Baseline</h2><span class="small muted">${cs.length} candidates from ${B.pages.length} page(s) · ${n("Accept")} accepted · ${n("Merge")} merged · ${n("Reject")} rejected · ${cs.filter(c => !c.verdict).length} to go</span></div>
    <div><button id="bl-export" class="primary">Export change set</button></div></div>
    <div class="progress"><div style="width:${Math.round(100 * cs.filter(c => c.verdict).length / Math.max(1, cs.length))}%"></div></div>
    ${clusters.length && BF.showClusters ? `<div class="section"><h3>Suggested duplicates <span class="small muted">${clusters.length} group(s)</span></h3>
      ${clusters.slice(0, 8).map(g => `<div class="cs"><div class="small muted">Pick the survivor; the rest merge into it and keep their sources.</div>${g.map(id => { const c = byId[id]; return `<div class="blk"><button class="ghost" data-survivor="${id}" data-group="${g.join(",")}">Keep this</button> <span class="id" style="${COLOR(c.kind)}">${c.kind}</span> ${esc(c.title)} <span class="small muted">${esc(c.page)}${c.ref ? " · " + esc(c.ref) : ""}${c.verdict ? " · " + esc(c.verdict) : ""}</span></div>`; }).join("")}</div>`).join("")}</div>` : ""}
    <div class="toolbar bl-filters">
      <select id="bf-kind">${opt(KINDS, BF.kind, "all types")}</select>
      <select id="bf-page">${opt(B.pages, BF.page, "all pages")}</select>
      <select id="bf-verdict"><option value="">any verdict</option><option value="none" ${BF.verdict === "none" ? "selected" : ""}>undecided</option>${["Accept", "Merge", "Reject"].map(v => `<option ${BF.verdict === v ? "selected" : ""}>${v}</option>`).join("")}</select>
      <input id="bf-q" placeholder="search titles" value="${esc(BF.q)}" style="width:220px">
      <span class="small muted">${f.length} shown · ${BF.sel.size} selected</span>
    </div>
    <div class="bulk"><label><input type="checkbox" id="bf-all"> select shown</label>
      <button data-bulk="Accept">Accept</button>
      <select id="bf-reason">${B.reasons.map(r => `<option ${BF.reason === r ? "selected" : ""}>${r}</option>`).join("")}</select><button data-bulk="Reject">Reject</button>
      <select id="bf-kindset"><option value="">retype as…</option>${KINDS.map(k => `<option value="${k}">${S.model.names[k]}</option>`).join("")}</select>
      <input id="bf-owner" placeholder="set owner" list="stk" style="width:160px"><datalist id="stk">${S.stakeholders.map(s => `<option value="${esc(s.name)}">`).join("")}</datalist>
      <select id="bf-moscow"><option value="">set MoSCoW…</option>${S.model.choices.moscow.map(m => `<option>${m}</option>`).join("")}</select>
      <button data-bulk="fields">Apply fields</button><button data-bulk="clear" class="ghost">Clear verdict</button></div>
    <div style="overflow-x:auto"><table><tr><th></th><th>Type</th><th>Title</th><th>Page · source id</th><th>Owner</th><th>MoSCoW</th><th>Confidence</th><th>Verdict</th></tr>
    ${f.map(c => `<tr class="row ${c.verdict ? "decided" : ""}"><td><input type="checkbox" data-sel="${c.id}" ${BF.sel.has(c.id) ? "checked" : ""}></td>
      <td><span class="id" style="${COLOR(c.kind)}">${c.kind}</span></td>
      <td class="t"><div>${esc(c.title)}${c.inferred ? '<span class="tag">inferred</span>' : ""}</div>${c.description ? `<div class="small muted">${esc(c.description.slice(0, 160))}</div>` : ""}</td>
      <td class="small">${esc(c.page)}${c.ref ? `<br><code>${esc(c.ref)}</code>` : ""}${c.source_status ? `<br><span class="muted">was ${esc(c.source_status)}</span>` : ""}</td>
      <td>${esc(c.owner)}</td><td>${esc(c.moscow)}</td><td class="small">${esc(c.confidence)}</td>
      <td class="st">${c.verdict === "Reject" ? `Reject<br><span class="small muted">${esc(c.reason)}</span>` : c.verdict === "Merge" ? `Merge → ${esc(byId[c.mergedInto]?.title?.slice(0, 40) || "?")}` : esc(c.verdict)}</td></tr>`).join("") || '<tr><td colspan="8" class="muted">nothing matches</td></tr>'}
    </table></div>`;
}
async function blPost(body) { await post("/api/baseline/verdict", body); await load(); }
function wireBaseline(m) {
  const re = () => { render(); };
  $("#bf-kind", m).onchange = e => { BF.kind = e.target.value; re(); };
  $("#bf-page", m).onchange = e => { BF.page = e.target.value; re(); };
  $("#bf-verdict", m).onchange = e => { BF.verdict = e.target.value; re(); };
  $("#bf-q", m).oninput = e => { BF.q = e.target.value; clearTimeout(BF.t); BF.t = setTimeout(re, 250); };
  $("#bf-reason", m).onchange = e => BF.reason = e.target.value;
  m.querySelectorAll("[data-sel]").forEach(el => el.onchange = () => { el.checked ? BF.sel.add(el.dataset.sel) : BF.sel.delete(el.dataset.sel); });
  $("#bf-all", m).onchange = e => { m.querySelectorAll("[data-sel]").forEach(el => { el.checked = e.target.checked; e.target.checked ? BF.sel.add(el.dataset.sel) : BF.sel.delete(el.dataset.sel); }); re(); };
  m.querySelectorAll("[data-bulk]").forEach(el => el.onclick = async () => {
    const ids = [...BF.sel]; if (!ids.length) return toast("Select some candidates first");
    try {
      const w = el.dataset.bulk;
      if (w === "Accept") await blPost({ids, verdict: "Accept"});
      else if (w === "Reject") await blPost({ids, verdict: "Reject", reason: $("#bf-reason", m).value});
      else if (w === "clear") await blPost({ids, verdict: ""});
      else if (w === "fields") { const kind = $("#bf-kindset", m).value || null, fields = {}; const o = $("#bf-owner", m).value.trim(), mo = $("#bf-moscow", m).value; if (o) fields.owner = o; if (mo) fields.moscow = mo; await blPost({ids, kind, fields}); }
      BF.sel.clear(); toast(`${ids.length} updated`);
    } catch (e) { toast(e.message); }
  });
  m.querySelectorAll("[data-survivor]").forEach(el => el.onclick = async () => {
    const keep = el.dataset.survivor, others = el.dataset.group.split(",").filter(x => x !== keep);
    try { await blPost({ids: [keep], verdict: "Accept"}); await blPost({ids: others, verdict: "Merge", mergedInto: keep}); toast("Merged"); } catch (e) { toast(e.message); }
  });
  $("#bl-export", m).onclick = async () => { try { const r = await post("/api/baseline/export", {}); toast(`${r.changeSet}: ${r.accepted} accepted, ${r.rejected} rejected`); await load(); } catch (e) { toast(e.message); } };
}
