(function () {
  const html = htm.bind(preact.h);
  const { useState } = preactHooks;
  const ORDER = ["REQ", "CR", "DEC", "LIM", "OI", "RSK"];
  const DEFAULT_COLUMNS = ["id", "title", "status", "owner"];

  function Item({ id, label, n, on, onClick, pill }) {
    return html`<div class=${"rl-it" + (on ? " on" : "")} onClick=${onClick}>
      <span>${pill ? html`<span class=${"pill " + pill}>${pill}</span> ` : null}${label}</span>
      ${n !== undefined ? html`<span class="n">${n}</span>` : null}</div>`;
  }

  // A register row in the Registers group, with a ⋯ menu (shown on hover) offering Renumber.
  function RegItem({ kind, label, n, on, onClick }) {
    const S = Store, [open, setOpen] = useState(false), [confirming, setConfirming] = useState(false);
    const renumber = async () => {
      setConfirming(false);
      try { const r = await S.post("/api/renumber", { type: kind }); Store.toast(`Renumbered ${Object.keys(r.map).length} items`); await S.load(); }
      catch (e) { Store.toast(e.message); }
    };
    return html`<div class="rl-itwrap">
      <div class=${"rl-it" + (on ? " on" : "")} onClick=${onClick}>
        <span><span class=${"pill " + kind}>${kind}</span> ${label}</span>
        <span class="n">${n}</span>

      </div>
      ${open ? html`<div class="menu" onClick=${e => e.stopPropagation()}>
        <div class="mi" onClick=${() => { setOpen(false); setConfirming(true); }}><span>Renumber…</span></div>
      </div>` : null}
      ${confirming ? html`<div class="menu" onClick=${e => e.stopPropagation()}>
        <div class="small">Renumber all ${label}. Needs a clean git tree in the engagement folder.</div>
        <div class="dlg-f"><button class="btn" onClick=${() => setConfirming(false)}>Cancel</button><button class="btn pri" onClick=${renumber}>Renumber</button></div>
      </div>` : null}
    </div>`;
  }

  // Copied from old/app.js:401-414 so both consoles agree on the localStorage key and behaviour.
  function setTheme(t) {
    try { t === "system" ? localStorage.removeItem("theme") : localStorage.setItem("theme", t); } catch {}
    if (t === "system") delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = t;
  }
  function currentTheme() { try { return localStorage.getItem("theme") || "system"; } catch { return "system"; } }

  function ThemeSwitch() {
    const [t, setT] = useState(currentTheme());
    const pick = v => { setTheme(v); setT(v); };
    return html`<span class="theme" title="Colour scheme">
      <button class=${t === "light" ? "on" : ""} onClick=${() => pick("light")}>Light</button>
      <button class=${t === "system" ? "on" : ""} onClick=${() => pick("system")}>Auto</button>
      <button class=${t === "dark" ? "on" : ""} onClick=${() => pick("dark")}>Dark</button>
    </span>`;
  }

  function Rail() {
    const S = Store, c = S.counts(), ui = S.ui;
    const [savingView, setSavingView] = useState(false), [viewName, setViewName] = useState("");
    const go = (view, extra = {}) => () => S.set({ view, selection: new Set(), open: null, filter: { ...S.ui.filter, rule: "", ...extra } });
    const rules = Object.entries(c.byRuleItems || {}).sort((a, b) => b[1] - a[1]);
    const saveCurrent = async () => {
      const name = viewName.trim(); if (!name) return;
      // A register tab (view is a type code, e.g. "REQ") is not itself part of the chip filter, so fold it
      // in here; a work queue (outstanding, integrity, …) has no type of its own and is left as is.
      const filter = { ...S.ui.filter };
      if (S.model.states[S.ui.view] && !filter.types.length) filter.types = [S.ui.view];
      const view = { name, filter, columns: S.ui.columns || S.columnsFor() || DEFAULT_COLUMNS, groupBy: S.ui.groupBy, sections: ["table"] };
      const vs = S.views.concat([view]);
      const r = await S.post("/api/views", { views: vs });
      S.views = r.views; setSavingView(false); setViewName("");
      S.set({ view: "report:" + (r.views.length - 1) });
    };
    return html`<nav class="rail">
      <div class="grp"><span class="lbl">Engagement</span><div class="rl-eng">${S.state.engagement.name}</div></div>
      <div class="grp"><span class="lbl">Workspace</span>
        <${Item} label="Desktop" on=${ui.mode === 'desktop' && !(/^(reviews|meetings)/.test(ui.view))} onClick=${() => S.set({mode:'desktop',view:'all',session:null,open:null,selection:new Set()})}/>
        <${Item} label="Rationalise" on=${ui.mode === 'rationalise'} onClick=${() => S.set({mode:'rationalise',view:'all',session:null,open:null,selection:new Set()})}/>
      </div>
      <div class="grp"><span class="lbl">Desktop by scope</span>
        ${S.model.scopes.map(scope => html`<${Item} label=${scope} on=${ui.mode==='desktop' && ui.view==='all' && ui.filter.scopes.length===1 && ui.filter.scopes[0]===scope} onClick=${()=>S.set({mode:'desktop',view:'all',session:null,open:null,selection:new Set(),filter:{types:[],statuses:[],scopes:[scope],owners:[],rule:'',q:''}})}/>`)}
      </div>
      <div class="grp"><span class="lbl">Work</span>
        <${Item} label="Outstanding" n=${c.outstanding} on=${ui.view === "outstanding"} onClick=${go("outstanding")} />
        <${Item} label="Integrity" n=${c.integrity} on=${ui.view === "integrity" && !ui.filter.rule} onClick=${go("integrity")} />
        ${ui.view === "integrity" ? rules.map(([r, n]) => html`<${Item} label=${r + " " + (S.model.rules[r] || "").split(" ").slice(0, 4).join(" ")} n=${n} on=${ui.filter.rule === r} onClick=${go("integrity", { rule: r })} />`) : null}
        <${Item} label="Suggested supports" n=${c.supports} on=${ui.view === "supports"} onClick=${go("supports")} />
        <${Item} label="Duplicates" n=${c.duplicates} on=${ui.view === "duplicates"} onClick=${go("duplicates")} />
        <${Item} label="Unreviewed" n=${c.unreviewed} on=${ui.view === "unreviewed"} onClick=${() => S.set({view:"reviews",open:null})} />
      </div>
      <div class="grp"><span class="lbl">Registers</span>
        <${Item} label="All items" n=${c.all} on=${ui.view === "all"} onClick=${go("all")} />
        ${ORDER.map(k => html`<${RegItem} kind=${k} label=${S.model.names[k] + "s"} n=${c.byType[k] || 0} on=${ui.view === k} onClick=${go(k)} />`)}
      </div>
      <div class="grp"><span class="lbl">Reports</span>
        ${S.views.map((v, i) => html`<${Item} label=${v.name} on=${ui.view === "report:" + i} onClick=${go("report:" + i)} />`)}
        ${savingView
          ? html`<div class="rl-it save"><input class="inp cell" value=${viewName} onInput=${e => setViewName(e.target.value)}
              onKeyDown=${e => { if (e.key === "Enter") saveCurrent(); if (e.key === "Escape") { setSavingView(false); setViewName(""); } }}
              placeholder="view name" /><button class="btn ghost" disabled=${!viewName.trim()} onClick=${saveCurrent}>Save</button></div>`
          : html`<div class="rl-it muted" onClick=${() => setSavingView(true)}>+ Save current view</div>`}
      </div>
      <div class="rl-foot">
        <${Item} label="Saved reviews" onClick=${()=>S.set({mode:'desktop',view:'reviews',open:null})}/>
        <${Item} label="Meeting records" onClick=${()=>S.set({mode:'desktop',view:'meetings',open:null})}/>
        <${Item} label="Recent operations" onClick=${go("operations")}/>
        <a class="rl-it muted" href="guide.html" target="_blank" rel="noopener">Guide</a>
        <${ThemeSwitch} />
      </div>
    </nav>`;
  }
  window.Rail = Rail;
})();
