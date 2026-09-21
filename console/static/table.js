(function () {
  const html = htm.bind(preact.h);
  const DEFAULT_COLS = ["id", "title", "status", "scope", "owner", "links", "issues"];
  function label(k) { return { id: "Id", title: "Title", links: "Links", issues: "Issues", gap: "Gap", support: "Support", group: "Duplicates", reviewed: "Reviewed" }[k] || Store.model.labels[k] || k; }
  const GROUP_LABELS = { "": "Group by…", kind: "Type", status: "Status", scope: "Scope", phase: "Phase", owner: "Owner" };
  function groupValue(i, by) { return by === "kind" ? (Store.model.names[i.kind] || i.kind) : (i[by] || ""); }
  // Rows in group order, a header entry ({ header, n }) ahead of each run when Store.ui.groupBy is set.
  function grouped(rows, by) {
    if (!by) return rows.map(row => ({ row }));
    const sorted = rows.slice().sort((a, b) => { const va = groupValue(a, by), vb = groupValue(b, by); return va < vb ? -1 : va > vb ? 1 : (a.id < b.id ? -1 : 1); });
    const out = []; let last = null;
    for (const r of sorted) {
      const v = groupValue(r, by);
      if (v !== last) { out.push({ header: v || "–", n: sorted.filter(x => groupValue(x, by) === v).length }); last = v; }
      out.push({ row: r });
    }
    return out;
  }
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
  // The one field a failure under the selected rule names, if any: an editor for a real field of this
  // item's type, a Link button when the failure names a missing link, else the failure text itself.
  function GapCell({ i }) {
    const [edit, setEdit] = preactHooks.useState(false), [linking, setLinking] = preactHooks.useState(false);
    const f = (Store.failuresById[i.id] || []).find(x => x.rule === Store.ui.filter.rule);
    if (!f) return html`<span class="muted">–</span>`;
    const text = f.text, lower = text.toLowerCase();
    const editable = k2 => (Store.model.short[i.kind] || []).includes(k2) || (Store.model.long[i.kind] || []).includes(k2) || k2 === "title";
    const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const field = Object.keys(Store.model.labels).find(k2 => {
      if (!editable(k2)) return false;
      const lbl = esc((Store.model.labels[k2] || k2).toLowerCase());
      return new RegExp("\\b" + lbl + "\\b(?=[:;]|\\s|$)").test(lower);
    });
    if (field) {
      if (edit) return html`<${Cells.Editor} item=${i} field=${field} long=${(Store.model.long[i.kind] || []).includes(field)} onDone=${() => setEdit(false)} />`;
      const v = i[field];
      return html`<span class="ed" onClick=${e => { e.stopPropagation(); setEdit(true); }}>${v ? v : html`<span class="muted">–</span>`}</span>`;
    }
    const m = /links:\s*(.+?)\s*…/i.exec(text);
    if (m) {
      const word = m[1].trim();
      return html`<span class="stwrap">
        <button class="btn ghost" onClick=${e => { e.stopPropagation(); setLinking(true); }}>Link ${word}</button>
        ${linking ? html`<${Picker.LinkTo} item=${i} word=${word} onClose=${() => setLinking(false)} />` : null}
      </span>`;
    }
    return html`<span class="muted small">${text}</span>`;
  }
  function Cell({ i, k }) {
    const [edit, setEdit] = preactHooks.useState(false);
    if (k === "id") return html`<span class=${"pill " + i.kind + " lnk"} onClick=${e => { e.stopPropagation(); Store.set({ open: i.id, focus: i.id }); }}>${i.id}</span>`;
    if (k === "status") return html`<${Cells.StatusCell} item=${i} />`;
    if (k === "links") return html`<span class="mono muted">${i.links.length || "–"}</span>`;
    if (k === "issues") { const n = (Store.failuresById[i.id] || []).length; return n ? html`<span class="warn"></span> ${n}` : html`<span class="muted">–</span>`; }
    if (k === "gap") return html`<${GapCell} i=${i} />`;
    if (k === "support") {
      const s = (Store.suggestionsById[i.id] || [])[0];
      if (!s) return html`<span class="muted">–</span>`;
      return html`<span class="small">${s.rule} · offers ${Store.model.names[s.kind]}: ${s.fields.title || ""}</span>
        <button class="btn ghost" onClick=${e => { e.stopPropagation(); Store.set({ open: i.id, focus: i.id }); }}>Open and accept</button>`;
    }
    if (k === "group") {
      const g = Store.state.dupes.find(x => (x.ids || x).includes(i.id));
      const ids = (g ? (g.ids || g) : []).filter(id => id !== i.id);
      if (!ids.length) return html`<span class="muted">–</span>`;
      return html`<span class="pills">${ids.map(id => html`<span class=${"pill " + (Store.byId[id]?.kind || "")} onClick=${e => { e.stopPropagation(); Store.set({ open: id, focus: id }); }}>${id}</span>`)}</span>
        <button class="btn ghost" onClick=${e => { e.stopPropagation(); Store.post("/api/rationalise/not-duplicates", { ids: g.ids || g }).then(Store.load).catch(err => Store.toast(err.message)); }}>Not duplicates</button>`;
    }
    if (k === "reviewed") return html`<button class="btn ghost" onClick=${e => { e.stopPropagation(); Store.post("/api/rationalise/reviewed", { id: i.id }).then(Store.load).catch(err => Store.toast(err.message)); }}>Mark reviewed</button>`;
    if (edit) return html`<${Cells.Editor} item=${i} field=${k} onDone=${() => setEdit(false)} />`;
    const v = i[k];
    return html`<span class="ed" onClick=${e => { e.stopPropagation(); setEdit(true); }}>${v ? v : html`<span class="muted">${k === "estimate" ? "Not sized" : "–"}</span>`}</span>`;
  }
  function Chip({ label, value, onClear }) {
    return html`<span class="chip">${label} ${value ? html`<b>${value}</b>` : null}${onClear ? html`<span class="x" onClick=${onClear}>×</span>` : null}</span>`;
  }
  function Table() {
    const S = Store, ui = S.ui, rows = S.rows();
    const cols = ui.columns || S.columnsFor() || DEFAULT_COLS;
    const f = ui.filter;
    const setF = patch => S.set({ filter: { ...f, ...patch } });
    const title = ui.view === "integrity" && f.rule ? `${f.rule} · ${S.model.rules[f.rule] || ""}`
      : ui.view === "all" ? "All items" : S.model.names[ui.view] ? S.model.names[ui.view] + "s" : ui.view[0].toUpperCase() + ui.view.slice(1);
    const disp = grouped(rows, ui.groupBy);
    // The screen order j/k should follow: the grouped, sorted rows, headers left out.
    Store.display = disp.filter(d => d.header === undefined).map(d => d.row);
    return html`<div class="main-col">
      <div class="bar top"><span class="h2">${ui.mode === "rationalise" ? "Rationalise" : "Desktop"} · ${title}</span><span class="muted">${rows.length}</span><div class="sp"></div>
        <input class="inp search" placeholder="Search title, id, notes" value=${f.q} onInput=${e => setF({ q: e.target.value })} />
        <input class="inp madeby" placeholder="Made by" value=${ui.madeBy} onInput=${e => { S.set({ madeBy: e.target.value }); try { localStorage.setItem("madeBy", e.target.value); } catch {} }} />
        <button class="btn pri" onClick=${() => CreateForm.open({ kind: Store.model.states[Store.ui.view] ? Store.ui.view : "OI" })}>+ New item</button></div>
      ${ui.mode === 'rationalise' ? html`<div class="bar muted">Corrections save immediately. Status changes skip workflow requirements; integrity gaps remain visible.</div>` : null}
      <div class="bar chips">
        ${ui.mode === 'rationalise' ? html`<${QuickFilters} f=${f} />` : null}
        ${f.types.includes("CP") || ui.view === "CP" ? html`<label>Phase <select class="inp" aria-label="Filter by phase" value=${JSON.stringify(f.phases || [])} onChange=${e => S.set({filter:{...f,phases:JSON.parse(e.target.value)},selection:new Set(),lastSel:null})}>
          <option value="[]">All phases</option>
          ${(f.phases || []).length > 1 ? html`<option value=${JSON.stringify(f.phases)}>Multiple phases</option>` : null}
          <option value='[""]'>No phase</option>
          ${[...new Set([...(S.model.phases || []),...S.state.items.map(i=>i.phase),...(f.phases || [])])].filter(Boolean).sort().map(p=>html`<option value=${JSON.stringify([p])}>${p}</option>`)}
        </select></label>` : null}
        ${f.types.length ? html`<${Chip} label="Type" value=${f.types.join(", ")} onClear=${() => setF({ types: [] })} />` : null}
        ${f.statuses.length ? html`<${Chip} label="Status" value=${f.statuses.join(", ")} onClear=${() => setF({ statuses: [] })} />` : null}
        ${f.scopes.length ? html`<${Chip} label="Scope" value=${f.scopes.map(s => s || "No scope").join(", ")} onClear=${() => setF({ scopes: [] })} />` : null}
        ${f.phases?.length ? html`<${Chip} label="Phase" value=${f.phases.map(p => p || "No phase").join(", ")} onClear=${() => setF({ phases: [] })} />` : null}
        ${f.owners.length ? html`<${Chip} label="Owner" value=${f.owners.join(", ")} onClear=${() => setF({ owners: [] })} />` : null}
        ${f.rule ? html`<${Chip} label="Failing" value=${f.rule} onClear=${() => setF({ rule: "" })} />` : null}
        <${FilterAdd} setF=${setF} f=${f} />
        <select class="chip add" value=${ui.groupBy} onChange=${e => S.set({ groupBy: e.target.value })}>
          ${Object.entries(GROUP_LABELS).map(([v, l]) => html`<option value=${v}>${v ? "Group by " + l : l}</option>`)}
        </select>
      </div>
      <div class="bar"><label>Show field <select class="inp" value="" onChange=${e=>{if(e.target.value)S.set({columns:[...new Set([...cols,e.target.value])]});}}><option value="">Choose…</option>${[...new Set(['raised-on','closed-on','description',...Object.values(S.model.short).flat(),...Object.values(S.model.long).flat()])].filter(k=>!cols.includes(k)).map(k=>html`<option value=${k}>${label(k)}</option>`)}</select></label><button class="btn ghost" onClick=${()=>S.set({columns:null})}>Reset columns</button></div>
      <${Bulk} key=${ui.mode} />
      <div class="tbl-wrap"><table>
        <thead><tr><th class="c-sel"><span class=${"cb" + (rows.length && rows.every(r => ui.selection.has(r.id)) ? " on" : "")} onClick=${() => {
          const all = rows.length && rows.every(r => ui.selection.has(r.id)), sel = new Set(ui.selection);
          rows.forEach(r => all ? sel.delete(r.id) : sel.add(r.id));
          S.set({ selection: sel });
        }}></span></th>${cols.map(k => html`<th class=${"c-" + k}>${label(k)}</th>`)}</tr></thead>
        <tbody>${disp.map(d => d.header !== undefined
          ? html`<tr class="grp"><td colspan=${cols.length + 1}>${d.header} · ${d.n}</td></tr>`
          : html`<tr key=${d.row.id} class=${(ui.focus === d.row.id ? "focus " : "") + (ui.selection.has(d.row.id) ? "sel" : "")} onClick=${() => S.set({ focus: d.row.id })}>
          <td class="c-sel"><span class=${"cb" + (ui.selection.has(d.row.id) ? " on" : "")} onClick=${e => { e.stopPropagation(); toggle(d.row.id, e.shiftKey); }}></span></td>
          ${cols.map(k => html`<td class=${"c-" + k}><${Cell} i=${d.row} k=${k} /></td>`)}</tr>`)}</tbody>
      </table></div>
      <div class="bar foot muted">${rows.length} of ${S.state.items.length} · j/k move · Enter opens · / search</div>
    </div>`;
  }
  // One "+ Filter" control: pick a facet, then a value from what the data holds.
  function QuickFilters({ f }) {
    const S = Store, register = S.model.states[S.ui.view] ? S.ui.view : null;
    const types = register ? [register] : f.types;
    const scopes = [...new Set([...S.model.scopes, ...S.state.items.map(i => i.scope || ""), ...f.scopes])].filter(Boolean).sort();
    const value = values => values.length ? JSON.stringify(values) : "";
    const change = (field, raw) => S.set({
      ...(field === "types" && register ? { view: "all" } : {}),
      filter: { ...S.ui.filter, [field]: raw ? JSON.parse(raw) : [] },
      selection: new Set(), lastSel: null,
    });
    return html`
      <label>Type <select class="inp" aria-label="Filter by item type" value=${value(types)} onChange=${e => change("types", e.target.value)}>
        <option value="">All types</option>
        ${types.length > 1 ? html`<option value=${value(types)}>Multiple types</option>` : null}
        ${Object.entries(S.model.names).map(([k, name]) => html`<option value=${value([k])}>${k} · ${name}</option>`)}
      </select></label>
      <label>Scope <select class="inp" aria-label="Filter by item scope" value=${value(f.scopes)} onChange=${e => change("scopes", e.target.value)}>
        <option value="">All scopes</option>
        ${f.scopes.length > 1 ? html`<option value=${value(f.scopes)}>Multiple scopes</option>` : null}
        <option value=${value([""])}>No scope</option>
        ${scopes.map(s => html`<option value=${value([s])}>${s}</option>`)}
      </select></label>`;
  }

  const FACET_LABELS = { types: "Type", statuses: "Status", scopes: "Scope", phases: "Phase", owners: "Owner", rule: "Failing rule" };
  function FilterAdd({ setF, f }) {
    const [facet, setFacet] = preactHooks.useState("");
    const S = Store;
    const values = { types: Object.keys(S.model.names), statuses: [...new Set(S.state.items.map(i => i.status))].sort(),
                     scopes: S.model.scopes, phases: [...new Set([...(S.model.phases || []), ...S.state.items.map(i=>i.phase)])].filter(Boolean).sort(), owners: S.model.owners, rule: Object.keys(S.counts().byRule).sort() };
    if (!facet) return html`<select class="chip add" value="" onChange=${e => setFacet(e.target.value)}>
      <option value="">+ Filter</option><option value="types">Type</option><option value="statuses">Status</option>
      <option value="scopes">Scope</option><option value="phases">Phase</option><option value="owners">Owner</option><option value="rule">Failing rule</option></select>`;
    return html`<select class="chip add" value="" onChange=${e => { const v = e.target.value; setFacet(""); if (!v) return;
        facet === "rule" ? setF({ rule: v }) : setF({ [facet]: [...new Set([...(f[facet] || []), v])] }); }}>
      <option value="">${FACET_LABELS[facet]}…</option>${values[facet].map(v => html`<option value=${v}>${v}</option>`)}</select>`;
  }
  Table.toggle = toggle;
  window.Table = Table;
})();
