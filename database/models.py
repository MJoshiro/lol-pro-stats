"""
Data models for LoL Pro Player Stats System.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class Player:
    """
    Represents a professional League of Legends player with their statistics.
    
    Stores raw totals to allow accurate computation of averages when new games are added.
    Computed properties (win_rate, kda, etc.) are calculated on-demand from raw data.
    """
    
    # Identity
    ign: str  # In-game name (unique identifier)
    role: str = ""  # Top, Jungle, Mid, ADC, Support
    team: str = ""
    
    # Raw game counts
    games_played: int = 0
    wins: int = 0
    
    # Raw stat totals (accumulated across all games)
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    total_gold: int = 0
    total_cs: int = 0
    total_damage: int = 0
    total_minutes: float = 0.0
    
    # Metadata
    id: Optional[int] = None
    last_updated: Optional[datetime] = None
    
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate as a percentage (0-100)."""
        if self.games_played == 0:
            return 0.0
        return (self.wins / self.games_played) * 100
    
    @property
    def kda(self) -> float:
        """
        Calculate KDA ratio.
        Formula: (Kills + Assists) / Deaths
        If deaths is 0, uses 1 to avoid division by zero (perfect KDA).
        """
        deaths = max(self.deaths, 1)
        return (self.kills + self.assists) / deaths
    
    @property
    def gold_per_min(self) -> float:
        """Calculate average gold earned per minute."""
        if self.total_minutes == 0:
            return 0.0
        return self.total_gold / self.total_minutes
    
    @property
    def cs_per_min(self) -> float:
        """Calculate average creep score per minute."""
        if self.total_minutes == 0:
            return 0.0
        return self.total_cs / self.total_minutes
    
    @property
    def dmg_per_min(self) -> float:
        """Calculate average damage to champions per minute."""
        if self.total_minutes == 0:
            return 0.0
        return self.total_damage / self.total_minutes
    
    @property
    def avg_kills(self) -> float:
        """Calculate average kills per game."""
        if self.games_played == 0:
            return 0.0
        return self.kills / self.games_played
    
    @property
    def avg_deaths(self) -> float:
        """Calculate average deaths per game."""
        if self.games_played == 0:
            return 0.0
        return self.deaths / self.games_played
    
    @property
    def avg_assists(self) -> float:
        """Calculate average assists per game."""
        if self.games_played == 0:
            return 0.0
        return self.assists / self.games_played
    
    
    def add_game(self, kills: int, deaths: int, assists: int, 
                 gold: int, cs: int, damage: int, minutes: float, won: bool) -> None:
        """
        Add stats from a single game to this player's totals.
        
        Args:
            kills: Kills in the game
            deaths: Deaths in the game
            assists: Assists in the game
            gold: Gold earned in the game
            cs: Creep score in the game
            damage: Damage to champions in the game
            minutes: Game duration in minutes
            won: Whether the player won the game
        """
        self.games_played += 1
        self.wins += 1 if won else 0
        self.kills += kills
        self.deaths += deaths
        self.assists += assists
        self.total_gold += gold
        self.total_cs += cs
        self.total_damage += damage
        self.total_minutes += minutes
        self.last_updated = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert player to dictionary for database operations."""
        return {
            "id": self.id,
            "ign": self.ign,
            "role": self.role,
            "team": self.team,
            "games_played": self.games_played,
            "wins": self.wins,
            "kills": self.kills,
            "deaths": self.deaths,
            "assists": self.assists,
            "total_gold": self.total_gold,
            "total_cs": self.total_cs,
            "total_damage": self.total_damage,
            "total_minutes": self.total_minutes,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_row(cls, row: dict) -> "Player":
        """Create a Player instance from a database row."""
        last_updated = None
        if row.get("last_updated"):
            try:
                last_updated = datetime.fromisoformat(row["last_updated"])
            except (ValueError, TypeError):
                pass
        
        return cls(
            id=row.get("id"),
            ign=row.get("ign", ""),
            role=row.get("role", ""),
            team=row.get("team", ""),
            games_played=row.get("games_played", 0),
            wins=row.get("wins", 0),
            kills=row.get("kills", 0),
            deaths=row.get("deaths", 0),
            assists=row.get("assists", 0),
            total_gold=row.get("total_gold", 0),
            total_cs=row.get("total_cs", 0),
            total_damage=row.get("total_damage", 0),
            total_minutes=row.get("total_minutes", 0.0),
            last_updated=last_updated
        )
    
    def __str__(self) -> str:
        return f"{self.ign} ({self.role}) - {self.games_played} games, {self.win_rate:.1f}% WR, {self.kda:.2f} KDA"

if __name__ == "__main__":
    # Test the Player model
    player = Player(ign="Faker", role="Mid", team="T1")
    
    # Simulate adding some games
    player.add_game(kills=5, deaths=2, assists=10, gold=15000, cs=250, damage=25000, minutes=30, won=True)
    player.add_game(kills=3, deaths=1, assists=8, gold=12000, cs=200, damage=20000, minutes=25, won=True)
    player.add_game(kills=2, deaths=4, assists=5, gold=10000, cs=180, damage=15000, minutes=28, won=False)
    
    print(player)
    print(f"  Gold/min: {player.gold_per_min:.1f}")
    print(f"  CS/min: {player.cs_per_min:.2f}")
    print(f"  DMG/min: {player.dmg_per_min:.1f}")
