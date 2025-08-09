import practice_squad_extractor
import re
import pandas as pd

def _norm_for_test(s: str) -> str:
    """
    Normalize player names for comparison in tests.
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

# Test the function
jp_breaks_players = practice_squad_extractor.get_practice_squad_players_by_team("JP BREAKS")
keenan_kelce_players = practice_squad_extractor.get_practice_squad_players_by_team("Keenan and Kelce")

expected_jp_breaks = {"JJ McCarthy", "Jermaine Burton", "Malachi Corley"}
expected_keenan_kelce = {"Cam Skattebo", "Jack Bech", "Xavier Legette"}

print("JP BREAKS actual players:")
for player in jp_breaks_players:
    print(f"  '{player}' -> '{_norm_for_test(player)}'")

print("\nJP BREAKS expected players:")
for player in expected_jp_breaks:
    print(f"  '{player}' -> '{_norm_for_test(player)}'")

print("\nKeenan and Kelce actual players:")
for player in keenan_kelce_players:
    print(f"  '{player}' -> '{_norm_for_test(player)}'")

print("\nKeenan and Kelce expected players:")
for player in expected_keenan_kelce:
    print(f"  '{player}' -> '{_norm_for_test(player)}'")

# Check normalized sets
normalized_actual = {_norm_for_test(name) for name in keenan_kelce_players}
normalized_expected = {_norm_for_test(name) for name in expected_keenan_kelce}

print(f"\nNormalized actual: {normalized_actual}")
print(f"Normalized expected: {normalized_expected}")
print(f"Equal: {normalized_actual == normalized_expected}")