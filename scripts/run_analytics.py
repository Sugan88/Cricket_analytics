"""
Main Cricket Analytics Pipeline
Runs complete analysis and generates recommendations
"""

import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our modules
from config.settings import CricketDataConfig, LoggingConfig
from data.data_manager import CricketDataCollectionManager
from analytics.performance_calculator import CricketPerformanceCalculator
from analytics.recommendation_engine import RecommendationEngine


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(text.center(70))
    print("="*70)


def print_section(text):
    """Print formatted section"""
    print("\n" + "-"*70)
    print(text)
    print("-"*70)


def run_cricket_analytics_pipeline():
    """
    Run the complete cricket analytics pipeline
    """
    
    print_header("🏏 CRICKET ANALYTICS PIPELINE v1.0")
    
    start_time = datetime.now()
    
    # Initialize components
    logger.info("Initializing components...")
    data_manager = CricketDataCollectionManager()
    calculator = CricketPerformanceCalculator()
    engine = RecommendationEngine()
    
    # Step 1: Get player list
    print_section("STEP 1: Australian Players to Track")
    players = data_manager.get_player_list()
    print(f"Total players: {len(players)}\n")
    for i, player in enumerate(players, 1):
        print(f"  {i:2}. {player}")
    
    # Step 2: Collect data
    print_section("STEP 2: Collecting Cricket Data")
    print("Fetching player profiles from Cricinfo...")
    results = data_manager.collect_australian_team_data()
    
    # Step 3: Demo analytics with sample data
    print_section("STEP 3: Running Performance Analysis")
    
    # Sample data (realistic cricket stats)
    players_data = {
        'Steve Smith': {
            'runs': [45, 67, 23, 89, 34, 56, 78, 45, 92, 12],
            'balls': [120, 145, 89, 176, 100, 130, 155, 120, 178, 45],
            'role': 'Batsman'
        },
        'Pat Cummins': {
            'wickets': [1, 3, 2, 4, 1, 2, 3, 2, 5, 1],
            'runs_conceded': [35, 42, 28, 51, 32, 38, 45, 34, 58, 25],
            'overs': [10, 10, 8, 10, 10, 10, 10, 10, 10, 8],
            'role': 'Bowler'
        },
        'David Warner': {
            'runs': [78, 56, 45, 92, 34, 67, 89, 45, 76, 28],
            'balls': [130, 120, 100, 150, 90, 140, 160, 110, 145, 85],
            'role': 'Batsman'
        },
        'Nathan Lyon': {
            'wickets': [2, 1, 3, 2, 1, 4, 2, 3, 1, 2],
            'runs_conceded': [42, 35, 48, 40, 32, 55, 38, 45, 28, 40],
            'overs': [10, 8, 10, 10, 10, 10, 10, 10, 10, 10],
            'role': 'Bowler'
        }
    }
    
    all_recommendations = {}
    
    for player_name, data in players_data.items():
        print(f"\n📊 Analyzing {player_name}...")
        
        if data['role'] == 'Batsman':
            # Calculate batting metrics
            metrics = calculator.calculate_batting_metrics(data['runs'], data['balls'])
            form = calculator.calculate_form_score(data['runs'])
            
            print(f"   Average: {metrics['average']}")
            print(f"   Strike Rate: {metrics['strike_rate']}")
            print(f"   Form: {form['form_status']} {form['trend']}")
            
            # Generate recommendations
            report = engine.generate_comprehensive_report(player_name, metrics)
            all_recommendations[player_name] = report
        
        elif data['role'] == 'Bowler':
            # Calculate bowling metrics
            metrics = calculator.calculate_bowling_metrics(
                data['wickets'], data['runs_conceded'], data['overs']
            )
            
            print(f"   Average: {metrics['average']}")
            print(f"   Economy: {metrics['economy']}")
            print(f"   Wickets: {metrics['wickets']}")
            
            # Generate recommendations
            report = engine.generate_comprehensive_report(player_name, metrics)
            all_recommendations[player_name] = report
    
    # Step 4: Display recommendations
    print_section("STEP 4: Player Improvement Recommendations")
    
    for player_name, report in all_recommendations.items():
        print(f"\n🎯 {player_name}")
        
        if report['total_recommendations'] > 0:
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"\n   {i}. [{rec['priority']}] {rec['category']}")
                print(f"      • {rec['recommendation']}")
                print(f"      • Action: {rec['action']}")
        else:
            print("   ✓ No critical improvements needed!")
    
    # Step 5: Summary
    duration = (datetime.now() - start_time).total_seconds()
    
    print_section("STEP 5: Pipeline Summary")
    
    total_recs = sum(r['total_recommendations'] for r in all_recommendations.values())
    
    print(f"\n✓ Players analyzed: {len(players_data)}")
    print(f"✓ Total recommendations: {total_recs}")
    print(f"✓ Average: {total_recs / len(players_data):.1f} recommendations per player")
    print(f"✓ Pipeline completed in: {duration:.2f} seconds")
    
    # Final summary
    print_header("✅ PIPELINE COMPLETED SUCCESSFULLY")
    
    return all_recommendations


if __name__ == "__main__":
    try:
        recommendations = run_cricket_analytics_pipeline()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        sys.exit(1)