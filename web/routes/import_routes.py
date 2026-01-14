"""
Import API routes for Leaguepedia data.
"""

from flask import Blueprint, jsonify, request
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.player_service import PlayerService

import_bp = Blueprint('import', __name__)


@import_bp.route('/import', methods=['POST'])
def import_from_leaguepedia():
    """
    Import player data from Leaguepedia.
    
    Expected JSON body:
        tournament: Tournament filter (e.g., "LCK", "LPL")
        year: Year to import (e.g., "2025")
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "No data provided"
        }), 400
    
    tournament = data.get('tournament', '').strip()
    year = data.get('year', '').strip()
    
    if not tournament or not year:
        return jsonify({
            "success": False,
            "error": "Tournament and year are required"
        }), 400
    
    try:
        fresh_service = PlayerService()
        
        imported, games, error = fresh_service.import_from_leaguepedia(
            tournament=tournament,
            year=year
        )
        
        if error:
            return jsonify({
                "success": False,
                "error": error
            }), 400
        
        return jsonify({
            "success": True,
            "message": f"Successfully imported {imported} players from {games} game records",
            "data": {
                "players_imported": imported,
                "games_processed": games
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@import_bp.route('/import/test', methods=['GET'])
def test_api_connection():
    """Test connection to Leaguepedia API."""
    try:
        player_service = PlayerService()
        if player_service.test_api_connection():
            return jsonify({
                "success": True,
                "message": "API connection successful"
            })
        else:
            return jsonify({
                "success": False,
                "error": "API connection failed"
            }), 503
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
