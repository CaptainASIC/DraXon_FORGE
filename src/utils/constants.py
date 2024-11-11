# utils/constants.py

# Version info
APP_VERSION = "2.2.0"
BUILD_DATE = "Nov 2024"

# Bot configuration
BOT_DESCRIPTION = "Fleet Operations & Resource Guidance Engine"

# Embed Colors (in decimal format)
COLOR_SUCCESS = 0x2ECC71  # Green
COLOR_ERROR = 0xE74C3C    # Red
COLOR_INFO = 0x3498DB     # Blue
COLOR_HANGAR = 0x9B59B6   # Purple

# Embed Icons
ICON_SUCCESS = "✅"
ICON_ERROR = "❌"
ICON_SYSTEM = "🖥️"
ICON_INFO = "ℹ️"
ICON_HANGAR = "🚀"
ICON_FLEET = "⚓"

# Command Descriptions
CMD_COLLECT_DESC = "Collect system specifications"
CMD_SYSTEM_DESC = "Display system specifications (yours or another member's)"
CMD_ABOUT_DESC = "Learn how to use DraXon FORGE"
CMD_UPLOAD_DESC = "Upload your hangar data from XPLOR addon JSON export"
CMD_HANGAR_DESC = "Display your hangar contents (auto-deletes after 3 minutes)"
CMD_FLEET_DESC = "Display total fleet counts across all members"
CMD_LOCATE_DESC = "Find members who own a specific ship model"

# Messages
MSG_NO_INFO = "Please use `/forge-collect` first to gather system information."
MSG_NO_MEMBER_INFO = "This member hasn't shared their system information yet."
MSG_COLLECTED = "System specifications have been captured. Use `/forge-system` to display them."
MSG_ERROR_TOKEN = "Error: DISCORD_TOKEN environment variable not set"

# Hangar Messages
MSG_UPLOAD_SUCCESS = "Successfully imported your hangar data."
MSG_UPLOAD_ERROR = "Error processing hangar data. Please ensure you've uploaded a valid JSON export from XPLOR addon."
MSG_NO_HANGAR = "No hangar data found. Use `/forge-upload` to import your ships."
MSG_NO_MEMBER_HANGAR = "This member hasn't uploaded their hangar data yet."
MSG_NO_FLEET_DATA = "No fleet data available. Members need to upload their hangar data first."

MSG_ABOUT = """
DraXon FORGE v2.2 is a comprehensive fleet and system management bot.

**System Commands:**
• `/forge-collect` - Opens a form to input your system specifications
• `/forge-system` - Displays your saved system information
• `/forge-system <member>` - View another member's system information

**Hangar Commands:**
• `/forge-upload` - Upload your hangar data from XPLOR addon JSON export
• `/forge-hangar [member]` - Display your hangar contents or another member's (auto-deletes after 3 minutes)

**Fleet Management:**
• `/forge-fleet` - Display total fleet counts across all members
• `/forge-locate` - Find members who own a specific ship model

**Quick Access:**
• Right-click any member > Apps > View System Info
• Right-click any member > Apps > View Hangar

**Getting Started:**
1. Use `/forge-collect` to register your system details
2. Export your hangar data from XPLOR addon as JSON
3. Upload your hangar data with `/forge-upload`
4. View your hangar with `/forge-hangar`
5. Explore the organization's fleet with `/forge-fleet` and `/forge-locate`

Your data is securely stored and can be updated at any time.
"""
