import discord
from discord.ext import commands
import os
import logging
import asyncpg
import redis.asyncio as redis
from dotenv import load_dotenv
from utils.constants import *
from db.database import Database, init_db, init_redis

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DraXon_FORGE')

# Load environment variables from env directory
load_dotenv('../env/.env')

class DraXonFORGE(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix=commands.when_mentioned_or('!'),
            intents=intents,
            help_command=None,
            description=BOT_DESCRIPTION,
            application_id=os.getenv('APPLICATION_ID')
        )
        
        self.db_pool = None
        self.redis_pool = None
        self.db = None

    async def setup_hook(self):
        """Setup hook for loading cogs and syncing commands"""
        try:
            # Initialize database and Redis connections
            logger.info("Connecting to database and Redis...")
            
            # Build database URL
            db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@" \
                     f"{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/" \
                     f"{os.getenv('DB_NAME')}"
            
            # Build Redis URL with authentication if provided
            redis_user = os.getenv('REDIS_USER')
            redis_password = os.getenv('REDIS_PASSWORD')
            auth_string = ''
            if redis_user and redis_password:
                auth_string = f"{redis_user}:{redis_password}@"
            elif redis_password:
                auth_string = f":{redis_password}@"
                
            redis_url = f"redis://{auth_string}{os.getenv('REDIS_HOST', 'localhost')}:" \
                       f"{os.getenv('REDIS_PORT', '6379')}/" \
                       f"{os.getenv('REDIS_DB', '0')}"
            
            # Initialize connections
            self.db_pool = await init_db(db_url)
            self.redis_pool = await init_redis(redis_url)
            
            # Create database interface
            self.db = Database(self.db_pool, self.redis_pool)
            logger.info("Database and Redis connections established")
            
            # Load all cogs
            logger.info("Loading cogs...")
            await self.load_extension('cogs.system')
            logger.info("System cog loaded")
            
            # Sync commands with Discord
            logger.info("Syncing commands...")
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
            
        except Exception as e:
            logger.error(f"Error during setup: {str(e)}")
            raise

    async def close(self):
        """Cleanup when bot is shutting down"""
        logger.info("Bot shutting down...")
        if self.db:
            await self.db.close()
        await super().close()

    async def on_ready(self):
        """Event handler for when the bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot Version: {APP_VERSION}')
        logger.info(f'Build Date: {BUILD_DATE}')
        
        # Print guilds the bot is in
        guilds = [guild.name for guild in self.guilds]
        logger.info(f"Bot is in {len(guilds)} guild(s): {', '.join(guilds)}")
        logger.info(f"Serving {sum(g.member_count for g in self.guilds)} users")
        
        # Set custom activity
        activity = discord.CustomActivity(name=BOT_DESCRIPTION)
        await self.change_presence(activity=activity, status=discord.Status.online)

def main():
    """Main function to run the bot"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error(MSG_ERROR_TOKEN)
        return
    
    app_id = os.getenv('APPLICATION_ID')
    if not app_id:
        logger.error("Error: APPLICATION_ID environment variable not set")
        return
    
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    if debug:
        logger.info("Debug mode enabled")
    
    bot = DraXonFORGE()
    bot.run(token)

if __name__ == "__main__":
    main()
