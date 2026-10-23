"""Check the committed submission against the template's initial commit."""
import subprocess
import sys

ALLOWED = {f"src/main/q{n}.sh" for n in range(1, 9)} | {"src/main/bonus.sh"}


def git(*args):
    return subprocess.check_output(["git", *args])


roots = git("rev-list", "--max-parents=0", "HEAD").decode().splitlines()
if len(roots) != 1:
    sys.exit("需要单一模板初始提交；不要合并无关仓库历史。")
base = roots[0]
changed = git("diff", "--name-only", "-z", base, "HEAD").split(b"\0")
bad = []
for raw in changed:
    if not raw:
        continue
    path = raw.decode()
    if path not in ALLOWED and not path.startswith(".agent-sessions/"):
        bad.append(path)
for path in sorted(ALLOWED):
    entry = git("ls-tree", "HEAD", "--", path).decode().strip()
    if not entry or entry.split()[0] not in {"100644", "100755"}:
        bad.append(path + "（缺失或不是普通文件）")
if bad:
    sys.exit("只允许修改 src/main/q1.sh–q8.sh、bonus.sh 和 AI 会话归档：\n" + "\n".join(bad))
print(f"基础设施完整性检查通过；基准 {base}")
