#!/usr/bin/env python3
"""Render every generated distribution artifact from the facts below.

One skill is published to four plugin ecosystems and to the discovery
standard, and all five want the same handful of facts: the name, the
release the contracts are verified against, the listing blurb, the
licence and the links. They are declared once here and rendered into
the committed files, so a release bumps one constant instead of four
manifests that silently disagree.

Generated (all committed, all checked by CI):

    .claude-plugin/marketplace.json       Claude Code marketplace
    .claude-plugin/plugin.json            Claude Code plugin manifest
    .codex-plugin/plugin.json             Codex plugin manifest
    plugin.json                           agent-plugins.org manifest
    .well-known/agent-skills/index.json   discovery index, RFC draft 0.2.0
    .well-known/agent-skills/<skill>.tar.gz   the artifact the index points at

Usage:
    tools/generate_manifests.py            # write the files
    tools/generate_manifests.py --check    # exit non-zero if any is stale

Each skill's own name and description come from its SKILL.md
frontmatter, which stays the single source for those two fields.
"""

import hashlib
import io
import json
import struct
import sys
import tarfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
WELL_KNOWN = ROOT / ".well-known" / "agent-skills"

# The CLI release whose contracts the skills here are verified against.
# Every manifest carries it as the plugin version, and the repository is
# tagged v<VERSION> at that release.
VERSION = "0.3.15"

NAME = "uniac"
OWNER = "Uniac"
HOMEPAGE = "https://uniac.ai"
REPOSITORY = "https://github.com/uniac-ai/agent-skills"
LICENSE = "MIT"
KEYWORDS = ["uniac", "deployment", "cloud", "devops"]

# The listing blurb, read by a human browsing a marketplace. A skill's
# frontmatter description is a different thing — it is written to make
# an agent load the skill at the right moment — so the two do not share
# a source.
BLURB = (
    "Deploy and run applications on Uniac, the cloud deployment platform "
    "— the uniac.yaml manifest, the uniac CLI, and the platform contract."
)
MARKETPLACE_BLURB = (
    "The official agent knowledge for Uniac, a cloud deployment platform."
)

# Draft 0.2.0 of the Cloudflare agent-skills discovery RFC. The URI is an
# opaque version selector; clients match it exactly and must not fetch it.
DISCOVERY_SCHEMA = "https://schemas.agentskills.io/discovery/0.2.0/schema.json"
AGENT_PLUGINS_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
CLAUDE_PLUGIN_SCHEMA = "https://json.schemastore.org/claude-code-plugin-manifest.json"
CLAUDE_MARKETPLACE_SCHEMA = "https://json.schemastore.org/claude-code-marketplace.json"


def skill_dirs() -> list[Path]:
    return sorted(p for p in SKILLS.iterdir() if p.is_dir())


def frontmatter_description(md: Path) -> str:
    for line in md.read_text(encoding="utf-8").splitlines():
        if line.startswith("description:"):
            value = line.split(":", 1)[1].strip()
            if value.startswith(("'", '"')) and value.endswith(value[0]):
                value = value[1:-1]
            return value
    return ""


def skill_files(d: Path) -> list[str]:
    return sorted(
        str(f.relative_to(d))
        for f in d.rglob("*")
        if f.is_file() and not f.name.startswith(".")
    )


def gzip_wrap(raw: bytes) -> bytes:
    """Frame deflate output as gzip with a fixed header.

    The header is written by hand so the bytes depend only on `raw`:
    no modification time, and a constant XFL/OS pair. That keeps the
    committed archive identical on every machine, which is what lets
    --check compare it byte for byte.
    """
    compressor = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    body = compressor.compress(raw) + compressor.flush()
    header = b"\x1f\x8b\x08\x00" + b"\x00\x00\x00\x00" + b"\x02\xff"
    trailer = struct.pack("<II", zlib.crc32(raw) & 0xFFFFFFFF, len(raw) & 0xFFFFFFFF)
    return header + body + trailer


def archive_of(d: Path) -> bytes:
    """Pack one skill as a gzipped tar with SKILL.md at the root.

    Consumers look for SKILL.md at the top level of the archive, so the
    skill directory itself is not a member. Every tar field that would
    otherwise record the packing machine — mtime, ownership, mode — is
    pinned.
    """
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for rel in skill_files(d):
            data = (d / rel).read_bytes()
            info = tarfile.TarInfo(rel)
            info.size = len(data)
            info.mtime = 0
            info.mode = 0o644
            info.type = tarfile.REGTYPE
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            tar.addfile(info, io.BytesIO(data))
    return gzip_wrap(buf.getvalue())


def discovery_index(archives: dict[str, bytes]) -> dict:
    """The RFC 0.2.0 index.

    Every skill is published as `type: "archive"`. The alternative,
    `skill-md`, carries exactly one file, and these skills bundle
    references alongside SKILL.md. `url` is relative, so it resolves
    against the index's own URL on whatever origin and base path serves
    it, and `digest` covers the artifact bytes the client will fetch.
    """
    return {
        "$schema": DISCOVERY_SCHEMA,
        "skills": [
            {
                "name": d.name,
                "type": "archive",
                "description": frontmatter_description(d / "SKILL.md"),
                "url": f"{d.name}.tar.gz",
                "digest": "sha256:" + hashlib.sha256(archives[d.name]).hexdigest(),
            }
            for d in skill_dirs()
        ],
    }


def claude_plugin() -> dict:
    """Claude Code plugin manifest.

    `agents` is declared empty on purpose: Claude Code scans a plugin's
    `agents/` directory, and this repository's `agents/agents.md` is the
    bootstrap page the website serves to visiting agents, not an agent
    definition. Without the empty list it loads as one.
    """
    return {
        "$schema": CLAUDE_PLUGIN_SCHEMA,
        "name": NAME,
        "version": VERSION,
        "description": BLURB,
        "author": {"name": OWNER, "url": HOMEPAGE},
        "homepage": HOMEPAGE,
        "repository": REPOSITORY,
        "license": LICENSE,
        "keywords": KEYWORDS,
        "skills": ["./skills"],
        "agents": [],
    }


def claude_marketplace() -> dict:
    """Claude Code marketplace, served from the repository root.

    `source: "./"` makes the repository itself the one plugin, which is
    what lets `/plugin marketplace add uniac-ai/agent-skills` install it
    with no further hosting.
    """
    return {
        "$schema": CLAUDE_MARKETPLACE_SCHEMA,
        "name": NAME,
        "description": MARKETPLACE_BLURB,
        "owner": {"name": OWNER, "url": HOMEPAGE},
        "plugins": [
            {
                "name": NAME,
                "source": "./",
                "description": BLURB,
                "version": VERSION,
                "homepage": HOMEPAGE,
                "repository": REPOSITORY,
                "license": LICENSE,
                "keywords": KEYWORDS,
            }
        ],
    }


def codex_plugin() -> dict:
    """Codex plugin manifest.

    `skills` is the documented string form; Codex rejects a path that is
    exactly "./", so the directory is named. The listing block Codex
    calls `interface` is not written here: the directory portal collects
    those fields at submission time, and its `category` and
    `capabilities` values are constrained by no published schema.
    """
    return {
        "name": NAME,
        "version": VERSION,
        "description": BLURB,
        "author": {"name": OWNER, "url": HOMEPAGE},
        "skills": "./skills/",
        "homepage": HOMEPAGE,
        "repository": REPOSITORY,
        "license": LICENSE,
        "keywords": KEYWORDS,
    }


def agent_plugins_manifest() -> dict:
    """agent-plugins.org manifest, the format Cursor imports.

    The schema is closed — only the fields below are permitted — and it
    has no component fields at all: skills are discovered from `skills/`
    and cannot be declared.
    """
    return {
        "$schema": AGENT_PLUGINS_SCHEMA,
        "name": NAME,
        "version": VERSION,
        "description": BLURB,
        "author": {"name": OWNER, "url": HOMEPAGE},
        "homepage": HOMEPAGE,
        "repository": REPOSITORY,
        "license": LICENSE,
        "keywords": KEYWORDS,
    }


def as_json(obj: dict) -> bytes:
    return (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def artifacts() -> dict[Path, bytes]:
    archives = {d.name: archive_of(d) for d in skill_dirs()}
    files: dict[Path, bytes] = {
        WELL_KNOWN / f"{name}.tar.gz": data for name, data in archives.items()
    }
    files[WELL_KNOWN / "index.json"] = as_json(discovery_index(archives))
    files[ROOT / ".claude-plugin" / "plugin.json"] = as_json(claude_plugin())
    files[ROOT / ".claude-plugin" / "marketplace.json"] = as_json(claude_marketplace())
    files[ROOT / ".codex-plugin" / "plugin.json"] = as_json(codex_plugin())
    files[ROOT / "plugin.json"] = as_json(agent_plugins_manifest())
    return files


def main() -> int:
    files = artifacts()
    if "--check" in sys.argv:
        stale = [
            path
            for path, data in sorted(files.items())
            if not path.exists() or path.read_bytes() != data
        ]
        for path in stale:
            print(f"FAIL {path.relative_to(ROOT)} is stale — run tools/generate_manifests.py")
        if stale:
            return 1
        print(f"ok: {len(files)} generated file(s) current")
        return 0
    for path, data in sorted(files.items()):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(f"wrote {len(files)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
