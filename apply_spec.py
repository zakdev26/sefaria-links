#!/usr/bin/env python3
"""
apply_spec.py — apply a Find/Replace edit spec to a code file.

Usage:
    python3 apply_spec.py SPEC.md INPUT_FILE -o OUTPUT_FILE
    python3 apply_spec.py spec_v29.md index.html -o index_v29.html

Spec format (exactly the v29 style):
  - Each edit is introduced by a heading like "## EDIT 3 — ..."  (optional,
    used only for error messages).
  - A line ending in "find:" or "Find:" is followed by a fenced code block
    (``` ... ```) containing the EXACT text to locate.
  - A line "Replace with:" is followed by a fenced code block containing the
    replacement text.
  - Everything else in the spec (background, notes, acceptance checks) is
    ignored, as long as it contains no fenced code blocks between a "find:"
    line and its "Replace with:" line.

Rules enforced:
  - Every Find must match the input EXACTLY ONCE. Zero matches or multiple
    matches abort the run (nothing is written) and the offending EDIT is named.
  - Edits are applied in spec order, each against the result of the previous.
  - Nothing else in the file is touched; output is byte-identical outside the
    edits. CRLF inputs are handled by retrying each Find with \\n -> \\r\\n.
"""

import argparse
import re
import sys


def parse_spec(spec_text):
    """Return a list of edits: [{'name': 'EDIT 1', 'find': str, 'replace': str}]."""
    lines = spec_text.replace("\r\n", "\n").split("\n")
    edits = []
    current_name = "?"
    state = "scan"          # scan -> find_block -> want_replace -> replace_block
    block = None
    pending_find = None

    i = 0
    while i < len(lines):
        line = lines[i]

        heading = re.match(r"^##\s+(EDIT\s+\d+)", line)
        if heading:
            current_name = heading.group(1)

        if state == "scan":
            if re.search(r"find:\s*$", line, re.IGNORECASE):
                state = "want_find_block"
        elif state == "want_find_block":
            if line.strip().startswith("```"):
                block = []
                state = "find_block"
        elif state == "find_block":
            if line.strip().startswith("```"):
                pending_find = "\n".join(block)
                state = "want_replace"
            else:
                block.append(line)
        elif state == "want_replace":
            if re.match(r"^replace with:\s*$", line.strip(), re.IGNORECASE):
                state = "want_replace_block"
        elif state == "want_replace_block":
            if line.strip().startswith("```"):
                block = []
                state = "replace_block"
        elif state == "replace_block":
            if line.strip().startswith("```"):
                edits.append({
                    "name": current_name,
                    "find": pending_find,
                    "replace": "\n".join(block),
                })
                pending_find = None
                state = "scan"
            else:
                block.append(line)
        i += 1

    if state != "scan":
        sys.exit("Spec parse error: spec ended mid-edit (near %s, state=%s)."
                 % (current_name, state))
    return edits


def apply_edits(text, edits):
    """Apply edits in order; abort with a clear message on 0 or >1 matches."""
    crlf = "\r\n" in text
    for e in edits:
        find, repl = e["find"], e["replace"]
        n = text.count(find)
        if n == 0 and crlf:
            find2 = find.replace("\n", "\r\n")
            if text.count(find2) >= 1:
                find, repl, n = find2, repl.replace("\n", "\r\n"), text.count(find2)
        if n == 0:
            preview = find.strip().split("\n")[0][:80]
            sys.exit("%s FAILED: Find text not present in the input.\n"
                     "  First line of Find: %r\n"
                     "  Check the spec against the input file version." % (e["name"], preview))
        if n > 1:
            sys.exit("%s FAILED: Find text matches %d places (must be unique).\n"
                     "  Widen the Find in the spec with more surrounding lines." % (e["name"], n))
        text = text.replace(find, repl, 1)
        print("  applied %s" % e["name"])
    return text


def main():
    p = argparse.ArgumentParser(description="Apply a Find/Replace edit spec to a code file.")
    p.add_argument("spec", help="spec markdown file (v29-style Find / Replace with blocks)")
    p.add_argument("input", help="the code file to patch")
    p.add_argument("-o", "--output", required=True, help="where to write the patched file")
    args = p.parse_args()

    with open(args.spec, encoding="utf-8") as f:
        spec_text = f.read()
    with open(args.input, encoding="utf-8", newline="") as f:
        code = f.read()

    edits = parse_spec(spec_text)
    if not edits:
        sys.exit("No edits found in the spec — expected 'Find:' / 'Replace with:' fenced blocks.")
    print("Parsed %d edits from %s" % (len(edits), args.spec))

    out = apply_edits(code, edits)

    with open(args.output, "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print("Done: wrote %s (%d edits applied, everything else untouched)." % (args.output, len(edits)))


if __name__ == "__main__":
    main()