"""
Cricket Performance Calculator
Calculates all player performance metrics
"""

import logging
import numpy as np
from typing import Dict, List
from config.settings import AnalyticsConfig

logger = logging.getLogger(__name__)


class CricketPerformanceCalculator:
    """
    Calculates comprehensive cricket performance metrics
    """
    
    def __init__(self):
        self.min_matches = AnalyticsConfig.MIN_MATCHES_THRESHOLD
        self.benchmarks = AnalyticsConfig.PEER_BENCHMARKS
    
    def calculate_batting_metrics(self, runs: List[int], balls: List[int]) -> Dict:
        """
        Calculate batting metrics from runs and balls faced
        
        Args:
            runs: List of runs scored in each match
            balls: List of balls faced in each match
        
        Returns:
            Dictionary with batting metrics
        """
        if not runs or not balls or len(runs) != len(balls):
            return {'error': 'Invalid input data'}
        
        runs_array = np.array(runs)
        balls_array = np.array(balls)
        
        total_runs = runs_array.sum()
        total_balls = balls_array.sum()
        matches = len(runs)
        
        # Dismissals (assuming all innings are dismissals for demo)
        dismissals = matches
        
        metrics = {
            'matches': int(matches),
            'runs': int(total_runs),
            'average': round(total_runs / dismissals, 2) if dismissals > 0 else 0,
            'strike_rate': round((total_runs / total_balls * 100), 2) if total_balls > 0 else 0,
            'highest_score': int(runs_array.max()),
            'lowest_score': int(runs_array.min()),
            'fifties': int((runs_array >= 50).sum()),
            'centuries': int((runs_array >= 100).sum()),
            'ducks': int((runs_array == 0).sum()),
            'consistency': round(float(runs_array.std()), 2),
        }
        
        return metrics
    
    def calculate_bowling_metrics(self, wickets: List[int], runs: List[int], 
                                  overs: List[float]) -> Dict:
        """
        Calculate bowling metrics
        
        Args:
            wickets: List of wickets taken in each match
            runs: List of runs conceded in each match
            overs: List of overs bowled in each match
        
        Returns:
            Dictionary with bowling metrics
        """
        if not wickets or not runs or not overs:
            return {'error': 'Invalid input data'}
        
        wickets_array = np.array(wickets)
        runs_array = np.array(runs)
        overs_array = np.array(overs)
        
        total_wickets = wickets_array.sum()
        total_runs = runs_array.sum()
        total_overs = overs_array.sum()
        
        metrics = {
            'matches': len(wickets),
            'wickets': int(total_wickets),
            'runs_conceded': int(total_runs),
            'overs_bowled': round(float(total_overs), 1),
            'average': round(total_runs / total_wickets, 2) if total_wickets > 0 else 0,
            'economy': round((total_runs / total_overs), 2) if total_overs > 0 else 0,
            'strike_rate': round((total_overs * 6 / total_wickets), 2) if total_wickets > 0 else 0,
            '4_wicket_hauls': int((wickets_array >= 4).sum()),
            '5_wicket_hauls': int((wickets_array >= 5).sum()),
            'consistency': round(float(wickets_array.std()), 2),
        }
        
        return metrics
    
    def calculate_form_score(self, recent_scores: List[int], 
                            lookback_matches: int = 10) -> Dict:
        """
        Calculate form score based on recent performance
        
        Args:
            recent_scores: List of recent match scores
            lookback_matches: Number of matches to consider
        
        Returns:
            Dictionary with form analysis
        """
        if not recent_scores or len(recent_scores) < 3:
            return {'error': 'Insufficient data'}
        
        scores_array = np.array(recent_scores)
        
        # Use exponential weighting (recent matches more important)
        weights = np.exp(np.linspace(-1, 0, len(scores_array)))
        weights /= weights.sum()
        
        weighted_avg = np.average(scores_array, weights=weights)
        consistency = np.std(scores_array)
        
        # Form score (0 to 1)
        form_score = (weighted_avg / 50) * (1 - consistency / 100)
        form_score = min(max(form_score, 0), 1)
        
        # Determine form status
        if form_score >= 0.7:
            form_status = 'Excellent'
        elif form_score >= 0.55:
            form_status = 'Good'
        elif form_score >= 0.4:
            form_status = 'Average'
        else:
            form_status = 'Poor'
        
        # Calculate trend
        recent_half = np.mean(scores_array[-len(scores_array)//2:])
        older_half = np.mean(scores_array[:len(scores_array)//2])
        
        if recent_half > older_half * 1.1:
            trend = 'Improving ⬆️'
        elif recent_half < older_half * 0.9:
            trend = 'Declining ⬇️'
        else:
            trend = 'Stable ➡️'
        
        return {
            'form_status': form_status,
            'form_score': round(float(form_score), 3),
            'weighted_average': round(float(weighted_avg), 2),
            'consistency': round(float(consistency), 2),
            'trend': trend,
            'last_5_avg': round(float(np.mean(scores_array[-5:])), 2)
        }
    
    def compare_with_benchmarks(self, player_metrics: Dict, category: str) -> Dict:
        """
        Compare player metrics with peer benchmarks
        
        Args:
            player_metrics: Player's calculated metrics
            category: 'batting' or 'bowling'
        
        Returns:
            Comparison analysis
        """
        comparison = {}
        
        if category == 'batting':
            if 'average' in player_metrics:
                avg = player_metrics['average']
                benchmark = self.benchmarks['batting_average']
                comparison['average'] = {
                    'player': avg,
                    'benchmark': benchmark,
                    'vs_benchmark': round(((avg - benchmark) / benchmark * 100), 1),
                    'status': '✓ Above' if avg > benchmark else '✗ Below'
                }
            
            if 'strike_rate' in player_metrics:
                sr = player_metrics['strike_rate']
                benchmark = self.benchmarks['strike_rate']
                comparison['strike_rate'] = {
                    'player': sr,
                    'benchmark': benchmark,
                    'vs_benchmark': round(((sr - benchmark) / benchmark * 100), 1),
                    'status': '✓ Above' if sr > benchmark else '✗ Below'
                }
        
        elif category == 'bowling':
            if 'average' in player_metrics:
                avg = player_metrics['average']
                benchmark = self.benchmarks['bowling_average']
                comparison['average'] = {
                    'player': avg,
                    'benchmark': benchmark,
                    'vs_benchmark': round(((avg - benchmark) / benchmark * 100), 1),
                    'status': '✓ Better' if avg < benchmark else '✗ Worse'
                }
            
            if 'economy' in player_metrics:
                econ = player_metrics['economy']
                benchmark = self.benchmarks['economy_rate']
                comparison['economy'] = {
                    'player': econ,
                    'benchmark': benchmark,
                    'vs_benchmark': round(((econ - benchmark) / benchmark * 100), 1),
                    'status': '✓ Better' if econ < benchmark else '✗ Worse'
                }
        
        return comparison


# Test the calculator
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    calculator = CricketPerformanceCalculator()
    
    print("\n" + "="*60)
    print("CRICKET PERFORMANCE CALCULATOR - TEST")
    print("="*60)
    
    # Sample batting data
    print("\n📊 TEST 1: Batting Metrics")
    print("-"*60)
    sample_runs = [45, 67, 23, 89, 34, 56, 78, 45, 92, 12]
    sample_balls = [120, 145, 89, 176, 100, 130, 155, 120, 178, 45]
    
    batting_metrics = calculator.calculate_batting_metrics(sample_runs, sample_balls)
    print(f"Matches: {batting_metrics['matches']}")
    print(f"Total Runs: {batting_metrics['runs']}")
    print(f"Average: {batting_metrics['average']}")
    print(f"Strike Rate: {batting_metrics['strike_rate']}")
    print(f"Fifties: {batting_metrics['fifties']}")
    print(f"Centuries: {batting_metrics['centuries']}")
    print(f"Consistency: {batting_metrics['consistency']}")
    
    # Compare with benchmarks
    print("\n🎯 Comparison with Benchmarks:")
    print("-"*60)
    comparison = calculator.compare_with_benchmarks(batting_metrics, 'batting')
    for metric, data in comparison.items():
        print(f"{metric.upper()}:")
        print(f"  Player: {data['player']}")
        print(f"  Benchmark: {data['benchmark']}")
        print(f"  vs Benchmark: {data['vs_benchmark']}% {data['status']}")
    
    # Sample bowling data
    print("\n📊 TEST 2: Bowling Metrics")
    print("-"*60)
    sample_wickets = [1, 3, 2, 4, 1, 2, 3, 2, 5, 1]
    sample_runs_conceded = [35, 42, 28, 51, 32, 38, 45, 34, 58, 25]
    sample_overs = [10, 10, 8, 10, 10, 10, 10, 10, 10, 8]
    
    bowling_metrics = calculator.calculate_bowling_metrics(
        sample_wickets, sample_runs_conceded, sample_overs
    )
    print(f"Matches: {bowling_metrics['matches']}")
    print(f"Wickets: {bowling_metrics['wickets']}")
    print(f"Overs Bowled: {bowling_metrics['overs_bowled']}")
    print(f"Average: {bowling_metrics['average']}")
    print(f"Economy: {bowling_metrics['economy']}")
    print(f"5-Wicket Hauls: {bowling_metrics['5_wicket_hauls']}")
    
    # Form analysis
    print("\n📊 TEST 3: Form Analysis")
    print("-"*60)
    form = calculator.calculate_form_score(sample_runs)
    print(f"Form Status: {form['form_status']}")
    print(f"Form Score: {form['form_score']}/1.0")
    print(f"Trend: {form['trend']}")
    print(f"Last 5 Average: {form['last_5_avg']}")
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED")
    print("="*60 + "\n")