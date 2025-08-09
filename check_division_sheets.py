import pandas as pd

# Load the Excel file
xl = pd.ExcelFile('🏈 Dine Nasty Football 2025.xlsx')

# Check the division sheets
division_sheets = ['Falco Division', 'Beamen Division']

for sheet in division_sheets:
    try:
        print(f"=== {sheet} ===")
        df = xl.parse(sheet, header=None)  # Parse without header to see raw data
        print(f"Shape: {df.shape}")
        
        # Look for "Practice Squad Stash" markers
        ps_rows = df[df.eq('Practice Squad Stash').any(axis=1)]
        print(f"Rows with 'Practice Squad Stash': {len(ps_rows)}")
        
        if len(ps_rows) > 0:
            print("Practice Squad Stash rows:")
            for idx in ps_rows.index:
                print(f"  Row {idx}: {df.iloc[idx].tolist()}")
        
        # Show first few rows to understand structure
        print("First 10 rows:")
        for i in range(min(10, len(df))):
            print(f"  {i}: {df.iloc[i].tolist()}")
        
        print()
    except Exception as e:
        print(f'Error reading sheet {sheet}: {e}')
        continue