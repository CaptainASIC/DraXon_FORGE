import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.constants import *
from utils.database import Database

# Load environment variables from env directory
load_dotenv('../env/.env')

class DraXonMechanic(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix=commands.when_mentioned_or('!'),
            intents=intents,
            help_command=None,
            application_id=os.getenv('APPLICATION_ID')
        )
        
        self.db = Database()

    async def setup_hook(self):
        """Setup hook for loading cogs and syncing commands"""
        try:
            # Connect to database and initialize
            print("Connecting to database...")
            await self.db.connect()
            print("Database connection established")
            
            # Load all cogs
            print("Loading cogs...")
            await self.load_extension('cogs.system')
            print("System cog loaded")
            
            # Sync commands with Discord
            print("Syncing commands...")
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
            
        except Exception as e:
            print(f"Error during setup: {str(e)}")
            raise  # Re-raise to ensure Railway restarts the bot

    async def close(self):
        """Cleanup when bot is shutting down"""
        await self.db.close()
        await super().close()

    async def on_ready(self):
        """Event handler for when the bot is ready"""
        print(f'{self.user} has connected to Discord!')
        print(f'Bot Version: {APP_VERSION}')
        print(f'Build Date: {BUILD_DATE}')
        
        # Print guilds the bot is in
        guilds = [guild.name for guild in self.guilds]
        print(f"Bot is in {len(guilds)} guild(s): {', '.join(guilds)}")
        
        await self.change_presence(activity=discord.Activity(
            type=getattr(discord.ActivityType, BOT_ACTIVITY_TYPE),
            name=BOT_ACTIVITY_NAME
        ))

def main():
    """Main function to run the bot"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print(MSG_ERROR_TOKEN)
        return
    
    app_id = os.getenv('APPLICATION_ID')
    if not app_id:
        print("Error: APPLICATION_ID environment variable not set")
        return
    
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    if debug:
        print("Debug mode enabled")
    
    bot = DraXonMechanic()
    bot.run(token)

if __name__ == "__main__":
    main()
