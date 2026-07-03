#!/usr/bin/env python
"""KYR deploy guard (audit R4/R6, 2026-07-02). Inspects the STAGED set and refuses
a commit that would ship junk or a desynced deploy. Runnable standalone
(`python _deploy_check.py`) and invoked by the PreToolUse hook before `git commit`.

Checks apply to added/modified/renamed staged entries ONLY (deletions are exempt --
`git rm --cached foo.pdf` is a CLEANUP, not a violation):
  1. no *.pdf / *.docx / KYR_* staged
  2. no staged file > 20 MB, EXCEPT the deploy blob wrench_deploy/data.*.js
  3. no nested-repo gitlink (mode 160000) staged
  4. if wrench_deploy/index.html is staged, every data.<hash>.js it references must
     be staged or already tracked (prevents the index<->blob 404 desync)
Exit 0 = pass, 1 = fail (prints a per-failure report). Never edits anything."""
import subprocess, re, sys, os, fnmatch

MAX_BYTES = 20 * 1024 * 1024
BLOB_GLOB = "wrench_deploy/data.*.js"


def sh(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def staged_entries():
    """[(status, path)] from the staged index; R/C report the destination path."""
    toks = sh("diff", "--cached", "--name-status", "-z").stdout.split("\0")
    entries, i = [], 0
    while i < len(toks):
        s = toks[i]
        if not s:
            i += 1
            continue
        code = s[0]
        if code in ("R", "C"):          # rename/copy: [status, src, dst]
            dst = toks[i + 2] if i + 2 < len(toks) else ""
            entries.append((code, dst))
            i += 3
        else:
            path = toks[i + 1] if i + 1 < len(toks) else ""
            entries.append((code, path))
            i += 2
    return entries


def gitlinks():
    """Paths staged with mode 160000 (an embedded git repo / submodule gitlink)."""
    out = sh("diff", "--cached", "--raw").stdout
    links = []
    for line in out.splitlines():
        m = re.match(r":\d+ (\d+) \w+ \w+ \w+\t(.+)", line)
        if m and m.group(1) == "160000":
            links.append(m.group(2))
    return links


def staged_size(path):
    r = sh("cat-file", "-s", ":" + path)
    return int(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip().isdigit() else 0


def tracked(path):
    return sh("ls-files", "--error-unmatch", path).returncode == 0


def in_head(path):
    """True if path was committed in HEAD (NOT merely staged now). `git ls-files`
    would count a just-`git add`ed new file as tracked; HEAD is the honest test of
    'already in the repo before this commit'."""
    return sh("cat-file", "-e", "HEAD:" + path).returncode == 0


def main():
    fails = []
    entries = staged_entries()
    live = [(c, p) for (c, p) in entries if c != "D"]      # deletions are fine

    for code, path in live:
        base = os.path.basename(path)
        low = path.lower()
        if low.endswith(".pdf") or low.endswith(".docx"):
            fails.append("forbidden file staged (%s): %s" % (code, path))
        elif base.startswith("KYR_") and not in_head(path):
            # Tracked provenance logs (verification logs, source map) are committed every
            # slice and must pass; only NEW KYR_ docs (private business/DoD material) block.
            fails.append("new private KYR_ doc staged (%s): %s "
                         "(tracked provenance logs allowed; new KYR_ docs blocked)" % (code, path))
        if not fnmatch.fnmatch(path, BLOB_GLOB):
            sz = staged_size(path)
            if sz > MAX_BYTES:
                fails.append("oversize staged file %.1fMB (>20MB): %s" % (sz / 1e6, path))

    for link in gitlinks():
        fails.append("nested-repo gitlink staged (mode 160000): %s" % link)

    idx = "wrench_deploy/index.html"
    if any(p == idx and c != "D" for c, p in entries):
        html = sh("show", ":" + idx).stdout
        refs = sorted(set(re.findall(r"data\.[0-9a-f]+\.js", html)))
        staged_paths = {p for c, p in entries if c != "D"}
        if not refs:
            fails.append("index.html staged but no data.<hash>.js reference found")
        for ref in refs:
            full = "wrench_deploy/" + ref
            if full not in staged_paths and not tracked(full):
                fails.append("index.html references %s but it is neither staged nor tracked (desync risk)" % ref)

    if fails:
        print("DEPLOY GUARD: FAIL")
        for f in fails:
            print("  x " + f)
        return 1
    print("DEPLOY GUARD: PASS (%d staged add/mod/rename file(s), no violations)" % len(live))
    return 0


if __name__ == "__main__":
    sys.exit(main())
