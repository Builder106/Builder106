#!/usr/bin/env python3
"""Generate repository-local Dependabot policy files from the fleet policy."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PAIR_LINE = re.compile(r"^\s*-\s+package-ecosystem:\s*(.*)$")
DIRECTORY_LINE = re.compile(r"^\s+directory:\s*(.*)$")
WORKFLOW_PATH = Path(".github/workflows/dependabot-auto-merge.yml")
DEPENDABOT_PATH = Path(".github/dependabot.yml")


def clean(value: str) -> str:
    return value.strip().strip(chr(34) + chr(39))


def load_policy(path: Path) -> dict:
    with path.open(encoding="utf-8") as policy_file:
        policy = json.load(policy_file)
    if policy.get("schema") != 1:
        raise ValueError("unsupported policy schema")
    update_types = policy["defaults"]["auto-merge"]["update-types"]
    if set(update_types) != {
        "version-update:semver-patch",
        "version-update:semver-minor",
    }:
        raise ValueError("auto-merge policy must allow only patch and minor updates")
    return policy


def entry_pairs(text: str) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    current_ecosystem: str | None = None
    for line in text.splitlines():
        ecosystem_match = PAIR_LINE.match(line)
        if ecosystem_match:
            current_ecosystem = clean(ecosystem_match.group(1))
            continue
        if current_ecosystem is not None:
            directory_match = DIRECTORY_LINE.match(line)
            if directory_match:
                pairs.add((current_ecosystem, clean(directory_match.group(1))))
                current_ecosystem = None
    return pairs


def migrate_entries(text: str, replacements: list[dict]) -> str:
    replacement_map = {
        (
            item["from"]["package-ecosystem"],
            item["from"]["directory"],
        ): (
            item["to"]["package-ecosystem"],
            item["to"]["directory"],
        )
        for item in replacements
    }
    if not replacement_map:
        return text

    lines = text.splitlines(keepends=True)
    pairs = entry_pairs(text)
    current_ecosystem: str | None = None
    current_line: int | None = None

    for index, line in enumerate(lines):
        ecosystem_match = PAIR_LINE.match(line)
        if ecosystem_match:
            current_ecosystem = clean(ecosystem_match.group(1))
            current_line = index
            continue
        if current_ecosystem is None:
            continue
        directory_match = DIRECTORY_LINE.match(line)
        if directory_match is None:
            continue
        old_pair = (current_ecosystem, clean(directory_match.group(1)))
        new_pair = replacement_map.get(old_pair)
        if new_pair is not None:
            if new_pair in pairs:
                raise ValueError(
                    f"replacement target already exists: {new_pair[0]} {new_pair[1]}"
                )
            assert current_line is not None
            indent = lines[current_line][
                : len(lines[current_line]) - len(lines[current_line].lstrip())
            ]
            newline = "\n" if lines[current_line].endswith("\n") else ""
            lines[current_line] = (
                f'{indent}- package-ecosystem: "{new_pair[0]}"{newline}'
            )
            pairs.remove(old_pair)
            pairs.add(new_pair)
        current_ecosystem = None
        current_line = None

    return "".join(lines)


def render_entry(entry: dict, policy: dict, *, actions: bool = False) -> str:
    schedule = policy["defaults"]["schedule"]
    lines = [
        f'  - package-ecosystem: "{entry["package-ecosystem"]}"',
        f'    directory: "{entry["directory"]}"',
        "    schedule:",
        f'      interval: "{schedule["interval"]}"',
    ]
    if actions:
        group = policy["defaults"]["github-actions"]["group"]
        lines.extend(
            [
                "    groups:",
                f"      {group['name']}:",
                "        patterns:",
            ]
        )
        lines.extend(f'          - "{pattern}"' for pattern in group["patterns"])
    return "\n".join(lines)


def github_expression(name: str) -> str:
    return "$" + "{{ " + name + " }}"


def render_workflow(policy: dict) -> str:
    update_types = policy["defaults"]["auto-merge"]["update-types"]
    conditions = " ||\n".join(
        f"          steps.metadata.outputs.update-type == '{update_type}'"
        for update_type in update_types
    )
    sha = policy["defaults"]["auto-merge"]["fetch-metadata-sha"]
    token = github_expression("secrets.GITHUB_TOKEN")
    url = github_expression("github.event.pull_request.html_url")
    return f"""name: Dependabot Auto-Merge

on:
  pull_request_target:

permissions: {{}}

jobs:
  dependabot:
    if: github.actor == 'dependabot[bot]'
    permissions:
      contents: write
      pull-requests: write
    runs-on: ubuntu-latest
    steps:
      - name: Dependabot metadata
        id: metadata
        uses: dependabot/fetch-metadata@{sha}
        with:
          github-token: "{token}"

      - name: Enable auto-merge for patch and minor updates
        if: |
{conditions}
        run: gh pr merge --auto --squash "$PR_URL"
        env:
          PR_URL: {url}
          GH_TOKEN: {token}
"""


def additions_for(repo_name: str, repo_dir: Path, policy: dict) -> list[dict]:
    repo_policy = policy.get("repositories", {}).get(repo_name, {})
    additions = list(repo_policy.get("add", []))
    if (
        policy["defaults"].get("github-actions")
        and (repo_dir / ".github/workflows").is_dir()
    ):
        additions.append({"package-ecosystem": "github-actions", "directory": "/"})
    return additions


def render_dependabot(
    existing: str | None,
    repo_name: str,
    repo_dir: Path,
    policy: dict,
) -> str:
    repo_policy = policy.get("repositories", {}).get(repo_name, {})
    migrated = migrate_entries(existing or "", repo_policy.get("replace", []))
    pairs = entry_pairs(migrated)
    additions = additions_for(repo_name, repo_dir, policy)
    missing = [
        entry
        for entry in additions
        if (entry["package-ecosystem"], entry["directory"]) not in pairs
    ]
    if existing is None:
        rendered = ["version: 2", "updates:"]
        rendered.extend(
            render_entry(
                entry,
                policy,
                actions=entry["package-ecosystem"] == "github-actions",
            )
            for entry in missing
        )
        return "\n".join(rendered) + "\n"
    if not missing:
        return migrated
    base = migrated.rstrip() + "\n\n"
    return (
        base
        + "\n\n".join(
            render_entry(
                entry,
                policy,
                actions=entry["package-ecosystem"] == "github-actions",
            )
            for entry in missing
        )
        + "\n"
    )


def write_or_check(path: Path, expected: str, check: bool) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == expected:
        return False
    if check:
        print(f"would change {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="utf-8")
        print(f"wrote {path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    policy_path = args.policy.resolve()
    policy = load_policy(policy_path)
    repository_policies = policy.get("repositories", {})
    known_names = {
        path.name
        for path in workspace.iterdir()
        if path.is_dir() and (path / ".git").exists()
    }
    unknown = sorted(set(repository_policies) - known_names)
    if unknown:
        raise ValueError(
            f"policy repositories missing from workspace: {', '.join(unknown)}"
        )

    changed = 0
    applicable = 0
    for repo_dir in sorted(workspace.iterdir(), key=lambda path: path.name.lower()):
        if not repo_dir.is_dir() or not (repo_dir / ".git").exists():
            continue
        additions = additions_for(repo_dir.name, repo_dir, policy)
        dependabot_path = repo_dir / DEPENDABOT_PATH
        workflow_path = repo_dir / WORKFLOW_PATH
        existing = (
            dependabot_path.read_text(encoding="utf-8")
            if dependabot_path.exists()
            else None
        )
        if existing is None and not additions:
            continue
        applicable += 1
        expected = render_dependabot(existing, repo_dir.name, repo_dir, policy)
        if write_or_check(dependabot_path, expected, args.check):
            changed += 1
        if write_or_check(
            workflow_path,
            render_workflow(policy),
            args.check,
        ):
            changed += 1

    print(f"applicable repositories: {applicable}")
    print(f"files {'that would change' if args.check else 'changed'}: {changed}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
