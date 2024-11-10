# DraXon FORGE

A Discord bot for collecting and displaying system specifications.

## Features

- `/forge-collect`: Opens a modal to input system specifications
- `/forge-show [member]`: Displays system information (yours or another member's)
- `/forge-about`: Learn how to use the bot
- Redis caching for improved performance
- PostgreSQL database for persistent storage

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DraXon_FORGE.git
cd DraXon_FORGE
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Discord bot:
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to the "Bot" section and create a bot
   - Copy the bot token and application ID

4. Configure environment variables:
   - Copy `.env.example` to `.env` in the env directory
   ```bash
   cp env/.env.example env/.env
   ```
   - Edit `.env` and set your configuration:
     * Discord bot token
     * Application ID
     * Database credentials
     * Redis configuration
   ```bash
   nano env/.env
   ```

## Database Setup

The bot requires both PostgreSQL and Redis. Here's how to set them up:

### PostgreSQL Setup

1. Install PostgreSQL:
   - Ubuntu/Debian: `sudo apt install postgresql`
   - Arch Linux: `sudo pacman -S postgresql`
   - macOS: `brew install postgresql`
   - Windows: Download from [PostgreSQL website](https://www.postgresql.org/download/windows/)

2. Create a database user:
```sql
CREATE USER your_db_user WITH PASSWORD 'your_db_password';
```

3. Create the database:
```sql
CREATE DATABASE your_db_name OWNER your_db_user;
```

### Redis Setup

1. Install Redis:
   - Ubuntu/Debian: `sudo apt install redis-server`
   - Arch Linux: `sudo pacman -S redis`
   - macOS: `brew install redis`
   - Windows: Download from [Redis website](https://redis.io/download)

2. Start Redis service:
   - Linux: `sudo systemctl start redis`
   - macOS: `brew services start redis`
   - Windows: Start Redis server from installation

3. Test Redis connection:
```bash
redis-cli ping
```
Should return "PONG"

### Environment Configuration

Update env/.env with your service credentials:

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_token
APPLICATION_ID=your_application_id

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
```

4. Initialize the database:
```bash
python src/utils/init_db.py
```

5. Run the bot:
```bash
cd src
python bot.py
```

## Project Structure

```
DraXon_FORGE/
├── src/
│   ├── cogs/
│   │   └── system.py    # Command implementations
│   ├── db/
│   │   └── database.py  # Database and Redis interface
│   ├── utils/
│   │   ├── constants.py # Constants and configuration
│   │   └── init_db.py   # Database initialization
│   └── bot.py          # Main bot implementation
├── env/
│   ├── .env           # Your configuration
│   └── .env.example   # Example configuration
├── requirements.txt   # Project dependencies
└── README.md         # This file
```

## Commands

All commands provide private responses visible only to the user who executed them.

- `/forge-collect`: Opens a form to input your system specifications
- `/forge-show`: Displays your saved system information
- `/forge-show <member>`: View another member's system information
- `/forge-about`: Shows information about how to use the bot

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or issues:
- GitHub Issues: [Create an issue](https://github.com/CaptainASIC/DraXon_FORGE/issues)
- DraXon Discord: [Join our server](https://discord.gg/bjFZBRhw8Q)

Created by DraXon (DraXon Industries)
