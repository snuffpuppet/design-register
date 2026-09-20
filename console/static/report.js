(function () {
  const html = htm.bind(preact.h);
  const { useState, useEffect } = preactHooks;
  function Report() {
    const S = Store, n = +S.ui.view.split(":")[1], view = S.views[n]; if (!view) return null;
    const [secs, setSecs] = useState(null), [text, setText] = useState(""), [msg, setMsg] = useState("");
    useEffect(() => { S.post("/api/report/sections", { view }).then(setSecs); setText(""); }, [S.ui.view, JSON.stringify(view.filter)]);
    const saveView = patch => { const vs = S.views.slice(); vs[n] = { ...view, ...patch }; S.post("/api/views", { views: vs }).then(r => { S.views = r.views; S.emit(); }); };
    const rows = secs?.table || [];
    const table = (xs, cols) => html`<table><thead><tr>${cols.map(c => html`<th>${S.model.labels[c] || c}</th>`)}</tr></thead>
      <tbody>${xs.map(r => html`<tr>${cols.map(c => html`<td>${c === "id" ? html`<span class=${"pill " + (r.kind || r.id.split("-")[0]) + " lnk"} onClick=${() => S.set({ open: r.id })}>${r.id}</span>` : c === "status" ? html`<span class="st">${r.status}</span>` : (r[c] ?? "–")}</td>`)}</tr>`)}</tbody></table>`;
    const summarise = async () => { const r = await S.post("/api/report/summary", { view }); setText(r.text); };
    const copy = async () => { try { await navigator.clipboard.writeText(text); setMsg("Copied."); } catch { setMsg("Copy is blocked here; select the text and copy it by hand."); } };
    const push = async () => { try { const r = await S.post("/api/push/build", {}); setMsg("Built " + (r.pages?.length ?? 0) + " pages into push/. Run /push-confluence to send."); } catch (e) { setMsg(e.message); } };
    return html`<div class="main-col">
      <div class="bar top"><span class="muted">Reports /</span><span class="h2">${view.name}</span><div class="sp"></div>
        <button class="btn" onClick=${summarise}>Draft email summary</button><button class="btn pri" onClick=${push}>Build full-register Confluence push</button></div>
      <div class="bar chips"><span class="chip">Since <input class="inp cell" style="width:150px" value=${view.filter.since || ""} onChange=${e => saveView({ filter: { ...view.filter, since: e.target.value } })} placeholder="8 September 2026" /></span>
        <span class="chip">Sections <b>${view.sections.join(", ")}</b></span><span class="chip">Columns <b>${view.columns.join(", ")}</b></span>
        <div class="sp"></div><span class="muted small">Saved view · edits change the saved filter</span></div>
      <div class="rep">
        <div class="rep-main">
          ${view.sections.includes("moved") && secs ? html`<div class="card"><div class="h3">Moved this week <span class="muted">${secs.moved.length}</span></div>${table(secs.moved.map(m => ({ ...m, status: m.from + " → " + m.to })), ["id", "title", "status", "owner"])}</div>` : null}
          ${view.sections.includes("raised") && secs ? html`<div class="card"><div class="h3">Raised <span class="muted">${secs.raised.length}</span></div>${table(secs.raised, ["id", "title", "status", "owner"])}</div>` : null}
          ${view.sections.includes("outstanding") && secs ? html`<div class="card"><div class="h3">Outstanding for SLT <span class="muted">${secs.outstanding.length}</span></div>${table(secs.outstanding.map(o => ({ ...o, due: o.overdue ? "Overdue " + o.overdue + " d" : o.due })), ["id", "title", "status", "due"])}</div>` : null}
          ${view.sections.includes("gaps") && secs ? html`<div class="card"><div class="h3">Register gaps <span class="muted">${secs.gaps.length}</span></div><div class="small">${Object.entries(secs.gaps.reduce((a, g) => (a[g.rule] = (a[g.rule] || 0) + 1, a), {})).sort((a, b) => b[1] - a[1]).map(([r, c]) => html`<span class="chip">${r} <b class="mono">${c}</b></span> `)}</div></div>` : null}
          ${secs?.corrections?.length ? html`<div class="card"><h3>Historical corrections</h3>${table(secs.corrections, ["id","title","from","to"])}</div>` : null}
          ${secs?.pending?.length ? html`<div class="card"><h3>Pending proposals</h3><p>These values include changes awaiting the ingester.</p>${table(secs.pending,["id","title","status"])}</div>` : null}
          ${view.sections.includes("table") ? html`<div class="card"><div class="h3">${view.name} <span class="muted">${rows.length}</span></div>${table(rows, view.columns)}</div>` : null}
        </div>
        <div class="card rep-side"><div class="h3">Email summary</div>
          <textarea class="inp" style="min-height:260px;font-size:12px" value=${text} onInput=${e => setText(e.target.value)} placeholder="Draft email summary fills this from the sections." />
          <button class="btn" disabled=${!text} onClick=${copy}>Copy</button>${msg ? html`<div class="muted small">${msg}</div>` : null}</div>
      </div></div>`;
  }
  window.Report = Report;
})();
