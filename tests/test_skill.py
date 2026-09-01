#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "SKILL.md").read_text(encoding="utf-8")

assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
frontmatter = text.split("---\n", 2)[1]
keys = {
    match.group(1)
    for line in frontmatter.splitlines()
    if (match := re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*):", line))
}
assert keys == {"name", "description"}, f"unexpected frontmatter keys: {sorted(keys)}"
assert re.search(r"^name:\s*ship\s*$", frontmatter, re.MULTILINE)
assert len(text.splitlines()) < 500, "SKILL.md should remain progressively disclosed"

required = [
    "Detect an Eve project without installing anything",
    "Create `evals/evals.config.ts`",
    "t.requireInputRequest",
    "Never let an eval call the production side-effecting backend",
    "Make the review merge-ready",
    "safe to close this chat",
]
for token in required:
    assert token in text, f"missing contract: {token}"

for forbidden in [
    "disable-model-invocation",
    "../babysit/SKILL.md",
    "npx eve eval --help` succeeds",
]:
    assert forbidden not in text, f"non-portable or unsafe contract present: {forbidden}"

print("ship skill validation: PASS")
