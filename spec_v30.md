# Spec v30 — Zohar daf grids that match Sefaria

Background (ignored by the applier): the Browse navigator already routes the
Zohar into its daf-grid path (Kabbalah is in CORPORA, a complex schema drills
through renderSchemaNodes, and a Talmud-addressed leaf draws a daf grid). The
one thing that breaks the Zohar is that dafLabel() hardcodes the Babylonian
Talmud convention of starting at daf 2a. The Zohar's parashot don't start at
2a — each node has its own daf range — so every generated ref is mislabelled.
These edits make the daf grid read its true starting daf and page count from
Sefaria at run time, falling back to the old 2a assumption when anything is
uncertain, so ordinary Talmud tractates are unchanged.

## EDIT 1 — bump the app version

Find:

```
const APP_VERSION = 28;   // bump when deploying, shows in footer + built books
```

Replace with:

```
const APP_VERSION = 30;   // bump when deploying, shows in footer + built books
```

## EDIT 2 — offset-aware dafLabel + a helper that reads the real start/count

Find:

```
function refJoin(prefix, sections) { return prefix + " " + sections.join(":"); }
function dafLabel(i) { const d = 2 + Math.floor(i / 2); return d + (i % 2 === 0 ? "a" : "b"); }
```

Replace with:

```
function refJoin(prefix, sections) { return prefix + " " + sections.join(":"); }
function dafLabel(i, start) { const s = (start == null ? 2 : start); const d = s + Math.floor(i / 2); return d + (i % 2 === 0 ? "a" : "b"); }
// The true first daf and amud-count for a daf-addressed node, read from
// Sefaria rather than assumed. Standard Talmud tractates open at 2a, but the
// Zohar's daf-addressed parashot open elsewhere and each node has its own
// range — so labelling from a fixed 2a start mislabels every Zohar page. Read
// the node's first available section ref for the start daf, and its shape for
// the page count; on any uncertainty fall back to the standard-Talmud
// assumption so ordinary tractates are unaffected.
async function dafGridInfo(prefix, node) {
  let start = 2, dapim = null;
  try {
    const r = await fetch(SHAPE_API + encodeURIComponent(prefix));
    if (r.ok) {
      const j = await r.json();
      let first = Array.isArray(j) ? j[0] : j;
      if (first && first.isComplex && Array.isArray(first.chapters)) {
        const leaf = first.chapters.find(c => c && c.title === prefix);
        if (leaf) first = leaf;
      }
      if (first && Array.isArray(first.chapters)) dapim = first.chapters.length;
      else if (first && typeof first.length === "number") dapim = first.length;
    }
  } catch (e) {}
  try {
    const r = await fetch(TEXTS_API + encodeURIComponent(prefix) + "?context=0&pad=0");
    if (r.ok) {
      const j = await r.json();
      const cand = j.firstAvailableSectionRef || j.ref || "";
      const m = String(cand).match(/\s(\d+)[ab](?::|\s|$)/);
      if (m) start = parseInt(m[1], 10);
    }
  } catch (e) {}
  const amudim = dapim ? dapim * 2 : ((node && node.lengths && node.lengths[0]) || 180);
  return { start, amudim };
}
```

## EDIT 3 — the daf grid uses the real start + count

Find:

```
  if (addr === "Talmud") {
    const build = (amudim) => {
      navBody().innerHTML = "";
      navBody().appendChild(mk('<div class="navnote">Pick a page \u2014 a is the front, b the back.</div>'));
      const grid = document.createElement("div"); grid.className = "navgrid";
      for (let i = 0; i < amudim; i++) {
        const b = document.createElement("button"); b.textContent = dafLabel(i);
        b.onclick = () => commitRef(prefix + " " + dafLabel(i));
        grid.appendChild(b);
      }
      navBody().appendChild(grid);
    };
    const n0 = node.lengths && node.lengths[0];
    if (n0) build(n0);
    else { navLoading(); shapeLen(prefix).then(len => build(len ? len * 2 : 180)).catch(() => build(180)); }
    return;
  }
```

Replace with:

```
  if (addr === "Talmud") {
    const build = (amudim, start) => {
      navBody().innerHTML = "";
      navBody().appendChild(mk('<div class="navnote">Pick a page \u2014 a is the front, b the back.</div>'));
      const grid = document.createElement("div"); grid.className = "navgrid";
      for (let i = 0; i < amudim; i++) {
        const label = dafLabel(i, start);
        const b = document.createElement("button"); b.textContent = label;
        b.onclick = () => commitRef(prefix + " " + label);
        grid.appendChild(b);
      }
      navBody().appendChild(grid);
    };
    navLoading();
    dafGridInfo(prefix, node)
      .then(info => build(info.amudim, info.start))
      .catch(() => build((node.lengths && node.lengths[0]) || 180, 2));
    return;
  }
```