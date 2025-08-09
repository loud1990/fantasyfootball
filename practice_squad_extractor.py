import csv
import re
import argparse
from typing import List, Dict, Tuple


# Constants and small utilities

EXCLUDED_TEAM_TOKENS = {
    "count",
    "number",  # handle Falco.csv header row "Number" when scanning for team names
    "practice squad stash",
    "new offseason contracts",
    "contract extentions",   # keep misspelling as provided in spec
    "contract extensions",   # include common spelling for resilience
    "rookie draft picks",
    "offseason free agent auction cash",
}

CLEAN_TRAILING_BRACED_SUFFIX = re.compile(r"\s*\{[^}]*\}\s*$")


def _cell(row: List[str], idx: int) -> str:
    """Safe cell access; returns '' when index is out of bounds or value is None."""
    if idx < 0 or idx >= len(row):
        return ""
    val = row[idx]
    return "" if val is None else str(val)


def _strip(s: str) -> str:
    return "" if s is None else str(s).strip()


def _contains_practice_squad_stash(row: List[str]) -> bool:
    for c in row:
        if isinstance(c, str) and "practice squad stash" in c.casefold():
            return True
    return False


def _is_excluded_team_token(val: str) -> bool:
    v = _strip(val)
    if not v:
        return True
    if v.isdigit():
        return True
    return v.casefold() in EXCLUDED_TEAM_TOKENS


def _find_team_name(rows: List[List[str]], start_row: int, base_col: int) -> str:
    """
    Scan upward in the same base column (b) to find the most recent non-empty
    value that is not an excluded token. Use that verbatim as the team name.
    """
    r = start_row - 1
    while r >= 0:
        candidate = _strip(_cell(rows[r], base_col))
        if candidate and not _is_excluded_team_token(candidate):
            return candidate
        r -= 1
    return ""  # If not found, return empty; entries for this group will be skipped


def _clean_player_display(name: str) -> str:
    """Remove a trailing ' {…}' token if present and trim whitespace."""
    if not name:
        return ""
    return CLEAN_TRAILING_BRACED_SUFFIX.sub("", name).strip()


def read_csv_rows(path: str) -> List[List[str]]:
    # Use utf-8-sig to handle potential BOM at beginning of file per spec
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        return [row for row in reader]


def extract_practice_squad(rows: List[List[str]]) -> List[Dict[str, str]]:
    """
    Parse all 'Practice Squad Stash' sections.

    CSV structure: teams placed side-by-side in 5-column groups:
    - Count (b), Position (b+1), Player (b+2), Contract/NFL code (b+3), empty sep (b+4)
    Team groups begin at columns 0, 5, 10, ...

    For each 'Practice Squad Stash' header row:
      - Determine team name for each group by scanning upward in the base column (b).
      - Then read subsequent rows, collecting non-empty player cells at (b+2) with position at (b+1).
      - Stop the section when a row is reached where all groups have empty player cells.
    """
    entries: List[Dict[str, str]] = []
    if not rows:
        return entries

    # Determine the maximum column count to identify potential group bases.
    max_cols = max(len(r) for r in rows)
    all_group_bases = [b for b in range(0, max_cols, 5) if b + 2 < max_cols]

    i = 0
    while i < len(rows):
        row = rows[i]
        if not _contains_practice_squad_stash(row):
            i += 1
            continue

        # Cache team names for this section by scanning upward in the same base column (b).
        team_for_base: Dict[int, str] = {}
        for b in all_group_bases:
            team_for_base[b] = _find_team_name(rows, i, b)

        # Consume subsequent rows for this practice squad section.
        j = i + 1
        while j < len(rows):
            current = rows[j]

            # Determine if all player cells for all bases are empty; if so, end of this section.
            all_empty_players = True
            for b in all_group_bases:
                player_raw = _strip(_cell(current, b + 2))
                if player_raw:
                    all_empty_players = False
                    break
            if all_empty_players:
                break

            # Collect entries for non-empty player cells.
            for b in all_group_bases:
                player_raw = _strip(_cell(current, b + 2))
                if not player_raw:
                    continue  # ignore rows with count/position but no player
                pos_raw = _strip(_cell(current, b + 1))
                team = _strip(team_for_base.get(b, ""))
                if not team:
                    # If we couldn't resolve the team name for this group, skip safely.
                    continue
                player = _clean_player_display(player_raw)
                if not player:
                    continue
                entries.append({"Team": team, "Position": pos_raw, "Player": player})
            j += 1

        # Continue searching after this section's terminating empty-player row (if present)
        i = j + 1

    return entries


def validate_entries(entries: List[Dict[str, str]]) -> Tuple[Dict[str, int], int]:
    """
    Validate that:
      - No team has more than 3 practice squad players.
      - Global total is at most 36.
    Returns (count_by_team, total).
    """
    count_by_team: Dict[str, int] = {}
    players_by_team: Dict[str, List[str]] = {}
    for e in entries:
        team = e["Team"]
        player = e["Player"]
        count_by_team[team] = count_by_team.get(team, 0) + 1
        players_by_team.setdefault(team, []).append(player)

    # Per-team constraint
    for team, cnt in count_by_team.items():
        if cnt > 3:
            raise ValueError(
                f"Team '{team}' has more than 3 practice squad players ({cnt}): {', '.join(players_by_team[team])}"
            )

    total = len(entries)
    if total > 36:
        raise ValueError(f"Total practice squad players exceeds 36 (found {total}).")

    return count_by_team, total


def write_output(entries: List[Dict[str, str]], out_path: str) -> None:
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Team", "Position", "Player"])
        for e in entries:
            writer.writerow([e["Team"], e["Position"], e["Player"]])


def _process_dataset(input_path: str, output_path: str, label: str = "") -> None:
    """
    Helper to run read -> extract -> validate -> write -> print in one place.

    When label is provided (non-empty), a header line '=== {label} ===' is printed
    before the 'Team, Player' lines and the trailing 'Total: N'.
    Exceptions are intentionally not caught here so that failures propagate and
    terminate the process with a non-zero exit code as required.
    """
    # Read
    rows = read_csv_rows(input_path)
    # Extract
    entries = extract_practice_squad(rows)
    # Validate (independent for each dataset)
    validate_entries(entries)
    # Write
    write_output(entries, output_path)
    # Report
    # Intentionally print only player names to stdout (no team names, headers, or totals)
    for e in entries:
        print(e["Player"])


def _norm_team(s: str) -> str:
    return _strip(s).casefold()


def get_practice_squad_players_by_team(team_name: str, input_csv: str = "BeamenDivision.csv") -> List[str]:
    """
    Convenience API: read the CSV and return the list of practice squad player display names
    for the given team. This uses the CSV extractor in this module.

    The returned list preserves the order encountered in the CSV.
    """
    rows = read_csv_rows(input_csv)
    entries = extract_practice_squad(rows)
    target = _norm_team(team_name)
    players: List[str] = [e["Player"] for e in entries if _norm_team(e["Team"]) == target]
    return players


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Practice Squad players from a division CSV.")
    parser.add_argument("--input", "-i", default="BeamenDivision.csv", help="Path to input CSV (default: BeamenDivision.csv)")
    parser.add_argument("--out", "-o", default="practice_squad_players.csv", help="Path to output CSV (default: practice_squad_players.csv)")
    # --both mode: process BeamenDivision and Falco in a single run; ignore --input/--out
    parser.add_argument(
        "--both",
        action="store_true",
        help="Process BeamenDivision.csv -> practice_squad_players.csv AND Falco.csv -> practice_squad_players_falco.csv in one run. Ignores --input/--out when provided."
    )
    args = parser.parse_args()

    if args.both:
        # In --both mode, run the pipeline twice with independent validation and outputs.
        _process_dataset("BeamenDivision.csv", "practice_squad_players.csv", label="BeamenDivision")
        _process_dataset("Falco.csv", "practice_squad_players_falco.csv", label="Falco")
        return

    rows = read_csv_rows(args.input)
    entries = extract_practice_squad(rows)

    # Validate constraints
    counts_by_team, total = validate_entries(entries)

    # Write CSV output
    write_output(entries, args.out)

    # Print only player names to stdout (no teams, headers, or totals)
    for e in entries:
        print(e["Player"])


if __name__ == "__main__":
    main()
