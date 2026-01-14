# LoL Pro Player Stats System

> **A project made in partial fulfillment of our subject Database Management Systems.**

A desktop application for tracking and analyzing professional League of Legends player statistics with data imported from Leaguepedia.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Framework-Flask-black.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-orange.svg)
![PyWebView](https://img.shields.io/badge/Desktop-PyWebView-purple.svg)

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Application Credentials](#application-credentials)
- [Project Structure](#project-structure)
- [API Integration](#api-integration)
- [Database Schema](#database-schema)
- [Screenshots](#screenshots)

---

## Features

### 🌐 Leaguepedia API Integration
- **Import pro player stats** directly from [Leaguepedia](https://lol.fandom.com)
- Filter by tournament (LCK, LPL, LEC, LCS, Worlds, etc.)
- Filter by year (2024, 2025, etc.)
- Automatic pagination for large datasets
- Bot password authentication for reliable API access
- Rate limit handling with exponential backoff retry

### 📊 Dashboard Statistics
- **Total Players** - Count of all players in the database
- **Average Win Rate** - Mean win rate across all players
- **Average KDA** - Mean KDA ratio across all players
- **Total Games** - Sum of all games played

### 📋 Player Data Table
- Sortable columns (click headers to sort)
- Columns displayed:
  - Player Name (IGN)
  - Role (Top, Jungle, Mid, ADC, Support)
  - Team
  - Games Played
  - Win Rate (%)
  - KDA Ratio
  - Gold per Minute
  - CS per Minute
  - Damage per Minute
- Real-time search/filter functionality
- Double-click to edit a player

### ➕ Player Management (CRUD)
- **Add Player** - Manually add a new player with stats
- **Edit Player** - Modify existing player information
- **Delete Player** - Remove a single player
- **Clear All** - Remove all players from database

### 🔐 Authentication
- Login system to protect access
- Demo credentials provided for easy testing

### 💾 Local Database
- SQLite database for offline data persistence
- Stores raw stat totals for accurate calculations
- Computed stats (KDA, per-minute values) calculated on-demand

---

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Steps

1. **Clone or download** the project to your local machine

2. **Install dependencies**:
   ```bash
   pip install requests
   ```
   
   Note: `tkinter` and `sqlite3` are included with Python by default.

3. **Run the application**:
   ```bash
   cd "path/to/final_project"
   python main.py
   ```

---

## Usage

### Starting the Application
```bash
python main.py
```

### Login
Enter the credentials when prompted (see [Application Credentials](#application-credentials)).

### Importing Data from Leaguepedia
1. Click the **"🌐 Import from Leaguepedia"** button
2. Enter a **Tournament Filter** (e.g., `LCK`, `LPL`, `Worlds`)
3. Enter a **Year** (e.g., `2025`, `2024`)
4. Click **Import**
5. Wait for the import to complete (progress shown in dialog)

### Managing Players
| Action | How To |
|--------|--------|
| Add Player | Click **"+ Add Player"** button |
| Edit Player | Select a player, click **"✎ Edit"** or double-click the row |
| Delete Player | Select a player, click **"🗑️ Delete"** |
| Clear All | Click **"🧹 Clear All"** (requires confirmation) |

### Searching/Filtering
- Type in the search box on the right side
- Filters by player name, role, or team in real-time

### Sorting
- Click any column header to sort by that column
- Click again to reverse sort order

---

## Application Credentials

### App Login
| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin` |

### Leaguepedia Bot (Pre-configured)
The application uses bot credentials to access the Leaguepedia API. These are already configured in `config.py`.

To create your own bot password:
1. Log in to [Leaguepedia](https://lol.fandom.com)
2. Go to [Special:BotPasswords](https://lol.fandom.com/wiki/Special:BotPasswords)
3. Create a bot with "Cargo query" permissions
4. Update `config.py` with your credentials

---

## Project Structure

```
final_project/
├── main.py                    # Application entry point
├── config.py                  # Configuration constants
├── README.md                  # This documentation file
│
├── api/                       # API layer
│   ├── __init__.py
│   └── leaguepedia.py         # Leaguepedia API client
│
├── database/                  # Database layer
│   ├── __init__.py
│   ├── connection.py          # SQLite connection manager
│   ├── models.py              # Player data model
│   └── repository.py          # CRUD operations
│
├── services/                  # Business logic layer
│   ├── __init__.py
│   ├── player_service.py      # Player operations
│   └── stats_service.py       # Statistics calculations
│
├── ui/                        # User interface layer
│   ├── __init__.py
│   ├── login_window.py        # Login dialog
│   ├── player_form.py         # Add/Edit player form
│   └── app.py                 # Main application window
│
└── lol_pro_stats.db           # SQLite database (auto-created)
```

---

## API Integration

### Endpoint
```
https://lol.fandom.com/api.php
```

### Authentication
Uses MediaWiki bot password authentication:
1. Fetches login token via `action=query&meta=tokens&type=login`
2. Authenticates via `action=login` with bot credentials
3. Maintains session cookies for subsequent requests

### Cargo Query
Data is fetched using `action=cargoquery` with these tables:
- **ScoreboardPlayers** - Individual player stats per game
- **ScoreboardGames** - Game metadata (length, winner, etc.)

### Key Fields Retrieved
| Field | Description |
|-------|-------------|
| `Link` | Player name (unique identifier) |
| `Role` | Position played |
| `Team` | Team name |
| `Champion` | Champion played |
| `Kills`, `Deaths`, `Assists` | KDA components |
| `Gold` | Gold earned |
| `CS` | Creep score |
| `DamageToChampions` | Damage dealt |
| `PlayerWin` | Win/Loss status |
| `Gamelength_Number` | Game duration in minutes |

### Rate Limiting
- 0.5 second delay between requests
- Automatic retry with exponential backoff (5s, 10s, 15s)
- Maximum 3 retry attempts

---

## Database Schema

### Players Table
```sql
CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ign TEXT NOT NULL UNIQUE,          -- In-game name
    role TEXT NOT NULL DEFAULT '',     -- Position
    team TEXT DEFAULT '',              -- Team name
    games_played INTEGER DEFAULT 0,    -- Total games
    wins INTEGER DEFAULT 0,            -- Total wins
    kills INTEGER DEFAULT 0,           -- Total kills
    deaths INTEGER DEFAULT 0,          -- Total deaths
    assists INTEGER DEFAULT 0,         -- Total assists
    total_gold INTEGER DEFAULT 0,      -- Total gold earned
    total_cs INTEGER DEFAULT 0,        -- Total creep score
    total_damage INTEGER DEFAULT 0,    -- Total damage dealt
    total_minutes REAL DEFAULT 0,      -- Total game time
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Computed Statistics
Stats are calculated from raw totals:
- **Win Rate** = `(wins / games_played) * 100`
- **KDA** = `(kills + assists) / max(deaths, 1)`
- **Gold/Min** = `total_gold / total_minutes`
- **CS/Min** = `total_cs / total_minutes`
- **DMG/Min** = `total_damage / total_minutes`

---

## Screenshots

*Screenshots will be added here after UI styling is enhanced.*

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| GUI Framework | Tkinter |
| Database | SQLite 3 |
| HTTP Client | Requests |
| API Source | Leaguepedia (lol.fandom.com) |

---

## Future Enhancements

- [ ] Enhanced UI styling with modern design
- [ ] Data visualization (charts/graphs)
- [ ] Export to CSV/Excel
- [ ] Player comparison feature
- [ ] Historical data tracking
- [ ] Multiple tournament management

---

## License

This project is for educational purposes.

---

## Credits

- **Data Source**: [Leaguepedia](https://lol.fandom.com) - League of Legends Esports Wiki
- **API**: MediaWiki Cargo Extension
