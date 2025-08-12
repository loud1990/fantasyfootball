# Fantasy Football Data Utilities

This repository provides Windows-friendly scripts to:
- extract practice squads and rosters from league spreadsheets,
- export Sleeper league rosters and teams,
- capture Sleeper auction/draft history to CSV,
- inspect and debug spreadsheet structures,
- support auction value calculations via a shared library.

All examples use python on Windows 11 Command Prompt.

## Prerequisites

- Python 3.6+ (recommended: 3.10+)
- Pip packages:
  - pandas
  - openpyxl
  - requests
- Optional for running tests:
  - pytest

Install packages:

```
pip install pandas openpyxl requests
```

To run tests:

```
pip install pytest
```

## Repository layout

Key files and directories:
- [`🏈 Dine Nasty Football 2025.xlsx`](🏈 Dine Nasty Football 2025.xlsx) and [`🏈 Dine Nasty Football 2025.csv`](🏈 Dine Nasty Football 2025.csv): master league workbook and CSV export.
- Division CSVs: [`BeamenDivision.csv`](BeamenDivision.csv), [`Falco.csv`](Falco.csv).
- Rankings: [`FantasyPros_2025_Dynasty_ALL_Rankings.csv`](FantasyPros_2025_Dynasty_ALL_Rankings.csv).
- Practice squad tools and data:
  - [`practice_squad_extractor.py`](practice_squad_extractor.py)
  - Outputs: [`practice_squad_players.csv`](practice_squad_players.csv), [`practice_squad_players_falco.csv`](practice_squad_players_falco.csv)
- Roster tools and data:
  - [`roster_extractor.py`](roster_extractor.py)
  - Outputs: [`roster_players.csv`](roster_players.csv), [`roster_players_falco.csv`](roster_players_falco.csv), combined [`extracted_roster.csv`](extracted_roster.csv)
- Sleeper exports:
  - [`export_sleeper.py`](export_sleeper.py) → [`sleeper_league_1180272148495294464_roster_players.csv`](sleeper_league_1180272148495294464_roster_players.csv), [`sleeper_league_1180272148495294464_teams.csv`](sleeper_league_1180272148495294464_teams.csv)
  - [`sleeper_auction_extractor.py`](sleeper_auction_extractor.py) → writes to [`sleeper_drafts_csv/`](sleeper_drafts_csv/)
- Debug/inspection helpers:
  - [`check_all_sheets_for_ps.py`](check_all_sheets_for_ps.py), [`check_excel.py`](check_excel.py), [`check_excel_detailed.py`](check_excel_detailed.py), [`check_division_sheets.py`](check_division_sheets.py), [`debug_practice_squad.py`](debug_practice_squad.py), [`debug_practice_squad_detailed.py`](debug_practice_squad_detailed.py), [`debug_team_names.py`](debug_team_names.py), [`debug_normalized.py`](debug_normalized.py)
- Library (not a CLI): [`auctionhelper.py`](auctionhelper.py)
- Other data: [`free_agents.csv`](free_agents.csv)
- Tests: [`tests/`](tests/) → [`tests/test_practice_squad_filter.py`](tests/test_practice_squad_filter.py)
- Examples of saved drafts: [`sleeper_drafts_csv/`](sleeper_drafts_csv/) → [`sleeper_drafts_csv/sleeper_draft_2024_1048776197225738241.csv`](sleeper_drafts_csv/sleeper_draft_2024_1048776197225738241.csv) and prior years

## Quick Start (Windows 11)

1) Install dependencies:

```
pip install pandas openpyxl requests
```

2) Extract practice squad lists from the default division CSV using [`practice_squad_extractor.py`](practice_squad_extractor.py):

```
python practice_squad_extractor.py --both
```

3) Export a Sleeper league using [`export_sleeper.py`](export_sleeper.py) (replace the ID as needed):

```
python export_sleeper.py --league 1180272148495294464
```

4) Optional: run validations:

```
python -m pytest tests/test_practice_squad_filter.py
```

## Usage by capability

### Extract practice squads

Use [`practice_squad_extractor.py`](practice_squad_extractor.py) to build per-division practice squad CSVs.

- Inputs (default): [`BeamenDivision.csv`](BeamenDivision.csv)
- Outputs (default): [`practice_squad_players.csv`](practice_squad_players.csv)
- Flags:
  - -i / --input: path to a division CSV
  - -o / --out: output CSV filename
  - --both: process both divisions and write both [`practice_squad_players.csv`](practice_squad_players.csv) and [`practice_squad_players_falco.csv`](practice_squad_players_falco.csv)
- Behavior: prints selected player names, enforces maximum 3 per team and maximum 36 total.

Examples:

```
python practice_squad_extractor.py
```

```
python practice_squad_extractor.py -i BeamenDivision.csv -o practice_squad_players.csv
```

```
python practice_squad_extractor.py --both
```

### Extract rosters

Use [`roster_extractor.py`](roster_extractor.py) to export roster lists per division and a combined list.

- Inputs (default): [`BeamenDivision.csv`](BeamenDivision.csv)
- Outputs (default): [`roster_players.csv`](roster_players.csv)
- Flags:
  - -i / --input: path to a division CSV
  - -o / --out: output CSV filename
  - --both: produce [`roster_players.csv`](roster_players.csv), [`roster_players_falco.csv`](roster_players_falco.csv), and combined [`extracted_roster.csv`](extracted_roster.csv)
- Behavior: prints player names as they are extracted.

Examples:

```
python roster_extractor.py
```

```
python roster_extractor.py --both
```

### Export Sleeper league rosters and teams

Use [`export_sleeper.py`](export_sleeper.py) to fetch league data from the Sleeper API.

- Required flag: --league or -l with your league ID
- Outputs: [`sleeper_league_{league_id}_roster_players.csv`](sleeper_league_1180272148495294464_roster_players.csv) and [`sleeper_league_{league_id}_teams.csv`](sleeper_league_1180272148495294464_teams.csv)
- Network access required.

Example:

```
python export_sleeper.py --league 1180272148495294464
```

### Fetch Sleeper auction/draft CSVs

Run [`sleeper_auction_extractor.py`](sleeper_auction_extractor.py) to download draft/auction data to [`sleeper_drafts_csv/`](sleeper_drafts_csv/). This script does not take CLI flags; it uses a hardcoded league ID.

- To change the league: open [`sleeper_auction_extractor.py`](sleeper_auction_extractor.py) and update the hardcoded league ID string near the top of the file, then save.
- Outputs: CSV files named like sleeper_draft_{year}_{id}.csv in [`sleeper_drafts_csv/`](sleeper_drafts_csv/).

Example:

```
python sleeper_auction_extractor.py
```

### Inspect and diagnose spreadsheets

The following helpers print structures, sheet names, and parsed rows to help verify assumptions:

- [`check_excel.py`](check_excel.py): quick sheet/content inspection for [`🏈 Dine Nasty Football 2025.xlsx`](🏈 Dine Nasty Football 2025.xlsx).
- [`check_excel_detailed.py`](check_excel_detailed.py): detailed per-sheet walkthrough of columns/sections.
- [`check_all_sheets_for_ps.py`](check_all_sheets_for_ps.py): scan all sheets for practice squad markers/sections.
- [`check_division_sheets.py`](check_division_sheets.py): verify division-specific sheets/sections exist and align.
- [`debug_practice_squad.py`](debug_practice_squad.py): show filtered practice squad candidates from a division CSV.
- [`debug_practice_squad_detailed.py`](debug_practice_squad_detailed.py): include reasons/filters for inclusion/exclusion.
- [`debug_team_names.py`](debug_team_names.py): verify normalization and mapping of team names.
- [`debug_normalized.py`](debug_normalized.py): inspect normalized player names across sources.

Examples:

```
python check_excel.py
```

```
python debug_practice_squad.py -i BeamenDivision.csv
```

### Auction value calculation library

[`auctionhelper.py`](auctionhelper.py) is a reusable module that centralizes data processing and auction value calculations used by the scripts. It is not intended to be executed directly; other scripts import it internally to keep logic consistent.

## Data flows and typical workflows

- From master workbook to practice squads:
  1. Confirm inputs: [`🏈 Dine Nasty Football 2025.xlsx`](🏈 Dine Nasty Football 2025.xlsx) and division CSVs [`BeamenDivision.csv`](BeamenDivision.csv), [`Falco.csv`](Falco.csv).
  2. Run [`practice_squad_extractor.py`](practice_squad_extractor.py) (optionally with --both).
  3. Review outputs: [`practice_squad_players.csv`](practice_squad_players.csv) and [`practice_squad_players_falco.csv`](practice_squad_players_falco.csv) if both divisions processed.

- Build roster lists:
  1. Run [`roster_extractor.py`](roster_extractor.py) (optionally with --both).
  2. Review outputs: [`roster_players.csv`](roster_players.csv), [`roster_players_falco.csv`](roster_players_falco.csv), and combined [`extracted_roster.csv`](extracted_roster.csv).

- Pull league data from Sleeper:
  1. Run [`export_sleeper.py`](export_sleeper.py) with your league ID.
  2. Review outputs: [`sleeper_league_{league_id}_roster_players.csv`](sleeper_league_1180272148495294464_roster_players.csv) and [`sleeper_league_{league_id}_teams.csv`](sleeper_league_1180272148495294464_teams.csv).

- Capture draft/auction history:
  1. Edit league ID in [`sleeper_auction_extractor.py`](sleeper_auction_extractor.py).
  2. Run the script; review CSVs written to [`sleeper_drafts_csv/`](sleeper_drafts_csv/).

- Inspect/diagnose when results seem off:
  1. Use the check/debug scripts listed above to verify sheet names, section markers, and normalization.
  2. Re-run extractors after fixing input data.

## Outputs and locations

- Practice squads:
  - [`practice_squad_players.csv`](practice_squad_players.csv)
  - [`practice_squad_players_falco.csv`](practice_squad_players_falco.csv)
- Rosters:
  - [`roster_players.csv`](roster_players.csv)
  - [`roster_players_falco.csv`](roster_players_falco.csv)
  - Combined: [`extracted_roster.csv`](extracted_roster.csv)
- Sleeper exports:
  - [`sleeper_league_{league_id}_roster_players.csv`](sleeper_league_1180272148495294464_roster_players.csv)
  - [`sleeper_league_{league_id}_teams.csv`](sleeper_league_1180272148495294464_teams.csv)
- Drafts/Auctions:
  - Files saved under [`sleeper_drafts_csv/`](sleeper_drafts_csv/) such as [`sleeper_drafts_csv/sleeper_draft_2024_1048776197225738241.csv`](sleeper_drafts_csv/sleeper_draft_2024_1048776197225738241.csv)

## Troubleshooting

Fragile assumptions and quick checks:
- Spreadsheet structure must match expected sheet names, column layouts, and section markers in [`🏈 Dine Nasty Football 2025.xlsx`](🏈 Dine Nasty Football 2025.xlsx). Use [`check_excel.py`](check_excel.py) and [`check_excel_detailed.py`](check_excel_detailed.py).
- Division CSVs must reflect current rosters. Verify with [`check_division_sheets.py`](check_division_sheets.py).
- Practice squad limits are enforced (max 3 per team, 36 total). If the counts seem wrong, run [`debug_practice_squad.py`](debug_practice_squad.py) or [`debug_practice_squad_detailed.py`](debug_practice_squad_detailed.py).
- Player and team name normalization can affect joins. Inspect with [`debug_normalized.py`](debug_normalized.py) and [`debug_team_names.py`](debug_team_names.py).
- Sleeper API calls require network access; if a request fails or returns empty, re-try later and confirm the league ID used by [`export_sleeper.py`](export_sleeper.py) or the edited ID in [`sleeper_auction_extractor.py`](sleeper_auction_extractor.py).

Validate quickly by running the targeted test:

```
python -m pytest tests/test_practice_squad_filter.py
```

If the test fails, inspect recent changes to division CSVs and re-run the debug helpers.

## Notes

- All scripts assume they are run from the repository root so that relative paths (e.g., to [`sleeper_drafts_csv/`](sleeper_drafts_csv/)) resolve correctly.
- Do not run [`auctionhelper.py`](auctionhelper.py) directly; it is used internally by the other scripts.
- Keep backups of source files like [`🏈 Dine Nasty Football 2025.xlsx`](🏈 Dine Nasty Football 2025.xlsx) before making bulk edits.