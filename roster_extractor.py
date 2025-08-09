"""
Roster extractor: outputs only regularly rostered players per team from division CSVs.

Usage:
  python roster_extractor.py
    - Reads BeamenDivision.csv and writes roster_players.csv
    - Also writes extracted_roster.csv containing only the player names (single column: Player)

  python roster_extractor.py --both
    - Processes:
        BeamenDivision.csv -> roster_players.csv
        Falco.csv -> roster_players_falco.csv
    - Also writes extracted_roster.csv containing all extracted player names from both datasets
      in order (BeamenDivision first, then Falco), with a single column: Player

Programmatic use:
  from roster_extractor import get_roster_players_by_team
  players = get_roster_players_by_team("Some Team")  # returns list of player display names
"""
import csv
import argparse
from typing import List, Dict, Set

# Reuse helpers from practice_squad_extractor to avoid drift
from practice_squad_extractor import (
    _cell,
    _strip,
    _find_team_name,
    _clean_player_display,
    read_csv_rows,
)

# Tokens that mark non-roster sections to exclude (case-insensitive substring match)
SECTION_TOKENS: Set[str] = {
    "practice squad stash",
    "new offseason contracts",
    "contract extentions",   # typo intentional to match data
    "contract extensions",
    "rookie draft picks",
    "offseason free agent auction cash",
}

HEADER_LIKE_PLAYER_VALUES: Set[str] = {"player", "players"}


def _norm_team(s: str) -> str:
    """Normalize team names for case-insensitive comparisons."""
    return _strip(s).casefold()


def _all_group_bases(rows: List[List[str]]) -> List[int]:
    """Return the list of base column indices (0,5,10,...) where b+2 exists."""
    if not rows:
        return []
    max_cols = max(len(r) for r in rows)
    return [b for b in range(0, max_cols, 5) if b + 2 < max_cols]


def _contains_section_token(row: List[str]) -> bool:
    """True if any cell contains any of the section tokens (case-insensitive substring)."""
    for c in row:
        if not isinstance(c, str):
            continue
        low = c.casefold()
        for t in SECTION_TOKENS:
            if t in low:
                return True
    return False


def _compute_excluded_row_indices(rows: List[List[str]]) -> Set[int]:
    """
    Identify and return the set of row indices that belong to excluded non-roster sections.
    Section start: a row that contains any SECTION_TOKENS.
    Section body: subsequent rows until a row where all group player cells are empty.
    """
    excluded: Set[int] = set()
    if not rows:
        return excluded
    bases = _all_group_bases(rows)
    i = 0
    n = len(rows)
    while i < n:
        row = rows[i]
        if not _contains_section_token(row):
            i += 1
            continue
        # Begin section on next row
        j = i + 1
        # Consume until a row where all player cells are empty
        while j < n:
            current = rows[j]
            # If all groups' player cells are empty, end the section (do not include this row)
            all_empty = True
            for b in bases:
                if _strip(_cell(current, b + 2)):
                    all_empty = False
                    break
            if all_empty:
                break
            excluded.add(j)
            j += 1
        # Continue after the terminator row
        i = j + 1
    return excluded


def _is_header_like_player_cell(value: str) -> bool:
    """Detect header-like artifacts in the Player column."""
    if not value:
        return False
    v = _strip(value).casefold()
    if not v:
        return False
    return v in HEADER_LIKE_PLAYER_VALUES


def extract_roster(rows: List[List[str]]) -> List[Dict[str, str]]:
    """
    Extract regularly rostered players from the CSV, excluding non-roster sections.

    CSV layout is 5-wide per team group:
      Count (b), Position (b+1), Player (b+2), Contract (b+3), sep (b+4)
    """
    entries: List[Dict[str, str]] = []
    if not rows:
        return entries
    bases = _all_group_bases(rows)
    excluded_rows = _compute_excluded_row_indices(rows)
    for i, row in enumerate(rows):
        if i in excluded_rows:
            continue
        for b in bases:
            player_raw = _strip(_cell(row, b + 2))
            if not player_raw or _is_header_like_player_cell(player_raw):
                continue
            team = _find_team_name(rows, i, b)
            team = _strip(team)
            if not team:
                continue
            pos_raw = _strip(_cell(row, b + 1))
            player = _clean_player_display(player_raw)
            if not player:
                continue
            entries.append({"Team": team, "Position": pos_raw, "Player": player})
    return entries

def write_output(entries: List[Dict[str, str]], out_path: str) -> None:
    """Write entries to CSV with header: Team, Position, Player."""
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Team", "Position", "Player"])
        for e in entries:
            writer.writerow([e["Team"], e["Position"], e["Player"]])


def write_players_output(entries: List[Dict[str, str]], out_path: str) -> None:
    """Write only player names to CSV with header: Player."""
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Player"])
        for e in entries:
            writer.writerow([e["Player"]])


def get_roster_players_by_team(team_name: str, input_csv: str = "BeamenDivision.csv") -> List[str]:
    """
    Convenience API: return the list of regularly rostered player display names for the given team.
    The list preserves the encounter order from the CSV.
    """
    rows = read_csv_rows(input_csv)
    entries = extract_roster(rows)
    target = _norm_team(team_name)
    return [e["Player"] for e in entries if _norm_team(e["Team"]) == target]


def _process_dataset(input_path: str, output_path: str, label: str = "") -> List[Dict[str, str]]:
    """
    Read -> extract -> write -> print. Intentionally prints only player names to stdout.
    The label parameter is accepted for parity with the practice squad tool; it is not used.
    Returns the extracted entries.
    """
    rows = read_csv_rows(input_path)
    entries = extract_roster(rows)
    write_output(entries, output_path)
    for e in entries:
        print(e["Player"])
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract regularly rostered players from a division CSV.")
    parser.add_argument("--input", "-i", default="BeamenDivision.csv", help="Path to input CSV (default: BeamenDivision.csv)")
    parser.add_argument("--out", "-o", default="roster_players.csv", help="Path to output CSV (default: roster_players.csv)")
    parser.add_argument(
        "--both",
        action="store_true",
        help="Process BeamenDivision.csv -> roster_players.csv AND Falco.csv -> roster_players_falco.csv in one run. Ignores --input/--out when provided.",
    )
    args = parser.parse_args()

    if args.both:
        entries_beamen = _process_dataset("BeamenDivision.csv", "roster_players.csv", label="BeamenDivision")
        entries_falco = _process_dataset("Falco.csv", "roster_players_falco.csv", label="Falco")
        write_players_output(entries_beamen + entries_falco, "extracted_roster.csv")
        return

    rows = read_csv_rows(args.input)
    entries = extract_roster(rows)
    write_output(entries, args.out)
    write_players_output(entries, "extracted_roster.csv")
    for e in entries:
        print(e["Player"])


if __name__ == "__main__":
    main()