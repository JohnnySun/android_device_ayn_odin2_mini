#!/usr/bin/env python3

import argparse
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import xml.etree.ElementTree as ET


def project_path(project):
    value = project.get("path") or project.get("name")
    if not value:
        raise ValueError("project is missing both path and name")

    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"unsafe project path: {value}")
    return value, path


def pinned_head(path):
    env = os.environ.copy()
    env["GIT_NO_LAZY_FETCH"] = "1"
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--verify", "HEAD^{commit}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        detail = result.stderr.strip().splitlines()
        message = detail[-1] if detail else "git rev-parse failed"
        raise RuntimeError(message)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Pin materialized repo projects and omit absent projects.",
    )
    parser.add_argument("--source-root", default=".")
    args = parser.parse_args()

    source_root = Path(args.source_root).resolve()
    tree = ET.parse(sys.stdin)
    root = tree.getroot()
    parents = {child: parent for parent in root.iter() for child in parent}
    projects = list(root.iter("project"))
    seen = set()
    included = 0
    omitted = 0
    invalid = []

    for project in projects:
        try:
            value, relative = project_path(project)
        except ValueError as error:
            invalid.append(str(error))
            continue

        if value in seen:
            invalid.append(f"duplicate project path: {value}")
            continue
        seen.add(value)

        checkout = source_root.joinpath(*relative.parts)
        if not checkout.exists():
            parents[project].remove(project)
            omitted += 1
            continue

        if not checkout.is_dir():
            invalid.append(f"materialized project is not a directory: {value}")
            continue

        try:
            project.set("revision", pinned_head(checkout))
        except RuntimeError as error:
            invalid.append(f"materialized project cannot be pinned: {value}: {error}")
            continue
        included += 1

    if invalid:
        for message in invalid:
            print(f"checked-out manifest error: {message}", file=sys.stderr)
        return 1
    if included == 0:
        print("checked-out manifest error: no materialized projects were pinned", file=sys.stderr)
        return 1

    ET.indent(tree, space="  ")
    tree.write(sys.stdout, encoding="unicode", xml_declaration=True)
    sys.stdout.write("\n")
    print(
        f"checked-out pinned manifest: included={included} omitted_absent={omitted}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
