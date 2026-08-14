#!/usr/bin/env python3
"""
Build a clean copy of the mod for release, plus the VDF that SteamCMD needs.

    python tools/build.py --changenote "..."

Produces build/NanameFloorsExpanded (the mod folder) and build/workshop.vdf 
(listing data) next to it.

Upload with:

    steamcmd +login <user> +workshop_build_item <abs path>/build/workshop.vdf +quit

"""

import argparse
import pathlib
import shutil
import sys
import xml.etree.ElementTree as ET

APP_ID = "294100"
FOLDER_NAME = "NanameFloorsExpanded"
SHIP = ["About", "Languages", "Textures", "LICENSE"]

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
CONTENT = BUILD / FOLDER_NAME
DESCRIPTION = ROOT / "workshop" / "description.bbcode"


def vdf_safe(value: str) -> str:
    """Valve's KeyValues parser reads these files with escape sequences off.

    A straight quote therefore ends the string early and corrupts the parse,
    and a backslash cannot be escaped either without showing up doubled on the
    page. Straight quotes become typographic ones, which parse cleanly and read
    better on Steam anyway.
    """
    out = []
    opening = True
    for char in value:
        if char == '"':
            out.append("“" if opening else "”")
            opening = not opening
        else:
            out.append(char)
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--changenote", default="", help="release notes for this upload")
    ap.add_argument("--visibility", default=None, choices=["0", "1", "2"],
                    help="0 public, 1 friends, 2 private. Defaults to 2 for a new item, 0 once published")
    args = ap.parse_args()

    missing = [name for name in SHIP if not (ROOT / name).exists()]
    if missing:
        print(f"missing from the repo: {', '.join(missing)}", file=sys.stderr)
        return 1

    if BUILD.exists():
        shutil.rmtree(BUILD)
    CONTENT.mkdir(parents=True)

    for name in SHIP:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, CONTENT / name, ignore=shutil.ignore_patterns(".DS_Store", "._*"))
        else:
            shutil.copy2(src, CONTENT / name)
        print(f"staged {name}")

    published_id = "0"
    id_file = ROOT / "About" / "PublishedFileId.txt"
    if id_file.exists():
        published_id = id_file.read_text().strip()

    visibility = args.visibility or ("2" if published_id == "0" else "0")

    title = ET.parse(ROOT / "About" / "About.xml").getroot().findtext("name", "").strip()
    if DESCRIPTION.exists():
        description = DESCRIPTION.read_text().strip()
    else:
        print(f"no {DESCRIPTION.relative_to(ROOT)}, falling back to the About.xml description")
        raw = ET.parse(ROOT / "About" / "About.xml").getroot().findtext("description", "").strip()
        # About.xml is indented for readability; Steam would show that indentation
        description = "\n".join(line.strip() for line in raw.splitlines())

    vdf = "\n".join([
        '"workshopitem"',
        "{",
        f'\t"appid" "{APP_ID}"',
        f'\t"publishedfileid" "{published_id}"',
        f'\t"contentfolder" "{vdf_safe(str(CONTENT))}"',
        f'\t"previewfile" "{vdf_safe(str(CONTENT / "About" / "Preview.png"))}"',
        f'\t"visibility" "{visibility}"',
        f'\t"title" "{vdf_safe(title)}"',
        f'\t"description" "{vdf_safe(description)}"',
        f'\t"changenote" "{vdf_safe(args.changenote)}"',
        "}",
        "",
    ])
    (BUILD / "workshop.vdf").write_text(vdf)

    files = sum(1 for p in CONTENT.rglob("*") if p.is_file())
    size = sum(p.stat().st_size for p in CONTENT.rglob("*") if p.is_file())
    action = "create a new item" if published_id == "0" else f"update item {published_id}"
    print(f"\n{files} files, {size // 1024} KB in {CONTENT.relative_to(ROOT)}")
    print(f"vdf will {action}, visibility {visibility}")
    print(f"\nsteamcmd +login <user> +workshop_build_item {BUILD / 'workshop.vdf'} +quit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
