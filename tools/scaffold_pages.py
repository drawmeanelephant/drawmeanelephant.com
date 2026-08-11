#!/usr/bin/env python3
"""Create auditable page scaffolds from a CSV export of the Addresses tab.

The workbook itself stays outside this repository. Export the first tab as CSV,
then run this script with that CSV as --input. Existing page IDs are never
overwritten; exact duplicate locations are merged into one scaffold.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
DEFAULT_LEDGER = ROOT / "data" / "elephant-ledger.csv"
DEFAULT_MANIFEST = ROOT / "data" / "page-scaffolding-manifest.csv"
DEFAULT_INDEX = CONTENT / "written-places.md"

BREWERY_TYPES = {
    "brewpub",
    "contract",
    "large",
    "largge",
    "micro",
    "microbrewery",
    "planning",
    "proprietor",
    "regional",
    "taproom",
}

OTHER_TYPES = {
    "artist",
    "bar",
    "distillery",
    "ecig",
    "other",
    "pens",
    "raoc",
    "vaporents",
}

# These are known historical title variants whose correspondence pages already
# exist but were not linked by the public ledger's exact-name matcher.
LEGACY_ALIASES = {
    "bell s general store": "breweries/bells-general-store",
    "hammer springs distillers": "breweries/hammer-spring-distillers",
    "magic hat brewing co north american breweries": "breweries/magic-hat-brewing",
    "outer light brewing company": "breweries/outer-light-brewery",
    "vikre distilling": "breweries/vikre-distillery",
}

# Keep the old public route available as a small legacy page while the
# canonical directory entry lives in the correct taxonomy.
LEGACY_REDIRECTS = {
    "breweries/cricket-press": "other-places/cricket-press",
}


@dataclass
class Candidate:
    name: str
    address: str = ""
    address2: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = ""
    place_type: str = ""
    written: list[str] = field(default_factory=list)
    drew: list[str] = field(default_factory=list)
    oob: list[str] = field(default_factory=list)
    website: str = ""
    instagram: str = ""
    twitter: str = ""
    facebook: str = ""
    source_rows: list[str] = field(default_factory=list)
    page_id: str = ""


def clean(value: object) -> str:
    return str(value or "").strip()


def key(value: object) -> str:
    text = unicodedata.normalize("NFKD", clean(value)).encode("ascii", "ignore").decode()
    text = text.casefold().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def slug(value: object) -> str:
    text = unicodedata.normalize("NFKD", clean(value)).encode("ascii", "ignore").decode()
    text = text.casefold().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "place"


def frontmatter_value(text: str, field_name: str) -> str:
    match = re.search(rf"^{re.escape(field_name)}:\s*(.+)$", text, flags=re.MULTILINE)
    if not match:
        return ""
    value = match.group(1).strip()
    if value.startswith('"') and value.endswith('"'):
        try:
            return str(json.loads(value))
        except json.JSONDecodeError:
            return value[1:-1]
    return value


def frontmatter_tags(text: str) -> list[str]:
    raw = frontmatter_value(text, "tags")
    return [key(part) for part in re.findall(r'"([^"]+)"|([^,\[\]]+)', raw) for part in [part[0] or part[1]]]


def parse_existing_pages() -> tuple[dict[str, str], set[str], list[dict[str, str]]]:
    existing_titles: dict[str, str] = {}
    existing_ids: set[str] = set()
    entries: list[dict[str, str]] = []

    for path in sorted(CONTENT.glob("breweries/*.md")) + sorted(CONTENT.glob("other-places/*.md")):
        text = path.read_text(encoding="utf-8")
        page_id = frontmatter_value(text, "id")
        title = frontmatter_value(text, "title")
        if not page_id or not title:
            continue
        existing_ids.add(page_id)
        existing_titles[key(title)] = page_id
        location_match = re.search(r"^> \* \*\*Location:\*\*\s*(.+)$", text, flags=re.MULTILINE)
        location = clean(location_match.group(1) if location_match else "")
        type_match = re.search(r"^> \* \*\*Type:\*\*\s*(.+)$", text, flags=re.MULTILINE)
        place_type = clean(type_match.group(1) if type_match else "")
        tags = frontmatter_tags(text)
        state = next((tag.upper() for tag in tags if len(tag) in {2, 3} and tag not in {"US", "UK"}), "")
        section = page_id.split("/", 1)[0] if "/" in page_id else "other-places"
        entries.append(
            {
                "page_id": page_id,
                "title": title,
                "location": location,
                "state": state,
                "section": section,
                "type": place_type,
                "scaffold": "scaffold" in tags,
            }
        )

    return existing_titles, existing_ids, entries


def read_exact_matches(path: Path) -> tuple[set[str], dict[str, list[str]]]:
    exact_source_rows: set[str] = set()
    candidate_names: dict[str, list[str]] = defaultdict(list)
    if not path.exists():
        return exact_source_rows, candidate_names

    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            source_row = clean(row.get("source_row"))
            if row.get("existing_site_match") == "exact" and clean(row.get("existing_site_path")):
                exact_source_rows.add(source_row)
            for name in clean(row.get("candidate_site_names")).split("|"):
                if name.strip():
                    candidate_names[source_row].append(name.strip())
    return exact_source_rows, candidate_names


def read_candidates(path: Path) -> list[Candidate]:
    grouped: dict[tuple[str, ...], Candidate] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = {clean(name).casefold(): name for name in reader.fieldnames or [] if clean(name)}
        if "name" not in headers or "written" not in headers:
            raise ValueError("input must be a CSV export of the Addresses tab with name and written columns")

        def value(row: dict[str, str], name: str) -> str:
            return clean(row.get(headers.get(name, ""), ""))

        for source_row_number, row in enumerate(reader, start=2):
            name = value(row, "name")
            written = value(row, "written")
            if not name or not written:
                continue

            identity = tuple(
                key(value(row, field_name))
                for field_name in ("name", "address", "address2", "city", "st", "zip", "country")
            )
            candidate = grouped.get(identity)
            if candidate is None:
                candidate = Candidate(
                    name=name,
                    address=value(row, "address"),
                    address2=value(row, "address2"),
                    city=value(row, "city"),
                    state=value(row, "st"),
                    zip_code=value(row, "zip").removesuffix(".0"),
                    country=value(row, "country"),
                    place_type=value(row, "type"),
                    website=value(row, "website"),
                    instagram=value(row, "instagram"),
                    twitter=value(row, "twitter"),
                    facebook=value(row, "facebook"),
                )
                grouped[identity] = candidate

            candidate.source_rows.append(str(source_row_number))
            candidate.written.append(written)
            candidate.drew.append(value(row, "drew one?"))
            candidate.oob.append(value(row, "OOB?"))
            for attr, field_name in (("website", "website"), ("instagram", "instagram"), ("twitter", "twitter"), ("facebook", "facebook")):
                if not getattr(candidate, attr):
                    setattr(candidate, attr, value(row, field_name))

    return list(grouped.values())


def section_for(name: str, place_type: str) -> str:
    type_key = key(place_type)
    if type_key in BREWERY_TYPES:
        return "breweries"
    if type_key in OTHER_TYPES:
        return "other-places"
    name_key = key(name)
    if re.search(r"\b(brew|beer|alehouse|brewpub|ferment)\b", name_key):
        return "breweries"
    return "other-places"


def format_date(value: str) -> str:
    raw = clean(value)
    if not raw:
        return ""
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return dt.datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return raw


def format_written(values: list[str]) -> str:
    formatted = sorted({format_date(value) for value in values if clean(value)})
    return ", ".join(formatted)


def response_status(values: list[str]) -> str:
    lowered = {key(value) for value in values if clean(value)}
    if lowered & {"yes", "true", "confirmed yes"}:
        return "Yes"
    if lowered & {"no", "false"}:
        return "No"
    if lowered:
        return "Needs review"
    return "Not recorded"


def location_text(candidate: Candidate) -> str:
    city_state = ", ".join(part for part in (candidate.city, candidate.state) if clean(part))
    if candidate.zip_code:
        city_state = f"{city_state} {candidate.zip_code}".strip()
    return city_state or candidate.country or "Not recorded"


def md_text(value: str) -> str:
    return clean(value).replace("\n", " ").replace("\r", " ")


def url_line(label: str, value: str) -> str:
    value = clean(value)
    if not value:
        return ""
    if re.match(r"^https?://", value, flags=re.IGNORECASE):
        return f"> * **{label}:** [{value}]({value})"
    return f"> * **{label}:** {md_text(value)}"


def page_text(candidate: Candidate, section: str, page_id: str) -> str:
    tag = "brewery" if section == "breweries" else "other-place"
    state_tag = candidate.state or candidate.country or "unknown"
    title = json.dumps(md_text(candidate.name), ensure_ascii=False)
    lines = [
        "---",
        f"id: {page_id}",
        f"title: {title}",
        "status: published",
        f"tags: [{tag}, {json.dumps(state_tag)}, scaffold]",
        "---",
        "",
        f"# {md_text(candidate.name)}",
        "",
        "> [!NOTE]",
        "> **Outreach Metadata**",
        f"> * **Location:** {md_text(location_text(candidate))}",
        f"> * **Type:** {md_text(candidate.place_type) or 'Not recorded'}",
        f"> * **Written:** {md_text(format_written(candidate.written))}",
        f"> * **Elephant Received:** {response_status(candidate.drew)}",
        f"> * **Mail Status:** {response_status(candidate.oob)}",
    ]
    for label, value in (("Website", candidate.website), ("Instagram", candidate.instagram), ("Twitter", candidate.twitter), ("Facebook", candidate.facebook)):
        if value:
            lines.append(url_line(label, value))

    lines.extend(
        [
            "",
            "This page is a scaffold for an outreach record. Correspondence, drawing scans, and notes can be added here as they are recovered.",
            "",
            "## Correspondence",
            "",
            "No correspondence archive has been attached yet.",
            "",
        ]
    )
    return "\n".join(lines)


def allocate_page_id(candidate: Candidate, section: str, used_ids: set[str]) -> str:
    base = slug(candidate.name)
    options = [base]
    location = slug("-".join(part for part in (candidate.city, candidate.state) if clean(part)))
    if location:
        options.append(f"{base}-{location}")
    if candidate.zip_code:
        options.append(f"{base}-{location}-{slug(candidate.zip_code)}" if location else f"{base}-{slug(candidate.zip_code)}")
    options.append(f"{base}-source-{candidate.source_rows[0]}")

    for option in options:
        page_id = f"{section}/{option}"
        if page_id not in used_ids and not (CONTENT / f"{page_id}.md").exists():
            used_ids.add(page_id)
            return page_id

    counter = 2
    while True:
        page_id = f"{section}/{base}-source-{candidate.source_rows[0]}-{counter}"
        if page_id not in used_ids and not (CONTENT / f"{page_id}.md").exists():
            used_ids.add(page_id)
            return page_id
        counter += 1


def candidate_is_existing(candidate: Candidate, exact_source_rows: set[str], candidate_names: dict[str, list[str]], existing_titles: dict[str, str]) -> bool:
    if any(source_row in exact_source_rows for source_row in candidate.source_rows):
        return True
    if any(key(name) in existing_titles for source_row in candidate.source_rows for name in candidate_names.get(source_row, [])):
        return True
    alias = LEGACY_ALIASES.get(key(candidate.name))
    if alias:
        return True

    title_key = key(candidate.name)
    if title_key in existing_titles:
        return True
    for existing_title in existing_titles:
        similarity = SequenceMatcher(None, title_key, existing_title).ratio()
        shared_words = set(title_key.split()) & set(existing_title.split())
        if similarity >= 0.90 and len(shared_words) >= 2:
            return True
    return False


def scaffold_match(candidate: Candidate, existing_entries: list[dict[str, str]], assigned_ids: set[str]) -> dict[str, str] | None:
    """Find a page previously generated for this candidate.

    Matching the title and rendered location keeps duplicate names in different
    cities attached to their original page IDs on subsequent runs.
    """

    title_key = key(candidate.name)
    location_key = key(location_text(candidate))
    exact = [
        entry
        for entry in existing_entries
        if entry.get("scaffold")
        and key(entry.get("title", "")) == title_key
        and key(entry.get("location", "")) == location_key
    ]
    unused_exact = [entry for entry in exact if entry["page_id"] not in assigned_ids]
    if unused_exact:
        return sorted(unused_exact, key=lambda entry: entry["page_id"])[0]

    same_title = [
        entry
        for entry in existing_entries
        if entry.get("scaffold") and key(entry.get("title", "")) == title_key and entry["page_id"] not in assigned_ids
    ]
    return same_title[0] if len(same_title) == 1 else None


def manifest_row(candidate: Candidate, page_id: str, section: str) -> dict[str, str]:
    return {
        "page_id": page_id,
        "section": section,
        "title": md_text(candidate.name),
        "city": md_text(candidate.city),
        "state": md_text(candidate.state),
        "zip": md_text(candidate.zip_code),
        "type": md_text(candidate.place_type),
        "written": format_written(candidate.written),
        "drew_one": response_status(candidate.drew),
        "source_rows": ",".join(candidate.source_rows),
    }


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["page_id", "section", "title", "city", "state", "zip", "type", "written", "drew_one", "source_rows"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_index(path: Path, entries: list[dict[str, str]]) -> None:
    canonical_ids = {entry["page_id"] for entry in entries}
    hidden_legacy_ids = {
        legacy_id
        for legacy_id, canonical_id in LEGACY_REDIRECTS.items()
        if canonical_id in canonical_ids
    }
    entries = [entry for entry in entries if entry["page_id"] not in hidden_legacy_ids]
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for entry in entries:
        section = entry["section"]
        state = entry.get("state") or "Other"
        grouped[(section, state)].append(entry)

    lines = [
        "---",
        "id: written-places",
        'title: "Written Places"',
        "parent: index",
        "status: published",
        "tags: [directory]",
        "---",
        "",
        "# Written Places",
        "",
        "This directory is generated from the outreach ledger. Pages marked `scaffold` contain tracking metadata and are waiting for correspondence material or drawing scans.",
        "",
    ]
    for section, heading in (("breweries", "Breweries"), ("other-places", "Other places and things")):
        lines.extend([f"## {heading}", ""])
        states = sorted(state for sec, state in grouped if sec == section)
        for state in states:
            lines.extend([f"### {state}", ""])
            for entry in sorted(grouped[(section, state)], key=lambda item: (key(item["title"]), item["page_id"])):
                detail = entry.get("location") or ""
                if entry.get("type"):
                    detail = f"{detail}; {entry['type']}" if detail else entry["type"]
                lines.append(f"- [{entry['title']}](/{entry['page_id']}.html)" + (f" — {detail}" if detail else ""))
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="CSV export of the Addresses tab")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER, help="public ledger used for exact existing-page matches")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    existing_titles, used_ids, existing_entries = parse_existing_pages()
    exact_source_rows, candidate_names = read_exact_matches(args.ledger)
    candidates = read_candidates(args.input)

    manifest_rows: list[dict[str, str]] = []
    new_entries = list(existing_entries)
    skipped_existing = 0
    skipped_files = 0
    assigned_scaffold_ids: set[str] = set()

    for candidate in sorted(candidates, key=lambda item: (key(item.name), key(item.city), key(item.state), item.source_rows[0])):
        if candidate_is_existing(candidate, exact_source_rows, candidate_names, existing_titles):
            previous_scaffold = scaffold_match(candidate, existing_entries, assigned_scaffold_ids)
            if previous_scaffold:
                manifest_rows.append(manifest_row(candidate, previous_scaffold["page_id"], previous_scaffold["section"]))
                assigned_scaffold_ids.add(previous_scaffold["page_id"])
            skipped_existing += 1
            continue
        section = section_for(candidate.name, candidate.place_type)
        page_id = allocate_page_id(candidate, section, used_ids)
        candidate.page_id = page_id
        output_path = CONTENT / f"{page_id}.md"
        if output_path.exists():
            skipped_files += 1
            continue
        manifest_rows.append(manifest_row(candidate, page_id, section))
        new_entries.append(
            {
                "page_id": page_id,
                "title": md_text(candidate.name),
                "location": location_text(candidate),
                "state": (candidate.state or candidate.country or "Other").upper(),
                "section": section,
                "type": md_text(candidate.place_type),
            }
        )
        if not args.dry_run:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(page_text(candidate, section, page_id), encoding="utf-8")

    if not args.dry_run:
        write_manifest(args.manifest, manifest_rows)
        write_index(args.index, new_entries)

    print(f"eligible unique written locations: {len(candidates)}")
    print(f"existing pages preserved: {skipped_existing}")
    print(f"new page scaffolds: {len(manifest_rows)}")
    print(f"existing-file collisions skipped: {skipped_files}")
    print(f"taxonomy: breweries={sum(row['section'] == 'breweries' for row in manifest_rows)}, other-places={sum(row['section'] == 'other-places' for row in manifest_rows)}")
    if args.dry_run:
        print("dry run: no files written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
