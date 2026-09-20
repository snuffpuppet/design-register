(function () {
  const html = htm.bind(preact.h);
  const { useState, useEffect } = preactHooks;
  const MoveForm = {
    open({ ids, to }) { Store.set({ move: { ids, to } }); },
    close() { Store.set({ move: null }); },
  };
  // Field keys behind a needs label, so a shared input can be drawn for each missing thing.
  function keyFor(kind, to, label) {
    const m = Store.model;
    for (const f of m.required[kind]?.[to] || []) {
      if (f.startsWith("link:")) { if (label.startsWith("Links: " + f.slice(5))) return { link: f.slice(5).split(":")[0] }; continue; }
      if ((m.labels[f] || f) === label || (f === "options" && label.startsWith("Options"))) return { field: f };
    }
    for (const sp of m.specials) if (sp.kind === kind && sp.state === to && sp.text === label) return { field: sp.field, prefix: sp.value };
    return { field: label.toLowerCase() };
  }
  function Form() {
    const S = Store, mv = S.ui.move; if (!mv) return null;
    const items = mv.ids.map(id => S.byId[id]).filter(Boolean);
    const [needs, setNeeds] = useState(null), [fields, setFields] = useState({}), [per, setPer] = useState({}), [note, setNote] = useState(""), [busy, setBusy] = useState(false), [err, setErr] = useState("");
    const kinds = [...new Set(items.map(i => i.kind))];
    useEffect(() => { S.post("/api/needs", { ids: mv.ids, to: mv.to, fields: {} }).then(r => setNeeds(r.needs)).catch(e => setErr(e.message)); }, [mv.ids.join(","), mv.to]);
    if (!needs) return html`<div class="modal" onClick=${MoveForm.close}><div class="dlg" onClick=${e => e.stopPropagation()}>
      <div class="dlg-b">${err ? html`<div class="miss">${err}</div>` : html`<div class="muted">Checking what ${mv.to} needs…</div>`}</div>
      <div class="dlg-f"><div class="sp"></div><button class="btn" onClick=${MoveForm.close}>Cancel</button></div>
    </div></div>`;
    // Shared: a label missing on every item of the same kind. Per item: the rest.
    const missing = id => (needs[id]?.missing || []).filter(x => !x.includes("not an allowed move"));
    const shared = kinds.length === 1 ? missing(items[0].id).filter(l => items.every(i => missing(i.id).includes(l))) : [];
    const blocked = items.filter(i => needs[i.id] && !needs[i.id].ok && (needs[i.id].missing || []).some(x => x.includes("not an allowed move")));
    const labelKind = kinds.length === 1 ? S.model.names[kinds[0]].toLowerCase() + (items.length > 1 ? "s" : "") : "items";
    const value = (id, label) => per[id]?.[label] ?? fields[label] ?? "";
    const ready = !blocked.length && items.every(i => missing(i.id).every(l => String(value(i.id, l)).trim()));
    const apply = async () => {
      setBusy(true); setErr("");
      try {
        if (!S.ui.madeBy.trim()) throw new Error("Say who you are first (Made by).");
        if (items.length === 1) {
          const i = items[0], f = {}, links = [];
          for (const l of missing(i.id)) {
            const k = keyFor(i.kind, mv.to, l);
            if (k.field) f[S.model.labels[k.field] || k.field] = value(i.id, l);
            else if (k.link) links.push(k.link + " " + value(i.id, l));
          }
          await S.post("/api/transition", { id: i.id, to: mv.to, fields: f, links, gist: note });
        } else {
          const f = {}, links = [];
          for (const l of shared) {
            const k = keyFor(kinds[0], mv.to, l);
            if (k.field) f[S.model.labels[k.field] || k.field] = fields[l];
            else if (k.link) links.push(k.link + " " + fields[l]);
          }
          const perItem = {};
          for (const i of items) {
            perItem[i.id] = {fields:{},links:[]};
            for (const l of missing(i.id)) if (!shared.includes(l) && per[i.id]?.[l]) {
              const k=keyFor(i.kind,mv.to,l);
              if(k.field) perItem[i.id].fields[S.model.labels[k.field] || k.field]=per[i.id][l];
              else if(k.link) perItem[i.id].links.push(k.link+' '+per[i.id][l]);
            }
          }
          const r = await S.post("/api/bulk", {ids:items.map(i=>i.id),op:"transition",to:mv.to,fields:f,links,perItem,gist:note});
          if (r.failed) throw new Error(`Wrote ${r.written.length}; stopped at ${r.failed.id}: ${r.failed.error}`);
        }
        await S.load(); MoveForm.close();
      } catch (e) { setErr(e.message); await S.load(); }
      setBusy(false);
    };
    const excl = items.length === 1 ? items[0].id : undefined;
    const input = (label, get, set, kind) => {
      const k = keyFor(kind, mv.to, label);
      const opts = k.field && (S.model.choices[k.field] || (k.field === "scope" ? S.model.scopes : k.field === "phase" ? S.model.phases : k.field === "owner" ? S.model.owners : null));
      if (k.link) return html`<${Picker.Inline} word=${k.link} kind=${kind} value=${get()} onPick=${set} exclude=${excl} />`;
      if (opts && opts.length) return html`<select class="inp" value=${get()} onChange=${e => set(e.target.value)}><option value="">–</option>${opts.map(o => html`<option value=${o}>${o}</option>`)}</select>`;
      if (k.field && S.model.long[kind].includes(k.field)) return html`<textarea class="inp" value=${get()} onInput=${e => set(e.target.value)} />`;
      return html`<input class="inp" value=${get()} onInput=${e => set(e.target.value)} placeholder=${k.prefix || ""} />`;
    };
    return html`<div class="modal" onClick=${MoveForm.close}><div class="dlg" onClick=${e => e.stopPropagation()}>
      <div class="dlg-h"><span class="h2">Move ${items.length} ${labelKind} to ${mv.to}</span>
        <span class="muted small">${shared.length ? "Shared: " + shared.join(", ") + "." : "Nothing shared to ask."}</span></div>
      <div class="dlg-b">
        ${!S.ui.madeBy ? html`<div class="field"><label>Made by</label><input class="inp" value=${S.ui.madeBy} onInput=${e => { S.set({ madeBy: e.target.value }); try { localStorage.setItem("madeBy", e.target.value); } catch {} }} /></div>` : null}
        ${shared.length ? html`<div class="grid2">${shared.map(l => html`<div class="field"><label>${l} · required for ${mv.to}</label>${input(l, () => fields[l] || "", v => setFields({ ...fields, [l]: v }), kinds[0])}</div>`)}</div>` : null}
        <div class="field"><label>Per item</label><div class="card tight">
          ${items.map(i => html`<div class="prow"><span class=${"pill " + i.kind}>${i.id}</span><span class="small">${needs[i.id]?.from} → ${mv.to}</span>
            ${blocked.includes(i) ? html`<span class="miss small">${needs[i.id].missing[0]}</span>` : null}
            ${missing(i.id).filter(l => !shared.includes(l)).map(l => html`<span class="miss small">${l}</span>${input(l, () => per[i.id]?.[l] || "", v => setPer({ ...per, [i.id]: { ...(per[i.id] || {}), [l]: v } }), i.kind)}`)}
            ${!blocked.includes(i) && !missing(i.id).filter(l => !shared.includes(l)).length ? html`<span class="muted small">ready</span>` : null}</div>`)}
        </div></div>
        <div class="field"><label>History note · applied to each item</label><input class="inp" value=${note} onInput=${e => setNote(e.target.value)} /></div>
        ${err ? html`<div class="miss">${err}</div>` : null}
      </div>
      <div class="dlg-f"><span class="muted small">Writes ${items.length} file${items.length === 1 ? "" : "s"}, stamps updated, appends History</span><div class="sp"></div>
        <button class="btn" onClick=${MoveForm.close}>Cancel</button><button class="btn pri" disabled=${!ready || busy} onClick=${apply}>Apply to ${items.length}</button></div>
    </div></div>`;
  }
  MoveForm.Form = Form;
  window.MoveForm = MoveForm;
})();
