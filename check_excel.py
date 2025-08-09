import pandas as pd

# Load the Excel file
xl = pd.ExcelFile('🏈 Dine Nasty Football 2025.xlsx')

# Define team columns to look for
team_columns = ['Team', 'Owner', 'Franchise', 'Manager']

# Check each sheet for the Practice Squad column
for sheet in xl.sheet_names:
    try:
        df = xl.parse(sheet)
        cols = [str(c).strip() for c in df.columns if str(c) != 'nan']
        if 'Practice Squad' in cols:
            team_col = [c for c in cols if c in team_columns]
            print(f'Sheet: {sheet}')
            print(f'  Practice Squad column: True')
            print(f'  Team column: {team_col}')
            print(f'  All columns: {cols}')
            print()
    except Exception as e:
        print(f'Error reading sheet {sheet}: {e}')
        continue