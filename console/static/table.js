(function () {
  const html = htm.bind(preact.h);
  const DEFAULT_COLS = ["id", "title", "status", "scope", "owner", "links", "issues"];
  function label(k) { return { id: "Id", title: "Title", links: "Links", issues: "Issues" }[k] || Store.model.labels[k] || k; }
  // Toggle one id in the selection, or (shift-click) the range from Store.ui.lastSel to it in rows() order.
  function toggle(id, shift) {
    const S = Store, sel = new Set(S.ui.selection);
    if (shift && S.ui.lastSel) {
      const rows = S.rows(), ids = rows.map(r => r.id);
      const a = ids.indexOf(S.ui.lastSel), b = ids.indexOf(id);
      if (a !== -1 && b !== -1) { const [lo, hi] = a < b ? [a, b] : [b, a]; for (let n = lo; n <= hi; n++) sel.add(ids[n]); }
      else sel.has(id) ? sel.delete(id) : sel.add(id);
    } else sel.has(id) ? sel.delete(id) : sel.add(id);
    S.set({ selection: sel, lastSel: id });
  }
  function Cell({ i, k }) {
    const [edit, setEdit] = preactHooks.useState(false);
    if (k === "id") return html`<span class=${"pill " + i.kind + " lnk"} onClick=${e => { e.stopPropagation(); Store.set({ open: i.id, focus: i.id }); }}>${i.id}</span>`;
    if (k === "status") return html`<${Cells.StatusCell} item=${i} />`;
    if (k === "links") return html`<span class="mono muted">${i.links.length || "–"}</span>`;
    if (k === "issues") { const n = (Store.failuresById[i.id] || []).length; return n ? html`<span class="warn"></span> ${n}` : html`<span class="muted">–</span>`; }
    if (edit) return html`<${Cells.Editor} item=${i} field=${k} onDone=${() => setEdit(false)} />`;
    const v = i[k];
    return html`<span class="ed" onClick=${e => { e.stopPropagation(); setEdit(true); }}>${v ? v : html`<span class="muted">–</span>`}</span>`;
  }
  function Chip({ label, value, onClear }) {
    return html`<span class="chip">${label} ${value ? html`<b>${value}</b>` : null}${onClear ? html`<span class="x" onClick=${onClear}>×</span>` : null}</span>`;
  }
  function Table() {
    const S = Store, ui = S.ui, rows = S.rows();
    const cols = ui.columns || DEFAULT_COLS;
    const f = ui.filter;
    const setF = patch => S.set({ filter: { ...f, ...patch } });
    const title = ui.view === "all" ? "All items" : S.model.names[ui.view] ? S.model.names[ui.view] + "s" : ui.view[0].toUpperCase() + ui.view.slice(1);
    return html`<div class="main-col">
      <div class="bar top"><span class="h2">${title}</span><span class="muted">${rows.length}</span><div class="sp"></div>
        <input class="inp search" placeholder="Search title, id, notes" value=${f.q} onInput=${e => setF({ q: e.target.value })} />
        <input class="inp madeby" placeholder="Made by" value=${ui.madeBy} onInput=${e => { S.set({ madeBy: e.target.value }); try { localStorage.setItem("madeBy", e.target.value); } catch {} }} />
        <button class="btn pri" onClick=${() => CreateForm.open({ kind: Store.model.states[Store.ui.view] ? Store.ui.view : "OI" })}>+ New item</button></div>
      <div class="bar chips">
        ${f.types.length ? html`<${Chip} label="Type" value=${f.types.join(", ")} onClear=${() => setF({ types: [] })} />` : null}
        ${f.statuses.length ? html`<${Chip} label="Status" value=${f.statuses.join(", ")} onClear=${() => setF({ statuses: [] })} />` : null}
        ${f.scopes.length ? html`<${Chip} label="Scope" value=${f.scopes.join(", ")} onClear=${() => setF({ scopes: [] })} />` : null}
        ${f.owners.length ? html`<${Chip} label="Owner" value=${f.owners.join(", ")} onClear=${() => setF({ owners: [] })} />` : null}
        ${f.rule ? html`<${Chip} label="Failing" value=${f.rule} onClear=${() => setF({ rule: "" })} />` : null}
        <${FilterAdd} setF=${setF} f=${f} />
      </div>
      <${Bulk} />
      <div class="tbl-wrap"><table>
        <thead><tr><th class="c-sel"><span class=${"cb" + (rows.length && rows.every(r => ui.selection.has(r.id)) ? " on" : "")} onClick=${() => {
          const all = rows.length && rows.every(r => ui.selection.has(r.id)), sel = new Set(ui.selection);
          rows.forEach(r => all ? sel.delete(r.id) : sel.add(r.id));
          S.set({ selection: sel });
        }}></span></th>${cols.map(k => html`<th class=${"c-" + k}>${label(k)}</th>`)}</tr></thead>
        <tbody>${rows.map(i => html`<tr key=${i.id} class=${(ui.focus === i.id ? "focus " : "") + (ui.selection.has(i.id) ? "sel" : "")} onClick=${() => S.set({ focus: i.id })}>
          <td class="c-sel"><span class=${"cb" + (ui.selection.has(i.id) ? " on" : "")} onClick=${e => { e.stopPropagation(); toggle(i.id, e.shiftKey); }}></span></td>
          ${cols.map(k => html`<td class=${"c-" + k}><${Cell} i=${i} k=${k} /></td>`)}</tr>`)}</tbody>
      </table></div>
      <div class="bar foot muted">${rows.length} of ${S.state.items.length} · j/k move · Enter opens · / search</div>
    </div>`;
  }
  // One "+ Filter" control: pick a facet, then a value from what the data holds.
  const FACET_LABELS = { types: "Type", statuses: "Status", scopes: "Scope", owners: "Owner", rule: "Failing rule" };
  function FilterAdd({ setF, f }) {
    const [facet, setFacet] = preactHooks.useState("");
    const S = Store;
    const values = { types: Object.keys(S.model.names), statuses: [...new Set(S.state.items.map(i => i.status))].sort(),
                     scopes: S.model.scopes, owners: S.model.owners, rule: Object.keys(S.counts().byRule).sort() };
    if (!facet) return html`<select class="chip add" value="" onChange=${e => setFacet(e.target.value)}>
      <option value="">+ Filter</option><option value="types">Type</option><option value="statuses">Status</option>
      <option value="scopes">Scope</option><option value="owners">Owner</option><option value="rule">Failing rule</option></select>`;
    return html`<select class="chip add" value="" onChange=${e => { const v = e.target.value; setFacet(""); if (!v) return;
        facet === "rule" ? setF({ rule: v }) : setF({ [facet]: [...new Set([...f[facet], v])] }); }}>
      <option value="">${FACET_LABELS[facet]}…</option>${values[facet].map(v => html`<option value=${v}>${v}</option>`)}</select>`;
  }
  Table.toggle = toggle;
  window.Table = Table;
})();
