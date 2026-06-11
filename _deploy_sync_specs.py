"""
Split-blob deploy sync: root wrench_demo.html  ->  wrench_deploy/index.html (+ data.<hash>.js)
Preserves the deploy-only <head> patch (cache metas + SW self-heal), bumps kyr-version,
extracts the inline __D__ dataset into a content-hashed data.<hash>.js, deletes the old one.
(Reproduces the proven inline sync from commit ce9204a5.)
"""
import os, re, glob, hashlib, datetime, shutil

ROOT = r"C:\Users\Robert\OneDrive\Desktop\Wrench App Data"
DEP = os.path.join(ROOT, "wrench_deploy")
IDX = os.path.join(DEP, "index.html")
DEMO = os.path.join(ROOT, "wrench_demo.html")
ANCHOR = '<link rel="preconnect" href="https://fonts.googleapis.com">'
NEW_VER = os.environ.get("KYR_NEW_VER", "2026-06-10-refactor-v32")

idx = open(IDX, "rb").read().decode("utf-8")
demo = open(DEMO, "rb").read().decode("utf-8")

# backup index.html
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(IDX, IDX + "." + ts + ".bak")
print("Backed up index.html ->", os.path.basename(IDX) + "." + ts + ".bak")
# keep only the 5 most recent index.html backups (prune older ones)
for _old in sorted(glob.glob(IDX + ".*.bak"))[:-5]:
    os.remove(_old)

ia = idx.find(ANCHOR)
da = demo.find(ANCHOR)
assert ia > 0 and da > 0 and idx.count(ANCHOR) == 1 and demo.count(ANCHOR) == 1, "anchor problem"

# 1) head patch (deploy) + new body (demo)
new_index = idx[:ia] + demo[da:]

# 2) bump kyr-version inside the head patch
new_index, n = re.subn(r'(<meta name="kyr-version" content=")[^"]*(">)',
                        lambda m: m.group(1) + NEW_VER + m.group(2), new_index, count=1)
assert n == 1, "kyr-version meta not found/replaced"
print("kyr-version ->", NEW_VER)

# 3) split: extract inline const __D__=...; block into data.<hash>.js
ds = new_index.find("const __D__=")
sopen = new_index.rfind("<script", 0, ds)
send = new_index.find("</script>", ds)
assert ds > 0 and sopen >= 0 and send > ds, "data script boundaries not found"

json_tail = new_index[ds + len("const __D__="):send]   # "<json>;\r\n"
json_str = json_tail.strip()
if json_str.endswith(";"):
    json_str = json_str[:-1]
data_content = "var __D__=" + json_str + ";"

h = hashlib.md5(data_content.encode("utf-8")).hexdigest()[:8]
data_name = "data.%s.js" % h
ext_tag = '<script src="/%s"></script>' % data_name
new_index = new_index[:sopen] + ext_tag + new_index[send + len("</script>"):]

with open(os.path.join(DEP, data_name), "wb") as f:
    f.write(data_content.encode("utf-8"))
print("Wrote %s  (%.2f MB)" % (data_name, len(data_content) / 1024 / 1024))

# 4) delete prior data.*.js (anything but the new one)
for p in glob.glob(os.path.join(DEP, "data.*.js")):
    if os.path.basename(p) != data_name:
        os.remove(p)
        print("Deleted old", os.path.basename(p))

with open(IDX, "wb") as f:
    f.write(new_index.encode("utf-8"))

print("\nindex.html -> %.1f KB" % (len(new_index.encode("utf-8")) / 1024))
print("references:", ext_tag)
print("inline __D__ remaining in index:", "const __D__=" in new_index)
print("Trim Variants render in index:", "Trim Variants" in new_index)
print("tnote in data file:", '"tnote":"Varies by trim' in data_content)
