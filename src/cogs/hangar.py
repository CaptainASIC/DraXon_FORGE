import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List
from utils.constants import *
import json
import asyncio
import logging
from collections import defaultdict

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
        ships = await self.bot.db.get_hangar_data(target_id)
        logger.info(f"Retrieved hangar data for {target_id}: {ships}")
        
        if not ships:
            return None

        # Group ships by manufacturer and name
        ship_groups = defaultdict(list)
        for ship in ships:
            key = f"{ship['manufacturer_name']} {ship['name']}"
            ship_groups[key].append(ship)

        # Sort manufacturers and ships
        sorted_manufacturers = sorted(set(ship['manufacturer_name'] for ship in ships))
        
        # Build the response message
        response = [f"The following ships are in {target_name}'s hangar:\n"]
        
        for manufacturer in sorted_manufacturers:
            # Get all ships for this manufacturer
            manu_ships = [s for s in ships if s['manufacturer_name'] == manufacturer]
            if manu_ships:
                response.append(f"\n**{manufacturer}**")
                
                # Group and sort ships by base name
                ship_names = sorted(set(s['name'] for s in manu_ships))
                for name in ship_names:
                    # Get all instances of this ship
                    instances = [s for s in manu_ships if s['name'] == name]
                    count = len(instances)
                    
                    # Check if any have custom names
                    custom_names = [s['ship_name'] for s in instances if s['ship_name'] != name]
                    custom_str = f" ({', '.join(custom_names)})" if custom_names else ""
                    
                    # Add LTI and Warbond indicators
                    lti_count = sum(1 for s in instances if s['lti'])
                    wb_count = sum(1 for s in instances if s['warbond'])
                    status = []
                    if lti_count == count:
                        status.append("LTI")
                    elif lti_count > 0:
                        status.append(f"{lti_count} LTI")
                    if wb_count > 0:
                        status.append(f"{wb_count} Warbond")
                    status_str = f" [{', '.join(status)}]" if status else ""
                    
                    response.append(f"• {count} x {name}{status_str}{custom_str}")
        
        # Add total count
        total_ships = len(ships)
        response.append(f"\nTotal ships: {total_ships}")
        
        return "\n".join(response)

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

    @app_commands.command(name="forge-fleet", description=CMD_FLEET_DESC)
    async def forge_fleet(self, interaction: discord.Interaction):
        """Display total fleet counts across all members"""
        await interaction.response.defer()

        try:
            # Get fleet totals
            fleet_data = await self.bot.db.get_fleet_total()
            
            if not fleet_data:
                await interaction.followup.send(MSG_NO_FLEET_DATA, ephemeral=True)
                return

            # Sort manufacturers and ships
            sorted_ships = sorted(fleet_data.items())
            
            # Build the response message
            response = ["Organization Fleet Summary:\n"]
            
            for ship_name, data in sorted_ships:
                count = data['count']
                lti_count = data['lti_count']
                wb_count = data['warbond_count']
                
                # Add status indicators
                status = []
                if lti_count == count:
                    status.append("All LTI")
                elif lti_count > 0:
                    status.append(f"{lti_count} LTI")
                if wb_count > 0:
                    status.append(f"{wb_count} Warbond")
                status_str = f" [{', '.join(status)}]" if status else ""
                
                # Add custom names if any
                custom_str = f" ({data['custom_names']})" if data.get('custom_names') else ""
                
                response.append(f"{count} x {ship_name}{status_str}{custom_str}")
            
            # Add total count
            total_ships = sum(data['count'] for data in fleet_data.values())
            response.append(f"\nTotal fleet size: {total_ships} ships")

            # Send message and set up deletion after 3 minutes
            message = await interaction.followup.send("\n".join(response))
            
            async def delete_message():
                await asyncio.sleep(180)
                try:
                    await message.delete()
                except discord.NotFound:
                    pass
                except Exception as e:
                    logger.error(f"Error deleting message: {e}")
            
            asyncio.create_task(delete_message())

        except Exception as e:
            logger.error(f"Error in forge-fleet: {str(e)}")
            embed = discord.Embed(
                title=f"{ICON_ERROR} Error",
                description=f"An error occurred: {str(e)}",
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="forge-locate", description=CMD_LOCATE_DESC)
    async def forge_locate(self, interaction: discord.Interaction):
        """Locate owners of a specific ship model"""
        try:
            # Get all ship models for autocomplete
            ship_models = await self.bot.db.get_all_ship_models()
            
            if not ship_models:
                await interaction.response.send_message(MSG_NO_FLEET_DATA, ephemeral=True)
                return

            # Create select menu with ship models
            select = discord.ui.Select(
                placeholder="Select a ship model",
                options=[
                    discord.SelectOption(label=model[:100]) # Discord has 100 char limit
                    for model in sorted(ship_models)
                ]
            )

            async def select_callback(select_interaction: discord.Interaction):
                await select_interaction.response.defer()
                
                ship_name = select.values[0]
                owners = await self.bot.db.get_ship_owners(ship_name)
                
                if not owners:
                    await select_interaction.followup.send(
                        f"No owners found for {ship_name}",
                        ephemeral=True
                    )
                    return

                # Get member objects and filter out None (left server)
                members = []
                for owner in owners:
                    member = select_interaction.guild.get_member(owner['user_id'])
                    if member:
                        members.append((member, owner))

                if not members:
                    await select_interaction.followup.send(
                        f"All owners of {ship_name} have left the server",
                        ephemeral=True
                    )
                    return

                # Format response
                response = [f"Members who own {ship_name}:"]
                for member, data in sorted(members, key=lambda x: x[0].display_name.lower()):
                    ship_info = []
                    if data['ship_name'] != ship_name:
                        ship_info.append(f"Named: {data['ship_name']}")
                    if data['lti']:
                        ship_info.append("LTI")
                    if data['warbond']:
                        ship_info.append("Warbond")
                    info_str = f" ({', '.join(ship_info)})" if ship_info else ""
                    response.append(f"• {member.display_name}{info_str}")

                await select_interaction.followup.send("\n".join(response), ephemeral=True)

            select.callback = select_callback
            
            view = discord.ui.View()
            view.add_item(select)
            
            await interaction.response.send_message(
                "Select a ship model to locate:",
                view=view,
                ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error in forge-locate: {str(e)}")
            embed = discord.Embed(
                title=f"{ICON_ERROR} Error",
                description=f"An error occurred: {str(e)}",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

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
