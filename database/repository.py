"""
Repository pattern for database CRUD operations.
"""

from typing import List, Optional
from .connection import get_connection
from .models import Player


class PlayerRepository:
    """
    Repository for Player CRUD operations.
    Handles all database interactions for player data.
    """
    
    def get_all(self, filter_text: str = "") -> List[Player]:
        """
        Get all players, optionally filtered by search text.
        
        Args:
            filter_text: Optional search string to filter by IGN, role, or team
            
        Returns:
            List of Player objects matching the filter
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            
            if filter_text:
                query = """
                    SELECT * FROM players
                    WHERE ign LIKE ? OR role LIKE ? OR team LIKE ?
                    ORDER BY ign COLLATE NOCASE
                """
                pattern = f"%{filter_text}%"
                cursor.execute(query, (pattern, pattern, pattern))
            else:
                cursor.execute("SELECT * FROM players ORDER BY ign COLLATE NOCASE")
            
            rows = cursor.fetchall()
            return [Player.from_row(dict(row)) for row in rows]
    
    def get_by_id(self, player_id: int) -> Optional[Player]:
        """
        Get a player by their database ID.
        
        Args:
            player_id: The player's database ID
            
        Returns:
            Player object if found, None otherwise
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM players WHERE id = ?", (player_id,))
            row = cursor.fetchone()
            
            if row:
                return Player.from_row(dict(row))
            return None
    
    def get_by_ign(self, ign: str) -> Optional[Player]:
        """
        Get a player by their in-game name.
        
        Args:
            ign: The player's in-game name
            
        Returns:
            Player object if found, None otherwise
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM players WHERE ign = ?", (ign,))
            row = cursor.fetchone()
            
            if row:
                return Player.from_row(dict(row))
            return None
    
    def add(self, player: Player) -> tuple[bool, Optional[str]]:
        """
        Add a new player to the database.
        
        Args:
            player: Player object to add
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO players (ign, role, team, games_played, wins, kills, deaths, 
                                        assists, total_gold, total_cs, total_damage, total_minutes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    player.ign, player.role, player.team, player.games_played,
                    player.wins, player.kills, player.deaths, player.assists,
                    player.total_gold, player.total_cs, player.total_damage, player.total_minutes
                ))
                conn.commit()
                player.id = cursor.lastrowid
                return True, None
            except Exception as e:
                return False, str(e)
    
    def update(self, player: Player) -> tuple[bool, Optional[str]]:
        """
        Update an existing player in the database.
        
        Args:
            player: Player object with updated data (must have valid id)
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        if player.id is None:
            return False, "Player ID is required for update"
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    UPDATE players SET 
                        ign = ?, role = ?, team = ?, games_played = ?, wins = ?,
                        kills = ?, deaths = ?, assists = ?, total_gold = ?,
                        total_cs = ?, total_damage = ?, total_minutes = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    player.ign, player.role, player.team, player.games_played,
                    player.wins, player.kills, player.deaths, player.assists,
                    player.total_gold, player.total_cs, player.total_damage,
                    player.total_minutes, player.id
                ))
                conn.commit()
                return True, None
            except Exception as e:
                return False, str(e)
    
    def upsert(self, player: Player) -> tuple[bool, Optional[str]]:
        """
        Insert or update a player based on IGN.
        If a player with the same IGN exists, updates their stats.
        Otherwise, inserts a new player.
        
        Args:
            player: Player object to upsert
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        existing = self.get_by_ign(player.ign)
        
        if existing:
            # Update existing player with new totals
            player.id = existing.id
            return self.update(player)
        else:
            return self.add(player)
    
    def delete(self, player_id: int) -> bool:
        """
        Delete a player from the database.
        
        Args:
            player_id: The ID of the player to delete
            
        Returns:
            True if deletion was successful
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM players WHERE id = ?", (player_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def clear_all(self) -> int:
        """
        Delete all players from the database.
        
        Returns:
            Number of players deleted
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM players")
            conn.commit()
            return cursor.rowcount
    
    def count(self) -> int:
        """Get the total number of players in the database."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM players")
            return cursor.fetchone()[0]
    
    def get_stats(self) -> dict:
        """
        Get aggregate statistics across all players.
        
        Returns:
            Dictionary with total_players, avg_win_rate, avg_kda
        """
        players = self.get_all()
        total = len(players)
        
        if total == 0:
            return {"total_players": 0, "avg_win_rate": 0.0, "avg_kda": 0.0}
        
        avg_win_rate = sum(p.win_rate for p in players) / total
        avg_kda = sum(p.kda for p in players) / total
        
        return {
            "total_players": total,
            "avg_win_rate": avg_win_rate,
            "avg_kda": avg_kda
        }


if __name__ == "__main__":
    # Test the repository
    from connection import init_db
    
    init_db()
    repo = PlayerRepository()
    
    # Test adding a player
    player = Player(ign="TestPlayer", role="Mid", team="TestTeam")
    player.add_game(5, 2, 10, 15000, 250, 25000, 30, True)
    
    success, error = repo.add(player)
    print(f"Add player: {'Success' if success else f'Failed: {error}'}")
    
    # Test fetching
    all_players = repo.get_all()
    print(f"Total players: {len(all_players)}")
    
    # Test stats
    stats = repo.get_stats()
    print(f"Stats: {stats}")
