import practice_squad_extractor

# Test the function
jp_breaks_players = practice_squad_extractor.get_practice_squad_players_by_team("JP BREAKS")
keenan_kelce_players = practice_squad_extractor.get_practice_squad_players_by_team("Keenan and Kelce")

print("JP BREAKS practice squad players:")
for player in jp_breaks_players:
    print(f"  {player}")

print("\nKeenan and Kelce practice squad players:")
for player in keenan_kelce_players:
    print(f"  {player}")
