"""
Constants used throughout the DraXon Mechanic bot
"""

# Bot Configuration
BOT_ACTIVITY_TYPE = "watching"
BOT_ACTIVITY_NAME = "system metrics"

# Embed Colors (in decimal format)
COLOR_SUCCESS = 0x2ECC71  # Green
COLOR_ERROR = 0xE74C3C    # Red
COLOR_INFO = 0x3498DB     # Blue

# Embed Icons
ICON_SUCCESS = "✅"
ICON_ERROR = "❌"
ICON_SYSTEM = "🖥️"

# Command Descriptions
CMD_COLLECT_DESC = "Collect system specifications"
CMD_SHOW_DESC = "Display collected system specifications"

# Messages
MSG_NO_INFO = "Please use `/system-collect` first to gather system information."
MSG_COLLECTED = "System specifications have been captured. Use `/system-show` to display them."
MSG_ERROR_TOKEN = "Error: DISCORD_TOKEN environment variable not set"

# Version info
APP_VERSION = "1.1.1"
BUILD_DATE = "Nov 2024"
