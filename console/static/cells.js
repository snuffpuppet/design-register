(function () {
  const html = htm.bind(preact.h);
  const { useState, useEffect, useRef } = preactHooks;
  const CHOICE_FIELDS = k => Store.model.choices[k] || (k === "scope" ? Store.model.scopes : k === "phase" ? Store.model.phases : k === "owner" ? Store.model.owners : null);
  async function write(item, field, value) {
    if (!Store.ui.madeBy?.trim()) {
      Store.toast("Set Made by first, at the top of the table.");
      document.querySelector(".inp.madeby")?.focus();
      return;
    }
    try { await Store.post("/api/edit", { id: item.id, fields: { [Store.model.labels[field] || field]: value }, gist: `${Store.model.labels[field] || field} set` }); await Store.load(); }
    catch (e) { Store.toast(e.message); }
  }
  // Text, date and choice editors. Saves on blur or Enter; Esc abandons.
  function Editor({ item, field, onDone, long }) {
    const [v, setV] = useState(item[field] || ""); const ref = useRef();
    useEffect(() => { ref.current?.focus(); ref.current?.select?.(); }, []);
    const done = async save => { if (save && v !== (item[field] || "")) await write(item, field, v); onDone(); };
    const opts = CHOICE_FIELDS(field);
    if (opts && opts.length && !long) return html`<select ref=${ref} class="inp cell" value=${v} onChange=${e => { setV(e.target.value); write(item, field, e.target.value).then(onDone); }} onBlur=${() => onDone()}>
      <option value="">–</option>${opts.map(o => html`<option value=${o}>${o}</option>`)}${v && !opts.includes(v) ? html`<option value=${v}>${v}</option>` : null}</select>`;
    if (long) return html`<textarea ref=${ref} class="inp cell long" value=${v} onInput=${e => setV(e.target.value)} onBlur=${() => done(true)}
      onKeyDown=${e => { if (e.key === "Escape") done(false); if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) done(true); }} />`;
    return html`<input ref=${ref} class="inp cell" value=${v} onInput=${e => setV(e.target.value)} onBlur=${() => done(true)}
      onKeyDown=${e => { if (e.key === "Escape") done(false); if (e.key === "Enter") done(true); }} />`;
  }
  // The status pill. Click lists every state for the type: reachable ones say what they need, others are greyed.
  function StatusCell({ item }) {
    const [open, setOpen] = useState(false);
    const S = Store, m = S.model, can = m.transitions[item.kind]?.[item.status] || [];
    const need = to => (m.required[item.kind]?.[to] || []).map(f => f.startsWith("link:") ? "link " + f.slice(5) : m.labels[f] || f);
    const pick = to => { setOpen(false); MoveForm.open({ ids: [item.id], to }); };
    return html`<span class="stwrap"><span class=${"st lnk" + (open ? " on" : "")} onClick=${e => { e.stopPropagation(); setOpen(!open); }}>${item.status} ▾</span>
      ${open ? html`<div class="menu" onClick=${e => e.stopPropagation()}>
        ${m.states[item.kind].filter(s => s !== item.status).map(s => can.includes(s)
          ? html`<div class="mi" onClick=${() => pick(s)}><span>${s}</span><span class="muted">${need(s).length ? "needs " + need(s).join(", ") : "ready"}</span></div>`
          : html`<div class="mi off"><span>${s}</span><span>not from ${item.status}</span></div>`)}
      </div>` : null}</span>`;
  }
  window.Cells = { Editor, StatusCell, write };
  Store.toast = msg => { const t = document.getElementById("toast") || Object.assign(document.body.appendChild(document.createElement("div")), { id: "toast", className: "toast" }); t.textContent = msg; t.hidden = false; clearTimeout(t._h); t._h = setTimeout(() => t.hidden = true, 4000); };
})();
