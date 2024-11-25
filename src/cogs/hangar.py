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

def format_ship_status(lti: bool, warbond: bool) -> str:
    """Format ship status indicators"""
    status = []
    if lti:
        status.append("LTI")
    if warbond:
        status.append("WB")
    return f"[{'+'.join(status)}]" if status else ""

def format_custom_name(ship_name: str, base_name: str) -> str:
    """Format custom ship name"""
    return f'"{ship_name}"' if ship_name != base_name else ""

class Hangar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Add context menu command
        self.context_menu = app_commands.ContextMenu(
            name='View Hangar',
            callback=self.view_hangar_context_menu,
        )
        self.bot.tree.add_command(self.context_menu)

    @app_commands.command(name="forge-debug", description="Debug database state")
    @app_commands.default_permissions(administrator=True)
    async def forge_debug(self, interaction: discord.Interaction):
        """Debug command to check database state"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with self.bot.db.pool.acquire() as conn:
                ship_count = await conn.fetchval('SELECT COUNT(*) FROM hangar_ships')
                user_count = await conn.fetchval('SELECT COUNT(DISTINCT user_id) FROM hangar_ships')
                manu_count = await conn.fetchval('SELECT COUNT(DISTINCT manufacturer_name) FROM hangar_ships')
                sample = await conn.fetch('SELECT * FROM hangar_ships LIMIT 1')
                
                debug_info = [
                    "```md",
                    "# Database Debug Info",
                    "",
                    f"* Total ships: {ship_count}",
                    f"* Unique users: {user_count}",
                    f"* Manufacturers: {manu_count}",
                ]
                
                if sample:
                    ship = dict(sample[0])
                    debug_info.extend([
                        "",
                        "# Sample Ship Data",
                        f"* Code: {ship['ship_code']}",
                        f"* Name: {ship['name']}",
                        f"* Manufacturer: {ship['manufacturer_name']}",
                        f"* User ID: {ship['user_id']}"
                    ])
                else:
                    debug_info.append("\n[No ships found in database]")
                
                debug_info.append("```")
                await interaction.followup.send("\n".join(debug_info), ephemeral=True)
        except Exception as e:
            logger.error(f"Error in forge-debug: {str(e)}")
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

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

            json_content = await file.read()
            json_str = json_content.decode('utf-8')
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
        ships = await self.bot.db.get_hangar_data(target_id)
        logger.info(f"Retrieved hangar data for {target_id}: {ships}")
        
        if not ships:
            return None

        # Group ships by manufacturer
        manu_groups = defaultdict(list)
        for ship in ships:
            manu_groups[ship['manufacturer_name']].append(ship)

        # Build the response message
        response = [
            "```md",
            f"# {target_name}'s Hangar",
            ""
        ]
        
        # Sort manufacturers
        for manufacturer in sorted(manu_groups.keys()):
            response.append(f"## {manufacturer}")
            
            # Group and sort ships by base name
            ship_groups = defaultdict(list)
            for ship in manu_groups[manufacturer]:
                ship_groups[ship['name']].append(ship)
            
            for base_name, instances in sorted(ship_groups.items()):
                count = len(instances)
                
                # Count LTI and Warbond
                lti_count = sum(1 for s in instances if s['lti'])
                wb_count = sum(1 for s in instances if s['warbond'])
                
                # Format status
                status = []
                if lti_count == count:
                    status.append("LTI")
                elif lti_count > 0:
                    status.append(f"{lti_count}LTI")
                if wb_count > 0:
                    status.append(f"{wb_count}WB")
                status_str = f" [{'+'.join(status)}]" if status else ""
                
                # Format custom names
                custom_names = [s['ship_name'] for s in instances if s['ship_name'] != base_name]
                custom_str = f' ("{", ".join(custom_names)}")' if custom_names else ""
                
                response.append(f"* {count:2d} × {base_name}{status_str}{custom_str}")
            
            response.append("")  # Add spacing between manufacturers
        
        # Add total count
        total_ships = len(ships)
        response.extend([
            "# Summary",
            f"* Total Ships: {total_ships}",
            "```"
        ])
        
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

            message = await interaction.followup.send(response)
            
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
            async with self.bot.db.pool.acquire() as conn:
                ship_count = await conn.fetchval('SELECT COUNT(*) FROM hangar_ships')
                logger.info(f"Total ships in database before fleet query: {ship_count}")
                
                if ship_count == 0:
                    await interaction.followup.send(MSG_NO_FLEET_DATA, ephemeral=True)
                    return

            fleet_data = await self.bot.db.get_fleet_total()
            logger.info(f"Retrieved fleet data: {fleet_data}")
            
            if not fleet_data:
                logger.error("No fleet data returned from database")
                await interaction.followup.send(MSG_NO_FLEET_DATA, ephemeral=True)
                return

            # Group by manufacturer
            manu_groups = defaultdict(list)
            for ship_name, data in fleet_data.items():
                manufacturer = data['manufacturer_name']
                manu_groups[manufacturer].append((ship_name, data))
            
            # Build the response message
            response = [
                "```md",
                "# Organization Fleet Summary",
                ""
            ]
            
            # Sort manufacturers
            for manufacturer in sorted(manu_groups.keys()):
                response.append(f"## {manufacturer}")
                
                # Sort ships within manufacturer
                for ship_name, data in sorted(manu_groups[manufacturer]):
                    count = data['count']
                    lti_count = data['lti_count']
                    wb_count = data['warbond_count']
                    
                    # Format status
                    status = []
                    if lti_count == count:
                        status.append("LTI")
                    elif lti_count > 0:
                        status.append(f"{lti_count}LTI")
                    if wb_count > 0:
                        status.append(f"{wb_count}WB")
                    status_str = f" [{'+'.join(status)}]" if status else ""
                    
                    # Format custom names
                    custom_str = f' ("{data["custom_names"]}")' if data.get('custom_names') else ""
                    
                    response.append(f"* {count:2d} × {ship_name}{status_str}{custom_str}")
                
                response.append("")  # Add spacing between manufacturers
            
            # Add total count
            total_ships = sum(data['count'] for data in fleet_data.values())
            response.extend([
                "# Summary",
                f"* Total Fleet Size: {total_ships} ships",
                "```"
            ])

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
            ship_models = await self.bot.db.get_all_ship_models()
            logger.info(f"Retrieved ship models: {ship_models}")
            
            if not ship_models:
                await interaction.response.send_message(MSG_NO_FLEET_DATA, ephemeral=True)
                return

            select = discord.ui.Select(
                placeholder="Select a ship model",
                options=[
                    discord.SelectOption(label=model[:100])
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

                response = [
                    "```md",
                    f"# Owners of {ship_name}",
                    ""
                ]
                
                for member, data in sorted(members, key=lambda x: x[0].display_name.lower()):
                    status = []
                    if data['ship_name'] != ship_name:
                        status.append(f'"{data["ship_name"]}"')
                    if data['lti']:
                        status.append("LTI")
                    if data['warbond']:
                        status.append("WB")
                    status_str = f" [{'+'.join(status)}]" if status else ""
                    response.append(f"* {member.display_name}{status_str}")

                response.append("```")
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

    @app_commands.command(name="forge-shipcount", description=CMD_SHIPCOUNT_DESC)
    async def forge_shipcount(self, interaction: discord.Interaction):
        """Display total ship counts per member"""
        await interaction.response.defer(ephemeral=True)

        try:
            ship_counts = await self.bot.db.get_ship_counts()
            
            if not ship_counts:
                await interaction.followup.send(MSG_NO_FLEET_DATA, ephemeral=True)
                return

            # Build the response message
            response = [
                "```md",
                "# DraXon Industries Fleet Size by Member",
                "",
                "| Member | Ships |",
                "|--------|-------|"
            ]
            
            total_ships = 0
            for data in ship_counts:
                member = interaction.guild.get_member(data['user_id'])
                if member:
                    ship_count = data['ship_count']
                    total_ships += ship_count
                    response.append(f"| {member.display_name:<30} | {ship_count:>5} |")
            
            response.extend([
                "",
                "# Summary",
                f"DraXon Industries Total Fleet Size: {total_ships} ships",
                "```"
            ])

            await interaction.followup.send("\n".join(response), ephemeral=True)

        except Exception as e:
            logger.error(f"Error in forge-shipcount: {str(e)}")
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
