import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from utils.constants import *

class AddPeripheralsButton(discord.ui.View):
    def __init__(self, cog, user_id: int):
        super().__init__()
        self.cog = cog
        self.user_id = user_id

    @discord.ui.button(label="Add Input Devices", style=discord.ButtonStyle.primary)
    async def add_peripherals(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get existing peripheral info
        info = await self.cog.bot.db.get_system_info(self.user_id)
        await interaction.response.send_modal(PeripheralsModal(self.cog, info))

class SystemSpecsModal(discord.ui.Modal, title="System Specifications"):
    def __init__(self, cog, existing_info=None):
        super().__init__()
        self.cog = cog
        
        # Pre-populate fields if info exists
        if existing_info:
            self.os.default = existing_info['os']
            self.cpu.default = existing_info['cpu']
            self.gpu.default = existing_info['gpu']
            self.memory.default = existing_info['memory']
            self.storage.default = existing_info['storage']

    os = discord.ui.TextInput(
        label="Operating System",
        placeholder="e.g., Arch Linux, Windows 11, macOS Sonoma",
        required=True
    )

    cpu = discord.ui.TextInput(
        label="CPU",
        placeholder="e.g., AMD Ryzen 9 5950X, Intel i9-13900K",
        required=True
    )

    gpu = discord.ui.TextInput(
        label="GPU",
        placeholder="e.g., NVIDIA RTX 4090, AMD RX 7900 XTX",
        required=True
    )

    memory = discord.ui.TextInput(
        label="Memory",
        placeholder="e.g., 32GB DDR5-6000",
        required=True
    )

    storage = discord.ui.TextInput(
        label="Storage",
        placeholder="e.g., 2TB NVMe SSD, 8TB HDD",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.save_system_info(
            interaction.user.id,
            str(self.os),
            str(self.cpu),
            str(self.gpu),
            str(self.memory),
            str(self.storage)
        )
        
        embed = discord.Embed(
            title=f"{ICON_SUCCESS} System Information Saved",
            description="Your system information has been saved. Would you like to add information about your input devices?",
            color=COLOR_SUCCESS
        )
        # Show button to add peripherals
        view = AddPeripheralsButton(self.cog, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class PeripheralsModal(discord.ui.Modal, title="Input Devices"):
    def __init__(self, cog, existing_info=None):
        super().__init__()
        self.cog = cog
        
        # Pre-populate fields if info exists
        if existing_info:
            if existing_info.get('keyboard'):
                self.keyboard.default = existing_info['keyboard']
            if existing_info.get('mouse'):
                self.mouse.default = existing_info['mouse']
            if existing_info.get('other_controllers'):
                self.other_controllers.default = existing_info['other_controllers']
            if existing_info.get('audio_config'):
                self.audio_config.default = existing_info['audio_config']

    keyboard = discord.ui.TextInput(
        label="Keyboard",
        placeholder="e.g., Keychron Q1 w/ Gateron Browns",
        required=False
    )

    mouse = discord.ui.TextInput(
        label="Mouse",
        placeholder="e.g., Logitech G Pro X Superlight",
        required=False
    )

    other_controllers = discord.ui.TextInput(
        label="Other Controllers",
        placeholder="e.g., Xbox Elite Controller, HOTAS",
        required=False,
        style=discord.TextStyle.paragraph
    )

    audio_config = discord.ui.TextInput(
        label="Audio Configuration",
        placeholder="e.g., Speakers, Mic, Headset",
        required=False,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.update_peripherals(
            interaction.user.id,
            str(self.keyboard),
            str(self.mouse),
            str(self.other_controllers),
            str(self.audio_config)
        )
        
        embed = discord.Embed(
            title=f"{ICON_SUCCESS} Input Devices Saved",
            description="Your input device information has been saved. Use `/forge-system` to display all your system information.",
            color=COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ForgeCog(commands.GroupCog, name="forge"):
    """Cog for system-related commands"""
    
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
        # Add context menu command
        self.context_menu = app_commands.ContextMenu(
            name='View System Info',
            callback=self.view_system_context_menu,
        )
        self.bot.tree.add_command(self.context_menu)

    async def save_system_info(self, user_id, os, cpu, gpu, memory, storage):
        """Save core system information to database"""
        await self.bot.db.save_system_info(user_id, os, cpu, gpu, memory, storage)

    async def update_peripherals(self, user_id, keyboard, mouse, other_controllers, audio_config):
        """Update peripherals information in database"""
        await self.bot.db.update_peripherals(user_id, keyboard, mouse, other_controllers, audio_config)

    async def view_system_context_menu(self, interaction: discord.Interaction, member: discord.Member):
        """Context menu command for viewing system info"""
        await interaction.response.defer(ephemeral=True)
        
        info = await self.bot.db.get_system_info(member.id)
        
        if not info:
            embed = discord.Embed(
                title=f"{ICON_ERROR} No System Information Available",
                description=MSG_NO_MEMBER_INFO,
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Parse the timestamp string if it's from cache
        if isinstance(info['updated_at'], str):
            updated_at = datetime.fromisoformat(info['updated_at'])
        else:
            updated_at = info['updated_at']

        embed = discord.Embed(
            title=f"{ICON_SYSTEM} {member.display_name}'s System Specifications",
            description=f"Last Updated: {updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            color=COLOR_INFO
        )

        # Set the author to the target user
        embed.set_author(
            name=member.display_name,
            icon_url=member.display_avatar.url
        )

        # Core system specs
        embed.add_field(name="Operating System", value=info['os'], inline=True)
        embed.add_field(name="CPU", value=info['cpu'], inline=True)
        embed.add_field(name="GPU", value=info['gpu'], inline=True)
        embed.add_field(name="Memory", value=info['memory'], inline=True)
        embed.add_field(name="Storage", value=info['storage'], inline=True)
        
        # Input devices (only show if they exist and have values)
        if 'keyboard' in info and info['keyboard']:
            embed.add_field(name="Keyboard", value=info['keyboard'], inline=True)
        if 'mouse' in info and info['mouse']:
            embed.add_field(name="Mouse", value=info['mouse'], inline=True)
        if 'other_controllers' in info and info['other_controllers']:
            embed.add_field(name="Other Controllers", value=info['other_controllers'], inline=False)
        if 'audio_config' in info and info['audio_config']:
            embed.add_field(name="Audio Configuration", value=info['audio_config'], inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="collect", description=CMD_COLLECT_DESC)
    async def collect(self, interaction: discord.Interaction):
        """Open modal to collect system specifications"""
        # Get existing info if available
        existing_info = await self.bot.db.get_system_info(interaction.user.id)
        modal = SystemSpecsModal(self, existing_info)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="system", description=CMD_SYSTEM_DESC)
    @app_commands.describe(member="The member whose system information you want to view (optional)")
    async def system(self, interaction: discord.Interaction, member: discord.Member = None):
        """Display collected system specifications"""
        # If no member specified, show own info
        target_user = member or interaction.user
        target_name = f"{target_user.display_name}'s" if member else "Your"
        
        info = await self.bot.db.get_system_info(target_user.id)
        
        if not info:
            embed = discord.Embed(
                title=f"{ICON_ERROR} No System Information Available",
                description=MSG_NO_MEMBER_INFO if member else MSG_NO_INFO,
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Parse the timestamp string if it's from cache
        if isinstance(info['updated_at'], str):
            updated_at = datetime.fromisoformat(info['updated_at'])
        else:
            updated_at = info['updated_at']

        embed = discord.Embed(
            title=f"{ICON_SYSTEM} {target_name} System Specifications",
            description=f"Last Updated: {updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            color=COLOR_INFO
        )

        # Set the author to the target user
        embed.set_author(
            name=target_user.display_name,
            icon_url=target_user.display_avatar.url
        )

        # Core system specs
        embed.add_field(name="Operating System", value=info['os'], inline=True)
        embed.add_field(name="CPU", value=info['cpu'], inline=True)
        embed.add_field(name="GPU", value=info['gpu'], inline=True)
        embed.add_field(name="Memory", value=info['memory'], inline=True)
        embed.add_field(name="Storage", value=info['storage'], inline=True)
        
        # Input devices (only show if they exist and have values)
        if 'keyboard' in info and info['keyboard']:
            embed.add_field(name="Keyboard", value=info['keyboard'], inline=True)
        if 'mouse' in info and info['mouse']:
            embed.add_field(name="Mouse", value=info['mouse'], inline=True)
        if 'other_controllers' in info and info['other_controllers']:
            embed.add_field(name="Other Controllers", value=info['other_controllers'], inline=False)
        if 'audio_config' in info and info['audio_config']:
            embed.add_field(name="Audio Configuration", value=info['audio_config'], inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="about", description=CMD_ABOUT_DESC)
    async def about(self, interaction: discord.Interaction):
        """Display information about how to use the bot"""
        embed = discord.Embed(
            title=f"{ICON_INFO} About DraXon FORGE",
            description=MSG_ABOUT,
            color=COLOR_INFO
        )
        embed.set_footer(text=f"Version {APP_VERSION} • Built {BUILD_DATE}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    """Setup function for the forge cog"""
    await bot.add_cog(ForgeCog(bot))
