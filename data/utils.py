"""
Utility functions for DOS-Simulator
"""
import os
import re
import shlex
import time
from colorama import Fore, Style

def format_file_size(size_bytes):
    """Format byte size to human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def parse_path(path):
    """Convert a DOS-style path to a list of directory components"""
    if not path:
        return []
        
    # Normalize path separators
    normalized = path.replace('/', '\\')
    
    # Split path
    parts = normalized.split('\\')
    
    # Handle drive letter specially
    if parts and ':' in parts[0]:
        drive = parts[0].upper()
        if len(drive) > 2:
            drive = drive[:2]  # C:somedir -> C:
        parts[0] = drive
    
    return parts

def is_valid_filename(filename):
    """Check if a filename is valid for DOS"""
    if not filename or filename in ('.', '..'):
        return False
        
    # Check for invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    if re.search(invalid_chars, filename):
        return False
        
    # DOS 8.3 filename format check (relaxed for this simulator)
    if len(filename) > 255:
        return False
        
    return True

def is_batch_file(filename):
    """Check if a file is a batch file (.BAT extension)"""
    return filename.upper().endswith('.BAT')

def run_batch_file(filesystem, filename, args=None):
    """Run a DOS batch file"""
    # Read the batch file
    content = filesystem.read_file(filename)
    if content is None:
        print(f"{Fore.RED}Batch file not found: {filename}{Style.RESET_ALL}")
        return False
    
    # Process the batch file content
    try:
        lines = content.split('\n')
        echo_on = True
        
        # Process each line
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Handle batch file specific commands
            if line.upper().startswith('@'):
                # @ suppresses command echo for this line
                command = line[1:].strip()
                process_batch_command(filesystem, command, args, echo=False)
            elif line.upper().startswith('ECHO '):
                # ECHO command can toggle echo state
                echo_text = line[5:].strip()
                if echo_text.upper() == 'OFF':
                    echo_on = False
                    if echo_on:
                        print("ECHO is now OFF")
                elif echo_text.upper() == 'ON':
                    echo_on = True
                    print("ECHO is now ON")
                else:
                    if echo_on:
                        print(f"{line}")
                    print(echo_text)
            elif line.upper().startswith('REM '):
                # REM is a comment
                if echo_on:
                    print(f"{line}")
            elif line.upper().startswith('PAUSE'):
                # PAUSE batch execution
                if echo_on:
                    print(f"{line}")
                input(f"{Fore.YELLOW}Press any key to continue...{Style.RESET_ALL}")
            else:
                # Regular command
                process_batch_command(filesystem, line, args, echo=echo_on)
        
        return True
    except Exception as e:
        print(f"{Fore.RED}Error executing batch file: {str(e)}{Style.RESET_ALL}")
        return False

def process_batch_command(filesystem, command, args, echo=True):
    """Process a command from a batch file"""
    from commands import DOSCommands
    
    # Replace batch file parameters
    if args:
        for i, arg in enumerate(args, 1):
            command = command.replace(f'%{i}', arg)
    
    # Echo command if echo is on
    if echo:
        print(f"{filesystem.get_current_path()}>{command}")
    
    # Execute the command
    cmd_parts = command.strip().split(' ', 1)
    cmd_name = cmd_parts[0].upper()
    cmd_args = cmd_parts[1] if len(cmd_parts) > 1 else ""
    
    commands = DOSCommands(filesystem)
    
    if hasattr(commands, f"do_{cmd_name}"):
        command_func = getattr(commands, f"do_{cmd_name}")
        result = command_func(cmd_args)
        if result is not None:
            print(result)
    else:
        print(f"{Fore.RED}Bad command or file name{Style.RESET_ALL}")
    
    # Small delay for readability
    time.sleep(0.1)
