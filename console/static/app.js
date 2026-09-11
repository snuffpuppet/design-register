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
    `<div class="gap"></div>`,
    ...KINDS.map(k => `<a href="#" data-v="${k}" style="${COLOR(k)}" class="${view === k ? "on" : ""}">${S.model.names[k]}s <span class="n">${counts(k)}</span></a>`),
    `<div class="gap"></div>`,
    `<a href="#" data-v="cs" style="--c:var(--cs)" class="${view === "cs" ? "on" : ""}">Change sets <span class="n">${pendingN}</span></a>`,
  ].join("");
  $("#nav").querySelectorAll("a").forEach(a => a.onclick = e => { e.preventDefault(); view = a.dataset.v; open = null; form = null; render(); });
  const m = $("#main");
  if (view === "outstanding") m.innerHTML = outstanding();
  else if (view === "cs") m.innerHTML = changeSets();
  else m.innerHTML = register(view);
  m.querySelectorAll("[data-open]").forEach(el => el.onclick = e => { e.preventDefault(); openItem(el.dataset.open); });
  m.querySelectorAll("[data-new]").forEach(el => el.onclick = () => { open = null; form = {mode: "create", kind: el.dataset.new, fields: {}, links: []}; renderDetail(); });
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
        <div class="small muted">${esc(b.fields.Gist || "")} — ${esc(b.evidence.join("; "))}</div></div>`).join("") || '<div class="blk muted">no blocks yet</div>'}
      <div id="raw-${c.id}"></div></div>`).join("") || '<p class="muted">No change sets yet. Open an item and make a move.</p>');
}

/* ---------- detail drawer ---------- */
function openItem(id) { open = id; form = null; renderDetail(); }
function renderDetail() {
  const d = $("#detail");
  if (!open && !form) { d.hidden = true; return; }
  d.hidden = false;
  if (form && form.mode === "create") { d.innerHTML = createForm(); wire(d); return; }
  const i = S.byId[open]; if (!i) { d.hidden = true; return; }
  const k = i.kind, changed = new Set();
  i.pending.forEach(p => { const b = S.change_sets.find(c => c.id === p.cs)?.blocks.find(b => b.n === p.n); if (b) Object.keys(b.fields).forEach(f => changed.add(f.toLowerCase())); });
  const fld = (key, v) => `<div class="field ${changed.has(key) ? "changed" : ""}"><label>${esc(S.model.labels[key] || key)}</label><div class="v">${esc(v) || '<span class="muted">—</span>'}</div></div>`;
  const moves = (S.model.transitions[k] || {})[i.status] || [];
  d.innerHTML = `<button class="ghost close" id="close-detail">×</button>
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
  wire(d);
}
function wire(d) {
  $("#close-detail", d)?.addEventListener("click", () => { open = null; form = null; renderDetail(); });
  d.querySelectorAll("[data-open]").forEach(el => el.onclick = e => { e.preventDefault(); openItem(el.dataset.open); });
  d.querySelectorAll("[data-move]").forEach(el => el.onclick = () => { form = {mode: "move", to: el.dataset.move, fields: {}, links: []}; renderDetail(); });
  $("#edit-btn", d)?.addEventListener("click", () => { form = {mode: "edit", fields: {}, links: []}; renderDetail(); });
  $("#cancel", d)?.addEventListener("click", () => { form = null; renderDetail(); });
  $("#submit", d)?.addEventListener("click", submit);
  d.querySelectorAll("[data-f]").forEach(el => el.oninput = () => form.fields[el.dataset.f] = el.value);
  $("#new-link", d)?.addEventListener("input", e => form.linkText = e.target.value);
  $("#new-link-word", d)?.addEventListener("change", e => form.linkWord = e.target.value);
  $("#evidence", d)?.addEventListener("input", e => form.evidence = e.target.value);
  $("#gist", d)?.addEventListener("input", e => form.gist = e.target.value);
}
const input = (key, val = "", req = false) => {
  const c = S.model.choices[key];
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
  return `<div class="form"><h3>${esc(i.status)} → ${esc(form.to)}</h3>
    ${fields.map(f => input(f, form.fields[f] ?? i[f] ?? "", true)).join("")}
    ${links.length ? `<p class="small muted">This move needs a link: ${links.map(esc).join(", ")}. ${i.links.some(l => links.some(w => l.toLowerCase().startsWith(w))) ? "Already present, or add another below." : "Add it below, or create the record first from its register and link <code>item n</code>."}</p>` : ""}
    ${linkAdder(k)}${tail()}</div>`;
}
function editForm(i) {
  const k = i.kind;
  return `<div class="form"><h3>Edit fields</h3>${["title", ...S.model.short[k], ...S.model.long[k]].map(f => input(f, form.fields[f] ?? i[f] ?? "")).join("")}${linkAdder(k)}${tail()}</div>`;
}
function createForm() {
  const k = form.kind, req = S.model.create[k];
  return `<button class="ghost close" id="close-detail">×</button><span class="eyebrow">New</span><h2>${S.model.names[k]}</h2>
    <div class="field"><label>Starts in</label><select data-f="__status">${[S.model.first[k], ...((S.model.transitions[k] || {})[S.model.first[k]] || [])].map(st => `<option ${form.fields.__status === st ? "selected" : ""}>${st}</option>`).join("")}</select></div><div class="form">
    ${["title", ...S.model.short[k], ...S.model.long[k]].filter(f => f !== "notes").map(f => input(f, form.fields[f] ?? "", req.includes(f))).join("")}
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
  } catch (e) { err.textContent = e.message; }
}
function parseDate(s) { const m = /^(\d{1,2}) (\w+) (\d{4})/.exec(s || ""); if (!m) return null; const mi = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"].indexOf(m[2]); return mi < 0 ? null : new Date(+m[3], mi, +m[1]); }

/* ---------- boot ---------- */
try { $("#made-by").value = localStorage.getItem("madeBy") || ""; } catch {}
$("#made-by").addEventListener("change", () => { try { localStorage.setItem("madeBy", madeBy()); } catch {} load(); });
$("#close-session").addEventListener("click", async () => { try { const r = await post("/api/close-session", {}); toast(`${r.changeSet} closed for the ingester`); load(); } catch (e) { toast(e.message); } });
load();
