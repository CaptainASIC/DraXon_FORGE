import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from utils.constants import *
import json

class Hangar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="forge-upload", description=CMD_UPLOAD_DESC)
    async def forge_upload(self, interaction: discord.Interaction):
        """Upload hangar data from XPLOR addon JSON export"""
        await interaction.response.send_message(
            "Please upload your shiplist.json file from XPLOR addon",
            ephemeral=True
        )

        def check(message):
            return (message.author.id == interaction.user.id and 
                   message.channel.id == interaction.channel_id and 
                   message.attachments)

        try:
            # Wait for file upload
            message = await self.bot.wait_for('message', timeout=60.0, check=check)
            
            if not message.attachments[0].filename.endswith('.json'):
                await interaction.followup.send(
                    "Please upload a JSON file.",
                    ephemeral=True
                )
                return

            # Read the JSON file
            json_content = await message.attachments[0].read()
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
            
            # Delete the file upload message for cleanliness
            try:
                await message.delete()
            except:
                pass

        except TimeoutError:
            await interaction.followup.send(
                "Upload timed out. Please try again.",
                ephemeral=True
            )
        except Exception as e:
            embed = discord.Embed(
                title=f"{ICON_ERROR} Error",
                description=f"An error occurred: {str(e)}",
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="forge-hangar", description=CMD_HANGAR_DESC)
    @app_commands.describe(member="View another member's hangar (optional)")
    async def forge_hangar(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """Display hangar contents"""
        await interaction.response.defer()

        try:
            target_id = member.id if member else interaction.user.id
            target_name = member.display_name if member else interaction.user.display_name

            # Get hangar data
            hangar_data = await self.bot.db.get_hangar_data(target_id)
            
            if not hangar_data:
                await interaction.followup.send(
                    MSG_NO_MEMBER_HANGAR if member else MSG_NO_HANGAR,
                    ephemeral=True
                )
                return

            # Sort ships by name
            sorted_ships = sorted(hangar_data.items())
            
            # Build the response message
            response = f"The following ships are in {target_name}'s hangar:\n"
            for ship_name, count in sorted_ships:
                response += f"{count}  x  {ship_name}\n"
            
            # Add total count
            total_ships = sum(count for _, count in sorted_ships)
            response += f"\nTotal ships: {total_ships}"

            await interaction.followup.send(response)

        except Exception as e:
            embed = discord.Embed(
                title=f"{ICON_ERROR} Error",
                description=f"An error occurred: {str(e)}",
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Hangar(bot))
