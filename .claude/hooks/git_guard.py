#!/usr/bin/env python
"""KYR PreToolUse git guard (audit R4/R6, 2026-07-02). Reads the tool call on stdin.
For Bash git commands it:
  1. HARD-BLOCKS `git add -A` / `git add .` / `git add --all` (and bundled -A flags)
  2. runs _deploy_check.py before `git commit` and blocks on any violation
Exit 2 blocks the tool call and returns the message to Claude; exit 0 allows.
Fails OPEN on any internal error (never wedge the session on a guard bug)."""
import sys, json, re, subprocess, os


def block(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(2)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    cmd = (data.get("tool_input") or {}).get("command", "") or ""

    # (1) block whole-tree adds and `git commit -a`, scanning each shell segment.
    # Only the COMMAND PREFIX is inspected -- truncate at the first message/heredoc/
    # subshell token so a commit MESSAGE that documents "git add -A" isn't matched
    # as a command (that false positive would block any commit mentioning the rule).
    MSG_INTRO = {"-m", "--message", "-F", "--file",
                 "-C", "--reuse-message", "-c", "--reedit-message"}
    for seg in re.split(r"&&|\|\||;|\|", cmd):
        toks = []
        for t in seg.strip().split():
            if t in MSG_INTRO or "$(" in t or "<<" in t:
                break
            toks.append(t)
        for i in range(len(toks) - 1):
            if toks[i] != "git":
                continue
            sub, args = toks[i + 1], toks[i + 2:]
            if sub == "add":
                for a in args:
                    if a in ("-A", "--all", ".") or re.fullmatch(r"-[A-Za-z]*A[A-Za-z]*", a):
                        block("BLOCKED by KYR git guard: `git add %s` stages the whole working "
                              "tree, which is full of untracked private docs and multi-MB PDFs "
                              "(deploy-hygiene rule / audit R4). Use targeted `git add <path>`." % a)
            elif sub == "commit":
                # -a / --all / bundled short cluster containing 'a' (e.g. -am, -avm).
                # `--amend` (long flag) and `-m` are NOT matched.
                for a in args:
                    if a == "--all" or (re.fullmatch(r"-[a-z]+", a) and "a" in a):
                        block("BLOCKED by KYR git guard: `git commit %s` auto-stages tracked "
                              "modifications, bypassing the targeted-add ritual (deploy-hygiene / "
                              "audit R4). Stage explicitly (`git add <path>`) then `git commit`." % a)

    # (2) deploy guard before commit
    if re.search(r"\bgit\s+(?:-\S+\s+)*commit\b", cmd):
        root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        check = os.path.join(root, "_deploy_check.py")
        if os.path.exists(check):
            try:
                r = subprocess.run([sys.executable, check], capture_output=True, text=True, cwd=root)
                if r.returncode != 0:
                    block((r.stdout or "") + (r.stderr or ""))
            except Exception:
                sys.exit(0)   # fail open
    sys.exit(0)


if __name__ == "__main__":
    main()
