# Spec: Sefaria Links v29 — circled markers, universal back-links, page breaks, unlabelled translations

## Task

You are given the complete v28 HTML file. Output the **complete replacement file** with ONLY the edits below applied. Every other line must be byte-identical to the input. Do not reformat, re-indent, rename, or "improve" anything not listed here. Do not add or remove blank lines outside the edits.

## Background (context only — do not paste into the file)

Four changes to the built documents (mainly the Kindle EPUB):

1. The marker row after each source segment shows circled glyphs Ⓡ Ⓣ Ⓢ (Unicode U+24C7 / U+24C9 / U+24C8) instead of the commentator names. Targets are unchanged: each glyph jumps to that commentator's first piece in place.
2. EVERY commentary piece — all commentators, not just Rashi/Tosafot/Steinsaltz — gets a small `◄ <source ref>` link at the top, folded into the end of its ref line (or its h3 heading when a lone piece has no ref line). In Section mode it jumps to the section heading; in Category mode to the exact verse in the Source section (requires the source to be included). The standalone `backlink` block type is removed entirely.
3. In the EPUB, every section heading (h1) and every commentator heading (h3 in Section mode, h2 in Category mode) starts on a new page via `page-break-before`.
4. The "AI translation (…)" label is removed from all three built formats; the translation text itself stays and is rendered in italics so it remains distinguishable from Sefaria's English. The label in the in-app preview's editing box (`aiTransBoxHtml`) is deliberately KEPT — do not touch the preview.

Word and PDF builders otherwise ignore the new fields (`pb`, `back`, `letter`) — that is intended.

---

## EDIT 1 — version bump

Find:
```js
const APP_VERSION = 28;   // bump when deploying, shows in footer + built books
```
Replace with:
```js
const APP_VERSION = 29;   // bump when deploying, shows in footer + built books
```

## EDIT 2 — gatherContent: rtsFor emits circled letters

Find:
```js
    if (!groups.length) return null;
    return { marks: groups.map(([name, links]) => ({ name, target: anchorForLink(links[0]) })) };
  };
```
Replace with:
```js
    if (!groups.length) return null;
    const LETTERS = ["\u24C7", "\u24C9", "\u24C8"];   // Ⓡ Ⓣ Ⓢ, indexed by commRank
    return { marks: groups.map(([name, links]) => ({ name, letter: LETTERS[commRank(name)], target: anchorForLink(links[0]) })) };
  };
```
(Use the `\u24C7` / `\u24C9` / `\u24C8` escapes exactly as shown — do not substitute raw glyphs.)

## EDIT 3 — gatherContent: Source h1 gets a page break

Find:
```js
    blocks.push({ type: "h1", text: "Source — " + srcLabel, anchor, first: true });
```
Replace with:
```js
    blocks.push({ type: "h1", text: "Source — " + srcLabel, anchor, first: true, pb: true });
```

## EDIT 4 — gatherContent: Section-mode h1 gets a page break

Find:
```js
      blocks.push({ type: "h1", text: h1text, anchor, first: blocks.length === 0 });
```
Replace with:
```js
      blocks.push({ type: "h1", text: h1text, anchor, first: blocks.length === 0, pb: true });
```

## EDIT 5 — gatherContent: Section-mode pieces — back on h3/ref, pb on h3, drop old backlink

Find:
```js
          const a3 = single ? anchorForLink(links[0]) : nextId();
          toc.push({ level: 3, text: h3text, anchor: a3 });
          blocks.push({ type: "h3", text: h3text, anchor: a3 });
          for (const l of links) {
            if (!single) {   // the h3 already names a lone link, so skip its ref line
              const enRef = l.sourceRef || l.ref || "";
              const heRef = l.sourceHeRef || "";
              blocks.push({ type: "ref", text: enRef + (heRef ? "  —  " + heRef : ""), anchor: anchorForLink(l) });
            }
            if (incHe) { const he = stripHtml(asText(l.he)); if (he) blocks.push({ type: "he", text: he }); }
            if (incEn) { const en = stripHtml(asText(l.text)); if (en) blocks.push({ type: "en", text: en }); }
            emitAiBlock(blocks, canonicalRef(l));
            emitNote("L" + l._i);   // this text's own note, right beneath it
            if (wantSrc && commRank(commName(l)) <= 2)
              blocks.push({ type: "backlink", text: seg, anchor: anchor });
            written++;
          }
```
Replace with:
```js
          const a3 = single ? anchorForLink(links[0]) : nextId();
          const back = { anchor: anchor, text: seg };   // this section's heading
          toc.push({ level: 3, text: h3text, anchor: a3 });
          blocks.push({ type: "h3", text: h3text, anchor: a3, pb: true, back });
          for (const l of links) {
            if (!single) {   // the h3 already names a lone link, so skip its ref line
              const enRef = l.sourceRef || l.ref || "";
              const heRef = l.sourceHeRef || "";
              blocks.push({ type: "ref", text: enRef + (heRef ? "  —  " + heRef : ""), anchor: anchorForLink(l), back });
            }
            if (incHe) { const he = stripHtml(asText(l.he)); if (he) blocks.push({ type: "he", text: he }); }
            if (incEn) { const en = stripHtml(asText(l.text)); if (en) blocks.push({ type: "en", text: en }); }
            emitAiBlock(blocks, canonicalRef(l));
            emitNote("L" + l._i);   // this text's own note, right beneath it
            written++;
          }
```
Note: `anchor` in the `back` object is the section's h1 anchor already in scope — do not rename anything.

## EDIT 6 — gatherContent: Category-mode h1 gets a page break

Find:
```js
    const catAnchor = nextId();
    toc.push({ level: 1, text: cat, anchor: catAnchor });
    blocks.push({ type: "h1", text: cat, anchor: catAnchor });
```
Replace with:
```js
    const catAnchor = nextId();
    toc.push({ level: 1, text: cat, anchor: catAnchor });
    blocks.push({ type: "h1", text: cat, anchor: catAnchor, pb: true });
```

## EDIT 7 — gatherContent: Category-mode pieces — pb on h2, back on every ref, drop old backlink

Find:
```js
      const commAnchor = nextId();
      toc.push({ level: 2, text: comm, anchor: commAnchor });
      blocks.push({ type: "h2", text: comm, anchor: commAnchor });

      for (const l of links) {
        const enRef = l.sourceRef || l.ref || "";
        const heRef = l.sourceHeRef || "";
        blocks.push({ type: "ref", text: enRef + (heRef ? "  —  " + heRef : ""), anchor: anchorForLink(l) });
        if (incHe) { const he = stripHtml(asText(l.he)); if (he) blocks.push({ type: "he", text: he }); }
        if (incEn) { const en = stripHtml(asText(l.text)); if (en) blocks.push({ type: "en", text: en }); }
        emitAiBlock(blocks, canonicalRef(l));
        emitNote("L" + l._i);   // this text's own note, right beneath it
        const bseg = segRefOf(l);
        if (haveSrc && commRank(comm) <= 2 && segSrcAnchor[bseg])
          blocks.push({ type: "backlink", text: bseg, anchor: segSrcAnchor[bseg] });
        written++;
      }
```
Replace with:
```js
      const commAnchor = nextId();
      toc.push({ level: 2, text: comm, anchor: commAnchor });
      blocks.push({ type: "h2", text: comm, anchor: commAnchor, pb: true });

      for (const l of links) {
        const enRef = l.sourceRef || l.ref || "";
        const heRef = l.sourceHeRef || "";
        const bseg = segRefOf(l);
        const back = (haveSrc && segSrcAnchor[bseg]) ? { anchor: segSrcAnchor[bseg], text: bseg } : null;
        blocks.push({ type: "ref", text: enRef + (heRef ? "  —  " + heRef : ""), anchor: anchorForLink(l), back });
        if (incHe) { const he = stripHtml(asText(l.he)); if (he) blocks.push({ type: "he", text: he }); }
        if (incEn) { const en = stripHtml(asText(l.text)); if (en) blocks.push({ type: "en", text: en }); }
        emitAiBlock(blocks, canonicalRef(l));
        emitNote("L" + l._i);   // this text's own note, right beneath it
        written++;
      }
```

## EDIT 8 — epubBody: back-link helper

Find:
```js
  const menu = kids => kids.map(k => `<a href="#${k.anchor}">${xmlEsc(k.text)}</a>`).join(" · ");
```
Replace with:
```js
  const menu = kids => kids.map(k => `<a href="#${k.anchor}">${xmlEsc(k.text)}</a>`).join(" · ");
  // small back-to-source link appended to a piece's heading / ref line
  const bkHtml = b => b.back ? ` <a class="bk" href="#${b.back.anchor}">\u25c4 ${xmlEsc(b.back.text)}</a>` : "";
```

## EDIT 9 — epubBody: h1 page-break class

Find:
```js
      s += `<h1 id="${b.anchor}">${xmlEsc(b.text)}</h1>\n`;
```
Replace with:
```js
      s += `<h1 id="${b.anchor}"${b.pb ? ' class="pb"' : ""}>${xmlEsc(b.text)}</h1>\n`;
```

## EDIT 10 — epubBody: h2 page-break class

Find:
```js
      s += `<h2 id="${b.anchor}">${xmlEsc(b.text)}</h2>\n`;
```
Replace with:
```js
      s += `<h2 id="${b.anchor}"${b.pb ? ' class="pb"' : ""}>${xmlEsc(b.text)}</h2>\n`;
```

## EDIT 11 — epubBody: h3 + ref get back-links, AI label dropped

Find:
```js
    else if (b.type === "h3") s += `<h3 id="${b.anchor}">${xmlEsc(b.text)}</h3>\n`;
    else if (b.type === "ref") s += `<p class="ref"${b.anchor ? ` id="${b.anchor}"` : ""}>${xmlEsc(b.text)}</p>\n`;
    else if (b.type === "note") s += `<p class="usernote">${xmlEsc(b.text)}</p>\n<p class="usernote-date">${xmlEsc(b.date || "")}</p>\n`;
    else if (b.type === "ai") s += `<p class="ai-label">AI translation (${xmlEsc(b.lang)})</p>\n<p class="ai">${xmlEsc(b.text)}</p>\n`;
```
Replace with:
```js
    else if (b.type === "h3") s += `<h3 id="${b.anchor}"${b.pb ? ' class="pb"' : ""}>${xmlEsc(b.text)}${bkHtml(b)}</h3>\n`;
    else if (b.type === "ref") s += `<p class="ref"${b.anchor ? ` id="${b.anchor}"` : ""}>${xmlEsc(b.text)}${bkHtml(b)}</p>\n`;
    else if (b.type === "note") s += `<p class="usernote">${xmlEsc(b.text)}</p>\n<p class="usernote-date">${xmlEsc(b.date || "")}</p>\n`;
    else if (b.type === "ai") s += `<p class="ai">${xmlEsc(b.text)}</p>\n`;
```

## EDIT 12 — epubBody: circled-glyph marker row; delete the backlink branch

Find:
```js
    else if (b.type === "rtsrow") {
      s += `<p class="rtsrow">` + b.marks.map(m => `<a class="rts" href="#${m.target}">${xmlEsc(m.name)}</a>`).join(" \u00b7 ") + `</p>\n`;
    }
    else if (b.type === "backlink") {
      s += `<p class="backlink"><a href="#${b.anchor}">\u25c4 ${xmlEsc(b.text)}</a></p>\n`;
    }
```
Replace with:
```js
    else if (b.type === "rtsrow") {
      s += `<p class="rtsrow">` + b.marks.map(m => `<a class="rts" href="#${m.target}" title="${xmlEsc(m.name)}">${xmlEsc(m.letter)}</a>`).join(" ") + `</p>\n`;
    }
```

## EDIT 13 — EPUB CSS: AI paragraph italic, label rule removed

In the `css` template string inside `buildEpub`, find:
```
p.ai-label { font-style: italic; font-size: .85em; color: #8a6d3b; margin: .5em 0 .1em; }
p.ai { line-height: 1.6; margin: 0 0 .6em; }
```
Replace with:
```
p.ai { font-style: italic; line-height: 1.6; margin: 0 0 .6em; }
```

## EDIT 14 — EPUB CSS: marker glyphs, back-links, page breaks

Find:
```
p.rtsrow { font-size: .7em; color: #6f675a; margin: .1em 0 .7em; }
a.rts { color: #6b5329; text-decoration: none; }
p.backlink { font-size: .7em; margin: .2em 0 .8em; }
p.backlink a { color: #6b5329; text-decoration: none; }
```
Replace with:
```
p.rtsrow { font-size: .95em; margin: .1em 0 .7em; }
a.rts { color: #6b5329; text-decoration: none; margin-right: .35em; }
a.bk { font-size: .72em; font-weight: normal; color: #6b5329; text-decoration: none; white-space: nowrap; }
h1.pb, h2.pb, h3.pb { page-break-before: always; }
```

## EDIT 15 — buildDocx: AI label removed

Find:
```js
    else if (b.type === "ai") body.push(new Paragraph({
      spacing: { before: 60, after: 100 },
      children: [
        new TextRun({ text: "AI translation (" + b.lang + "): ", bold: true, size: 20, color: "8a6d3b" }),
        new TextRun({ text: b.text, italics: true, size: 22 })
      ]
    }));
```
Replace with:
```js
    else if (b.type === "ai") body.push(new Paragraph({
      spacing: { before: 60, after: 100 },
      children: [
        new TextRun({ text: b.text, italics: true, size: 22 })
      ]
    }));
```

## EDIT 16 — buildPdf: AI label removed

Find:
```js
    else if (b.type === "ai") bodyHtml += `<p class="ai-label">AI translation (${escapeHtml(b.lang)})</p><p class="ai">${escapeHtml(b.text)}</p>`;
```
Replace with:
```js
    else if (b.type === "ai") bodyHtml += `<p class="ai">${escapeHtml(b.text)}</p>`;
```

## EDIT 17 — buildPdf CSS: AI paragraph italic, label rule removed

Find:
```
  p.ai-label { font-style: italic; font-size: 12px; color: #8a6d3b; margin: 6px 0 1px; }
  p.ai { font-size: 14px; line-height: 1.6; margin: 0 0 8px; }
```
Replace with:
```
  p.ai { font-style: italic; font-size: 14px; line-height: 1.6; margin: 0 0 8px; }
```

---

## Out of scope — must NOT change

- The in-app preview: `aiTransBoxHtml` keeps its "AI translation (…)" label and the `.aitransbox .ai-label` CSS keeps its rule — this is the editing UI, not the built file.
- `renderPreview`, the tree, the AI helper, the browse navigator, nav.xhtml/toc.ncx generation, the docx Contents/bookmarks, and everything else in the file.
- The doctitle heading in epubBody (`<h1 class="doctitle">…`) gets NO pb class.

## Acceptance checks

1. The `<script>` parses (extract it and run `node --check`).
2. Grep: the string `backlink` appears NOWHERE in the output (block type, epubBody branch, and CSS all removed).
3. Grep: `AI translation (` appears exactly once — inside `aiTransBoxHtml` (the preview). `ai-label` appears only in the preview markup and its `.aitransbox .ai-label` CSS rule.
4. Grep: `\u24C7`, `\u24C9`, `\u24C8` each appear exactly once (in `rtsFor`).
5. Talmud daf EPUB, Section mode, source + everything ticked: each source segment is followed by a Ⓡ Ⓣ Ⓢ row whose glyphs jump to those commentators' first pieces in that section; every commentator heading (Rashi, Tosafot, Meiri…) starts on a new page and carries a small `◄ <section ref>` link back to its section heading; every multi-piece ref line carries the same link; every section heading starts on a new page.
6. Same build in Category mode: each commentator's h2 starts a new page; every piece's ref line ends with `◄ <verse ref>` jumping to its exact verse in Source (absent when the Original Text is unticked).
7. Footer shows app v29.