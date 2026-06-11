"""
Split-blob deploy sync: root wrench_demo.html  ->  wrench_deploy/index.html (+ data.<hash>.js)
Preserves the deploy-only <head> patch (cache metas + SW self-heal), bumps kyr-version,
extracts the inline __D__ dataset into a content-hashed data.<hash>.js, deletes the old one.
(Reproduces the proven inline sync from commit ce9204a5.)

Hardened: all parsing/validation happens IN MEMORY first; disk is only mutated once every
check passes; index.html is written atomically via os.replace so a crash can never leave a
truncated/half-built file; KYR_NEW_VER is required and must differ from the live version.
"""
import os, re, glob, hashlib, datetime, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))   # portable: the dir this script lives in
DEP = os.path.join(ROOT, "wrench_deploy")
IDX = os.path.join(DEP, "index.html")
DEMO = os.path.join(ROOT, "wrench_demo.html")
ANCHOR = '<link rel="preconnect" href="https://fonts.googleapis.com">'

NEW_VER = os.environ.get("KYR_NEW_VER", "").strip()
if not NEW_VER:
    raise SystemExit(
        "ERROR: KYR_NEW_VER is required. Set it before deploying, e.g.\n"
        "  PowerShell:  $env:KYR_NEW_VER='2026-06-10-myfeature'; python _deploy_sync_specs.py\n"
        "Refusing to ship a stale/default version string.")

idx = open(IDX, "rb").read().decode("utf-8")
demo = open(DEMO, "rb").read().decode("utf-8")

# Guard: the new version must actually differ from the one already live in index.html,
# otherwise the SW self-heal / cache-bust keyed on kyr-version won't pick up the build.
cur = re.search(r'<meta name="kyr-version" content="([^"]*)"', idx)
if cur and cur.group(1) == NEW_VER:
    raise SystemExit("ERROR: KYR_NEW_VER (%s) matches the version already in index.html. Bump it." % NEW_VER)

ia = idx.find(ANCHOR)
da = demo.find(ANCHOR)
assert ia > 0 and da > 0 and idx.count(ANCHOR) == 1 and demo.count(ANCHOR) == 1, "anchor problem"

# 1) head patch (deploy) + new body (demo)
new_index = idx[:ia] + demo[da:]

# 2) bump kyr-version inside the head patch
new_index, n = re.subn(r'(<meta name="kyr-version" content=")[^"]*(">)',
                       lambda m: m.group(1) + NEW_VER + m.group(2), new_index, count=1)
assert n == 1, "kyr-version meta not found/replaced"

# 3) split: extract inline const __D__=...; block into data.<hash>.js
ds = new_index.find("const __D__=")
sopen = new_index.rfind("<script", 0, ds)
send = new_index.find("</script>", ds)
assert ds > 0 and sopen >= 0 and send > ds, \
    "data script boundaries not found (root wrench_demo.html is missing its inline 'const __D__=' block?)"

json_tail = new_index[ds + len("const __D__="):send]   # "<json>;\r\n"
json_str = json_tail.strip()
if json_str.endswith(";"):
    json_str = json_str[:-1]
data_content = "var __D__=" + json_str + ";"

h = hashlib.md5(data_content.encode("utf-8")).hexdigest()[:8]
data_name = "data.%s.js" % h
ext_tag = '<script src="/%s"></script>' % data_name
new_index = new_index[:sopen] + ext_tag + new_index[send + len("</script>"):]

# Sanity: the rebuilt index must reference the new data file and no longer inline the blob.
assert "const __D__=" not in new_index, "inline __D__ still present after split"
assert ext_tag in new_index, "new data.<hash>.js reference missing after split"

# ---------- all validation passed; only now do we touch disk ----------

# backup index.html (keep the 5 most recent)
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(IDX, IDX + "." + ts + ".bak")
print("Backed up index.html ->", os.path.basename(IDX) + "." + ts + ".bak")
for _old in sorted(glob.glob(IDX + ".*.bak"))[:-5]:
    os.remove(_old)

# write the new data blob
data_bytes = data_content.encode("utf-8")
with open(os.path.join(DEP, data_name), "wb") as f:
    f.write(data_bytes)
print("Wrote %s  (%.2f MB)" % (data_name, len(data_bytes) / 1024 / 1024))

# write index.html ATOMICALLY (temp + os.replace; replace is atomic on the same volume)
tmp = IDX + ".tmp"
with open(tmp, "wb") as f:
    f.write(new_index.encode("utf-8"))
os.replace(tmp, IDX)

# prune prior data.*.js only AFTER index.html points at the new one
for p in glob.glob(os.path.join(DEP, "data.*.js")):
    if os.path.basename(p) != data_name:
        os.remove(p)
        print("Deleted old", os.path.basename(p))

print("kyr-version ->", NEW_VER)
print("index.html -> %.1f KB" % (len(new_index.encode("utf-8")) / 1024))
print("references:", ext_tag)
print("inline __D__ remaining in index:", "const __D__=" in new_index)
print("Trim Variants render in index:", "Trim Variants" in new_index)
print("tnote in data file:", '"tnote":"Varies by trim' in data_content)
