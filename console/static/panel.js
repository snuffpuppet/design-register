(function () {
  const html = htm.bind(preact.h);
  function Hop({ h, word }) {
    return html`<div class="hop"><span class=${"pill " + h.kind}>${h.id}</span><span class="t" onClick=${() => Store.set({ open: h.id, focus: h.id })}>${h.title}</span><span class="st">${h.status}</span></div>`;
  }
  function Panel() {
    const S = Store, id = S.ui.open, i = S.byId[id];
    if (!i) return null;
    const rows = S.rows(); const at = rows.findIndex(r => r.id === id);
    const prov = S.state.provenance[id] || { back: [], forward: [], dangling: [] };
    const fails = S.failuresById[id] || [], sugg = S.suggestionsById[id] || [];
    const moves = S.model.transitions[i.kind]?.[i.status] || [];
    const needs = to => S.model.required[i.kind]?.[to] || [];
    const need = to => needs(to).map(f => f.startsWith("link:") ? "link " + f.slice(5) : S.model.labels[f] || f).join(", ");
    const short = S.model.short[i.kind].filter(k => k !== "scope"), long = S.model.long[i.kind];
    // Words a later state will need, drawn as dashed slots in the forward column.
    const later = Object.entries(S.model.required[i.kind] || {}).flatMap(([st, fs]) => fs.filter(f => f.startsWith("link:")).map(f => ({ st, word: f.slice(5).split(":")[0] })))
      .filter(x => S.model.forward[i.kind].includes(x.word) && !i.links.some(l => l.toLowerCase().startsWith(x.word)));
    return html`<aside class="panel">
      <div class="bar top"><span class=${"pill " + i.kind}>${i.id}</span><span class="muted small">${at + 1} of ${rows.length} · ↑↓ to step</span><div class="sp"></div>
        <button class="btn ghost" onClick=${() => S.set({ open: null })}>Esc ✕</button></div>
      <div class="panel-body">
        <div class="panel-main">
          <div class="ttl">${i.title}</div>
          <div class="chips"><span class="st on">${i.status}</span>
            ${i.scope ? html`<span class="chip">Scope <b>${i.scope}</b></span>` : null}
            ${short.map(k => i[k] ? html`<span class="chip">${S.model.labels[k] || k} <b>${i[k]}</b></span>` : null)}</div>
          <div class="card"><div class="h3">Next moves</div><div class="moves">
            ${moves.map(to => html`<span class="btn">${to}${need(to) ? html` <span class="muted">needs ${need(to)}</span>` : null}</span>`)}
            ${!moves.length ? html`<span class="muted">${i.status} is terminal.</span>` : null}</div></div>
          ${long.map(k => i[k] ? html`<div class="sec"><div class="h3">${S.model.labels[k] || k}</div><p>${i[k]}</p></div>` : null)}
          ${i.links.length ? html`<div class="sec"><div class="h3">Links</div>${i.links.map(l => html`<div class="mono small">${l}</div>`)}</div>` : null}
          ${i.history?.length ? html`<div class="sec"><div class="h3">History</div>${i.history.slice().reverse().map(h => html`<div class="mono small muted">${h}</div>`)}</div>` : null}
        </div>
        <div class="panel-side">
          <div class="h3">Where it came from</div>
          ${prov.back.length ? prov.back.map(h => html`<${Hop} h=${h} />`) : html`<div class="muted small">Nothing links back.</div>`}
          <div class="hop cur"><span class=${"pill " + i.kind}>${i.id}</span><span class="t">This item</span></div>
          <div class="h3">What it produces</div>
          ${prov.forward.map(h => html`<div class="word">${h.word}</div><${Hop} h=${h} />`)}
          ${later.map(x => html`<div class="hop slot"><span class="muted small">${x.word} · none yet, needed for ${x.st}</span></div>`)}
          ${prov.dangling.map(l => html`<div class="hop slot bad"><span class="small">${l} · target not found</span></div>`)}
          <div class="h3">Gaps</div>
          ${fails.map(f => html`<div class="gap"><span class="warn"></span><span class="small">${f.rule} · ${f.text}</span></div>`)}
          ${sugg.map(s => html`<div class="gap"><span class="warn amber"></span><span class="small">${s.rule} · ${s.link ? "needs " + s.link.trim() : "support suggested"}</span></div>`)}
          ${!fails.length && !sugg.length ? html`<div class="muted small">None.</div>` : null}
        </div>
      </div>
    </aside>`;
  }
  window.Panel = Panel;
})();
