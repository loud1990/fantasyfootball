import pandas as pd
import re
import unicodedata
from functools import lru_cache

############ 1. CONFIG ############
FILE = '🏈 Dine Nasty Football 2025.xlsx'   # path to your league workbook
DIVISION_SHEETS = ['Falco Division', 'Beamen Division']
RANKINGS_CSV = 'FantasyPros_2025_Dynasty_ALL_Rankings.csv'  # local rankings file
###############################

def _norm(s: str) -> str:
    """
    Normalize player names for comparison across sources.
    Lowercase; strip leading/trailing spaces; collapse internal whitespace;
    remove punctuation like periods, commas, apostrophes, hyphens; remove diacritics;
    remove common suffixes like Jr, Sr, II, III, IV.
    """
    if pd.isna(s):
        return ""
    # Convert to string and lowercase
    s = str(s).lower()
    # Remove diacritics
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
    # Remove punctuation like periods, commas, apostrophes, hyphens
    s = re.sub(r'[.,\'\-]', '', s)
    # Remove common suffixes
    s = re.sub(r'\s+(jr|sr|ii|iii|iv)\s*$', '', s)
    # Collapse internal whitespace
    s = re.sub(r'\s+', ' ', s)
    # Strip leading/trailing spaces
    s = s.strip()
    # Remove any remaining non-alphanumeric characters except spaces
    s = re.sub(r'[^a-z0-9 ]', '', s)
    return s
def get_practice_squad_players(xl_path: str, sheets):
    """
    Read practice squad players from the division sheets and return a DataFrame
    with player names and Status column.
    
    Args:
        xl_path: Path to the Excel file
        sheets: List of sheet names to process
        
    Returns:
        DataFrame with columns: Player, Status
    """
    # Check if openpyxl is installed
    try:
        import openpyxl
    except ImportError:
        raise ImportError("openpyxl is required to read Excel files. Please install it with: pip install openpyxl")
    
    practice_squad_data = []
    
    try:
        xl = pd.ExcelFile(xl_path)
    except Exception as e:
        raise ValueError(f"Failed to read Excel file {xl_path}: {str(e)}")
    
    for sh in sheets:
        if sh not in xl.sheet_names:
            raise ValueError(f"Sheet '{sh}' not found in Excel file. Available sheets: {xl.sheet_names}")
            
        df = xl.parse(sh, header=None)
        
        # Find all column indices where the header is "Number" or "Count"
        header_rows = df[df.eq('Number').any(axis=1) | df.eq('Count').any(axis=1)]
        if len(header_rows) == 0:
            continue
            
        header_row_idx = header_rows.index[0]
        header = df.iloc[header_row_idx]
        starts = [i for i, v in header.items() if v in ('Number', 'Count')]
        
        # Find rows with "Practice Squad Stash" marker
        practice_squad_rows = df[df.eq('Practice Squad Stash').any(axis=1)]
        if len(practice_squad_rows) == 0:
            continue
            
        # Process each team block
        for col in starts:
            # Find the practice squad stash row for this team block
            practice_squad_row_idx = None
            for idx in practice_squad_rows.index:
                if col in df.columns and not pd.isna(df.iloc[idx, col]):
                    practice_squad_row_idx = idx
                    break
            
            if practice_squad_row_idx is None:
                continue
                
            # Collect practice squad players
            # Practice squad starts after "Practice Squad Stash" row
            for player in df.iloc[practice_squad_row_idx+1:, col+2].dropna():
                player_name = str(player)
                # Only add non-empty player names
                if player_name.strip():
                    practice_squad_data.append({
                        'Player': player_name,
                        'Status': 'PS'
                    })
    
    # Create DataFrame
    if practice_squad_data:
        return pd.DataFrame(practice_squad_data)
    else:
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=['Player', 'Status'])

def _norm_for_comparison(s: str) -> str:
    """
    Normalize player names for comparison purposes only.
    Casefold, strip, collapse spaces, and remove periods/apostrophes/hyphens.
    """
    if pd.isna(s):
        return ""
    # Convert to string
    s = str(s)
    # Casefold for case-insensitive comparison
    s = s.casefold()
    # Strip leading/trailing spaces
    s = s.strip()
    # Collapse internal whitespace
    s = re.sub(r'\s+', ' ', s)
    # Remove punctuation like periods, apostrophes, hyphens
    s = re.sub(r'[.\'\-]', '', s)
    return s

def _is_truthy_practice_squad_value(value) -> bool:
    """
    Determine if a value should be considered True for practice squad designation.
    True if value is: True, 1, any non-zero number; or a string that, after
    strip/lower and removing punctuation, is one of {"y", "yes", "true", "ps",
    "practicesquad", "x", "1"}.
    """
    if pd.isna(value):
        return False
    
    # Handle boolean values
    if isinstance(value, bool):
        return value
    
    # Handle numeric values
    if isinstance(value, (int, float)):
        return value != 0
    
    # Handle string values
    if isinstance(value, str):
        # Strip and normalize
        normalized = value.strip().casefold()
        # Remove punctuation
        normalized = re.sub(r'[.\'\-]', '', normalized)
        # Check against truthy values
        truthy_values = {"y", "yes", "true", "ps", "practicesquad", "x", "1"}
        return normalized in truthy_values
    
    # For any other type, convert to string and check
    str_value = str(value).strip().casefold()
    str_value = re.sub(r'[.\'\-]', '', str_value)
    truthy_values = {"y", "yes", "true", "ps", "practicesquad", "x", "1"}
    return str_value in truthy_values

def _load_practice_squad_data_cached(xl_path: str) -> dict:
    """
    Load practice squad data from Excel file with fixed positions.
    Returns a mapping of normalized team names to lists of raw player names.
    """
    # Import the practice squad extractor
    try:
        import practice_squad_extractor
        return practice_squad_extractor._load_practice_squad_data_cached(xl_path)
    except ImportError:
        # Fallback to the original implementation if practice_squad_extractor is not available
        # Check if openpyxl is installed
        try:
            import openpyxl
        except ImportError:
            raise ImportError("openpyxl is required to read Excel files. Please install it with: pip install openpyxl")
        
        # Load all sheets
        try:
            xl = pd.ExcelFile(xl_path)
        except Exception as e:
            raise ValueError(f"Failed to read Excel file {xl_path}: {str(e)}")
        
        # Look for a sheet with both "Practice Squad" column and a team column
        team_columns = {"Team", "Owner", "Franchise", "Manager"}
        practice_squad_column = "Practice Squad"
        
        selected_sheet = None
        selected_team_column = None
        df = None
        
        # Try to find the best sheet
        for sheet_name in xl.sheet_names:
            try:
                sheet_df = xl.parse(sheet_name)
                if sheet_df.empty:
                    continue
                
                # Get column names (strip whitespace and convert to string)
                columns = [str(col).strip() if not pd.isna(col) else "" for col in sheet_df.columns]
                
                # Check if this sheet has the Practice Squad column
                if practice_squad_column in columns:
                    # Check if it has a team column
                    found_team_cols = [col for col in columns if col in team_columns]
                    if found_team_cols:
                        # Found a sheet with both columns, use it
                        selected_sheet = sheet_name
                        selected_team_column = found_team_cols[0]
                        df = sheet_df
                        break
            except Exception:
                # Skip sheets that cause errors
                continue
        
        # If no sheet found with both columns, try sheets with just Practice Squad column
        if selected_sheet is None:
            for sheet_name in xl.sheet_names:
                try:
                    sheet_df = xl.parse(sheet_name)
                    if sheet_df.empty:
                        continue
                    
                    # Get column names
                    columns = [str(col).strip() if not pd.isna(col) else "" for col in sheet_df.columns]
                    
                    # Check if this sheet has the Practice Squad column
                    if practice_squad_column in columns:
                        selected_sheet = sheet_name
                        df = sheet_df
                        break
                except Exception:
                    # Skip sheets that cause errors
                    continue
        
        if selected_sheet is None:
            raise ValueError(f"No sheet found with '{practice_squad_column}' column. Available sheets: {xl.sheet_names}")
        
        if df is None:
            raise ValueError("Failed to load data from Excel file")
        
        # Get column indices
        columns = [str(col).strip() if not pd.isna(col) else "" for col in df.columns]
        practice_squad_col_idx = columns.index(practice_squad_column)
        team_col_idx = columns.index(selected_team_column) if selected_team_column else None
        
        # If we don't have a team column, fail with a clear error
        if team_col_idx is None:
            available_columns = [col for col in columns if col]  # Filter out empty strings
            raise ValueError(f"Sheet '{selected_sheet}' has '{practice_squad_column}' column but none of the expected team columns {team_columns}. Available columns: {available_columns}")
        
        # Process the data
        team_to_players = {}
        
        # Track normalized names to deduplicate
        team_normalized_names = {}
        
        # Process each row
        for idx, row in df.iterrows():
            # Skip rows with missing data
            if pd.isna(row.iloc[practice_squad_col_idx]) or pd.isna(row.iloc[team_col_idx]):
                continue
            
            # Check if this player is on the practice squad
            if not _is_truthy_practice_squad_value(row.iloc[practice_squad_col_idx]):
                continue
            
            # Get player name (from index 1, assuming standard format)
            player_name_raw = row.iloc[1] if len(row) > 1 else None
            if player_name_raw is None or pd.isna(player_name_raw):
                continue
            
            # Convert to string and strip
            player_name = str(player_name_raw).strip()
            if not player_name:
                continue
            
            # Get team name
            team_name_raw = row.iloc[team_col_idx]
            team_name = str(team_name_raw).strip() if not pd.isna(team_name_raw) else ""
            if not team_name:
                continue
            
            # Normalize team name for comparison
            normalized_team = _norm_for_comparison(team_name)
            
            # Initialize team in dictionaries if needed
            if normalized_team not in team_to_players:
                team_to_players[normalized_team] = []
                team_normalized_names[normalized_team] = set()
            
            # Normalize player name for deduplication
            normalized_player = _norm_for_comparison(player_name)
            
            # Only add if not already present (deduplication)
            if normalized_player not in team_normalized_names[normalized_team]:
                team_to_players[normalized_team].append(player_name)
                team_normalized_names[normalized_team].add(normalized_player)
        
        return team_to_players

def get_practice_squad_players_by_team(team_name: str) -> list[str]:
    """
    Get practice squad players for a specific team from the Excel file.
    Returns a deterministic order (sorted by casefolded name) of raw names as they appear in Excel.
    
    Args:
        team_name: The name of the team to get practice squad players for
        
    Returns:
        List of player names on the practice squad for the specified team, sorted deterministically
    """
    # Load data (cached)
    team_to_players = _load_practice_squad_data_cached(FILE)
    
    # Normalize team name for lookup
    normalized_team = _norm_for_comparison(team_name)
    
    # Get players for team or return empty list
    players = team_to_players.get(normalized_team, [])
    
    # Return sorted list (deterministic order)
    return sorted(players, key=str.casefold)

def pull_roster_players(xl_path: str, sheets):
    """
    Parse the rosters and budgets from the Excel file.
    
    Target sheets: "Falco Division" and "Beamen Division".
    Each sheet presents three teams per horizontal block of 4 columns (Number/Count, Position, Player, Contract) repeated;
    the team name is in row 1 of each 4-column block.
    Identify the roster table header row by "Number" or "Count" in the first column of each team's block.
    Active roster rows are from the row after that header down to the row above the "Practice Squad Stash" marker in that block.
    Count non-empty Player cells there to get the number of active players. Open slots = 15 - active_players.
    Also collect all Player names from both active roster and below "Practice Squad Stash" (practice squad) to build the "rostered" set.
    These must be excluded from free agents.
    Find the row that contains "Offseason Free Agent Auction Cash" in each team block;
    read the cash value from the next row in that same block. Values are strings like "$125 ($75 currently tradeable)";
    parse the leading dollar amount as an integer/float.
    """
    xl = pd.ExcelFile(xl_path)
    names = set()
    total_budget = 0
    total_open_slots = 0
    
    for sh in sheets:
        df = xl.parse(sh, header=None)
        
        # Find all column indices where the header is "Number" or "Count"
        header_rows = df[df.eq('Number').any(axis=1) | df.eq('Count').any(axis=1)]
        if len(header_rows) == 0:
            continue
            
        header_row_idx = header_rows.index[0]
        header = df.iloc[header_row_idx]
        starts = [i for i, v in header.items() if v in ('Number', 'Count')]
        
        # Find the row with "Offseason Free Agent Auction Cash"
        cash_rows = df[df.eq('Offseason Free Agent Auction Cash').any(axis=1)]
        if len(cash_rows) == 0:
            continue
            
        # Process each team block
        for col in starts:
            # Collect rostered players (active roster only)
            # Active roster: from header row + 1 to "Practice Squad Stash" row - 1
            practice_squad_rows = df[df.eq('Practice Squad Stash').any(axis=1)]
            if len(practice_squad_rows) == 0:
                # If no practice squad stash, collect all players as active roster
                for player in df.iloc[header_row_idx+1:, col+2].dropna():
                    names.add(_norm(str(player)))
                continue
                
            # Find the practice squad stash row for this team block
            practice_squad_row_idx = None
            for idx in practice_squad_rows.index:
                if col in df.columns and not pd.isna(df.iloc[idx, col]):
                    practice_squad_row_idx = idx
                    break
            
            if practice_squad_row_idx is None:
                # If no practice squad stash for this team block, collect all players as active roster
                for player in df.iloc[header_row_idx+1:, col+2].dropna():
                    names.add(_norm(str(player)))
                continue
            
            # Collect active roster players only
            for player in df.iloc[header_row_idx+1:practice_squad_row_idx, col+2].dropna():
                names.add(_norm(str(player)))
            
            # Count active players and calculate open slots
            active_players = df.iloc[header_row_idx+1:practice_squad_row_idx, col+2].dropna().count()
            open_slots = max(0, 15 - active_players)
            total_open_slots += open_slots
        
        # Process cash values for each team block
        for cash_row_idx in cash_rows.index:
            # Get the row after the cash row
            if cash_row_idx + 1 < len(df):
                cash_row = df.iloc[cash_row_idx + 1]
                # Process each team block in the cash row
                for col in starts:
                    if col < len(cash_row) and not pd.isna(cash_row[col]):
                        cash_str = str(cash_row[col])
                        # Extract the dollar amount (first number after $)
                        match = re.search(r'\$(\d+)', cash_str)
                        if match:
                            total_budget += int(match.group(1))
    
    return names, total_budget, total_open_slots

def fetch_dynasty_rankings():
    """
    Read the rankings from FantasyPros_2025_Dynasty_ALL_Rankings.csv.
    Robustly detect columns for player name and overall rank.
    """
    df = pd.read_csv(RANKINGS_CSV, encoding='utf-8-sig')
    
    # Rename columns to match downstream expectations
    rename_map = {
        'RK': 'Rank',
        'PLAYER NAME': 'Player',
        'TEAM': 'Tm',
        'POS': 'Pos',
        # Also support old online headers
        'Overall': 'Rank',
        'Player Name': 'Player',
        'Team': 'Tm',
        'Player Position': 'Pos'
    }
    df = df.rename(columns=rename_map)
    
    # Select only the columns that exist
    columns_to_select = [col for col in ['Rank', 'Player', 'Pos'] if col in df.columns]
    df = df[columns_to_select]
    
    # Coerce Rank to numeric and drop rows where Rank or Player are NaN
    df['Rank'] = pd.to_numeric(df['Rank'], errors='coerce')
    df = df.dropna(subset=['Rank', 'Player'])
    
    # Normalize Pos column to extract alpha prefix only (e.g., 'WR','RB','QB','TE','K','DST')
    df['Pos'] = df['Pos'].astype(str).str.extract(r'([A-Za-z]+)', expand=False)
    
    # Sort by Rank and reset index
    df = df.sort_values('Rank').reset_index(drop=True)
    
    return df

def calculate_auction_values(excel_path: str = FILE, rankings_csv: str = RANKINGS_CSV):
    """
    Calculate local auction values based on:
    1. Player rankings from FantasyPros_2025_Dynasty_ALL_Rankings.csv
    2. Each team's remaining Offseason Free Agent Auction Cash from Excel file
    3. Each team's remaining open roster slots (active roster) from Excel file
    
    Returns a DataFrame with columns: Player, Pos, Value
    """
    # Parse the rosters and budgets from Excel file
    rostered_players, total_budget, total_open_slots = pull_roster_players(excel_path, DIVISION_SHEETS)
    
    # Get practice squad players to exclude from free agent pool
    # Use the new Excel-driven source of truth
    practice_squad_names = set()
    
    # Define the teams we need to check for practice squad players
    team_names = [
        "JP BREAKS", "Savage Speeders", "The Firefly Funhouse",  # Falco Division teams
        "Sharp Bananas", "Raspberry Racers", "DeAndre 3000"       # Beamen Division teams
    ]
    
    # Collect all practice squad players from all teams
    for team_name in team_names:
        ps_players = get_practice_squad_players_by_team(team_name)
        for player in ps_players:
            practice_squad_names.add(_norm(player))
    
    # Log info about excluded practice squad players
    ps_count = len(practice_squad_names)
    if ps_count > 0:
        print(f"INFO: Excluded {ps_count} practice squad players from free agent pool.")
    else:
        print("INFO: No practice squad players found to exclude from free agent pool.")
    
    # Read the rankings from CSV
    rankings = fetch_dynasty_rankings()
    
    # Normalize player names in rankings for comparison
    rankings['norm_player'] = rankings['Player'].apply(_norm)
    
    # Filter out practice squad players
    free_agents = rankings[~rankings['norm_player'].isin(practice_squad_names)].copy()
    
    # Consider only the top M free agents (where M = total_open_slots)
    top_free_agents = free_agents.head(total_open_slots)
    
    # Calculate scores: score_i = 1 / rank_i
    top_free_agents['score'] = 1 / top_free_agents['Rank']
    
    # Sum scores
    total_score = top_free_agents['score'].sum()
    
    # Calculate values: Value_i = TotalBudget * (score_i / S)
    top_free_agents['Value'] = total_budget * (top_free_agents['score'] / total_score)
    top_free_agents['Value'] = top_free_agents['Value'].round(2)
    
    # Lightweight validation: sum of all Value_i should equal TotalBudget
    value_sum = top_free_agents['Value'].sum()
    difference = total_budget - value_sum
    
    # If off by more than $0.10, adjust the largest value by the difference
    if abs(difference) > 0.10:
        max_value_idx = top_free_agents['Value'].idxmax()
        top_free_agents.loc[max_value_idx, 'Value'] += difference
        top_free_agents.loc[max_value_idx, 'Value'] = round(top_free_agents.loc[max_value_idx, 'Value'], 2)
    
    # Return structured list with player name, position, and computed value
    result = top_free_agents[['Player', 'Pos', 'Value']].copy()
    return result.reset_index(drop=True)

def fetch_auction_values():
    """
    Legacy function name for backward compatibility.
    Replaced with local calculation instead of online fetching.
    """
    return calculate_auction_values()

def main():
    # Calculate auction values using local computation
    auction_values = calculate_auction_values()
    
    # Save to CSV
    out = 'free_agents.csv'
    auction_values.to_csv(out, index=False)
    print(f"Saved {len(auction_values)} free agents → {out}")
    
    # Print top 50 players with values
    print("\nTop 50 Free Agents:")
    print(auction_values.head(50).to_string(index=False))

if __name__ == '__main__':
    main()
