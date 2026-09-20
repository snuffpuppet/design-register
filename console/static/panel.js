(function () {
  const html = htm.bind(preact.h);
  function Hop({ h, word }) {
    return html`<div class="hop"><span class=${"pill " + h.kind}>${h.id}</span><span class="t" onClick=${() => Store.set({ open: h.id, focus: h.id })}>${h.title}</span><span class="st">${h.status}</span></div>`;
  }
  function Title({ i }) {
    const [edit, setEdit] = preactHooks.useState(false);
    if (edit) return html`<${Cells.Editor} item=${i} field="title" onDone=${() => setEdit(false)} />`;
    return html`<div class="ttl ed" onClick=${() => setEdit(true)}>${i.title}</div>`;
  }
  function Chip({ i, field, label }) {
    const [edit, setEdit] = preactHooks.useState(false);
    if (edit) return html`<${Cells.Editor} item=${i} field=${field} onDone=${() => setEdit(false)} />`;
    const v = i[field];
    return html`<span class=${"chip ed" + (v ? "" : " muted")} onClick=${() => setEdit(true)}>${v ? html`${label} <b>${v}</b>` : `${label} –`}</span>`;
  }
  function LongField({ i, field }) {
    const [edit, setEdit] = preactHooks.useState(false);
    if (edit) return html`<${Cells.Editor} item=${i} field=${field} long onDone=${() => setEdit(false)} />`;
    return html`<p class="ed" onClick=${() => setEdit(true)}>${i[field] || "Add " + (Store.model.labels[field] || field)}</p>`;
  }
  function More({ i }) {
    const S = Store, [open, setOpen] = preactHooks.useState(false);
    const [merging, setMerging] = preactHooks.useState(false), [mergeTarget, setMergeTarget] = preactHooks.useState("");
    const [deleting, setDeleting] = preactHooks.useState(false), [reason, setReason] = preactHooks.useState("");
    const guarded = () => { if (!S.ui.madeBy?.trim()) { Store.toast("Set Made by first, at the top of the table."); return false; } return true; };
    const after = async () => { await S.load(); if (!S.byId[i.id]) S.set({ open: null }); };
    const markReviewed = async () => { setOpen(false); try { await S.post("/api/rationalise/reviewed", { id: i.id }); await after(); } catch (e) { S.toast(e.message); } };
    const merge = async () => { if (!guarded() || !mergeTarget.trim()) return; try { await S.post("/api/merge", { survivor: mergeTarget, losers: [i.id] }); setMerging(false); setMergeTarget(""); await after(); } catch (e) { S.toast(e.message); } };
    const del = async () => { if (!guarded() || !reason.trim()) return; try { await S.post("/api/delete", { id: i.id, reason }); setDeleting(false); setReason(""); await after(); } catch (e) { S.toast(e.message); } };
    return html`<span class="stwrap">
      <button class="btn ghost" onClick=${() => setOpen(!open)}>⋯</button>
      ${open ? html`<div class="menu right" onClick=${e => e.stopPropagation()}>

        <div class="mi" onClick=${() => { setOpen(false); S.post('/api/reviews/create',{name:'Merge review '+i.id,ids:[i.id]}).then(async r=>{await S.load();S.set({view:'reviews:'+r.id,open:null});}).catch(e=>S.toast(e.message)); }}><span>Merge into…</span></div>
        <div class="mi" onClick=${() => { setOpen(false); setDeleting(true); }}><span>Delete</span></div>
      </div>` : null}
      ${merging ? html`<div class="menu right" onClick=${e => e.stopPropagation()}>
        <div class="field"><label>Merge ${i.id} into</label><${Picker.Inline} kind=${i.kind} types=${[i.kind]} value=${mergeTarget} onPick=${setMergeTarget} exclude=${i.id} /></div>
        <div class="dlg-f"><button class="btn" onClick=${() => { setMerging(false); setMergeTarget(""); }}>Cancel</button><button class="btn pri" disabled=${!mergeTarget.trim()} onClick=${merge}>Merge</button></div>
      </div>` : null}
      ${deleting ? html`<div class="menu right" onClick=${e => e.stopPropagation()}>
        <div class="field"><label>Reason</label><input class="inp" value=${reason} onInput=${e => setReason(e.target.value)} placeholder="reason, goes into History" /></div>
        <div class="dlg-f"><button class="btn" onClick=${() => { setDeleting(false); setReason(""); }}>Cancel</button><button class="btn pri danger" disabled=${!reason.trim()} onClick=${del}>Delete</button></div>
      </div>` : null}
    </span>`;
  }
  function Panel() {
    const S = Store, id = S.ui.open, i = S.byId[id];
    const [linkTo, setLinkTo] = preactHooks.useState(null);
    const [acceptingKey, setAcceptingKey] = preactHooks.useState(null), [ownerVal, setOwnerVal] = preactHooks.useState("");
    const [dismissingKey, setDismissingKey] = preactHooks.useState(null), [dismissReason, setDismissReason] = preactHooks.useState("");
    const [linkingKey, setLinkingKey] = preactHooks.useState(null), [linkTarget, setLinkTarget] = preactHooks.useState("");
    if (!i) return null;
    const guarded = () => { if (!S.ui.madeBy?.trim()) { Store.toast("Set Made by first, at the top of the table."); return false; } return true; };
    const accept = async (s, owner) => {
      if (!guarded()) return;
      if (s.needsOwner && !owner?.trim()) { setAcceptingKey(s.key); return; }
      try { await S.post("/api/support/accept", { id: i.id, key: s.key, fields: owner ? { Owner: owner } : {} }); setAcceptingKey(null); setOwnerVal(""); await S.load(); }
      catch (e) { S.toast(e.message); }
    };
    const dismiss = async s => {
      if (!guarded() || !dismissReason.trim()) return;
      try { await S.post("/api/support/dismiss", { id: i.id, key: s.key, rule: s.rule, reason: dismissReason }); setDismissingKey(null); setDismissReason(""); await S.load(); }
      catch (e) { S.toast(e.message); }
    };
    const linkExisting = async s => {
      if (!guarded() || !linkTarget.trim()) return;
      try { await S.post("/api/support/link", { id: i.id, key: s.key, target: linkTarget.trim() }); setLinkingKey(null); setLinkTarget(""); await S.load(); }
      catch (e) { S.toast(e.message); }
    };
    const rows = S.rows(); const at = rows.findIndex(r => r.id === id);
    const prov = S.state.provenance[id] || { back: [], forward: [], dangling: [] };
    const fails = S.failuresById[id] || [], sugg = S.suggestionsById[id] || [];
    const moves = S.model.transitions[i.kind]?.[i.status] || [];
    const needs = to => S.model.required[i.kind]?.[to] || [];
    const specials = to => (S.model.specials || []).filter(sp => sp.kind === i.kind && sp.state === to).map(sp => sp.text);
    const need = to => needs(to).map(f => f.startsWith("link:") ? "link " + f.slice(5) : S.model.labels[f] || f).concat(specials(to)).join(", ");
    const short = [...new Set([...S.model.short[i.kind], "raised-on", "closed-on"])].filter(k => k !== "scope"), long = S.model.long[i.kind];
    // Words a later state will need, drawn as dashed slots in the forward column.
    const later = Object.entries(S.model.required[i.kind] || {}).flatMap(([st, fs]) => fs.filter(f => f.startsWith("link:")).map(f => ({ st, word: f.slice(5).split(":")[0] })))
      .filter(x => S.model.forward[i.kind].includes(x.word) && !i.links.some(l => l.toLowerCase().startsWith(x.word)));
    return html`<aside class="panel">
      <div class="bar top"><span class=${"pill " + i.kind}>${i.id}</span><span class="muted small">${at + 1} of ${rows.length} · ↑↓ to step</span><div class="sp"></div>
        <button class="btn" onClick=${() => setLinkTo({})}>Link to…</button>
        <button class="btn" onClick=${() => { navigator.clipboard.writeText(location.origin + '/#item/' + encodeURIComponent(i.id)).then(() => S.toast('Link copied'), () => S.toast('Copy this URL: ' + location.origin + '/#item/' + i.id)); }}>Copy link</button>
        <button class="btn" onClick=${async () => { try {const r=await S.post('/api/reviews/create',{name:'Review '+i.id,ids:[i.id]});await S.load();S.set({view:'reviews:'+r.id,open:null});}catch(e){S.toast(e.message);} }}>Structured review</button>
        <${More} i=${i} />
        <button class="btn ghost" onClick=${() => S.set({ open: null })}>Esc ✕</button></div>
      ${linkTo ? html`<${Picker.LinkTo} item=${i} word=${linkTo.word} onClose=${() => setLinkTo(null)} />` : null}
      <div class="panel-body">
        <div class="panel-main">
          <${Title} i=${i} />
          <div class="chips"><${Cells.StatusCell} item=${i} />
            ${S.model.scopes.length || i.scope ? html`<${Chip} i=${i} field="scope" label="Scope" />` : null}
            ${short.map(k => html`<${Chip} i=${i} field=${k} label=${S.model.labels[k] || k} />`)}</div>
          ${S.ui.mode !== "rationalise" ? html`<div class="card"><div class="h3">Next moves</div><div class="moves">
            ${moves.map(to => html`<span class="btn" onClick=${() => MoveForm.open({ ids: [i.id], to })}>${to}${need(to) ? html` <span class="muted">needs ${need(to)}</span>` : null}</span>`)}
            ${!moves.length ? html`<span class="muted">${i.status} is terminal.</span>` : null}</div></div>` : null}
          ${long.map(k => html`<div class="sec"><div class="h3">${S.model.labels[k] || k}</div><${LongField} i=${i} field=${k} /></div>`)}
          ${i.links.length ? html`<div class="sec"><div class="h3">Links</div>${i.links.map(l => html`<div class="mono small">${l}</div>`)}</div>` : null}
          ${i.history?.length ? html`<div class="sec"><div class="h3">History</div>${i.history.slice().reverse().map(h => html`<div class="mono small muted">${h}</div>`)}</div>` : null}
        </div>
        <div class="panel-side">
          <div class="h3">Where it came from</div>
          ${prov.back.length ? prov.back.map(h => html`<${Hop} h=${h} />`) : html`<div class="muted small">Nothing links back.</div>`}
          <div class="hop cur"><span class=${"pill " + i.kind}>${i.id}</span><span class="t">This item</span></div>
          <div class="h3">What it produces</div>
          ${prov.forward.map(h => html`<div class="word">${h.word}</div><${Hop} h=${h} />`)}
          ${later.map(x => html`<div class="hop slot"><span class="muted small ed" onClick=${() => setLinkTo({ word: x.word })}>${x.word} · none yet, needed for ${x.st}</span></div>`)}
          ${prov.dangling.map(l => html`<div class="hop slot bad"><span class="small">${l} · target not found</span></div>`)}
          <div class="h3">Gaps</div>
          ${fails.map(f => html`<div class="gap"><span class="warn"></span><span class="small">${f.rule} · ${f.text}</span></div>`)}
          ${sugg.map(s => html`<div class="gap sugg"><span class="warn amber"></span><div>
            <div class="small">${s.rule} · offers ${S.model.names[s.kind]}: ${s.fields.title || ""}</div>
            ${acceptingKey === s.key ? html`<div class="mini"><input class="inp" value=${ownerVal} onInput=${e => setOwnerVal(e.target.value)} placeholder="Owner" />
              <button class="btn pri" disabled=${!ownerVal.trim()} onClick=${() => accept(s, ownerVal)}>Accept</button>
              <button class="btn ghost" onClick=${() => { setAcceptingKey(null); setOwnerVal(""); }}>Cancel</button></div>`
            : dismissingKey === s.key ? html`<div class="mini"><input class="inp" value=${dismissReason} onInput=${e => setDismissReason(e.target.value)} placeholder="reason" />
              <button class="btn pri danger" disabled=${!dismissReason.trim()} onClick=${() => dismiss(s)}>Dismiss</button>
              <button class="btn ghost" onClick=${() => { setDismissingKey(null); setDismissReason(""); }}>Cancel</button></div>`
            : linkingKey === s.key ? html`<div class="mini"><${Picker.Inline} kind=${i.kind} types=${[s.kind]} word=${s.link.trim()} value=${linkTarget} onPick=${setLinkTarget} exclude=${i.id} />
              <button class="btn pri" disabled=${!linkTarget.trim()} onClick=${() => linkExisting(s)}>Link</button>
              <button class="btn ghost" onClick=${() => { setLinkingKey(null); setLinkTarget(""); }}>Cancel</button></div>`
            : html`<div class="mini">
              <button class="btn ghost" onClick=${() => accept(s)}>Accept</button>
              <button class="btn ghost" onClick=${() => setLinkingKey(s.key)}>Link existing</button>
              <button class="btn ghost" onClick=${() => setDismissingKey(s.key)}>Dismiss</button></div>`}
          </div></div>`)}
          ${!fails.length && !sugg.length ? html`<div class="muted small">None.</div>` : null}
        </div>
      </div>
    </aside>`;
  }
  window.Panel = Panel;
})();
