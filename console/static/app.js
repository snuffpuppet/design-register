(function () {
  const html = htm.bind(preact.h);
  function App() {
    const [, tick] = preactHooks.useState(0);
    preactHooks.useEffect(() => Store.subscribe(() => tick(n => n + 1)), []);
    if (!Store.state) return html`<div class="loading">Loading the registers…</div>`;
    return html`<div class="layout2">
      <${Rail} />
      <${Table} />
    </div>`;
  }
  async function boot(retries = 20) {
    try { await Store.load(); }
    catch (e) { if (retries > 0) return setTimeout(() => boot(retries - 1), 500); document.getElementById("root").textContent = "The console could not load: " + e.message; return; }
    preact.render(html`<${App} />`, document.getElementById("root"));
  }
  document.addEventListener("keydown", e => {
    if (["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
    const rows = Store.rows(); const at = rows.findIndex(r => r.id === Store.ui.focus);
    if (e.key === "j") Store.set({ focus: rows[Math.min(at + 1, rows.length - 1)]?.id || null });
    if (e.key === "k") Store.set({ focus: rows[Math.max(at - 1, 0)]?.id || null });
    if (e.key === "/") { e.preventDefault(); document.querySelector(".search")?.focus(); }
    if (e.key === "Escape") Store.set({ open: null, selection: new Set() });
  });
  boot();
})();
