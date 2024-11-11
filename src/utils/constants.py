# utils/constants.py

# Version info
APP_VERSION = "2.0.0"
BUILD_DATE = "Nov 2024"

# Bot configuration
BOT_DESCRIPTION = "Fleet Operations & Resource Guidance Engine"

# Embed Colors (in decimal format)
COLOR_SUCCESS = 0x2ECC71  # Green
COLOR_ERROR = 0xE74C3C    # Red
COLOR_INFO = 0x3498DB     # Blue

# Embed Icons
ICON_SUCCESS = "✅"
ICON_ERROR = "❌"
ICON_SYSTEM = "🖥️"
ICON_INFO = "ℹ️"

# Command Descriptions
CMD_COLLECT_DESC = "Collect system specifications"
CMD_SHOW_DESC = "Display system specifications (yours or another member's)"
CMD_ABOUT_DESC = "Learn how to use DraXon FORGE"

# Messages
MSG_NO_INFO = "Please use `/forge-collect` first to gather system information."
MSG_NO_MEMBER_INFO = "This member hasn't shared their system information yet."
MSG_COLLECTED = "System specifications have been captured. Use `/forge-show` to display them."
MSG_ERROR_TOKEN = "Error: DISCORD_TOKEN environment variable not set"
MSG_ABOUT = """
DraXon FORGE is a system information collection and display bot.

**Available Commands:**
• `/forge-collect` - Opens a form to input your system specifications
• `/forge-show` - Displays your saved system information
• `/forge-show <member>` - View another member's system information
• `/forge-about` - Shows this help message

**How to use:**
1. Start by using `/forge-collect` to input your system details
2. Fill out the form with your specifications
3. Optionally add input device information when prompted
4. Use `/forge-show` to view your saved information
5. Use `/forge-show <member>` to view another member's system

Your data is securely stored and can be updated at any time by using `/forge-collect` again.
"""
