import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from utils.constants import *
import json
import asyncio
import logging

logger = logging.getLogger('DraXon_FORGE')

class Hangar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Add context menu command
        self.context_menu = app_commands.ContextMenu(
            name='View Hangar',
            callback=self.view_hangar_context_menu,
        )
        self.bot.tree.add_command(self.context_menu)

    @app_commands.command(name="forge-upload", description=CMD_UPLOAD_DESC)
    @app_commands.describe(file="Your shiplist.json file from XPLOR addon")
    async def forge_upload(self, interaction: discord.Interaction, file: discord.Attachment):
        """Upload hangar data from XPLOR addon JSON export"""
        await interaction.response.defer(ephemeral=True)

        try:
            if not file.filename.endswith('.json'):
                await interaction.followup.send(
                    "Please upload a JSON file.",
                    ephemeral=True
                )
                return

            # Read the JSON file
            json_content = await file.read()
            json_str = json_content.decode('utf-8')

            # Save the hangar data
            success = await self.bot.db.save_hangar_data(interaction.user.id, json_str)
            
            if success:
                embed = discord.Embed(
                    title=f"{ICON_SUCCESS} Hangar Updated",
                    description=MSG_UPLOAD_SUCCESS,
                    color=COLOR_SUCCESS
                )
            else:
                embed = discord.Embed(
                    title=f"{ICON_ERROR} Upload Error",
                    description=MSG_UPLOAD_ERROR,
                    color=COLOR_ERROR
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in forge-upload: {str(e)}")
            embed = discord.Embed(
                title=f"{ICON_ERROR} Error",
                description=f"An error occurred: {str(e)}",
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def display_hangar(self, target_id: int, target_name: str):
        """Helper function to format hangar display"""
        # Get hangar data
        ship_counts = await self.bot.db.get_hangar_data(target_id)
        logger.info(f"Retrieved hangar data for {target_id}: {ship_counts}")
        
        if not ship_counts:
            return None

        # Sort ships by name
        sorted_ships = sorted(ship_counts.items())
        
        # Build the response message
        response = f"The following ships are in {target_name}'s hangar:\n"
        for ship_name, count in sorted_ships:
            response += f"{count}  x  {ship_name}\n"
        
        # Add total count
        total_ships = sum(count for _, count in sorted_ships)
        response += f"\nTotal ships: {total_ships}"
        
        return response

    @app_commands.command(name="forge-hangar", description=CMD_HANGAR_DESC)
    @app_commands.describe(member="View another member's hangar (optional)")
    async def forge_hangar(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """Display hangar contents"""
        await interaction.response.defer()

        try:
            target_id = member.id if member else interaction.user.id
            target_name = member.display_name if member else interaction.user.display_name

            response = await self.display_hangar(target_id, target_name)
            
            if not response:
                await interaction.followup.send(
                    MSG_NO_MEMBER_HANGAR if member else MSG_NO_HANGAR,
                    ephemeral=True
                )
                return

            # Send message and set up deletion after 3 minutes
            message = await interaction.followup.send(response)
            
            # Schedule message deletion
            async def delete_message():
                await asyncio.sleep(180)  # Wait 3 minutes
                try:
                    await message.delete()
                except discord.NotFound:
                    pass  # Message was already deleted
                except Exception as e:
                    logger.error(f"Error deleting message: {e}")
            
            # Start deletion task
            asyncio.create_task(delete_message())

        except Exception as e:
            logger.error(f"Error in forge-hangar: {str(e)}")
            embed = discord.Embed(
                title=f"{ICON_ERROR} Error",
                description=f"An error occurred: {str(e)}",
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def view_hangar_context_menu(self, interaction: discord.Interaction, member: discord.Member):
        """Context menu command for viewing hangar"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            response = await self.display_hangar(member.id, member.display_name)
            
            if not response:
                await interaction.followup.send(MSG_NO_MEMBER_HANGAR, ephemeral=True)
                return

            await interaction.followup.send(response, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in view_hangar_context_menu: {str(e)}")
            embed = discord.Embed(
                title=f"{ICON_ERROR} Error",
                description=f"An error occurred: {str(e)}",
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Hangar(bot))
