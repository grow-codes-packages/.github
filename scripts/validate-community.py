"""Check the organization profile and inherited GitHub community files."""

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_DOCS = (
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
)
REPO_LINK = re.compile(
    r"\[[^\]]+\]\(https://github\.com/grow-codes-packages/([a-z0-9-]+)\)"
)


def validate_profile(profile):
    section = re.search(r"^## SDKs\s*\n(.*?)(?=^## |\Z)", profile, re.M | re.S)
    if not section:
        raise ValueError("profile/README.md: expected an SDKs section")

    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in section.group(1).splitlines()
        if line.strip().startswith("|")
    ]
    if len(rows) < 3 or rows[0] != ["Service", "Category", "Status"]:
        raise ValueError("profile/README.md: expected a populated SDK catalog table")
    if len(rows[1]) != 3 or any(not re.fullmatch(r":?-{3,}:?", cell) for cell in rows[1]):
        raise ValueError("profile/README.md: invalid SDK catalog table separator")

    repositories = set()
    for row in rows[2:]:
        if len(row) != 3 or not all(row):
            raise ValueError(f"profile/README.md: incomplete SDK row {row!r}")

        link = REPO_LINK.fullmatch(row[0])
        if not link:
            raise ValueError(f"profile/README.md: invalid SDK repository link {row[0]!r}")
        repository = link.group(1)
        if repository in repositories:
            raise ValueError(f"profile/README.md: duplicate SDK repository {repository!r}")
        repositories.add(repository)


def validate_templates(directory):
    config = directory / "config.yml"
    settings = yaml.safe_load(config.read_text(encoding="utf-8"))
    if not isinstance(settings, dict):
        raise ValueError(f"{config}: expected an issue template configuration mapping")

    templates = sorted(directory.glob("*.md"))
    if not templates:
        raise ValueError(f"{directory}: expected at least one issue template")
    for template in templates:
        markdown = template.read_text(encoding="utf-8")
        front_matter = re.match(r"^---\n(.*?)\n---\n", markdown, re.S)
        if not front_matter:
            raise ValueError(f"{template}: expected YAML front matter")
        fields = yaml.safe_load(front_matter.group(1))
        if not isinstance(fields, dict) or any(
            not isinstance(fields.get(key), str) or not fields[key].strip()
            for key in ("name", "about")
        ):
            raise ValueError(f"{template}: expected nonempty name and about fields")


def main():
    for filename in REQUIRED_DOCS:
        if not (ROOT / filename).read_text(encoding="utf-8").strip():
            raise ValueError(f"{filename}: expected a nonempty document")
    validate_profile((ROOT / "profile/README.md").read_text(encoding="utf-8"))
    validate_templates(ROOT / ".github/ISSUE_TEMPLATE")
    print("Organization profile and community files passed validation.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, yaml.YAMLError) as error:
        sys.exit(str(error))
