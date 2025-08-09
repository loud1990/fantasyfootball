import pandas as pd

# Load the Excel file
xl = pd.ExcelFile('🏈 Dine Nasty Football 2025.xlsx')

# Define team columns to look for
team_columns = ['Team', 'Owner', 'Franchise', 'Manager']

# Check each sheet for practice squad data
for sheet in xl.sheet_names:
    try:
        df = xl.parse(sheet)
        
        # Check if any column contains "Practice Squad" (case insensitive)
        ps_columns = [col for col in df.columns if 'Practice Squad' in str(col)]
        
        # Check for team columns
        found_team_cols = [col for col in df.columns if str(col).strip() in team_columns]
        
        if ps_columns or found_team_cols:
            print(f'Sheet: {sheet}')
            print(f'  Shape: {df.shape}')
            print(f'  Columns: {list(df.columns)}')
            print(f'  Practice Squad columns: {ps_columns}')
            print(f'  Team columns: {found_team_cols}')
            
            # Show sample data if we have relevant columns
            if ps_columns or found_team_cols:
                print('  Sample data:')
                print(df.head(10).to_string())
            print()
    except Exception as e:
        print(f'Error reading sheet {sheet}: {e}')
        continue