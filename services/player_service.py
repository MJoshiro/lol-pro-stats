"""
Player service for business logic and API integration.
"""

from typing import List, Optional, Callable, Tuple
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.repository import PlayerRepository
from database.models import Player
from api.leaguepedia import LeaguepediaClient

class PlayerService:
    """
    Service layer for player-related operations.
    Orchestrates between API client and database repository.
    """
    
    def __init__(
        self,
        repository: PlayerRepository = None,
        api_client: LeaguepediaClient = None
    ):
        self.repo = repository or PlayerRepository()
        self.api_client = api_client or LeaguepediaClient()
    
    
    def get_all_players(self, filter_text: str = "") -> List[Player]:
        """
        Get all players with optional search filter.
        
        Args:
            filter_text: Optional text to filter by IGN, role, or team
            
        Returns:
            List of Player objects
        """
        return self.repo.get_all(filter_text)
    
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """Get a single player by ID."""
        return self.repo.get_by_id(player_id)
    
    def get_player_by_ign(self, ign: str) -> Optional[Player]:
        """Get a single player by in-game name."""
        return self.repo.get_by_ign(ign)
    
    def add_player(self, player: Player) -> Tuple[bool, Optional[str]]:
        """
        Add a new player manually.
        
        Args:
            player: Player object to add
            
        Returns:
            Tuple of (success, error_message)
        """
        if not player.ign or not player.ign.strip():
            return False, "Player name cannot be empty"
        
        player.ign = player.ign.strip()
        return self.repo.add(player)
    
    def update_player(self, player: Player) -> Tuple[bool, Optional[str]]:
        """
        Update an existing player.
        
        Args:
            player: Player object with updated data
            
        Returns:
            Tuple of (success, error_message)
        """
        if player.id is None:
            return False, "Player ID is required for update"
        
        if not player.ign or not player.ign.strip():
            return False, "Player name cannot be empty"
        
        player.ign = player.ign.strip()
        return self.repo.update(player)
    
    def delete_player(self, player_id: int) -> bool:
        """
        Delete a player by ID.
        
        Args:
            player_id: ID of the player to delete
            
        Returns:
            True if deletion was successful
        """
        return self.repo.delete(player_id)
    
    def clear_all_players(self) -> int:
        """
        Delete all players from the database.
        
        Returns:
            Number of players deleted
        """
        return self.repo.clear_all()
    
    
    def import_from_leaguepedia(
        self,
        tournament: str = "LCK",
        year: str = "2025",
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Tuple[int, int, Optional[str]]:
        """
        Import player statistics from Leaguepedia.
        
        Args:
            tournament: Tournament filter (e.g., "LCK", "LPL", "Worlds")
            year: Year to import (e.g., "2024", "2025")
            progress_callback: Optional callback(stage, current, total) for progress updates
            
        Returns:
            Tuple of (players_imported, games_processed, error_message)
        """
        try:
            # Stage 1: Fetch game stats
            if progress_callback:
                progress_callback("Fetching data from Leaguepedia...", 0, 0)
            
            def api_progress(count):
                if progress_callback:
                    progress_callback(f"Fetched {count} game records...", count, 0)
            
            game_stats = self.api_client.fetch_player_game_stats(
                tournament_filter=tournament,
                year=year,
                progress_callback=api_progress
            )
            
            total_games = len(game_stats)
            
            if total_games == 0:
                return 0, 0, f"No data found for {tournament} {year}"
            
            # Stage 2: Aggregate player stats
            if progress_callback:
                progress_callback("Aggregating player statistics...", 0, total_games)
            
            aggregated = self.api_client.aggregate_player_stats(game_stats)
            total_players = len(aggregated)
            
            # Stage 3: Save to database
            if progress_callback:
                progress_callback("Saving to database...", 0, total_players)
            
            imported_count = 0
            for i, (name, stats) in enumerate(aggregated.items()):
                player = Player(
                    ign=stats["ign"],
                    role=stats["role"],
                    team=stats["team"],
                    games_played=stats["games_played"],
                    wins=stats["wins"],
                    kills=stats["kills"],
                    deaths=stats["deaths"],
                    assists=stats["assists"],
                    total_gold=stats["total_gold"],
                    total_cs=stats["total_cs"],
                    total_damage=stats["total_damage"],
                    total_minutes=stats["total_minutes"]
                )
                
                success, _ = self.repo.upsert(player)
                if success:
                    imported_count += 1
                
                if progress_callback and (i + 1) % 10 == 0:
                    progress_callback(f"Saved {i + 1}/{total_players} players...", i + 1, total_players)
            
            if progress_callback:
                progress_callback("Import complete!", imported_count, total_players)
            
            return imported_count, total_games, None
            
        except Exception as e:
            error_msg = str(e)
            if "ratelimit" in error_msg.lower():
                return 0, 0, "API rate limit reached. Please wait a few minutes and try again."
            return 0, 0, f"Import failed: {error_msg}"
    
    def test_api_connection(self) -> bool:
        """
        Test if the Leaguepedia API is accessible.
        
        Returns:
            True if connection successful
        """
        return self.api_client.test_connection()
    
    
    def get_available_tournaments(self, year: str = "2025") -> List[str]:
        """
        Get list of available tournaments for a year.
        
        Args:
            year: Year to query
            
        Returns:
            List of tournament names
        """
        try:
            return self.api_client.get_tournaments(year)
        except Exception:
            return []
    
    def create_manual_player(
        self,
        ign: str,
        role: str = "",
        team: str = "",
        games_played: int = 0,
        win_rate: float = 0.0,
        kda: float = 0.0,
        gold_per_min: float = 0.0,
        cs_per_min: float = 0.0,
        dmg_per_min: float = 0.0
    ) -> Tuple[bool, Optional[str]]:
        """
        Create a player with manual stat entry.
        Converts display stats (win_rate, kda, per-min values) to raw totals.
        
        This is for manual data entry where user provides computed averages
        instead of raw totals.
        """
        if games_played <= 0:
            # No games, just create empty player
            player = Player(ign=ign, role=role, team=team)
            return self.add_player(player)
        
        # Estimate reasonable defaults for conversion
        avg_game_minutes = 30.0
        total_minutes = games_played * avg_game_minutes
        
        # Convert rates to totals
        wins = int((win_rate / 100) * games_played)
        
        # Estimate K/D/A from KDA ratio (very rough estimation)
        # Assuming average 5 deaths per game as baseline
        avg_deaths = 5
        total_deaths = avg_deaths * games_played
        total_ka = int(kda * total_deaths)
        total_kills = int(total_ka * 0.4)  # Rough split
        total_assists = total_ka - total_kills
        
        # Convert per-minute to totals
        total_gold = int(gold_per_min * total_minutes)
        total_cs = int(cs_per_min * total_minutes)
        total_damage = int(dmg_per_min * total_minutes)
        
        player = Player(
            ign=ign,
            role=role,
            team=team,
            games_played=games_played,
            wins=wins,
            kills=total_kills,
            deaths=total_deaths,
            assists=total_assists,
            total_gold=total_gold,
            total_cs=total_cs,
            total_damage=total_damage,
            total_minutes=total_minutes
        )
        
        return self.add_player(player)

    def update_manual_player(
        self,
        player_id: int,
        ign: str,
        role: str,
        team: str,
        games_played: int,
        win_rate: float,
        kda: float,
        gold_per_min: float,
        cs_per_min: float,
        dmg_per_min: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Update a player with manual stat entry.
        Recalculates totals from display stats.
        """
        player = self.get_player_by_id(player_id)
        if not player:
            return False, "Player not found"
        
        # Update identity
        player.ign = ign
        player.role = role
        player.team = team
        
        # Update calculated stats only if games > 0
        if games_played > 0:
            player.games_played = games_played
            
            # Estimate reasonable defaults
            avg_game_minutes = 30.0
            player.total_minutes = games_played * avg_game_minutes
            
            # Convert rates to totals
            player.wins = int((win_rate / 100) * games_played)
            
            # Estimate K/D/A
            avg_deaths = 5
            total_deaths = avg_deaths * games_played
            total_ka = int(kda * total_deaths)
            player.kills = int(total_ka * 0.4)
            player.deaths = total_deaths
            player.assists = total_ka - player.kills
            
            # Convert per-minute to totals
            player.total_gold = int(gold_per_min * player.total_minutes)
            player.total_cs = int(cs_per_min * player.total_minutes)
            player.total_damage = int(dmg_per_min * player.total_minutes)
        else:
            # If resetting to 0 games, clear stats? Or keep old?
            # Assuming user wants to reset if they pass 0
            if games_played == 0:
                player.games_played = 0
                player.wins = 0
                player.kills = 0
                player.deaths = 0
                player.assists = 0
                player.total_gold = 0
                player.total_cs = 0
                player.total_damage = 0
                player.total_minutes = 0
            # If negative, do nothing (keep existing stats but update info) - minimal safety
        
        return self.repo.update(player)

if __name__ == "__main__":
    from database.connection import init_db
    
    init_db()
    service = PlayerService()
    
    # Test API connection
    print("Testing API connection...")
    if service.test_api_connection():
        print("✓ API connection successful!")
    else:
        print("✗ API connection failed!")
    
    # Test basic operations
    print("\nCurrent player count:", len(service.get_all_players()))
