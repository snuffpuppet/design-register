(function () {
  const html = htm.bind(preact.h);
  const { useState, useEffect, useRef } = preactHooks;
  function typesFor(kind, word) {
    const t = Store.model.linkWords[kind]?.[word] || "ANY";
    return ["ANY", "CLAIM"].includes(t) ? [] : t.split("|");
  }
  function Inline({ word, kind, value, onPick, exclude, fieldKey }) {
    const [q, setQ] = useState(value || ""), [hits, setHits] = useState([]), [open, setOpen] = useState(false), [failed, setFailed] = useState(false);
    const types = typesFor(kind, word);
    useEffect(() => {
      if (!open) return;
      setFailed(false);
      const u = `/api/items?q=${encodeURIComponent(q)}&types=${types.join(",")}` + (exclude ? `&exclude=${encodeURIComponent(exclude)}` : "");
      fetch(u).then(r => r.json()).then(j => setHits(j.items)).catch(() => { setHits([]); setFailed(true); });
    }, [q, open, exclude]);
    return html`<span class="pkwrap"><input class="inp" value=${q} placeholder=${"pick " + (types.join(" or ") || "an item")} onFocus=${() => setOpen(true)} onInput=${e => { setQ(e.target.value); onPick(e.target.value); }} onBlur=${() => setTimeout(() => setOpen(false), 150)} />
      ${open ? html`<div class="menu pk">
        ${hits.map(h => html`<div class="mi" onMouseDown=${() => { onPick(h.id); setQ(h.id); setOpen(false); }}><span><span class=${"pill " + h.kind}>${h.id}</span> ${h.title}</span><span class="muted">${h.status}</span></div>`)}
        ${failed ? html`<div class="mi off">Search failed</div>` : (!hits.length ? html`<div class="mi off">No match</div>` : null)}
        ${types.map(t => html`<div class="mi new" onMouseDown=${() => CreateForm.nest({ kind: t, prefill: { title: q }, onCreated: id => { onPick(id); setQ(id); } }, fieldKey)}>+ New ${Store.model.names[t].toLowerCase()}</div>`)}
      </div>` : null}</span>`;
  }
  function LinkTo({ item, word: initialWord, onClose }) {
    const words = Object.keys(Store.model.linkWords[item.kind] || {});
    const [word, setWord] = useState(initialWord || words[0]), [target, setTarget] = useState(""), [err, setErr] = useState("");
    const apply = async () => { try { await Store.post("/api/edit", { id: item.id, links: [word + " " + target], gist: "linked " + word + " " + target }); await Store.load(); onClose(); } catch (e) { setErr(e.message); } };
    return html`<div class="modal" onClick=${onClose}><div class="dlg" onClick=${e => e.stopPropagation()}>
      <div class="dlg-h"><span class="h2">Link ${item.id}</span></div>
      <div class="dlg-b"><div class="grid2">
        <div class="field"><label>Link word</label><select class="inp" value=${word} onChange=${e => { setWord(e.target.value); setTarget(""); }}>${words.map(w => html`<option value=${w}>${w}</option>`)}</select></div>
        <div class="field"><label>Target</label><${Inline} word=${word} kind=${item.kind} value=${target} onPick=${setTarget} exclude=${item.id} /></div></div>
        ${err ? html`<div class="miss">${err}</div>` : null}</div>
      <div class="dlg-f"><div class="sp"></div><button class="btn" onClick=${onClose}>Cancel</button><button class="btn pri" disabled=${!target.trim()} onClick=${apply}>Add link</button></div>
    </div></div>`;
  }
  // New item: every field in model.create[kind], link needs through the picker. A stack of in-progress
  // dialogs: nest() opens a second create on top of one already open, snapshotting the live parent's
  // typed state (read off the ref Create keeps current) so it can be restored rather than lost. The
  // snapshot's prefill is a plain object outside React state, so the nested dialog's own onCreated can
  // patch the picked id straight into it before the parent is restored — sidesteps any race between that
  // restore and whatever the picker's own onPick callback (stale once the parent dialog swaps away) does.
  const CreateForm = {
    open(o) { o.parent = Store.ui.create || null; Store.set({ create: o }); },
    nest(o, fieldKey) {
      const cur = Store.ui.create;
      if (cur) {
        const live = (CreateForm._live && CreateForm._live.current) || {};
        const parent = { ...cur, kind: live.kind ?? cur.kind, prefill: { ...(live.f ?? cur.prefill) } };
        if (fieldKey) {
          const onCreated = o.onCreated;
          o.onCreated = id => { onCreated?.(id); parent.prefill = { ...parent.prefill, [fieldKey]: id }; };
        }
        o.parent = parent;
      }
      Store.set({ create: o });
    },
    close() { Store.set({ create: null }); },
  };
  function Create() {
    const S = Store, c = S.ui.create; if (!c) return null;
    const [kind, setKind] = useState(c.kind || "OI"), [f, setF] = useState(c.prefill || {}), [err, setErr] = useState("");
    // A create dialog can already be open when a picker's "+ New" row opens another one (a link field
    // inside this very form); resync local state whenever CreateForm hands us a new request object.
    useEffect(() => { setKind(c.kind || "OI"); setF(c.prefill || {}); setErr(""); }, [c]);
    // Kept current for CreateForm.nest to read the live typed state at the moment a nested create opens.
    const live = useRef({}); live.current = { kind, f }; CreateForm._live = live;
    const req = S.model.create[kind] || [];
    const key = x => x.startsWith("link:") ? null : x;
    const opts = k => S.model.choices[k] || (k === "scope" ? S.model.scopes : k === "phase" ? S.model.phases : k === "owner" ? S.model.owners : null);
    const back = () => { if (c.parent) Store.set({ create: c.parent }); else CreateForm.close(); };
    const apply = async () => {
      try {
        const fields = {}; for (const x of req) if (key(x)) fields[S.model.labels[x] || x] = f[x] || "";
        const links = req.filter(x => x.startsWith("link:")).map(x => x.slice(5) + " " + (f[x] || ""));
        const r = await S.post("/api/create", { kind, fields, links });
        await S.load(); c.onCreated?.(r.item);
        if (c.parent) Store.set({ create: c.parent }); else { CreateForm.close(); S.set({ open: r.item, focus: r.item }); }
      } catch (e) { setErr(e.message); }
    };
    return html`<div class="modal" onClick=${back}><div class="dlg" onClick=${e => e.stopPropagation()}>
      <div class="dlg-h"><span class="h2">New ${S.model.names[kind].toLowerCase()}</span>
        <select class="inp" value=${kind} onChange=${e => { setKind(e.target.value); setF({ title: f.title }); }}>${Object.keys(S.model.names).map(k => html`<option value=${k}>${S.model.names[k]}</option>`)}</select></div>
      <div class="dlg-b">${req.map(x => html`<div class="field"><label>${x.startsWith("link:") ? "Link: " + x.slice(5) : S.model.labels[x] || x}</label>
        ${x.startsWith("link:") ? html`<${Inline} word=${x.slice(5)} kind=${kind} value=${f[x] || ""} onPick=${v => setF({ ...f, [x]: v })} fieldKey=${x} />`
        : opts(x)?.length ? html`<select class="inp" value=${f[x] || ""} onChange=${e => setF({ ...f, [x]: e.target.value })}><option value="">–</option>${opts(x).map(o => html`<option value=${o}>${o}</option>`)}</select>`
        : S.model.long[kind].includes(x) ? html`<textarea class="inp" value=${f[x] || ""} onInput=${e => setF({ ...f, [x]: e.target.value })} />`
        : html`<input class="inp" value=${f[x] || ""} onInput=${e => setF({ ...f, [x]: e.target.value })} />`}</div>`)}
        ${err ? html`<div class="miss">${err}</div>` : null}</div>
      <div class="dlg-f"><div class="sp"></div><button class="btn" onClick=${back}>Cancel</button><button class="btn pri" onClick=${apply}>Create</button></div>
    </div></div>`;
  }
  CreateForm.Form = Create;
  window.Picker = { Inline, LinkTo, typesFor };
  window.CreateForm = CreateForm;
})();
