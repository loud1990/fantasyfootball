import pandas as pd

# Load the Excel file
xl = pd.ExcelFile('🏈 Dine Nasty Football 2025.xlsx')

# Define team columns to look for
team_columns = ['Team', 'Owner', 'Franchise', 'Manager']

# Check each sheet for the Practice Squad column
for sheet in xl.sheet_names:
    try:
        df = xl.parse(sheet)
        print(f'Sheet: {sheet}')
        print(f'  Shape: {df.shape}')
        print(f'  Columns: {list(df.columns)}')
        
        # Check if any column contains "Practice Squad" (case insensitive)
        ps_columns = [col for col in df.columns if 'Practice Squad' in str(col)]
        print(f'  Practice Squad columns: {ps_columns}')
        
        # Check for team columns
        found_team_cols = [col for col in df.columns if str(col).strip() in team_columns]
        print(f'  Team columns: {found_team_cols}')
        
        # If we found a Practice Squad column, show some sample data
        if ps_columns:
            print(f'  Sample data for first few rows:')
            for col in ps_columns[:3]:  # Show first 3 PS columns
                print(f'    {col}: {df[col].head().tolist()}')
        
        print()
    except Exception as e:
        print(f'Error reading sheet {sheet}: {e}')
        continue