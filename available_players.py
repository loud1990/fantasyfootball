"""
CLI to generate consolidated taken players and filtered available players from existing CSVs.

Reads:
- extracted_roster.csv with a "Player" column
- practice_squad_players.csv with a "Player" column
- FantasyPros_2025_Dynasty_ALL_Rankings.csv with a "PLAYER NAME" column

Produces:
- all_taken_players.csv containing the de-duplicated union of Player names (one "Player" column)
- available_players.csv containing all ranking rows whose "PLAYER NAME" is not in the taken set

Windows 11 usage examples:
- python available_players.py
- python available_players.py --roster extracted_roster.csv --practice practice_squad_players.csv --rankings FantasyPros_2025_Dynasty_ALL_Rankings.csv --out-taken all_taken_players.csv --out-available available_players.csv
"""

import argparse
import sys
import unicodedata
import re
from typing import Iterable, List, Dict, Set

import pandas as pd

SUFFIX_TOKENS: Set[str] = {"jr", "sr", "ii", "iii", "iv", "v"}


def normalize_name(name: str) -> str:
    """
    Normalize player names to improve matching across variants:
    - lowercase
    - Unicode NFKD fold and strip accents
    - remove punctuation and apostrophes
    - remove common suffix tokens (jr, sr, ii, iii, iv, v)
    - collapse whitespace
    """
    if name is None:
        return ""
    s = str(name).strip().lower()
    if not s:
        return ""
    # Unicode fold and strip accents
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    # Remove punctuation (keep alphanumerics and whitespace)
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    # Remove suffix tokens when present as separate words
    tokens = [t for t in s.split() if t and t not in SUFFIX_TOKENS]
    s = " ".join(tokens)
    # Final collapse of whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def collect_players_from_csv(path: str, column: str = "Player") -> List[str]:
    """
    Read a CSV and collect non-empty names from the specified column.
    Uses dtype=str and keep_default_na=False to avoid NaNs.
    """
    # Read with UTF-8 BOM handling
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    if column not in df.columns:
        print(f"Warning: Column '{column}' not found in {path}. Treating as empty.", file=sys.stderr)
        return []
    series = df[column].astype(str)
    names = [x.strip() for x in series.tolist() if isinstance(x, str) and x.strip()]
    return names


def dedupe_by_normalized(names: Iterable[str]) -> List[str]:
    """
    De-duplicate names by their normalized form, preserving the first seen original.
    """
    seen: Set[str] = set()
    unique: List[str] = []
    for n in names:
        norm = normalize_name(n)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        unique.append(n.strip())
    return unique


def build_available_players(
    roster_csv: str = "extracted_roster.csv",
    practice_csv: str = "practice_squad_players.csv",
    rankings_csv: str = "FantasyPros_2025_Dynasty_ALL_Rankings.csv",
    out_taken_csv: str = "all_taken_players.csv",
    out_available_csv: str = "available_players.csv",
):
    """
    End-to-end workflow:
    - Read roster and practice squad player names
    - Write de-duplicated union to out_taken_csv
    - Read rankings and filter out taken players using robust normalization
    - Write available players (all original columns) to out_available_csv
    Returns a summary dict with counts and output paths.
    """
    roster_names = collect_players_from_csv(roster_csv, column="Player")
    practice_names = collect_players_from_csv(practice_csv, column="Player")

    taken_all = roster_names + practice_names
    taken_unique = dedupe_by_normalized(taken_all)
    taken_norm_set = {normalize_name(n) for n in taken_unique}

    # Write all_taken_players.csv
    taken_sorted = sorted(taken_unique, key=lambda s: s.lower())
    df_taken = pd.DataFrame({"Player": taken_sorted})
    df_taken.to_csv(out_taken_csv, index=False, encoding="utf-8")

    # Read rankings and filter
    df_rankings = pd.read_csv(rankings_csv, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    if "PLAYER NAME" not in df_rankings.columns:
        raise ValueError(f"Required column 'PLAYER NAME' not found in rankings file: {rankings_csv}")
    mask_taken = df_rankings["PLAYER NAME"].map(normalize_name).isin(taken_norm_set)
    df_available = df_rankings[~mask_taken]
    df_available.to_csv(out_available_csv, index=False, encoding="utf-8")

    summary: Dict[str, object] = {
        "roster_count": len(roster_names),
        "practice_count": len(practice_names),
        "taken_unique_count": len(taken_norm_set),
        "rankings_total": len(df_rankings),
        "available_total": len(df_available),
        "out_taken": out_taken_csv,
        "out_available": out_available_csv,
    }
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate consolidated taken players and filtered available players from CSVs."
    )
    parser.add_argument(
        "--roster",
        "-r",
        default="extracted_roster.csv",
        help="Path to roster CSV (default: extracted_roster.csv)",
    )
    parser.add_argument(
        "--practice",
        "-p",
        default="practice_squad_players.csv",
        help="Path to practice squad CSV (default: practice_squad_players.csv)",
    )
    parser.add_argument(
        "--rankings",
        "-k",
        default="FantasyPros_2025_Dynasty_ALL_Rankings.csv",
        help="Path to rankings CSV (default: FantasyPros_2025_Dynasty_ALL_Rankings.csv)",
    )
    parser.add_argument(
        "--out-taken",
        "-t",
        dest="out_taken",
        default="all_taken_players.csv",
        help="Output path for taken players CSV (default: all_taken_players.csv)",
    )
    parser.add_argument(
        "--out-available",
        "-a",
        dest="out_available",
        default="available_players.csv",
        help="Output path for available players CSV (default: available_players.csv)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_available_players(
        roster_csv=args.roster,
        practice_csv=args.practice,
        rankings_csv=args.rankings,
        out_taken_csv=args.out_taken,
        out_available_csv=args.out_available,
    )
    # Concise summary
    print(f"Roster players: {summary['roster_count']}")
    print(f"Practice squad players: {summary['practice_count']}")
    print(f"Combined unique taken: {summary['taken_unique_count']}")
    print(f"Total rankings rows: {summary['rankings_total']}")
    print(f"Available players rows: {summary['available_total']}")
    print(f"Wrote taken CSV: {summary['out_taken']}")
    print(f"Wrote available CSV: {summary['out_available']}")


if __name__ == "__main__":
    main()