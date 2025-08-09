import pandas as pd
from auctionhelper import fetch_dynasty_rankings

def test_fetch_dynasty_rankings():
    # Test that the function returns the expected schema
    df = fetch_dynasty_rankings()
    
    # Check that the dataframe has the expected columns
    expected_columns = ['Rank', 'Player', 'Pos']
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    # Check that Rank is numeric and sorted
    assert pd.api.types.is_numeric_dtype(df['Rank']), "Rank column should be numeric"
    assert df['Rank'].is_monotonic_increasing, "Rank column should be sorted in ascending order"
    
    # Check that there are no NaN values in Rank or Player columns
    assert not df['Rank'].isna().any(), "Rank column should not contain NaN values"
    assert not df['Player'].isna().any(), "Player column should not contain NaN values"
    
    # Check that Pos column contains expected position values
    expected_positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
    unique_positions = df['Pos'].dropna().unique()
    # Check that all positions in the dataframe are from the expected positions
    for pos in unique_positions:
        assert pos in expected_positions, f"Unexpected position: {pos}"
    
    print("All tests passed!")
    print(f"Dataframe shape: {df.shape}")
    print("First 10 rows:")
    print(df.head(10))

if __name__ == '__main__':
    test_fetch_dynasty_rankings()