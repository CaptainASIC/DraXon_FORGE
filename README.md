# FORGE Bot (Fleet Operations & Resource Guidance Engine)

FORGE is a Discord bot designed for managing system specifications and Star Citizen ship hangars. It provides a reliable system for users to share system information and track their fleet through Discord.

## Features

- System specification collection and management
- Star Citizen ship hangar tracking
- Redis-based caching system
- PostgreSQL database for persistence
- Comprehensive logging system

## Installation

1. Clone the repository:
```bash
git clone https://github.com/CaptainASIC/DraXon_FORGE
cd DraXon_FORGE
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp env/.env.example env/.env
```

5. Edit `env/.env` with your configuration:
```
DISCORD_TOKEN=your_bot_token_here
APPLICATION_ID=your_application_id_here

# PostgreSQL Configuration
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password
```

## Discord Bot Setup

1. Required Permissions:
   - View Channels
   - Send Messages
   - Send Messages in Threads
   - Read Message History
   - Add Reactions
   - Use Slash Commands
   - Manage Roles

2. Permission Integer: `326417516608`

## Project Structure

```
DraXon_FORGE/
├── env/                # Environment variables
├── src/
│   ├── cogs/          # Bot command modules
│   │   ├── system.py  # System commands
│   │   └── hangar.py  # Hangar commands
│   ├── db/            # Database modules
│   │   └── database.py # Database interface
│   ├── utils/         # Utility modules
│   │   ├── constants.py # Configuration constants
│   │   └── init_db.py  # Database initialization
│   └── bot.py         # Main bot file
└── README.md          # Documentation
```

## Commands

### System Management
- `/forge-collect` - Opens a form to input system specifications
- `/forge-show` - Displays your saved system information
- `/forge-show <member>` - View another member's system information
- `/forge-about` - Shows information about using the bot

### Hangar Management
- `/forge-upload` - Upload your hangar data from XPLOR addon JSON export
- `/forge-hangar [member]` - Display your hangar contents or another member's

## Database Schema

The bot uses PostgreSQL for persistent storage and Redis for caching:

### System Information Table
- User system specifications
- Input device information
- User data

### Hangar Ships Table
- User ID
- Ship inventory (stored as JSONB)
- Last update timestamp

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Version History

### v2.1.0 (Current)
- Added Star Citizen ship hangar tracking
- XPLOR addon JSON import support
- Simplified hangar display format
- Enhanced error handling

### v2.0.0
- Initial public release
- System specification collection
- Basic user information management

## License 

This project is licensed under the GNU General Public License v3.0 (GPL-3.0). See the [LICENSE](LICENSE) file for details.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
