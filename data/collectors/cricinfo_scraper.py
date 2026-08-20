"""
Cricinfo Data Scraper
Collects cricket player data from Cricinfo
"""

import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CricinfoCricketScraper:
    """
    Scrapes cricket data from ESPN Cricinfo
    Note: Uses web scraping (Cricinfo doesn't have public API)
    """
    
    BASE_URL = "https://www.espncricinfo.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.timeout = 10
    
    def get_player_profile(self, player_id: int) -> Dict:
        """Get player profile information"""
        try:
            url = f"{self.BASE_URL}/ci/content/player/{player_id}.html"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            player_data = {
                'player_id': player_id,
                'fetched_at': datetime.now().isoformat(),
                'status': 'success'
            }
            
            logger.info(f"✓ Fetched profile for player ID {player_id}")
            return player_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Error fetching player profile {player_id}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def test_connection(self) -> bool:
        """Test if Cricinfo is accessible"""
        try:
            response = self.session.get(self.BASE_URL, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Cannot reach Cricinfo: {e}")
            return False


# Test the scraper
if __name__ == "__main__":
    print("Testing Cricinfo Scraper...")
    scraper = CricinfoCricketScraper()
    
    # Test connection
    if scraper.test_connection():
        print("✓ Connected to Cricinfo")
    else:
        print("✗ Cannot connect to Cricinfo")
    
    # Test fetching Steve Smith's profile (player ID: 267192)
    profile = scraper.get_player_profile(267192)
    print(f"✓ Fetched: {profile}")