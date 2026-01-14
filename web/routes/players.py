from flask import Blueprint, jsonify, request
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.models import Player
from services.player_service import PlayerService

players_bp = Blueprint('players', __name__)
player_service = PlayerService()


def player_to_dict(player: Player) -> dict:
    return {
        "id": player.id,
        "ign": player.ign,
        "role": player.role,
        "team": player.team,
        "games_played": player.games_played,
        "wins": player.wins,
        "win_rate": round(player.win_rate, 1),
        "kda": round(player.kda, 2),
        "gold_per_min": round(player.gold_per_min, 0),
        "cs_per_min": round(player.cs_per_min, 1),
        "dmg_per_min": round(player.dmg_per_min, 0),
        "kills": player.kills,
        "deaths": player.deaths,
        "assists": player.assists
    }

@players_bp.route('/players', methods=['GET', 'POST', 'DELETE'])
def players_handler():
    if request.method == 'DELETE':
        count = player_service.clear_all_players()
        return jsonify({
            "success": True,
            "message": f"Cleared {count} players",
            "count": count
        })
    
    if request.method == 'POST':
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        ign = data.get('ign', '').strip()
        if not ign:
            return jsonify({
                "success": False,
                "error": "Player name is required"
            }), 400
        
        try:
            success, error = player_service.create_manual_player(
                ign=ign,
                role=data.get('role', ''),
                team=data.get('team', ''),
                games_played=int(data.get('games_played', 0)),
                win_rate=float(data.get('win_rate', 0)),
                kda=float(data.get('kda', 0)),
                gold_per_min=float(data.get('gold_per_min', 0)),
                cs_per_min=float(data.get('cs_per_min', 0)),
                dmg_per_min=float(data.get('dmg_per_min', 0))
            )
            
            if success:
                return jsonify({
                    "success": True,
                    "message": f"Player '{ign}' added successfully"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": error
                }), 400
                
        except (ValueError, TypeError) as e:
            return jsonify({
                "success": False,
                "error": f"Invalid data: {str(e)}"
            }), 400
    
    search = request.args.get('search', '').strip()
    players = player_service.get_all_players(search)
    
    return jsonify({
        "success": True,
        "data": [player_to_dict(p) for p in players],
        "count": len(players)
    })


@players_bp.route('/players/<int:player_id>', methods=['GET'])
def get_player(player_id: int):
    """Get a single player by ID."""
    player = player_service.get_player_by_id(player_id)
    
    if not player:
        return jsonify({
            "success": False,
            "error": "Player not found"
        }), 404
    
    return jsonify({
        "success": True,
        "data": player_to_dict(player)
    })


@players_bp.route('/players/<int:player_id>/profile', methods=['GET'])
def get_player_profile(player_id: int):
    
    from api.leaguepedia import LeaguepediaClient
    
    player = player_service.get_player_by_id(player_id)
    
    if not player:
        return jsonify({
            "success": False,
            "error": "Player not found"
        }), 404
    
    leaguepedia = LeaguepediaClient()
    leaguepedia_info = leaguepedia.get_player_info(player.ign)
    
    profile = {
        "id": player.id,
        "ign": player.ign,
        "role": player.role,
        "team": player.team,
        "games_played": player.games_played,
        "wins": player.wins,
        "win_rate": round(player.win_rate, 1),
        
        "kills": player.kills,
        "deaths": player.deaths,
        "assists": player.assists,
        "kda": round(player.kda, 2),
        "total_gold": player.total_gold,
        "total_cs": player.total_cs,
        "total_damage": player.total_damage,
        "total_minutes": round(player.total_minutes, 1),
        
        "gold_per_min": round(player.gold_per_min, 0),
        "cs_per_min": round(player.cs_per_min, 2),
        "dmg_per_min": round(player.dmg_per_min, 0),
        
        "avg_kills": round(player.kills / max(player.games_played, 1), 1),
        "avg_deaths": round(player.deaths / max(player.games_played, 1), 1),
        "avg_assists": round(player.assists / max(player.games_played, 1), 1),
        
        "image_url": leaguepedia_info.get("image_url") if leaguepedia_info else None,
        "real_name": leaguepedia_info.get("real_name", "") if leaguepedia_info else "",
        "country": leaguepedia_info.get("country", "") if leaguepedia_info else "",
        
        "chart_data": {
            "labels": ["Win Rate", "KDA", "Gold/Min", "CS/Min", "DMG/Min"],
            "values": [
                min(player.win_rate, 100),
                min(player.kda * 10, 100),
                min(player.gold_per_min / 5, 100),
                min(player.cs_per_min * 10, 100),
                min(player.dmg_per_min / 10, 100)
            ]
        }
    }
    
    return jsonify({
        "success": True,
        "data": profile
    })



@players_bp.route('/players/<int:player_id>', methods=['PUT'])
def update_player(player_id: int):
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "No data provided"
        }), 400
    
    player = player_service.get_player_by_id(player_id)
    if not player:
        return jsonify({
            "success": False,
            "error": "Player not found"
        }), 404
    
    ign = data.get('ign', '').strip()
    if not ign:
        return jsonify({
            "success": False,
            "error": "Player name is required"
        }), 400
    
    success, error = player_service.update_manual_player(
        player_id=player_id,
        ign=ign,
        role=data.get('role', ''),
        team=data.get('team', ''),
        games_played=int(data.get('games_played', 0)),
        win_rate=float(data.get('win_rate', 0)),
        kda=float(data.get('kda', 0)),
        gold_per_min=float(data.get('gold_per_min', 0)),
        cs_per_min=float(data.get('cs_per_min', 0)),
        dmg_per_min=float(data.get('dmg_per_min', 0))
    )
    
    if success:
        return jsonify({
            "success": True,
            "message": f"Player '{ign}' updated successfully"
        })
    else:
        return jsonify({
            "success": False,
            "error": error
        }), 400


@players_bp.route('/players/<int:player_id>', methods=['DELETE'])
def delete_player(player_id: int):
    """Delete a player by ID."""
    player = player_service.get_player_by_id(player_id)
    
    if not player:
        return jsonify({
            "success": False,
            "error": "Player not found"
        }), 404
    
    ign = player.ign
    player_service.delete_player(player_id)
    
    return jsonify({
        "success": True,
        "message": f"Player '{ign}' deleted successfully"
    })


@players_bp.route('/players/clear', methods=['DELETE'])
def clear_all_players():
    """Delete all players."""
    count = player_service.clear_all_players()
    
    return jsonify({
        "success": True,
        "message": f"Cleared {count} players",
        "count": count
    })


@players_bp.route('/clear-all', methods=['POST'])
def clear_all_endpoint():
    """Clear all players - dedicated endpoint."""
    count = player_service.clear_all_players()
    return jsonify({
        "success": True,
        "message": f"Cleared {count} players",
        "count": count
    })
