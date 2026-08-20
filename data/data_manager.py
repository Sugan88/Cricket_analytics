"""
Data Collection Manager
Orchestrates all data collection operations
"""

import logging
from typing import Dict, List
import time
from datetime import datetime
from config.settings import CricketDataConfig
from data.collectors.cricinfo_scraper import CricinfoCricketScraper

logger = logging.getLogger(__name__)


class CricketDataCollectionManager:
    """
    Manages cricket data collection from all sources
    """
    
    def __init__(self):
        self.scraper = CricinfoCricketScraper()
        self.australian_players = CricketDataConfig.AUSTRALIAN_PLAYERS
        logger.info("Cricket Data Collection Manager initialized")
    
    def collect_australian_team_data(self) -> Dict:
        """
        Collect data for all Australian players
        """
        logger.info("="*60)
        logger.info("STARTING AUSTRALIAN TEAM DATA COLLECTION")
        logger.info("="*60)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'players_collected': 0,
            'players_failed': 0,
            'player_data': {}
        }
        
        total_players = len(self.australian_players)
        
        for index, (player_name, player_id) in enumerate(self.australian_players.items(), 1):
            try:
                print(f"\n[{index}/{total_players}] Collecting data for {player_name}...")
                
                # Fetch profile
                profile = self.scraper.get_player_profile(player_id)
                
                if profile.get('status') == 'success':
                    results['player_data'][player_name] = {
                        'player_id': player_id,
                        'profile': profile,
                        'collected_at': datetime.now().isoformat()
                    }
                    results['players_collected'] += 1
                    print(f"  ✓ Success - {player_name}")
                else:
                    results['players_failed'] += 1
                    print(f"  ✗ Failed - {player_name}")
                
                # Rate limiting (be respectful to Cricinfo)
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error collecting data for {player_name}: {e}")
                results['players_failed'] += 1
        
        # Print summary
        print("\n" + "="*60)
        print("COLLECTION SUMMARY")
        print("="*60)
        print(f"Total Players: {total_players}")
        print(f"Successfully Collected: {results['players_collected']}")
        print(f"Failed: {results['players_failed']}")
        print(f"Success Rate: {(results['players_collected']/total_players*100):.1f}%")
        print("="*60 + "\n")
        
        return results
    
    def get_player_list(self) -> List[str]:
        """Get list of all Australian players"""
        return list(self.australian_players.keys())
    
    def get_countries_to_track(self) -> Dict:
        """Get all countries being tracked"""
        return CricketDataConfig.COUNTRIES


# Main execution
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create manager
    manager = CricketDataCollectionManager()
    
    # Show available players
    print("\n📋 AUSTRALIAN PLAYERS TO TRACK:")
    print("-" * 40)
    for i, player in enumerate(manager.get_player_list(), 1):
        print(f"  {i}. {player}")
    
    print("\n🌍 COUNTRIES TO COMPARE:")
    print("-" * 40)
    for country, code in manager.get_countries_to_track().items():
        print(f"  {code} - {country}")
    
    # Collect data (demo - will collect 2 players to start)
    print("\n🔄 Starting data collection...")
    results = manager.collect_australian_team_data()