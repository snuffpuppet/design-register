(function () {
  const html = htm.bind(preact.h);
  const { useState } = preactHooks;
  function Bulk() {
    const S = Store, ids = [...S.ui.selection], items = ids.map(id => S.byId[id]).filter(Boolean);
    const [mode, setMode] = useState(null), [field, setField] = useState(""), [value, setValue] = useState(""), [word, setWord] = useState(""), [target, setTarget] = useState(""), [survivor, setSurvivor] = useState(""), [reason, setReason] = useState(""), [err, setErr] = useState("");
    if (!items.length) return null;
    const kinds = [...new Set(items.map(i => i.kind))];
    const common = arrs => arrs.reduce((a, b) => a.filter(x => b.includes(x)));
    const fields = common(kinds.map(k => ["title", ...S.model.short[k], ...S.model.long[k]]));
    const states = common(kinds.map(k => [...new Set(Object.values(S.model.transitions[k] || {}).flat())]));
    const words = common(kinds.map(k => Object.keys(S.model.linkWords[k] || {})));
    const done = async () => { setMode(null); setErr(""); await S.load(); S.set({ selection: new Set() }); };
    const run = async fn => { try { await fn(); await done(); } catch (e) { setErr(e.message); await S.load(); } };
    const bulk = body => S.post("/api/bulk", { ids, ...body }).then(r => { if (r.failed) throw new Error(`Wrote ${r.written.length}; stopped at ${r.failed.id}: ${r.failed.error}`); });
    const opts = k => S.model.choices[k] || (k === "scope" ? S.model.scopes : k === "phase" ? S.model.phases : k === "owner" ? S.model.owners : null);
    // Set field, Link to, Withdraw and Delete write; refuse locally before the round trip, same message as cells.js.
    const guarded = fn => () => { if (!S.ui.madeBy?.trim()) { Store.toast("Set Made by first, at the top of the table."); return; } run(fn); };
    return html`<div class="bar bulk">
      <span class="b">${items.length} selected</span><span class="muted">·</span>
      ${!mode ? html`
        <button class="btn" onClick=${() => setMode("set")}>Set field</button>
        <button class="btn" onClick=${() => setMode("move")}>Move to…</button>
        <button class="btn" onClick=${() => setMode("link")}>Link to…</button>
        <button class="btn" onClick=${() => run(async()=>{const r=await S.post('/api/reviews/create',{name:'Review selected items',ids});S.set({view:'reviews:'+r.id,open:null});})}>Review / merge</button>
        <button class="btn" onClick=${() => run(async()=>{const r=await S.post('/api/meetings/create',{name:'Meeting agenda',ids});S.set({view:'meetings:'+r.id,session:r.id,open:null});})}>Meeting agenda</button>
        <button class="btn" onClick=${guarded(() => bulk({ op: "withdraw", gist: "withdrawn in bulk" }))}>Withdraw</button>
        <button class="btn ghost danger" onClick=${() => setMode("delete")}>Delete</button>` : null}
      ${mode === "set" ? html`<select class="inp" value=${field} onChange=${e => { setField(e.target.value); setValue(""); }}><option value="">field…</option>${fields.map(f => html`<option value=${f}>${S.model.labels[f] || f}</option>`)}</select>
        ${field && opts(field)?.length ? html`<select class="inp" value=${value} onChange=${e => setValue(e.target.value)}><option value="">–</option>${opts(field).map(o => html`<option value=${o}>${o}</option>`)}</select>` : html`<input class="inp" value=${value} onInput=${e => setValue(e.target.value)} placeholder="value" />`}
        <button class="btn pri" disabled=${!field} onClick=${guarded(() => bulk({ op: "set", fields: { [S.model.labels[field] || field]: value }, gist: (S.model.labels[field] || field) + " set in bulk" }))}>Apply to ${items.length}</button>` : null}
      ${mode === "move" ? html`<select class="inp" value="" onChange=${e => { if (e.target.value) { MoveForm.open({ ids, to: e.target.value }); setMode(null); } }}><option value="">state…</option>${states.map(s => html`<option value=${s}>${s}</option>`)}</select>` : null}
      ${mode === "link" ? html`<select class="inp" value=${word} onChange=${e => setWord(e.target.value)}><option value="">link word…</option>${words.map(w => html`<option value=${w}>${w}</option>`)}</select>
        ${word ? html`<${Picker.Inline} word=${word} kind=${kinds[0]} value=${target} onPick=${setTarget} />` : null}
        <button class="btn pri" disabled=${!word || !target.trim()} onClick=${guarded(() => bulk({ op: "link", links: [word + " " + target], gist: "linked in bulk" }))}>Apply to ${items.length}</button>` : null}
      ${mode === "merge" ? html`<span class="small">Survivor</span><select class="inp" value=${survivor} onChange=${e => setSurvivor(e.target.value)}><option value="">pick…</option>${items.map(i => html`<option value=${i.id}>${i.id} ${i.title}</option>`)}</select>
        <button class="btn pri" disabled=${!survivor} onClick=${() => run(() => S.post("/api/merge", { survivor, losers: ids.filter(x => x !== survivor) }))}>Merge ${items.length - 1} into ${survivor || "…"}</button>` : null}
      ${mode === "delete" ? html`<input class="inp" value=${reason} onInput=${e => setReason(e.target.value)} placeholder="reason, goes into History" />
        <button class="btn pri danger" disabled=${!reason.trim()} onClick=${guarded(async () => { let n = 0; for (const id of ids) { try { await S.post("/api/delete", { id, reason }); n++; } catch (e) { throw new Error(`Deleted ${n}; stopped at ${id}: ${e.message}`); } } })}>Delete ${items.length}</button>` : null}
      ${mode ? html`<button class="btn ghost" onClick=${() => { setMode(null); setErr(""); }}>Cancel</button>` : null}
      ${err ? html`<span class="miss small">${err}</span>` : null}
      <div class="sp"></div><span class="muted small">Esc to clear</span>
    </div>`;
  }
  window.Bulk = Bulk;
})();
