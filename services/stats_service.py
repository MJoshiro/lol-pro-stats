"""
Statistics service for aggregate computations.
"""

from typing import List, Dict, Any
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.repository import PlayerRepository
from database.models import Player


class StatsService:
    """
    Service for computing aggregate statistics across players.
    """
    
    def __init__(self, repository: PlayerRepository = None):
        self.repo = repository or PlayerRepository()
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for the dashboard.
        
        Returns:
            Dictionary with:
            - total_players: int
            - avg_win_rate: float
            - avg_kda: float
            - total_games: int
        """
        players = self.repo.get_all()
        total = len(players)
        
        if total == 0:
            return {
                "total_players": 0,
                "avg_win_rate": 0.0,
                "avg_kda": 0.0,
                "total_games": 0
            }
        
        total_games = sum(p.games_played for p in players)
        avg_win_rate = sum(p.win_rate for p in players) / total
        avg_kda = sum(p.kda for p in players) / total
        
        return {
            "total_players": total,
            "avg_win_rate": avg_win_rate,
            "avg_kda": avg_kda,
            "total_games": total_games
        }
    
    def get_top_players_by_win_rate(self, limit: int = 10, min_games: int = 5) -> List[Player]:
        """
        Get top players ranked by win rate.
        
        Args:
            limit: Maximum number of players to return
            min_games: Minimum games played to qualify
            
        Returns:
            List of Player objects sorted by win rate
        """
        players = self.repo.get_all()
        qualified = [p for p in players if p.games_played >= min_games]
        sorted_players = sorted(qualified, key=lambda p: p.win_rate, reverse=True)
        return sorted_players[:limit]
    
    def get_top_players_by_kda(self, limit: int = 10, min_games: int = 5) -> List[Player]:
        """
        Get top players ranked by KDA.
        
        Args:
            limit: Maximum number of players to return
            min_games: Minimum games played to qualify
            
        Returns:
            List of Player objects sorted by KDA
        """
        players = self.repo.get_all()
        qualified = [p for p in players if p.games_played >= min_games]
        sorted_players = sorted(qualified, key=lambda p: p.kda, reverse=True)
        return sorted_players[:limit]
    
    def get_role_distribution(self) -> Dict[str, int]:
        """
        Get distribution of players by role.
        
        Returns:
            Dictionary mapping role names to player counts
        """
        players = self.repo.get_all()
        distribution = {}
        
        for p in players:
            role = p.role or "Unknown"
            distribution[role] = distribution.get(role, 0) + 1
        
        return distribution
    
    def get_team_distribution(self) -> Dict[str, int]:
        """
        Get distribution of players by team.
        
        Returns:
            Dictionary mapping team names to player counts
        """
        players = self.repo.get_all()
        distribution = {}
        
        for p in players:
            team = p.team or "Unknown"
            distribution[team] = distribution.get(team, 0) + 1
        
        return distribution
    
    def get_role_averages(self) -> Dict[str, Dict[str, float]]:
        """
        Get average statistics grouped by role.
        
        Returns:
            Dictionary mapping role to average stats
        """
        players = self.repo.get_all()
        role_stats = {}
        
        for p in players:
            role = p.role or "Unknown"
            if role not in role_stats:
                role_stats[role] = {
                    "count": 0,
                    "total_win_rate": 0.0,
                    "total_kda": 0.0,
                    "total_gpm": 0.0,
                    "total_cspm": 0.0,
                    "total_dpm": 0.0
                }
            
            stats = role_stats[role]
            stats["count"] += 1
            stats["total_win_rate"] += p.win_rate
            stats["total_kda"] += p.kda
            stats["total_gpm"] += p.gold_per_min
            stats["total_cspm"] += p.cs_per_min
            stats["total_dpm"] += p.dmg_per_min
        
        averages = {}
        for role, stats in role_stats.items():
            count = stats["count"]
            averages[role] = {
                "player_count": count,
                "avg_win_rate": stats["total_win_rate"] / count,
                "avg_kda": stats["total_kda"] / count,
                "avg_gpm": stats["total_gpm"] / count,
                "avg_cspm": stats["total_cspm"] / count,
                "avg_dpm": stats["total_dpm"] / count
            }
        
        return averages


if __name__ == "__main__":
    from database.connection import init_db
    
    init_db()
    stats_service = StatsService()
    
    print("Summary Stats:", stats_service.get_summary_stats())
    print("Role Distribution:", stats_service.get_role_distribution())
