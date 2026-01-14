from flask import Blueprint, jsonify
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.stats_service import StatsService

stats_bp = Blueprint('stats', __name__)
stats_service = StatsService()


@stats_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics."""
    stats = stats_service.get_summary_stats()
    
    return jsonify({
        "success": True,
        "data": {
            "total_players": stats["total_players"],
            "avg_win_rate": round(stats["avg_win_rate"], 1),
            "avg_kda": round(stats["avg_kda"], 2),
            "total_games": stats["total_games"]
        }
    })


@stats_bp.route('/stats/roles', methods=['GET'])
def get_role_stats():
    """Get statistics grouped by role."""
    role_stats = stats_service.get_role_averages()
    
    return jsonify({
        "success": True,
        "data": role_stats
    })


@stats_bp.route('/stats/top/winrate', methods=['GET'])
def get_top_by_winrate():
    """Get top players by win rate."""
    players = stats_service.get_top_players_by_win_rate(limit=10)
    
    return jsonify({
        "success": True,
        "data": [{
            "ign": p.ign,
            "role": p.role,
            "team": p.team,
            "win_rate": round(p.win_rate, 1),
            "games_played": p.games_played
        } for p in players]
    })


@stats_bp.route('/stats/top/kda', methods=['GET'])
def get_top_by_kda():
    """Get top players by KDA."""
    players = stats_service.get_top_players_by_kda(limit=10)
    
    return jsonify({
        "success": True,
        "data": [{
            "ign": p.ign,
            "role": p.role,
            "team": p.team,
            "kda": round(p.kda, 2),
            "games_played": p.games_played
        } for p in players]
    })
