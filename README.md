# DraXon Mechanic

A Discord bot for collecting and displaying system specifications.

## Features

- `/system collect`: Opens a modal to input system specifications
- `/system show`: Displays the collected system information

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DraXon_Mechanic.git
cd DraXon_Mechanic
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
   ```bash
   nano env/.env
   ```

5. Initialize the database:
```bash
cd src/utils
python init_db.py
```

6. Run the bot:
```bash
cd src
python bot.py
```

## Database Setup

The bot requires PostgreSQL. Make sure you have PostgreSQL installed and running.

1. Install PostgreSQL:
   - Ubuntu/Debian: `sudo apt install postgresql`
   - Arch Linux: `sudo pacman -S postgresql`
   - macOS: `brew install postgresql`
   - Windows: Download from [PostgreSQL website](https://www.postgresql.org/download/windows/)

2. Create a database user:
```sql
CREATE USER your_db_user WITH PASSWORD 'your_db_password';
```

3. Update env/.env with your database credentials

4. Run the database initialization script:
```bash
python src/utils/init_db.py
```

## Project Structure

```
DraXon_Mechanic/
├── src/
│   ├── cogs/
│   │   └── system.py    # System commands implementation
│   ├── utils/
│   │   ├── constants.py # Constants and configuration
│   │   ├── database.py  # Database interface
│   │   └── init_db.py   # Database initialization
│   └── bot.py          # Main bot implementation
├── env/
│   ├── .env           # Your configuration
│   └── .env.example   # Example configuration
├── requirements.txt   # Project dependencies
└── README.md         # This file
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or issues:
- GitHub Issues: [Create an issue](https://github.com/CaptainASIC/DraXon_Mechanic/issues)
- DraXon Discord: [Join our server](https://discord.gg/bjFZBRhw8Q)

Created by DraXon (DraXon Industries)
