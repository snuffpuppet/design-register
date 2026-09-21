(function () {
  const html = htm.bind(preact.h), { useState, useEffect } = preactHooks;
  const label = k => Store.model.labels[k] || (k.charAt(0).toUpperCase() + k.slice(1));
  const run = async fn => { try { return await fn(); } catch (e) { Store.toast(e.message); return null; } };
  function download(text, name) {
    const url = URL.createObjectURL(new Blob([text], {type: 'text/markdown'}));
    const a = Object.assign(document.createElement('a'), {href: url, download: name}); a.click(); URL.revokeObjectURL(url);
  }
  function Maker() {
    return html`<label class="maker">Made by <input class="inp madeby" value=${Store.ui.madeBy} onInput=${e => { Store.set({madeBy: e.target.value}); localStorage.setItem('madeBy', e.target.value); }} /></label>`;
  }
  function Home({category}) {
    const S = Store, [name, setName] = useState(''), [scope, setScope] = useState(category === 'meetings' ? 'open' : 'all');
    const rows = S.state[category] || [];
    const create = () => run(async () => {
      const ids = scope === 'selected' ? [...S.ui.selection] : scope === 'open' ? S.state.items.filter(i => i.kind === 'OI' && i.status !== 'Closed').map(i => i.id) : S.rows().map(i => i.id);
      const r = await S.post(`/api/${category}/create`, {name, ids}); await S.load(); S.set({view: category + ':' + r.id, open: null});
    });
    return html`<main class="main-col workspace"><div class="bar top"><h2>${category === 'reviews' ? 'Rationalisation reviews' : 'Meetings'}</h2><div class="sp"></div><${Maker}/></div>
      <div class="workspace-content"><p>${category === 'reviews' ? 'Review the current position, propose corrections and retain evidence. Lifecycle status and review progress are independent.' : 'Prepare a fixed agenda. Record outcomes and progress linked records without losing your place.'}</p>
      <div class="card"><h3>${category === 'reviews' ? 'Start a review batch' : 'Prepare a meeting'}</h3><div class="session-create"><input aria-label="Session name" class="inp" placeholder="Name" value=${name} onInput=${e => setName(e.target.value)} />
      <select class="inp" value=${scope} onChange=${e => setScope(e.target.value)}><option value="all">Current filter</option><option value="selected">Selected items (${S.ui.selection.size})</option><option value="open">Open items</option></select>
      <button class="btn pri" disabled=${!name.trim()} onClick=${create}>Create</button></div></div>
      ${rows.slice().reverse().map(r => html`<button class="session-card card" onClick=${() => S.set({view: category + ':' + r.id, open: null})}><b>${r.name}</b><span>${r.ids.length} items · ${Object.keys(r.entries).length} recorded · ${r.status}</span><small>${r.id} · ${r.created}</small></button>`)}</div></main>`;
  }
  function Snapshot({item, title}) {
    if (!item) return html`<div class="card">Item no longer exists. Use its alias or review history.</div>`;
    const fields = ['status', 'owner', 'source', 'description', ...Store.model.short[item.kind], ...Store.model.long[item.kind]];
    return html`<div class="card snapshot"><h3>${title}</h3><b>${item.id} · ${item.title}</b>${[...new Set(fields)].filter(k => item[k]).map(k => html`<div><small class="muted">${label(k)}</small><p>${item[k]}</p></div>`)}<small>Links</small>${item.links.map(l => html`<p>${l}</p>`)}</div>`;
  }
  function Fields({kind, values, onChange}) {
    const keys = ['title', 'status', ...Store.model.short[kind], ...Store.model.long[kind], 'description', 'raised-on', 'closed-on'];
    return html`<div class="review-fields">${keys.filter(k => k !== 'scope' || Store.model.scopes.length).map(k => {
      const opts = k === 'status' ? Store.model.states[kind] : k === 'scope' ? Store.model.scopes : k === 'phase' ? Store.model.phases : k === 'impact' && kind !== 'RSK' ? null : Store.model.choices[k];
      return html`<label class="field">${label(k)}${opts ? html`<select class="inp" value=${values[k] || ''} onChange=${e => onChange({...values, [k]: e.target.value})}><option value="">Unspecified</option>${opts.map(o => html`<option value=${o}>${o}</option>`)}</select>` : html`<textarea class="inp" rows=${Store.model.long[kind].includes(k) ? 3 : 1} value=${values[k] || ''} onInput=${e => onChange({...values, [k]: e.target.value})} />`}</label>`;
    })}</div>`;
  }
  function ReviewEntry({record, id, next}) {
    const S = Store, current = S.byId[id], original = record.snapshot[id], saved = record.entries[id] || {};
    const [entry, setEntry] = useState({...saved, outcome: saved.outcome || 'confirmed', fields: saved.fields || {}, links: saved.links || current?.links || [], kind: saved.kind || current?.kind || original.kind});
    const [compare, setCompare] = useState(null);
    const set = patch => setEntry(e => ({...e, ...patch}));
    const kind = entry.kind, values = {...current, ...entry.fields};
    useEffect(() => { setCompare(null); if (entry.outcome === 'merged' && entry.survivor) run(async () => setCompare(await S.post('/api/merge/preview', {survivor: entry.survivor, losers: [id]}))); }, [entry.outcome, entry.survivor]);
    const save = () => run(async () => { await S.post('/api/reviews/update', {batch: record.id, revision: record.revision, id, entry}); await S.load(); next(); });
    const correction = ['corrected', 'retyped'].includes(entry.outcome);
    return html`<div class="review-detail"><div class="compare-grid"><${Snapshot} item=${original} title="At start of review"/><${Snapshot} item=${current} title="Current register"/></div>
      <div class="card"><h3>Review outcome</h3><label class="field">Outcome<select class="inp" value=${entry.outcome} onChange=${e => set({outcome: e.target.value})}>${(S.model.reviewOutcomes || ['confirmed','corrected','merged','excluded','needs clarification','retyped','split']).map(v => html`<option>${v}</option>`)}</select></label>
      ${entry.outcome === 'retyped' ? html`<label class="field">New type<select class="inp" value=${kind} onChange=${e => set({kind: e.target.value, fields: {title: current.title, status: S.model.first[e.target.value], source: current.source, owner: current.owner}})}>${Object.entries(S.model.names).map(([k,v]) => html`<option value=${k}>${v}</option>`)}</select></label>` : null}
      ${correction ? html`<${Fields} kind=${kind} values=${values} onChange=${v => set({fields: Object.fromEntries(Object.entries(v).filter(([k,val]) => val !== current?.[k] && ['title','status','description','raised-on','closed-on',...S.model.short[kind],...S.model.long[kind]].includes(k)))})}/><label class="field">Links (one per line)<textarea class="inp" value=${entry.links.join('\n')} onInput=${e => set({links: e.target.value.split('\n').filter(Boolean)})}/></label>` : null}
      ${entry.outcome === 'merged' ? html`<label class="field">Survivor<${Picker.Inline} kind=${original.kind} types=${[original.kind]} exclude=${id} value=${entry.survivor || ''} onPick=${v => set({survivor:v, resolutions:{}})}/></label>
        ${compare ? html`<${Snapshot} item=${compare.items[0]} title="Survivor"/>${Object.entries(compare.conflicts).map(([k,vs]) => html`<label class="field">Resolve ${label(k)}<select class="inp" value=${entry.resolutions?.[k] ?? ''} onChange=${e => set({resolutions:{...entry.resolutions,[k]:e.target.value}})}><option value="">Choose a value</option>${vs.map(v => html`<option value=${v}>${v}</option>`)}</select></label>`)}` : null}` : null}
      ${entry.outcome === 'split' ? html`<p>The original keeps its ID and points to the new records, preserving incoming references.</p>${(entry.children || [{kind,fields:{title:''}},{kind,fields:{title:''}}]).map((child,n) => html`<div class="card"><h4>New record ${n+1}</h4><${Fields} kind=${child.kind || kind} values=${child.fields} onChange=${fields => { const children = [...(entry.children || [{kind,fields:{title:''}},{kind,fields:{title:''}}])]; children[n] = {...child,fields}; set({children}); }}/></div>`)}` : null}
      <label class="field">Review reason<textarea class="inp" value=${entry.reason || ''} onInput=${e => set({reason:e.target.value})}/></label>
      <label class="field">Evidence<textarea class="inp" placeholder="Source reference or meeting evidence; do not infer approval" value=${entry.evidence || ''} onInput=${e => set({evidence:e.target.value})}/></label>
      <label class="field">Effective on (when it actually happened, if known)<input class="inp" value=${entry.effectiveOn || ''} onInput=${e => set({effectiveOn:e.target.value})} placeholder="1 September 2026"/></label>
      <p class="muted">${(S.failuresById[id] || []).length} integrity findings remain visible. Review completion does not imply every historical gap is resolved.</p>
      ${(S.failuresById[id] || []).map(f => html`<p class="small">${f.rule}: ${f.text}</p>`)}
      <button class="btn pri" disabled=${record.status !== 'open' || !current} onClick=${save}>Save and next unresolved</button></div></div>`;
  }
  function MeetingEntry({record,id,next}) {
    const S = Store, saved = record.entries[id] || {}, [entry,setEntry] = useState({status:'not discussed',...saved});
    const set = (k,v) => setEntry(e => ({...e,[k]:v}));
    const save = () => run(async () => { await S.post('/api/meetings/update',{batch:record.id,revision:record.revision,id,entry}); await S.load(); next(); });
    const it = S.byId[id];
    return html`<div class="review-detail"><${Snapshot} item=${it || record.snapshot[id]} title="Agenda item"/>
      <div class="card"><button class="btn" disabled=${!it} onClick=${() => S.set({open:id,session:record.id})}>Open linked records and workflow</button>
      <label class="field">Progress<select class="inp" value=${entry.status} onChange=${e => set('status',e.target.value)}>${['not discussed','discussed','deferred'].map(v => html`<option>${v}</option>`)}</select></label>
      ${['outcome','evidence','action','owner','due','references'].map(k => html`<label class="field">${{action:'Follow-up action',references:'Register IDs created or changed'}[k] || label(k)}<textarea class="inp" value=${entry[k] || ''} onInput=${e => set(k,e.target.value)}/></label>`)}
      ${S.model.scopes.length ? html`<label class="field">Follow-up scope<select class="inp" value=${entry.scope || ''} onChange=${e=>set('scope',e.target.value)}><option value="">Choose scope</option>${S.model.scopes.map(v=>html`<option>${v}</option>`)}</select></label>`:null}
      <button class="btn pri" disabled=${record.status !== 'open'} onClick=${save}>Save outcome and next</button>
      <button class="btn" disabled=${record.status !== 'open' || !entry.action?.trim() || !entry.owner?.trim() || !!entry.actionItem} onClick=${() => run(async () => {
        const r=await S.post('/api/meetings/action',{batch:record.id,revision:record.revision,id,entry,scope:entry.scope || '',session:record.id});
        setEntry(r.entries[id]); await S.load();
      })}>Create follow-up open item</button>${entry.actionItem ? html`<p>Follow-up recorded: ${entry.actionItem}</p>`:null}</div></div>`;
  }
  function Session({category,record}) {
    const S = Store, [at,setAt] = useState(0), [preview,setPreview] = useState(null), id = record.ids[at] || record.ids[0];
    useEffect(()=>{const detail=document.querySelector('.review-detail');if(detail)detail.scrollTop=0;document.querySelector('.agenda-item.on')?.scrollIntoView({block:'nearest'});},[id]);
    const next = () => { const updated = S.state[category].find(r => r.id === record.id); const ids = record.ids;
      const order = [...ids.slice(at+1),...ids.slice(0,at+1)]; const found = order.find(x => !updated.entries[x] || updated.entries[x].outcome === 'needs clarification' || updated.entries[x].status === 'not discussed');
      if (found) setAt(ids.indexOf(found)); else setAt(Math.min(at+1,ids.length-1)); };
    const reorder = delta => run(async () => { const order = [...record.ids], target = at+delta; if(target<0 || target>=order.length)return; [order[at],order[target]]=[order[target],order[at]];
      await S.post(`/api/${category}/update`,{batch:record.id,revision:record.revision,order}); await S.load(); setAt(target); });
    return html`<main class="main-col workspace"><div class="bar top"><button class="btn" onClick=${() => S.set({view:category,session:null})}>Back</button><h2>${record.name}</h2><div class="sp"></div><${Maker}/></div>
      <div class="bar"><span class="muted">${record.id} · ${record.status} · ${Object.keys(record.entries).length}/${record.ids.length} recorded</span>
      <button class="btn" onClick=${() => run(async () => {const r=await S.post(`/api/${category}/summary`,{batch:record.id});download(r.text,record.id+'.md');})}>Export summary</button>
      ${category === 'reviews' ? html`<button class="btn" disabled=${record.status !== 'open'} onClick=${() => run(async () => setPreview(await S.post('/api/reviews/preview',{batch:record.id,revision:record.revision})))}>Preview corrections</button>` : null}
      <button class="btn" disabled=${record.status !== 'open'} onClick=${() => run(async () => {await S.post(`/api/${category}/update`,{batch:record.id,revision:record.revision,close:true});await S.load();})}>${category==='reviews'?'Complete review':'Close meeting'}</button></div>
      ${preview ? html`<div class="card preview"><h3>Proposed corrections</h3>${preview.errors.map(e=>html`<p class="miss">${e.id}: ${e.error}</p>`)}${preview.changes.map(c=>html`<div><b>${c.id} · ${c.outcome}</b>${c.survivor?html`<p>Survivor: ${c.survivor}</p>${Object.entries(c.resolutions||{}).map(([k,v])=>html`<p>${label(k)}: ${v}</p>`)}`:null}${c.children?html`<p>New records: ${c.children.map(x=>x.fields.title).join('; ')}</p>`:null}${Object.keys(c.after).filter(k=>!['revision','history','pending'].includes(k)&&JSON.stringify(c.before[k])!==JSON.stringify(c.after[k])).map(k=>html`<p>${label(k)}: ${String(c.before[k] ?? '')} → ${String(c.after[k] ?? '')}</p>`)}${c.gaps.map(g=>html`<p class="muted">Remaining gap: ${g}</p>`)}</div>`)}<button class="btn pri" disabled=${preview.errors.length || !preview.changes.length || S.state.engagement.writes !== 'direct'} onClick=${()=>run(async()=>{await S.post('/api/reviews/apply',{batch:record.id,revision:preview.revision,context:'rationalise'});setPreview(null);await S.load();})}>Apply ${preview.changes.length} corrections</button><button class="btn" onClick=${()=>setPreview(null)}>Close preview</button>${S.state.engagement.writes!=='direct'?html`<p>Corrections remain proposals until applied in direct mode. They cannot be exported to the existing ingester contract.</p>`:null}</div>`:null}
      <div class="session-body"><nav class="agenda">${record.ids.map((x,n)=>html`<button class=${'agenda-item '+(n===at?'on':'')} onClick=${()=>{setAt(n);S.set({open:null,session:category==='meetings'?record.id:null});}}><b>${n+1}. ${x}</b><span>${record.snapshot[x].title}</span><small>${record.entries[x]?.status || record.entries[x]?.outcome || 'unreviewed'}${record.entries[x]?.applied?' · applied':''}</small></button>`)}
      ${category==='meetings'&&record.status==='open'?html`<button class="btn" onClick=${()=>reorder(-1)}>Move up</button><button class="btn" onClick=${()=>reorder(1)}>Move down</button>`:null}</nav>
      ${category==='reviews'?html`<${ReviewEntry} key=${record.id+id+record.status} record=${record} id=${id} next=${next}/>`:html`<${MeetingEntry} key=${record.id+id+record.status} record=${record} id=${id} next=${next}/>`}</div></main>`;
  }
  function Import() {
    const S=Store;
    return html`<main class="workspace workspace-content"><h1>Import working registers</h1><p>${S.baseline?.candidates?.length || 0} source rows are ready. Import preserves source references and opens a rationalisation review over the resulting register items.</p><${Maker}/>
      ${(S.baseline?.allPages || []).map(page=>html`<label class="field"><input style="width:auto" type="checkbox" checked=${!(S.baseline.skipped || []).includes(page)} onChange=${e=>run(async()=>{await S.post('/api/baseline/skip-page',{page,undo:e.target.checked});await S.load();})}/> Import register rows from ${page}</label>`)}
      <button class="btn pri" onClick=${()=>run(async()=>{await S.post('/api/import',{});await S.load();S.set({mode:'rationalise',view:'all'});})}>Import and review</button></main>`;
  }
  function Operations() {
    return html`<main class="main-col workspace"><div class="bar top"><h2>Recent operations</h2><div class="sp"></div><${Maker}/></div><div class="workspace-content"><p>Undo checks that affected register data has not changed. Recovery runs automatically after an interrupted write.</p>${Store.state.operations.slice().reverse().map(o=>html`<div class="card"><b>${o.action}</b><p>${o.at} · ${o.by} · ${o.status}</p>${o.action==='migration/CR-to-CP' ? html`<p>Model migration: rollback requires the matching old code and engagement backup, with the console stopped.</p>` : html`<button class="btn" disabled=${o.status!=='applied'} onClick=${()=>run(async()=>{await Store.post('/api/operations/undo',{operation:o.id});await Store.load();})}>Undo operation</button>`}</div>`)}</div></main>`;
  }
  function Workspace() {
    const [category,id]=Store.ui.view.split(':');
    const record=id&&(Store.state[category]||[]).find(r=>r.id===id);
    return record?html`<${Session} key=${record.id} category=${category} record=${record}/>`:html`<${Home} key=${category} category=${category}/>`;
  }
  window.Workspace=Workspace; window.ImportRegisters=Import; window.Operations=Operations;
})();
