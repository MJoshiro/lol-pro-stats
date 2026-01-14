"""
Leaguepedia API client for fetching pro player statistics.

Uses the MediaWiki Cargo API to query structured data from lol.fandom.com.
Requires bot password authentication for cargo queries.
"""

import requests
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    API_BASE_URL, API_USER_AGENT, API_REQUEST_DELAY, 
    API_MAX_LIMIT, API_MAX_RETRIES, BOT_USERNAME, BOT_PASSWORD
)


@dataclass
class GameStats:
    """Represents a single game's stats for a player."""
    game_id: str
    player_name: str
    role: str
    team: str
    champion: str
    kills: int
    deaths: int
    assists: int
    gold: int
    cs: int
    damage: int
    won: bool
    game_length_minutes: float


class LeaguepediaClient:
    """
    Client for the Leaguepedia Cargo API.
    
    Provides methods to query player statistics and game data from professional
    League of Legends matches tracked on lol.fandom.com.
    
    Uses bot password authentication as required by Fandom's rate limits.
    """
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": API_USER_AGENT,
            "Accept": "application/json"
        })
        self.last_request_time = 0
        self.is_logged_in = False
    
    def _rate_limit(self) -> None:
        """Enforce rate limiting between API requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < API_REQUEST_DELAY:
            time.sleep(API_REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def login(self) -> bool:
        """
        Log in to the Leaguepedia wiki using bot credentials.
        
        This is required due to Fandom's rate limits on cargo queries.
        
        Returns:
            True if login successful, False otherwise
        """
        if self.is_logged_in:
            return True
        
        try:
            print("Logging in to Leaguepedia...")
            
            # Step 1: Get login token
            self._rate_limit()
            params = {
                "action": "query",
                "meta": "tokens",
                "type": "login",
                "format": "json"
            }
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            login_token = data.get("query", {}).get("tokens", {}).get("logintoken")
            if not login_token:
                print("Failed to get login token")
                return False
            
            # Step 2: Perform login with bot credentials
            self._rate_limit()
            login_data = {
                "action": "login",
                "lgname": BOT_USERNAME,
                "lgpassword": BOT_PASSWORD,
                "lgtoken": login_token,
                "format": "json"
            }
            response = self.session.post(self.base_url, data=login_data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            login_result = result.get("login", {}).get("result")
            
            if login_result == "Success":
                self.is_logged_in = True
                print("[OK] Login successful!")
                return True
            else:
                print(f"Login failed: {result.get('login', {})}")
                return False
                
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def _cargo_query(
        self,
        tables: str,
        fields: str,
        where: str = "",
        join_on: str = "",
        order_by: str = "",
        group_by: str = "",
        limit: int = API_MAX_LIMIT,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cargo query against the Leaguepedia API.
        
        Args:
            tables: Comma-separated table names
            fields: Comma-separated field names to retrieve
            where: SQL WHERE clause conditions
            join_on: JOIN conditions for multiple tables
            order_by: ORDER BY clause
            group_by: GROUP BY clause
            limit: Maximum results to return (max 500)
            offset: Pagination offset
            
        Returns:
            List of result dictionaries
        """
        # Ensure we're logged in first
        if not self.is_logged_in:
            self.login()
        
        params = {
            "action": "cargoquery",
            "format": "json",
            "tables": tables,
            "fields": fields,
            "limit": min(limit, API_MAX_LIMIT),
            "offset": offset
        }
        
        if where:
            params["where"] = where
        if join_on:
            params["join_on"] = join_on
        if order_by:
            params["order_by"] = order_by
        if group_by:
            params["group_by"] = group_by
        
        # Retry logic for rate limits
        for attempt in range(API_MAX_RETRIES):
            try:
                self._rate_limit()
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Check for rate limit error
                if "error" in data:
                    error_code = data["error"].get("code", "")
                    if error_code == "ratelimited":
                        wait_time = 5 * (attempt + 1)  # Exponential backoff
                        print(f"Rate limited, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"API error: {data['error']}")
                        raise Exception(f"API error: {data['error'].get('info', 'Unknown error')}")
                
                # Extract results from Cargo response format
                results = data.get("cargoquery", [])
                return [item.get("title", {}) for item in results]
                
            except requests.exceptions.RequestException as e:
                if attempt < API_MAX_RETRIES - 1:
                    wait_time = 3 * (attempt + 1)
                    print(f"Request failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"API request failed after {API_MAX_RETRIES} attempts: {e}")
                    raise
        
        return []
    
    def _cargo_query_all(
        self,
        tables: str,
        fields: str,
        where: str = "",
        join_on: str = "",
        order_by: str = "",
        group_by: str = "",
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cargo query with automatic pagination to get all results.
        
        Args:
            tables, fields, where, join_on, order_by, group_by: Same as _cargo_query
            progress_callback: Optional function called with current result count
            
        Returns:
            List of all result dictionaries
        """
        all_results = []
        offset = 0
        max_results = 2500  # Cap to avoid rate limiting
        
        while True:
            results = self._cargo_query(
                tables=tables,
                fields=fields,
                where=where,
                join_on=join_on,
                order_by=order_by,
                group_by=group_by,
                limit=API_MAX_LIMIT,
                offset=offset
            )
            
            all_results.extend(results)
            
            if progress_callback:
                progress_callback(len(all_results))
            
            # Stop if no more results or hit max cap
            if len(results) < API_MAX_LIMIT or len(all_results) >= max_results:
                break
            
            offset += API_MAX_LIMIT
        
        return all_results[:max_results]  # Ensure we don't exceed cap
    
    def get_tournaments(self, year: str = "2025") -> List[str]:
        """
        Get list of tournaments for a given year.
        
        Args:
            year: Year to filter tournaments (e.g., "2024", "2025")
            
        Returns:
            List of tournament overview page names
        """
        results = self._cargo_query(
            tables="Tournaments",
            fields="OverviewPage,Name,Region",
            where=f"Year='{year}'",
            order_by="Name",
            limit=100
        )
        
        return [r.get("OverviewPage", "") for r in results if r.get("OverviewPage")]
    
    def fetch_player_game_stats(
        self,
        tournament_filter: str = "",
        year: str = "2025",
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[GameStats]:
        """
        Fetch individual game statistics for players.
        
        Args:
            tournament_filter: Filter by tournament name (e.g., "LCK", "LPL", "Worlds")
            year: Year to filter (e.g., "2024", "2025")
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of GameStats objects for each player-game combination
        """
        # Build WHERE clause with flexible tournament pattern matching
        where_parts = []
        if tournament_filter:
            # Handle special tournament naming patterns
            if tournament_filter.upper() == "LCS" and int(year) >= 2025:
                # LCS was rebranded to LTA (League of Legends Championship Americas) in 2025
                where_parts.append(f"(SP.OverviewPage LIKE '%LTA%{year}%' OR SP.OverviewPage LIKE '%LCS%{year}%' OR SP.OverviewPage LIKE '%Americas%{year}%')")
            elif tournament_filter.upper() == "LCK":
                # LCK tier 1 only - use specific patterns to avoid challengers league
                where_parts.append(f"(SP.OverviewPage LIKE 'LCK/{year}%' OR SP.OverviewPage LIKE 'LCK {year}%' OR SP.OverviewPage LIKE '%LCK%Cup%{year}%')")
            elif tournament_filter.upper() == "LPL":
                # LPL tier 1 only
                where_parts.append(f"(SP.OverviewPage LIKE 'LPL/{year}%' OR SP.OverviewPage LIKE 'LPL {year}%')")
            elif tournament_filter.upper() == "LEC":
                # LEC tier 1 only
                where_parts.append(f"(SP.OverviewPage LIKE 'LEC/{year}%' OR SP.OverviewPage LIKE 'LEC {year}%')")
            elif tournament_filter.upper() == "WORLDS":
                where_parts.append(f"(SP.OverviewPage LIKE '%{year}%Season%World%Championship%' OR SP.OverviewPage LIKE '%World%Championship%{year}%' OR SP.OverviewPage LIKE '%Worlds%{year}%' OR SP.OverviewPage LIKE '%{year}%Worlds%')")
            elif tournament_filter.upper() == "MSI":
                where_parts.append(f"(SP.OverviewPage LIKE '%{year}%Mid%Season%Invitational%' OR SP.OverviewPage LIKE '%MSI%{year}%' OR SP.OverviewPage LIKE '%{year}%MSI%')")
            else:
                where_parts.append(f"(SP.OverviewPage LIKE '%{tournament_filter}%{year}%' OR SP.OverviewPage LIKE '%{tournament_filter}/{year}%')")
        else:
            where_parts.append(f"SP.OverviewPage LIKE '%{year}%'")
        
        # Exclude tier 2 and below leagues (academy, challengers, amateur, etc.)
        # Only for regional leagues, not for international events like Worlds/MSI
        if tournament_filter and tournament_filter.upper() not in ["WORLDS", "MSI"]:
            tier2_exclusions = [
                "SP.OverviewPage NOT LIKE '%Academy%'",
                "SP.OverviewPage NOT LIKE '%Challengers%'",
                "SP.OverviewPage NOT LIKE '%Amateur%'",
                "SP.OverviewPage NOT LIKE '%CL%'",  # LCK CL (Challengers League)
                "SP.OverviewPage NOT LIKE '%LDL%'",  # LPL Development League
                "SP.OverviewPage NOT LIKE '%LTAN%'",  # LTA North (tier 2)
                "SP.OverviewPage NOT LIKE '%LTAS%'",  # LTA South (tier 2)
                "SP.OverviewPage NOT LIKE '%NLC%'",  # Northern League of Legends Championship
                "SP.OverviewPage NOT LIKE '%Prime%League%'",  # EU regional
                "SP.OverviewPage NOT LIKE '%Ultraliga%'",  # Poland regional
                "SP.OverviewPage NOT LIKE '%SuperLiga%'",  # Spain regional
                "SP.OverviewPage NOT LIKE '%LFL%'",  # French league
                "SP.OverviewPage NOT LIKE '%LVP%'",  # Spain league
                "SP.OverviewPage NOT LIKE '%PCS%'",  # Pacific Championship Series
                "SP.OverviewPage NOT LIKE '%VCS%'",  # Vietnam Championship Series
                "SP.OverviewPage NOT LIKE '%LJL%'",  # Japan league
                "SP.OverviewPage NOT LIKE '%LLA%'",  # Latin America league
                "SP.OverviewPage NOT LIKE '%CBLOL%'",  # Brazil league
                "SP.OverviewPage NOT LIKE '%LCO%'",  # Oceania league
                "SP.OverviewPage NOT LIKE '%TCL%'",  # Turkey league
            ]
            where_parts.extend(tier2_exclusions)
        
        where_clause = " AND ".join(where_parts) if where_parts else ""
        
        # Query player stats with game info join
        results = self._cargo_query_all(
            tables="ScoreboardPlayers=SP,ScoreboardGames=SG",
            fields="SP.Link,SP.Role,SP.Team,SP.Champion,SP.Kills,SP.Deaths,SP.Assists,"
                   "SP.Gold,SP.CS,SP.DamageToChampions,SP.PlayerWin,SP.GameId,"
                   "SG.Gamelength_Number",
            where=where_clause,
            join_on="SP.GameId=SG.GameId",
            order_by="SP.DateTime_UTC DESC",
            progress_callback=progress_callback
        )
        
        game_stats = []
        for r in results:
            try:
                # Parse player win status
                player_win = r.get("PlayerWin", "").lower()
                won = player_win in ("yes", "1", "true")
                
                # Parse game length (in minutes)
                game_length = 30.0  # Default
                gl = r.get("Gamelength Number")
                if gl:
                    try:
                        game_length = float(gl)
                    except (ValueError, TypeError):
                        pass
                
                # Parse numeric fields with defaults
                def safe_int(val, default=0):
                    try:
                        return int(val) if val else default
                    except (ValueError, TypeError):
                        return default
                
                stats = GameStats(
                    game_id=r.get("GameId", ""),
                    player_name=r.get("Link", ""),
                    role=r.get("Role", ""),
                    team=r.get("Team", ""),
                    champion=r.get("Champion", ""),
                    kills=safe_int(r.get("Kills")),
                    deaths=safe_int(r.get("Deaths")),
                    assists=safe_int(r.get("Assists")),
                    gold=safe_int(r.get("Gold")),
                    cs=safe_int(r.get("CS")),
                    damage=safe_int(r.get("DamageToChampions")),
                    won=won,
                    game_length_minutes=game_length
                )
                
                if stats.player_name:  # Only add if we have a player name
                    game_stats.append(stats)
                    
            except Exception as e:
                print(f"Error parsing game stats: {e}")
                continue
        
        return game_stats
    
    def aggregate_player_stats(
        self,
        game_stats: List[GameStats]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate individual game stats into per-player totals.
        
        Args:
            game_stats: List of GameStats from individual games
            
        Returns:
            Dictionary mapping player names to aggregated stats
        """
        players = {}
        
        for gs in game_stats:
            name = gs.player_name
            
            if name not in players:
                players[name] = {
                    "ign": name,
                    "role": gs.role,
                    "team": gs.team,
                    "games_played": 0,
                    "wins": 0,
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0,
                    "total_gold": 0,
                    "total_cs": 0,
                    "total_damage": 0,
                    "total_minutes": 0.0
                }
            
            p = players[name]
            p["games_played"] += 1
            p["wins"] += 1 if gs.won else 0
            p["kills"] += gs.kills
            p["deaths"] += gs.deaths
            p["assists"] += gs.assists
            p["total_gold"] += gs.gold
            p["total_cs"] += gs.cs
            p["total_damage"] += gs.damage
            p["total_minutes"] += gs.game_length_minutes
            
            # Update role/team to most recent
            if gs.role:
                p["role"] = gs.role
            if gs.team:
                p["team"] = gs.team
        
        return players
    
    def get_player_info(self, player_name: str) -> Optional[Dict[str, Any]]:
        """
        Get player profile information from the Players table.
        
        Args:
            player_name: The player's in-game name (IGN)
            
        Returns:
            Dictionary with player info or None if not found
        """
        try:
            results = self._cargo_query(
                tables="Players",
                fields="Player,Image,Team,Role,Country,Name,OverviewPage",
                where=f'Player="{player_name}"',
                limit=1
            )
            
            if results:
                player_data = results[0]
                image_filename = player_data.get("Image", "")
                team = player_data.get("Team", "")
                
                # Try multiple methods to get player image
                image_url = None
                
                # Method 1: Use Image field if available
                if image_filename:
                    image_url = self.get_image_url(image_filename)
                
                # Method 2: Search for player image by name pattern
                if not image_url:
                    image_url = self.search_player_image(player_name, team)
                
                return {
                    "player": player_data.get("Player", ""),
                    "real_name": player_data.get("Name", ""),
                    "team": team,
                    "role": player_data.get("Role", ""),
                    "country": player_data.get("Country", ""),
                    "image_url": image_url,
                    "overview_page": player_data.get("OverviewPage", "")
                }
            
            return None
            
        except Exception as e:
            print(f"Error fetching player info: {e}")
            return None
    
    def search_player_image(self, player_name: str, team: str = "") -> Optional[str]:
        """
        Search for a player's image using MediaWiki allimages API.
        
        Searches for images matching patterns like:
        - {Team}_{Player}_2025
        - {Player}_2025
        - {Player}
        
        Uses scoring to prioritize:
        1. Exact team + player name match
        2. Recent images (by year in filename)
        3. Common player photo formats
        
        Args:
            player_name: Player's IGN
            team: Player's team (optional)
            
        Returns:
            URL of the best matching player image or None
        """
        try:
            # Try different search patterns in order of specificity
            prefixes = []
            
            # Pattern 1: Team_Player (most specific) - e.g., "T1_Faker"
            if team:
                # Clean team name (remove special chars that might break search)
                clean_team = team.replace(" ", "_").replace(".", "")
                prefixes.append(f"{clean_team}_{player_name}")
            
            # Pattern 2: Just player name - e.g., "Faker"
            prefixes.append(player_name)
            
            best_image = None
            best_score = -1
            
            for prefix in prefixes:
                self._rate_limit()
                
                # Use aiprefix to find images starting with this prefix
                params = {
                    "action": "query",
                    "list": "allimages",
                    "aiprefix": prefix.replace(" ", "_"),
                    "ailimit": 50,  # Get more results for better matching
                    "aiprop": "url|timestamp",
                    "format": "json"
                }
                
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                images = data.get("query", {}).get("allimages", [])
                
                player_lower = player_name.lower().replace(" ", "_")
                team_lower = team.lower().replace(" ", "_") if team else ""
                
                for img in images:
                    img_name = img.get("name", "").lower()
                    
                    # Must be an image file
                    if not any(img_name.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                        continue
                    
                    # Skip common non-portrait images
                    skip_patterns = [
                        "logo", "icon", "banner", "emote", "allstar", "signature", 
                        "sticker", "split", "trophy", "mvp", "championship", "team",
                        "roster", "group", "celebration", "stage", "interview",
                        "square", "infobox", "tab", "header"
                    ]
                    if any(skip in img_name for skip in skip_patterns):
                        continue
                    
                    # Player name must be in the image name
                    if player_lower not in img_name:
                        continue
                    
                    # Score this image
                    score = 0
                    
                    # Bonus for team match
                    if team_lower and team_lower in img_name:
                        score += 100
                    
                    # Bonus for recent years in filename
                    for year in ["2025", "2024", "2023"]:
                        if year in img_name:
                            score += (int(year) - 2020) * 10  # 2025 = 50pts, 2024 = 40pts, 2023 = 30pts
                            break
                    
                    # Bonus for common player photo patterns
                    if "player" in img_name or "headshot" in img_name:
                        score += 20
                    
                    # Slight penalty for very long filenames (likely composite/group photos)
                    if len(img_name) > 50:
                        score -= 10
                    
                    # Use timestamp as tiebreaker (newer is better)
                    timestamp = img.get("timestamp", "")
                    if timestamp:
                        # Add small score based on timestamp year
                        try:
                            ts_year = int(timestamp[:4])
                            score += (ts_year - 2020) * 2
                        except (ValueError, IndexError):
                            pass
                    
                    if score > best_score:
                        best_score = score
                        best_image = img
            
            if best_image:
                url = best_image.get("url")
                return self._make_scaled_url(url)
            
            # Fallback: Try search API for player name
            return self._search_image_by_title(player_name, team)
            
        except Exception as e:
            print(f"Error searching player image: {e}")
            return None
    
    def _search_image_by_title(self, player_name: str, team: str = "") -> Optional[str]:
        """
        Fallback search using MediaWiki search API.
        """
        try:
            self._rate_limit()
            
            # Search for files containing player name
            search_query = f"{team} {player_name}".strip() if team else player_name
            
            params = {
                "action": "query",
                "list": "search",
                "srsearch": f"File:{search_query}",
                "srnamespace": "6",  # File namespace
                "srlimit": 10,
                "format": "json"
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("query", {}).get("search", [])
            
            if results:
                # Get the first matching file's URL
                file_title = results[0].get("title", "")
                if file_title:
                    return self.get_image_url(file_title.replace("File:", ""))
            
            return None
            
        except Exception as e:
            print(f"Error in search fallback: {e}")
            return None
    
    def get_image_url(self, filename: str) -> Optional[str]:
        """
        Convert an image filename to its full URL using MediaWiki imageinfo API.
        
        Args:
            filename: The image filename (e.g., "Faker.png")
            
        Returns:
            Full URL to the image or None if not found
        """
        if not filename:
            return None
        
        try:
            self._rate_limit()
            
            params = {
                "action": "query",
                "titles": f"File:{filename}",
                "prop": "imageinfo",
                "iiprop": "url",
                "format": "json"
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Parse the response to get the URL
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id != "-1":  # -1 means not found
                    imageinfo = page_data.get("imageinfo", [])
                    if imageinfo:
                        url = imageinfo[0].get("url")
                        return self._make_scaled_url(url)
            
            return None
            
        except Exception as e:
            print(f"Error getting image URL: {e}")
            return None
    
    def _make_scaled_url(self, url: str, width: int = 300) -> str:
        """
        Transform a Fandom image URL to use scaled format for better browser compatibility.
        
        Transforms:
            .../images/a/ab/Image.png/revision/latest?cb=...
        To:
            .../images/a/ab/Image.png/revision/latest/scale-to-width-down/300?cb=...
        
        Args:
            url: Original image URL
            width: Target width in pixels
            
        Returns:
            Scaled image URL
        """
        if not url:
            return url
        
        # Check if it's a Fandom/Wikia URL with /revision/latest
        if "/revision/latest" in url and "/scale-to-width" not in url:
            # Insert scale-to-width-down before the query string
            if "?" in url:
                base, query = url.split("?", 1)
                url = f"{base}/scale-to-width-down/{width}?{query}"
            else:
                url = f"{url}/scale-to-width-down/{width}"
        
        return url
    
    def test_connection(self) -> bool:
        """
        Test if the API connection is working.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # First ensure we're logged in
            if not self.login():
                return False
            
            results = self._cargo_query(
                tables="ScoreboardPlayers",
                fields="Link",
                limit=1
            )
            return True  # If we got here without exception, we're connected
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


if __name__ == "__main__":
    # Test the API client
    print("Testing Leaguepedia API Client...")
    print("=" * 50)
    
    client = LeaguepediaClient()
    
    # Test login
    print("\n1. Testing login...")
    if client.login():
        print("   ✓ Login successful!")
    else:
        print("   ✗ Login failed!")
        exit(1)
    
    # Test connection
    print("\n2. Testing cargo query...")
    if client.test_connection():
        print("   ✓ Connection successful!")
    else:
        print("   ✗ Connection failed!")
        exit(1)
    
    # Test fetching some player stats
    print("\n3. Fetching sample player stats from LCK 2025...")
    
    def progress(count):
        print(f"   Fetched {count} game records...")
    
    game_stats = client.fetch_player_game_stats(
        tournament_filter="LCK",
        year="2025",
        progress_callback=progress
    )
    
    print(f"   ✓ Retrieved {len(game_stats)} game records")
    
    if game_stats:
        # Show first few
        print("\n   Sample data:")
        for gs in game_stats[:3]:
            print(f"   - {gs.player_name} ({gs.role}): {gs.kills}/{gs.deaths}/{gs.assists} on {gs.champion}")
        
        # Aggregate stats
        print("\n4. Aggregating player stats...")
        players = client.aggregate_player_stats(game_stats)
        print(f"   ✓ Aggregated stats for {len(players)} unique players")
        
        # Show top 5 by games
        sorted_players = sorted(players.values(), key=lambda x: x["games_played"], reverse=True)
        print("\n   Top 5 players by games played:")
        for p in sorted_players[:5]:
            wins = p["wins"]
            games = p["games_played"]
            wr = (wins / games * 100) if games > 0 else 0
            print(f"   - {p['ign']} ({p['role']}): {games} games, {wr:.1f}% WR")
    
    print("\n" + "=" * 50)
    print("✓ API client test complete!")
