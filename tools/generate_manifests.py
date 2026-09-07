#!/usr/bin/env python3
"""Render committed plugin manifests from shared metadata.

Generated (all committed, all checked by CI):

    .claude-plugin/marketplace.json       Claude Code marketplace
    .claude-plugin/plugin.json            Claude Code plugin manifest
    .codex-plugin/plugin.json             Codex plugin manifest
    plugin.json                           agent-plugins.org manifest

Usage:
    tools/generate_manifests.py            # write the files
    tools/generate_manifests.py --check    # exit non-zero if any is stale

"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The CLI release whose contracts the skills here are verified against.
# Every manifest carries it as the plugin version, and the repository is
# tagged v<VERSION> at that release.
VERSION = "0.3.18"

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
    "Define, deploy, and operate applications on Uniac "
    "with connected services, storage, and public endpoints."
)
MARKETPLACE_BLURB = (
    "The official agent knowledge for Uniac, a cloud deployment platform."
)

AGENT_PLUGINS_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
CLAUDE_PLUGIN_SCHEMA = "https://json.schemastore.org/claude-code-plugin-manifest.json"
CLAUDE_MARKETPLACE_SCHEMA = "https://json.schemastore.org/claude-code-marketplace.json"


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
    return {
        ROOT / ".claude-plugin" / "plugin.json": as_json(claude_plugin()),
        ROOT / ".claude-plugin" / "marketplace.json": as_json(claude_marketplace()),
        ROOT / ".codex-plugin" / "plugin.json": as_json(codex_plugin()),
        ROOT / "plugin.json": as_json(agent_plugins_manifest()),
    }


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
