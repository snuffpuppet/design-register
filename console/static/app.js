(function () {
  const html = htm.bind(preact.h);
  function App() {
    const [, tick] = preactHooks.useState(0);
    preactHooks.useEffect(() => Store.subscribe(() => tick(n => n + 1)), []);
    if (!Store.state) return html`<div class="loading">Loading the registers…</div>`;
    if (Store.baseline?.present && !Store.baseline.frozen && !Store.state.items.length) {
      return html`<${ImportRegisters}/>`;
    }
    const main = /^(reviews|meetings)(:|$)/.test(Store.ui.view) ? html`<${Workspace}/>` : Store.ui.view === 'operations' ? html`<${Operations}/>` : Store.ui.view.startsWith("report:") ? html`<${Report} key=${Store.ui.view}/>` : html`<${Table} key=${Store.ui.mode} />`;
    return html`<div class="layout2"><${Rail} />${main}${Store.ui.open ? html`<${Panel} key=${Store.ui.mode + Store.ui.open} />` : null}${Store.ui.move ? html`<${MoveForm.Form} key=${Store.ui.move.ids.join(",")+Store.ui.move.to}/>` : null}${Store.ui.create ? html`<${CreateForm.Form}/>` : null}</div>`;
  }
  async function boot(retries = 20) {
    try { await Store.load(); }
    catch (e) { if (retries > 0) return setTimeout(() => boot(retries - 1), 500); document.getElementById("root").textContent = "The console could not load: " + e.message; return; }
    const match = /^#item\/(.+)$/.exec(location.hash);
    if (match) { let id=decodeURIComponent(match[1]); const seen=new Set(); while(!Store.byId[id] && Store.state.aliases[id]?.targets?.length && !seen.has(id)){seen.add(id);id=Store.state.aliases[id].targets[0];} Store.ui.open=Store.byId[id] ? id : null; }
    preact.render(html`<${App} />`, document.getElementById("root"));
  }
  document.addEventListener("keydown", e => {
    const modal = Store.ui.move || Store.ui.create;
    // Escape reaches through a modal's own input. An input in the panel or a table cell keeps its own Escape
    // (cells.js cancels the edit); the panel closes on Escape only from outside an input.
    if (e.key === "Escape" && modal) { Store.set({ move: null, create: null }); return; }
    if (["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
    if (modal) return;
    if (/^(reviews|meetings)(:|$)/.test(Store.ui.view) && !Store.ui.open) return;
    const rows = Store.display || Store.rows(); const cur = Store.ui.open || Store.ui.focus; const at = rows.findIndex(r => r.id === cur);
    if (e.key === "j") Store.set({ focus: rows[Math.min(at + 1, rows.length - 1)]?.id || null });
    if (e.key === "k") Store.set({ focus: rows[Math.max(at - 1, 0)]?.id || null });
    if (e.key === "/") { e.preventDefault(); document.querySelector(".search")?.focus(); }
    if (e.key === "Escape") Store.set({ move: null, create: null, open: null, selection: new Set() });
    if (e.key === "Enter" && Store.ui.focus) Store.set({ open: Store.ui.focus });
    if (e.key === "x" && Store.ui.focus) Table.toggle(Store.ui.focus);
    if (e.key === "e" && Store.ui.focus) document.querySelector("tr.focus .c-title .ed")?.click();
    if (e.key === "m" && Store.ui.focus) document.querySelector("tr.focus .st")?.click();
    if (Store.ui.open && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
      e.preventDefault(); const n = rows[e.key === "ArrowDown" ? Math.min(at + 1, rows.length - 1) : Math.max(at - 1, 0)];
      if (n) Store.set({ open: n.id, focus: n.id });
    }
  });
  boot();
})();
