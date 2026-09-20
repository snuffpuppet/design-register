(function () {
  const html = htm.bind(preact.h), {useState, useEffect} = preactHooks;
  const label = k => Store.model.labels[k] || k;
  function Record({item}) {
    const keys = [...new Set(['title','status','raised-on','closed-on','description',...Store.model.short[item.kind],...Store.model.long[item.kind]])];
    return html`<div class="card"><b>${item.id} · ${Store.model.names[item.kind]}</b>${keys.filter(k=>item[k]).map(k=>html`<div><small class="muted">${label(k)}</small><p style="white-space:pre-wrap">${item[k]}</p></div>`)}<small class="muted">Links</small>${item.links.map(l=>html`<p>${l}</p>`)}</div>`;
  }
  function Dialog() {
    const S=Store, config=S.ui.structure, action=config.action, ids=config.ids;
    const [lead,setLead]=useState(''),[kind,setKind]=useState(''),[status,setStatus]=useState('');
    const [preview,setPreview]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[loading,setLoading]=useState(false);
    const close=()=>{if(!busy)S.set({structure:null});};
    const actualIds=action==='merge' && ids.length===1 ? [...new Set([...ids,lead].filter(Boolean))] : ids;
    const request={ids:actualIds,...(action==='merge'?{lead}:{kind,status})};
    useEffect(()=>{
      let active=true;setPreview(null);setError('');
      if(action==='merge'?!lead:!kind){setLoading(false);return;}
      setLoading(true);
      S.post(`/api/rationalise/${action}/preview`,request).then(p=>{if(active)setPreview(p);}).catch(e=>{if(active)setError(e.message);}).finally(()=>{if(active)setLoading(false);});
      return ()=>{active=false;};
    },[lead,kind,status]);
    preactHooks.useLayoutEffect(()=>{const escape=e=>{if(e.key==='Escape'){e.stopImmediatePropagation();close();}};document.addEventListener('keydown',escape,true);return()=>document.removeEventListener('keydown',escape,true);},[busy]);
    const accept=async()=>{
      if(!S.ui.madeBy?.trim()){setError('Set Made by before accepting.');return;}
      setBusy(true);setError('');
      try {
        const r=await S.post(`/api/rationalise/${action}/apply`,{...request,token:preview.token});
        await S.load();S.set({structure:null,selection:new Set(),open:action==='merge'?r.survivor:ids.length===1?r.mapping[ids[0]]:null});
        S.toast(action==='merge'?'Merge complete. Recent operations can undo it.':'Type changed. Old IDs redirect to the new records.');
      } catch(e){setError(e.message);setBusy(false);}
    };
    const candidates=ids.length===1?S.state.items.filter(i=>i.kind===S.byId[ids[0]]?.kind && i.id!==ids[0]):ids.map(id=>S.byId[id]).filter(Boolean);
    return html`<div class="modal" onClick=${close}><div class="dlg structural" role="dialog" aria-label=${action==='merge'?'Merge records':'Change type'} onClick=${e=>e.stopPropagation()}>
      <div class="dlg-h"><h2>${action==='merge'?'Merge records':'Change type'}</h2></div>
      <div class="dlg-b">
      ${action==='merge'?html`<label class="field">Lead record<select class="inp" aria-label="Lead record" disabled=${busy} value=${lead} onChange=${e=>setLead(e.target.value)}><option value="">Choose the lead…</option>${candidates.map(i=>html`<option value=${i.id}>${i.id} · ${i.title}</option>`)}</select></label><p>The lead keeps its populated fields. Blank fields are filled where possible; differing values and previous history are retained in Notes. Incoming references follow the lead.</p>`:html`<label class="field">New type<select class="inp" aria-label="New type" disabled=${busy} value=${kind} onChange=${e=>{setKind(e.target.value);setStatus('');}}><option value="">Choose type…</option>${Object.entries(S.model.names).filter(([k])=>ids.every(id=>S.byId[id]?.kind!==k)).map(([k,n])=>html`<option value=${k}>${n}</option>`)}</select></label>${kind?html`<label class="field">Status<select class="inp" aria-label="New status" disabled=${busy} value=${status} onChange=${e=>setStatus(e.target.value)}><option value="">Keep if valid, otherwise initial status</option>${S.model.states[kind].map(v=>html`<option>${v}</option>`)}</select></label>`:null}<p>Each record receives an ID for its new type. Existing references follow it; previous fields and history are retained.</p>`}
      ${loading?html`<p>Preparing preview…</p>`:null}
      ${preview?html`<div class="structure-preview"><div class="compare-grid"><section><h3>Before</h3>${(action==='merge'?preview.before:preview.changes.map(c=>c.before)).map(item=>html`<${Record} item=${item}/>` )}</section><section><h3>After</h3>${(action==='merge'?[preview.after]:preview.changes.map(c=>c.after)).map(item=>html`<${Record} item=${item}/>` )}</section></div></div>`:null}
      ${error?html`<p class="miss">${error}</p>`:null}</div>
      <div class="dlg-f"><button class="btn" disabled=${busy} onClick=${close}>Cancel</button><button class="btn pri" disabled=${!preview||loading||busy} onClick=${accept}>${busy?'Saving…':action==='merge'?'Accept merge':'Accept type change'}</button></div>
    </div></div>`;
  }
  function Bin() {
    const S=Store,[error,setError]=useState(''),[busy,setBusy]=useState(null);
    const restore=async entry=>{setBusy(entry.key);setError('');try{const r=await S.post('/api/trash/restore',{key:entry.key,revision:entry.revision});await S.load();S.toast(r.missingSources.length?'Restored item. Some referring records no longer exist: '+r.missingSources.join(', '):'Item and incoming links restored.');}catch(e){setError(e.message);}finally{setBusy(null);}};
    return html`<main class="main-col workspace"><div class="bar top"><h2>Rubbish bin</h2><div class="sp"></div><input class="inp madeby" placeholder="Made by" value=${S.ui.madeBy} onInput=${e=>{S.set({madeBy:e.target.value});localStorage.setItem("madeBy",e.target.value);}}/></div><div class="workspace-content"><p>Restore a deleted record with its original ID and history. Removed incoming links are added back to referring records that still exist.</p>${error?html`<p class="miss">${error}</p>`:null}${!(S.state.rubbish||[]).length?html`<p>The rubbish bin is empty.</p>`:null}${(S.state.rubbish||[]).slice().reverse().map(e=>html`<div class="card"><h3>${e.item.id} · ${e.item.title}</h3><p>${e.deletedOn} · ${e.by} · ${e.reason}</p><details><summary>Deleted record</summary><${Record} item=${e.item}/></details><button class="btn pri" disabled=${!!busy} onClick=${()=>restore(e)}>${busy===e.key?'Restoring…':'Restore '+e.item.id}</button></div>`)}</div></main>`;
  }
  window.StructuralDialog=Dialog;window.RubbishBin=Bin;
})();
