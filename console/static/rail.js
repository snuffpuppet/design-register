(function () {
  const html = htm.bind(preact.h);
  const ORDER = ["REQ", "CR", "DEC", "LIM", "OI", "RSK"];
  function Item({ id, label, n, on, onClick, pill }) {
    return html`<div class=${"rl-it" + (on ? " on" : "")} onClick=${onClick}>
      <span>${pill ? html`<span class=${"pill " + pill}>${pill}</span> ` : null}${label}</span>
      ${n !== undefined ? html`<span class="n">${n}</span>` : null}</div>`;
  }
  function Rail() {
    const S = Store, c = S.counts(), ui = S.ui;
    const go = (view, extra = {}) => () => S.set({ view, selection: new Set(), open: null, filter: { ...S.ui.filter, rule: "", ...extra } });
    const rules = Object.entries(c.byRule || {}).sort((a, b) => b[1] - a[1]);
    return html`<nav class="rail">
      <div class="grp"><span class="lbl">Engagement</span><div class="rl-eng">${S.state.engagement.name}</div></div>
      <div class="grp"><span class="lbl">Work</span>
        <${Item} label="Outstanding" n=${c.outstanding} on=${ui.view === "outstanding"} onClick=${go("outstanding")} />
        <${Item} label="Integrity" n=${S.state.integrity.failures.length} on=${ui.view === "integrity" && !ui.filter.rule} onClick=${go("integrity")} />
        ${ui.view === "integrity" ? rules.map(([r, n]) => html`<${Item} label=${r + " " + (S.model.rules[r] || "").split(" ").slice(0, 4).join(" ")} n=${n} on=${ui.filter.rule === r} onClick=${go("integrity", { rule: r })} />`) : null}
        <${Item} label="Suggested supports" n=${c.supports} on=${ui.view === "supports"} onClick=${go("supports")} />
        <${Item} label="Duplicates" n=${c.duplicates} on=${ui.view === "duplicates"} onClick=${go("duplicates")} />
        <${Item} label="Unreviewed" n=${c.unreviewed} on=${ui.view === "unreviewed"} onClick=${go("unreviewed")} />
      </div>
      <div class="grp"><span class="lbl">Registers</span>
        <${Item} label="All items" n=${c.all} on=${ui.view === "all"} onClick=${go("all")} />
        ${ORDER.map(k => html`<${Item} pill=${k} label=${S.model.names[k] + "s"} n=${c.byType[k] || 0} on=${ui.view === k} onClick=${go(k)} />`)}
      </div>
      <div class="grp"><span class="lbl">Reports</span>
        ${S.views.map((v, i) => html`<${Item} label=${v.name} on=${ui.view === "report:" + i} onClick=${go("report:" + i)} />`)}
      </div>
    </nav>`;
  }
  window.Rail = Rail;
})();
