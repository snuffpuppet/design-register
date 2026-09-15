(function () {
  const html = htm.bind(preact.h);
  function App() {
    const [, tick] = preactHooks.useState(0);
    preactHooks.useEffect(() => Store.subscribe(() => tick(n => n + 1)), []);
    if (!Store.state) return html`<div class="loading">Loading the registers…</div>`;
    if (Store.baseline?.present && !Store.state.items.length) {
      return html`<div class="baselining"><p>This engagement is still baselining. The baseline screens open in the previous console until the freeze.</p><a class="btn pri" href="/old/">Open the baseline console</a></div>`;
    }
    const main = Store.ui.view.startsWith("report:") ? html`<${Report} />` : html`<${Table} />`;
    return html`<div class="layout2"><${Rail} />${main}${Store.ui.open ? html`<${Panel} />` : null}<${MoveForm.Form} /><${CreateForm.Form} /></div>`;
  }
  async function boot(retries = 20) {
    try { await Store.load(); }
    catch (e) { if (retries > 0) return setTimeout(() => boot(retries - 1), 500); document.getElementById("root").textContent = "The console could not load: " + e.message; return; }
    preact.render(html`<${App} />`, document.getElementById("root"));
  }
  document.addEventListener("keydown", e => {
    if (["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
    const rows = Store.rows(); const cur = Store.ui.open || Store.ui.focus; const at = rows.findIndex(r => r.id === cur);
    if (e.key === "j") Store.set({ focus: rows[Math.min(at + 1, rows.length - 1)]?.id || null });
    if (e.key === "k") Store.set({ focus: rows[Math.max(at - 1, 0)]?.id || null });
    if (e.key === "/") { e.preventDefault(); document.querySelector(".search")?.focus(); }
    if (e.key === "Escape") Store.set({ move: null, open: null, selection: new Set() });
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
