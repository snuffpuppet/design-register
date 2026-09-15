// Client state for the console. One object, one subscribe, every write goes to the API and reloads state.
(function () {
  const listeners = new Set();
  const Store = {
    state: null, model: null, views: [],
    ui: { view: "all", filter: { types: [], statuses: [], scopes: [], owners: [], rule: "", since: "", q: "" },
          selection: new Set(), focus: null, open: null, groupBy: "", columns: null, madeBy: "" },
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    emit() { listeners.forEach(fn => fn()); },
    set(patch) { Object.assign(Store.ui, patch); Store.emit(); },
    async load() {
      const [s, m, v] = await Promise.all([fetch("/api/state").then(r => r.json()), fetch("/api/model").then(r => r.json()), fetch("/api/views").then(r => r.json())]);
      Store.state = s; Store.model = m; Store.views = v.views;
      Store.byId = Object.fromEntries(s.items.map(i => [i.id, i]));
      Store.failuresById = {};
      for (const f of s.integrity.failures) (Store.failuresById[f.id] ||= []).push(f);
      Store.suggestionsById = {};
      for (const g of s.integrity.suggestions) (Store.suggestionsById[g.id] ||= []).push(g);
      try { Store.ui.madeBy = localStorage.getItem("madeBy") || Store.ui.madeBy; } catch {}
      Store.emit();
    },
    async post(url, body) {
      const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ madeBy: Store.ui.madeBy, ...body }) });
      const j = await r.json();
      if (!r.ok || j.error) throw new Error(j.error || r.statusText);
      return j;
    },
    // The rows the current view shows: the view's fixed filter, then the user's chips, then free text.
    rows() {
      const { filter, view } = Store.ui; const S = Store.state; if (!S) return [];
      let xs = S.items.slice();
      const fixed = Store.viewFilter(view);
      xs = xs.filter(i => fixed(i));
      if (filter.types.length) xs = xs.filter(i => filter.types.includes(i.kind));
      if (filter.statuses.length) xs = xs.filter(i => filter.statuses.includes(i.status));
      if (filter.scopes.length) xs = xs.filter(i => filter.scopes.includes(i.scope || ""));
      if (filter.owners.length) xs = xs.filter(i => filter.owners.includes(i.owner || ""));
      if (filter.rule) xs = xs.filter(i => (Store.failuresById[i.id] || []).some(f => f.rule === filter.rule));
      if (filter.since) { const d = Store.parseDate(filter.since); if (d) xs = xs.filter(i => (Store.parseDate(i.updated) || 0) >= d); }
      if (filter.q) { const q = filter.q.toLowerCase(); xs = xs.filter(i => (i.id + " " + i.title + " " + (i.notes || "")).toLowerCase().includes(q)); }
      return xs.sort((a, b) => a.id < b.id ? -1 : 1);
    },
    viewFilter(view) {
      const term = i => (Store.model.terminal[i.kind] || []).includes(i.status);
      if (view === "all") return () => true;
      if (view === "outstanding") return i => !term(i);
      if (view === "integrity") return i => (Store.failuresById[i.id] || []).length > 0;
      if (view === "supports") return i => (Store.suggestionsById[i.id] || []).length > 0;
      if (view === "duplicates") { const ids = new Set(Store.state.dupes.flatMap(g => g.ids || g)); return i => ids.has(i.id); }
      if (view === "unreviewed") { const ids = new Set(Store.state.unreviewed); return i => ids.has(i.id); }
      if (Store.model.states[view]) return i => i.kind === view;
      return () => true;
    },
    parseDate(s) {
      const m = /^(\d{1,2}) (\w+) (\d{4})/.exec(s || ""); if (!m) return null;
      const mi = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"].indexOf(m[2]);
      return mi < 0 ? null : new Date(+m[3], mi, +m[1]);
    },
    // The column list for the current view: fixed sets for the work queues, a computed set for a register.
    columnsFor() {
      const { view, filter } = Store.ui;
      if (view === "integrity" && filter.rule) {
        const f = Store.state.integrity.failures.find(x => x.rule === filter.rule);
        // The failing field is the first word of the rule text that names a model field, else Owner.
        const text = (f?.text || "").toLowerCase();
        const key = Object.keys(Store.model.labels).find(k => text.includes((Store.model.labels[k] || k).toLowerCase())) || "owner";
        return ["id", "title", "status", "scope", key, "issues"];
      }
      if (view === "supports") return ["id", "title", "status", "support"];
      if (view === "duplicates") return ["id", "title", "status", "scope", "group"];
      if (view === "unreviewed") return ["id", "title", "status", "scope", "owner", "reviewed"];
      if (Store.model.states[view]) return ["id", "title", "status", "scope", "owner", ...Store.model.short[view].filter(k => !["scope", "owner"].includes(k)).slice(0, 2), "links", "issues"];
      return null;
    },
    counts() {
      const S = Store.state; if (!S) return {};
      const c = { all: S.items.length, outstanding: 0, integrity: 0, supports: 0, duplicates: 0, unreviewed: S.unreviewed.length, byType: {}, byRule: {} };
      const term = i => (Store.model.terminal[i.kind] || []).includes(i.status);
      for (const i of S.items) { c.byType[i.kind] = (c.byType[i.kind] || 0) + 1; if (!term(i)) c.outstanding++; }
      c.integrity = Object.keys(Store.failuresById).length; c.supports = Object.keys(Store.suggestionsById).length;
      c.duplicates = S.dupes.length;
      for (const f of S.integrity.failures) c.byRule[f.rule] = (c.byRule[f.rule] || 0) + 1;
      return c;
    },
  };
  window.Store = Store;
})();
