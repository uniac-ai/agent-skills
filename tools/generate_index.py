#!/usr/bin/env python3
"""Emit the .well-known agent-skills discovery index.

The index is what lets `npx skills add uniac.ai` resolve the domain
itself as a skills source, and what a verifying installer checks
installed files against: one entry per skill with its description, its
file list, and a sha256 digest per file.

Shape (the Stripe/Cloudflare-RFC layout):

    {"skills": [{"name": ..., "description": ...,
                 "files": ["SKILL.md", "references/..."],
                 "digests": {"SKILL.md": "sha256:..."}}]}

Usage:
    tools/generate_index.py            # write .well-known/agent-skills/index.json
    tools/generate_index.py --check    # exit non-zero if the committed index is stale

The UniacWeb build vendors this repository at the tag matching the
released CLI and serves the index plus the skill files same-origin at
uniac.ai/.well-known/agent-skills/ (with a legacy alias at
.well-known/skills/).
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
OUT = ROOT / ".well-known" / "agent-skills" / "index.json"


def description_of(md: Path) -> str:
    for line in md.read_text(encoding="utf-8").splitlines():
        if line.startswith("description:"):
            value = line.split(":", 1)[1].strip()
            if value.startswith(("'", '"')) and value.endswith(value[0]):
                value = value[1:-1]
            return value
    return ""


def build_index() -> dict:
    skills = []
    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        files = sorted(
            str(f.relative_to(d))
            for f in d.rglob("*")
            if f.is_file() and not f.name.startswith(".")
        )
        digests = {
            f: "sha256:" + hashlib.sha256((d / f).read_bytes()).hexdigest()
            for f in files
        }
        skills.append(
            {
                "name": d.name,
                "description": description_of(d / "SKILL.md"),
                "files": files,
                "digests": digests,
            }
        )
    return {"skills": skills}


def main() -> int:
    rendered = json.dumps(build_index(), indent=2, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != rendered:
            print(f"FAIL {OUT.relative_to(ROOT)} is stale — run tools/generate_index.py")
            return 1
        print("ok: index is current")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
