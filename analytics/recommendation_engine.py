"""
Cricket Recommendation Engine
Generates data-backed player improvement suggestions
"""

import logging
from typing import Dict, List
from config.settings import AnalyticsConfig

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Generates recommendations based on player performance analysis
    """
    
    def __init__(self):
        self.benchmarks = AnalyticsConfig.PEER_BENCHMARKS
        self.avg_warning = AnalyticsConfig.AVERAGE_WARNING_THRESHOLD
        self.consistency_warning = AnalyticsConfig.CONSISTENCY_WARNING
    
    def generate_batting_recommendations(self, player_data: Dict) -> List[Dict]:
        """
        Generate batting-specific recommendations
        
        Args:
            player_data: Dictionary with player metrics
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check 1: Batting Average
        avg = player_data.get('average', 0)
        benchmark_avg = self.benchmarks['batting_average']
        
        if avg < benchmark_avg * self.avg_warning:
            recommendations.append({
                'category': 'Batting Average',
                'priority': 'HIGH',
                'issue': f'Average ({avg}) significantly below peer group ({benchmark_avg})',
                'recommendation': 'Focus on building innings. Reduce aggressive strokes in first 10 balls.',
                'action': f'Target: Increase average to {benchmark_avg}',
                'gap': round(benchmark_avg - avg, 1)
            })
        
        # Check 2: Strike Rate
        sr = player_data.get('strike_rate', 0)
        benchmark_sr = self.benchmarks['strike_rate']
        
        if sr < benchmark_sr * 0.85:
            recommendations.append({
                'category': 'Strike Rate',
                'priority': 'MEDIUM',
                'issue': f'Strike rate ({sr}) below peer group ({benchmark_sr})',
                'recommendation': 'Improve shot execution. Practice scoring areas (leg side, short balls).',
                'action': f'Target: Increase SR to {benchmark_sr}',
                'gap': round(benchmark_sr - sr, 1)
            })
        
        # Check 3: Consistency
        consistency = player_data.get('consistency', 0)
        
        if consistency > self.consistency_warning:
            recommendations.append({
                'category': 'Consistency',
                'priority': 'HIGH',
                'issue': f'High variance in scores (std dev: {consistency})',
                'recommendation': 'Work on temperament. Focus on specific bowling types that trouble you.',
                'action': f'Target: Reduce variance to <{self.consistency_warning}',
                'gap': round(consistency - self.consistency_warning, 1)
            })
        
        # Check 4: Ducks
        ducks = player_data.get('ducks', 0)
        matches = player_data.get('matches', 1)
        duck_pct = (ducks / matches * 100) if matches > 0 else 0
        
        if duck_pct > 10:
            recommendations.append({
                'category': 'Early Dismissals',
                'priority': 'CRITICAL',
                'issue': f'High rate of dismissals without scoring ({duck_pct:.1f}% ducks)',
                'recommendation': 'Strengthen defensive technique. Practice against new ball for first 10 deliveries.',
                'action': 'Target: Reduce duck percentage to <5%',
                'gap': round(duck_pct - 5, 1)
            })
        
        return recommendations
    
    def generate_bowling_recommendations(self, player_data: Dict) -> List[Dict]:
        """
        Generate bowling-specific recommendations
        """
        recommendations = []
        
        # Check 1: Bowling Average
        avg = player_data.get('average', 0)
        benchmark_avg = self.benchmarks['bowling_average']
        
        if avg > benchmark_avg * 1.15:
            recommendations.append({
                'category': 'Bowling Average',
                'priority': 'HIGH',
                'issue': f'Bowling average ({avg}) above peer group ({benchmark_avg})',
                'recommendation': 'Focus on accuracy and consistency. Develop death bowling variations.',
                'action': f'Target: Reduce average to {benchmark_avg}',
                'gap': round(avg - benchmark_avg, 1)
            })
        
        # Check 2: Economy Rate
        economy = player_data.get('economy', 0)
        benchmark_econ = self.benchmarks['economy_rate']
        
        if economy > benchmark_econ * 1.2:
            recommendations.append({
                'category': 'Economy Rate',
                'priority': 'HIGH',
                'issue': f'Economy rate ({economy}) above peer group ({benchmark_econ})',
                'recommendation': 'Work on tight bowling lines. Develop yorkers and slower balls for death overs.',
                'action': f'Target: Reduce economy to {benchmark_econ}',
                'gap': round(economy - benchmark_econ, 2)
            })
        
        # Check 3: Consistency
        consistency = player_data.get('consistency', 0)
        
        if consistency > 1.5:
            recommendations.append({
                'category': 'Wicket-taking Consistency',
                'priority': 'MEDIUM',
                'issue': f'High variance in wicket-taking (std dev: {consistency})',
                'recommendation': 'Build consistent line and length. Practice specific bowling against different styles.',
                'action': 'Target: Reduce variance to <1.5',
                'gap': round(consistency - 1.5, 2)
            })
        
        return recommendations
    
    def generate_comprehensive_report(self, player_name: str, 
                                     batting_metrics: Dict, 
                                     bowling_metrics: Dict = None) -> Dict:
        """
        Generate complete player improvement report
        """
        all_recommendations = []
        
        # Generate batting recommendations
        batting_recs = self.generate_batting_recommendations(batting_metrics)
        all_recommendations.extend(batting_recs)
        
        # Generate bowling recommendations if applicable
        if bowling_metrics:
            bowling_recs = self.generate_bowling_recommendations(bowling_metrics)
            all_recommendations.extend(bowling_recs)
        
        # Sort by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        all_recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return {
            'player_name': player_name,
            'total_recommendations': len(all_recommendations),
            'recommendations': all_recommendations,
            'action_plan': self._create_action_plan(all_recommendations)
        }
    
    def _create_action_plan(self, recommendations: List[Dict]) -> List[str]:
        """Create actionable plan from recommendations"""
        plan = []
        
        for i, rec in enumerate(recommendations, 1):
            plan.append(f"{i}. [{rec['priority']}] {rec['category']}: {rec['recommendation']}")
        
        return plan


# Test the recommendation engine
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    engine = RecommendationEngine()
    
    print("\n" + "="*70)
    print("CRICKET RECOMMENDATION ENGINE - TEST")
    print("="*70)
    
    # Sample player data (below benchmarks)
    sample_player = {
        'average': 32,  # Below 40 benchmark
        'strike_rate': 48,  # Below 55 benchmark
        'matches': 20,
        'ducks': 3,  # 15% duck rate
        'consistency': 32,  # High variance
        'fifties': 2,
        'centuries': 0
    }
    
    print("\n🏏 STEVE SMITH - PERFORMANCE ANALYSIS")
    print("-"*70)
    print(f"Average: {sample_player['average']} (Benchmark: {engine.benchmarks['batting_average']})")
    print(f"Strike Rate: {sample_player['strike_rate']} (Benchmark: {engine.benchmarks['strike_rate']})")
    print(f"Consistency: {sample_player['consistency']} (Warning: >{engine.consistency_warning})")
    print(f"Duck Rate: {(sample_player['ducks']/sample_player['matches']*100):.1f}%")
    
    # Generate recommendations
    print("\n💡 GENERATED RECOMMENDATIONS:")
    print("-"*70)
    report = engine.generate_comprehensive_report('Steve Smith', sample_player)
    
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"\n{i}. [{rec['priority']}] {rec['category']}")
        print(f"   Issue: {rec['issue']}")
        print(f"   Recommendation: {rec['recommendation']}")
        print(f"   Action: {rec['action']}")
        print(f"   Gap: {rec['gap']}")
    
    # Action plan
    print("\n📋 ACTION PLAN:")
    print("-"*70)
    for action in report['action_plan']:
        print(f"  {action}")
    
    print("\n" + "="*70)
    print(f"✓ TOTAL RECOMMENDATIONS: {report['total_recommendations']}")
    print("="*70 + "\n")