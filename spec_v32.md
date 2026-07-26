# v32 — in-chapter daf grid for Talmud

Fixes the Browse regression where tapping a Bavli tractate leads to a chapter
list whose chapters offer only a whole-range button, with no page grid.

Three functional edits plus a version bump. All Find strings are taken verbatim
from the v31 `dev.html` on `main`. `apply_spec.py` aborts on any non-unique or
missing match, so a failure means the file has drifted — re-paste the affected
function rather than loosening the match.

---

## EDIT 1

Find:
```
const APP_VERSION = 31;
```

Replace with:
```
const APP_VERSION = 32;
```

> If this one aborts, the declaration reads differently in your file (`var`, a
> string literal, quotes). Grep `APP_VERSION` and adjust the Find to match
> exactly; nothing else in the spec depends on it.

---

## EDIT 2 — make the v2 upgrade fire for Talmud chapter nodes

The raw index gives a Berakhot chapter node no `addressTypes` **and** no
`refs` — only a `wholeRef`. The existing predicate keys off `addressTypes`, so
it never fires, the non-raw fetch never happens, and the chapter arrives with
zero reference data. That is the actual cause of the missing grid; the
labelling fix in EDIT 3 is inert without this.

Find:
```
      if ((at.indexOf("Talmud") >= 0 || at.indexOf("Folio") >= 0) && !n.startingAddress) return true;
      if (Array.isArray(n.nodes) && walk(n.nodes)) return true;
```

Replace with:
```
      if ((at.indexOf("Talmud") >= 0 || at.indexOf("Folio") >= 0) && !n.startingAddress) return true;
      // A leaf that names a whole range but carries no refs is missing its
      // per-section data. The raw index omits refs for Talmud chapter nodes
      // (and their addressTypes with them), so this is the only signal that
      // the non-raw index would return more: Berakhot chapter 1 goes from
      // refs:0 to refs:23 across the two endpoints.
      if (n.wholeRef && !(Array.isArray(n.refs) && n.refs.length)
          && !(Array.isArray(n.nodes) && n.nodes.length)) return true;
      if (Array.isArray(n.nodes) && walk(n.nodes)) return true;
```

---

## EDIT 3 — draw the grid, labelled from each ref

Widens the daf branch past `startingAddress`, which Talmud never carries, and
adds a second label source. `startingAddress` stays first in priority, so the
Zohar path is unchanged and its verification still stands.

Find:
```
  // Daf-addressed leaf: each ref is one amud, and Sefaria supplies the real
  // opening page in startingAddress, so the grid is labelled from there —
  // never from a fixed 2a start, and never by counting preceding nodes.
  if (node.startingAddress) {
    navBody().appendChild(mk('<div class="navnote">Pick a page \u2014 a is the front, b the back.</div>'));
    const grid = document.createElement("div"); grid.className = "navgrid";
    refs.forEach((r, i) => {
      const b = document.createElement("button");
      b.textContent = dafLabelFrom(node.startingAddress, i);
      b.onclick = () => commitRef(r);
      grid.appendChild(b);
    });
    navBody().appendChild(grid);
    return;
  }
```

Replace with:
```
  // Daf-addressed leaf. Two label sources, in priority order:
  //  1. startingAddress — Sefaria's own precomputed opening amud. The Zohar
  //     needs this and nothing else will do: a parasha's main text and its
  //     Tosefta / Sitrei Torah / Midrash HaNe'elam passages share physical
  //     dapim, so neither counting nor reading refs reproduces the labels.
  //  2. the ref's own daf token. Talmud chapter nodes come back with
  //     addressTypes ["Talmud"] but startingAddress null, and their refs
  //     already name the page ("Berakhot 2b"), so read the label off each.
  const at0 = Array.isArray(node.addressTypes) ? node.addressTypes : [];
  const isDaf = !!node.startingAddress
    || at0.indexOf("Talmud") >= 0 || at0.indexOf("Folio") >= 0;
  if (isDaf) {
    navBody().appendChild(mk('<div class="navnote">Pick a page \u2014 a is the front, b the back.</div>'));
    const grid = document.createElement("div"); grid.className = "navgrid";
    refs.forEach((r, i) => {
      const b = document.createElement("button");
      b.textContent = node.startingAddress
        ? dafLabelFrom(node.startingAddress, i)
        : (dafFromRef(r) || String(i + 1));
      b.onclick = () => commitRef(r);
      grid.appendChild(b);
    });
    navBody().appendChild(grid);
    return;
  }
```

---

## EDIT 4 — the ref-reading label helper

Find:
```
function dafLabelFrom(start, i) {
  const m = String(start).match(/^(\d+)\s*([ab])$/);
  if (!m) return dafLabel(i, 2);
  const sides = parseInt(m[1], 10) * 2 + (m[2] === "b" ? 1 : 0) + i;
  return Math.floor(sides / 2) + (sides % 2 === 0 ? "a" : "b");
}
```

Replace with:
```
function dafLabelFrom(start, i) {
  const m = String(start).match(/^(\d+)\s*([ab])$/);
  if (!m) return dafLabel(i, 2);
  const sides = parseInt(m[1], 10) * 2 + (m[2] === "b" ? 1 : 0) + i;
  return Math.floor(sides / 2) + (sides % 2 === 0 ? "a" : "b");
}

// "Berakhot 2a:1-14" → "2a", "Berakhot 2b" → "2b". A chapter's refs are
// already page-addressed, so the label is read rather than derived — which
// also means a chapter that opens mid-tractate labels itself correctly with
// no offset arithmetic anywhere.
function dafFromRef(ref) {
  const m = String(ref).match(/\s(\d+[ab])(?::|\s*-|$)/);
  return m ? m[1] : null;
}
```

---

## Expected result

Berakhot → (single "By chapters" row, auto-skipped) → chapter list →
**Chapter 1** → whole-chapter button, then a 23-button grid reading
`2a 2b 3a 3b … 13a`. Tapping `2a` commits `Berakhot 2a:1-14` — only the slice
of that daf belonging to chapter 1, which is more precise than the old
tractate-wide grid was.

## Verify after applying

1. `node --check` — as always.
2. **Berakhot** → chapter 1 → grid starts `2a`, last button `13a`; tap one and
   confirm the links tree populates.
3. **A later chapter** — chapter 4 should start partway through the tractate,
   not at 2a. This is the check that the labels are being read, not counted.
4. **Zohar** → "By daf" → Volume I → Bereshit → still `15a`, and Bereshit's
   own Tosefta still `31b`. EDIT 3 must not have disturbed this.
5. **Genesis** → still "By chapter"/"By parasha", aliyah names intact.
6. A non-daf Kabbalah book (an E-tagged one) → still an integer grid, no
   spurious daf labels.

Step 4 is the one worth doing carefully: it is the whole Phase 2 result, and
EDIT 3 rewrites the branch it depends on.