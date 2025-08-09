import pandas as pd
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import re
import unicodedata

# Add the parent directory to the path so we can import auctionhelper
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import auctionhelper

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

class TestPracticeSquadFilter(unittest.TestCase):
    
    def test_practice_squad_filter(self):
        """
        Test that practice squad players are correctly filtered out from the free agent pool.
        """
        # Create a mock DataFrame for practice squad players
        mock_practice_squad_df = pd.DataFrame({
            'Player': ['Test Player 1', 'Test Player 2'],
            'Status': ['PS', 'PS']
        })
        
        # Create a mock DataFrame for rankings
        mock_rankings_df = pd.DataFrame({
            'RK': [1, 2, 3, 4, 5],
            'PLAYER NAME': ['Test Player 1', 'Test Player 2', 'Test Player 3', 'Test Player 4', 'Test Player 5'],
            'POS': ['QB', 'RB', 'WR', 'TE', 'K']
        })
        # Add the columns that the function expects after processing
        mock_rankings_df['Rank'] = mock_rankings_df['RK']
        mock_rankings_df['Player'] = mock_rankings_df['PLAYER NAME']
        mock_rankings_df['Pos'] = mock_rankings_df['POS']
        
        # Mock the get_practice_squad_players function to return our mock DataFrame
        with patch('auctionhelper.get_practice_squad_players', return_value=mock_practice_squad_df), \
             patch('auctionhelper.fetch_dynasty_rankings', return_value=mock_rankings_df), \
             patch('auctionhelper.pull_roster_players', return_value=(set(), 1000, 20)):  # Empty set for rostered players, 1000 budget, 20 open slots
            
            # Call the function that performs the filtering
            result = auctionhelper.calculate_auction_values()
            
            # Check that the result has the expected structure
            self.assertIn('Player', result.columns)
            self.assertIn('Pos', result.columns)
            self.assertIn('Value', result.columns)
            
            # Check that practice squad players are not in the result
            practice_squad_names = set(mock_practice_squad_df['Player'])
            free_agent_names = set(result['Player'])
            
            # Ensure no practice squad players are in the free agent list
            self.assertEqual(len(practice_squad_names.intersection(free_agent_names)), 0)
            # Ensure some players are still in the free agent list
            self.assertGreater(len(free_agent_names), 0)
    
    def test_practice_squad_players_by_team(self):
        """
        Test that get_practice_squad_players_by_team returns the correct players for specific teams.
        """
        # Test JP Breaks practice squad
        jp_breaks_ps = auctionhelper.get_practice_squad_players_by_team("JP BREAKS")
        expected_jp_breaks = {"JJ McCarthy", "Jermaine Burton", "Malachi Corley"}
        
        # Normalize both lists for comparison
        normalized_actual = {_norm_for_test(name) for name in jp_breaks_ps}
        normalized_expected = {_norm_for_test(name) for name in expected_jp_breaks}
        
        self.assertEqual(normalized_actual, normalized_expected)
        
        # Test Keenan and Kelce practice squad
        keenan_kelce_ps = auctionhelper.get_practice_squad_players_by_team("Keenan and Kelce")
        expected_keenan_kelce = {"Cam Skattebo", "Jack Bech", "Xavier Legette"}
        
        # Normalize both lists for comparison
        normalized_actual_kk = {_norm_for_test(name) for name in keenan_kelce_ps}
        normalized_expected_kk = {_norm_for_test(name) for name in expected_keenan_kelce}
        
        self.assertEqual(normalized_actual_kk, normalized_expected_kk)
    
    def test_name_normalization(self):
        """
        Test that name normalization works correctly for common cases.
        """
        # Test basic normalization
        self.assertEqual(auctionhelper._norm("John Doe"), "john doe")
        
        # Test removing periods
        self.assertEqual(auctionhelper._norm("J.D. Smith"), "jd smith")
        
        # Test removing commas
        self.assertEqual(auctionhelper._norm("Smith, John"), "smith john")
        
        # Test removing suffixes
        self.assertEqual(auctionhelper._norm("John Doe Jr"), "john doe")
        self.assertEqual(auctionhelper._norm("John Doe Sr"), "john doe")
        self.assertEqual(auctionhelper._norm("John Doe II"), "john doe")
        self.assertEqual(auctionhelper._norm("John Doe III"), "john doe")
        self.assertEqual(auctionhelper._norm("John Doe IV"), "john doe")
        
        # Test removing diacritics
        self.assertEqual(auctionhelper._norm("José María"), "jose maria")
        
        # Test collapsing whitespace
        self.assertEqual(auctionhelper._norm("John  Doe"), "john doe")
        self.assertEqual(auctionhelper._norm(" John Doe "), "john doe")

if __name__ == '__main__':
    unittest.main()