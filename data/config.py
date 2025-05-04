"""
Configuration settings for the DOS Simulator
"""

# Version information
VERSION = "1.0.0"

# ASCII Art for the title screen
ASCII_ART = r"""
  _____   ____   _____       _____ _                 _       _             
 |  __ \ / __ \ / ____|     / ____(_)               | |     | |            
 | |  | | |  | | (___ _____| (___  _ _ __ ___  _   _| | __ _| |_ ___  _ __ 
 | |  | | |  | |\___ \______\___ \| | '_ ` _ \| | | | |/ _` | __/ _ \| '__|
 | |__| | |__| |____) |     ____) | | | | | | | |_| | | (_| | || (_) | |   
 |_____/ \____/|_____/     |_____/|_|_| |_| |_|\__,_|_|\__,_|\__\___/|_|   
                                                                           
"""

# Boot sequence messages
BOOT_MESSAGES = [
    "Starting MS-DOS...",
    "HIMEM is testing extended memory...",
    "HIMEM is testing protected-mode...",
    "DOS=HIGH",
    "Loading device drivers...",
    "MSCDEX Version 2.25",
    "Initializing Mouse Driver...",
    "Loading environment variables..."
]

# Default system configuration
SYSTEM_CONFIG = {
    "computer_name": "IBM_PC",
    "prompt": "$P$G",
    "path": "C:\\DOS;C:\\",
    "temp_dir": "C:\\TEMP",
    "comspec": "C:\\COMMAND.COM"
}

# Help topics
HELP_TOPICS = {
    "GENERAL": """
DOS-Simulator Help System
=========================
Type HELP <command> for specific help on a command.
Type HELP COMMANDS for a list of available commands.
""",
    
    "COMMANDS": """
Available Commands:
------------------
CD/CHDIR    - Change directory
CLS         - Clear screen
COPY        - Copy files
DATE        - Display or set date
DEL/ERASE   - Delete files
DIR         - List directory contents
ECHO        - Display messages
EDIT        - Edit text files
EXIT/QUIT   - Exit DOS-Simulator
FIND        - Search for text in files
HELP        - Display help
MD/MKDIR    - Make directory
MEM         - Display memory information
MORE        - Display output one screen at a time
PATH        - Set command search path
PROMPT      - Change command prompt
RD/RMDIR    - Remove directory
REN/RENAME  - Rename files
SET         - Set environment variables
SORT        - Sort text
SYS         - Show system information
TIME        - Display or set time
TREE        - Display directory structure
TYPE        - Display file contents
VER         - Show version information
VOL         - Display disk volume information
""",
    
    "BATCH": """
Batch File Commands:
------------------
@           - Suppress command echo
CALL        - Call another batch file
ECHO        - Display message or toggle echo
FOR         - Loop through commands
GOTO        - Jump to label
IF          - Conditional processing
PAUSE       - Pause execution
REM         - Insert comment
SET         - Set environment variable
SHIFT       - Shift batch parameters
"""
}
