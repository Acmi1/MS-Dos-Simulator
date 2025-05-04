#!/usr/bin/env python3
"""
DOS-Simulator - A Python-based MS-DOS style console operating system simulation
"""
import cmd
import os
import sys
import time
import random
from colorama import init, Fore, Style

from filesystem import FileSystem
from commands import DOSCommands
from config import ASCII_ART, VERSION, BOOT_MESSAGES

# Initialize colorama for cross-platform colored terminal output
init()

class DOSSimulator(cmd.Cmd):
    """Main class for the DOS-like console simulator"""
    
    intro = f"{Fore.CYAN}{ASCII_ART}{Style.RESET_ALL}\nType 'help' or '?' to list commands.\n"
    
    def __init__(self):
        super().__init__()
        self.filesystem = FileSystem()
        self.commands = DOSCommands(self.filesystem)
        self.update_prompt()
        
    def update_prompt(self):
        """Update the command prompt based on current directory"""
        current_dir = self.filesystem.get_current_path()
        self.prompt = f"{Fore.YELLOW}{current_dir}>{Style.RESET_ALL} "
        
    def default(self, line):
        """Handle unknown commands"""
        cmd_parts = line.strip().split(' ', 1)
        cmd_name = cmd_parts[0].upper()
        args = cmd_parts[1] if len(cmd_parts) > 1 else ""
        
        # Check if this is a valid command
        if hasattr(self.commands, f"do_{cmd_name}"):
            command_func = getattr(self.commands, f"do_{cmd_name}")
            result = command_func(args)
            if result is not None:
                print(result)
            self.update_prompt()
        else:
            print(f"{Fore.RED}Bad command or file name{Style.RESET_ALL}")
        
    def emptyline(self):
        """Do nothing on empty line input"""
        pass
    
    def do_help(self, arg):
        """Show help information"""
        if not arg:
            print(f"{Fore.GREEN}Available commands:{Style.RESET_ALL}")
            commands = [cmd[3:] for cmd in dir(self.commands) 
                       if cmd.startswith('do_') and not cmd.startswith('do__')]
            commands.sort()
            for cmd in commands:
                print(f"  {cmd}")
            print("\nType HELP <command> for more information on a specific command.")
        else:
            cmd_name = arg.upper()
            if hasattr(self.commands, f"do_{cmd_name}"):
                cmd_func = getattr(self.commands, f"do_{cmd_name}")
                print(f"{Fore.GREEN}{cmd_name}{Style.RESET_ALL} - {cmd_func.__doc__}")
            else:
                print(f"{Fore.RED}Help topic not found: {arg}{Style.RESET_ALL}")
    
    def do_exit(self, arg):
        """Exit the simulator"""
        print(f"{Fore.CYAN}Shutting down DOS-Simulator...{Style.RESET_ALL}")
        return True
        
    def do_quit(self, arg):
        """Exit the simulator"""
        return self.do_exit(arg)
        
    def do_EOF(self, arg):
        """Handle EOF (Ctrl+D)"""
        print()
        return self.do_exit(arg)

def simulate_boot_sequence():
    """Simulate a DOS-style boot sequence"""
    print(f"{Fore.CYAN}Starting DOS-Simulator v{VERSION}...{Style.RESET_ALL}")
    
    # Memory check simulation
    mem_total = random.randint(600, 640)
    print(f"\nChecking memory...")
    time.sleep(0.5)
    for i in range(0, mem_total, 64):
        print(f"{i}K OK", end="\r")
        time.sleep(0.1)
    print(f"{mem_total}K OK")
    
    # Boot messages
    for message in BOOT_MESSAGES:
        print(message)
        time.sleep(0.2)
    
    print("\nInitializing file system...")
    time.sleep(0.5)
    print("Loading command processor...")
    time.sleep(0.3)
    
    print(f"\n{Fore.GREEN}DOS-Simulator loaded successfully!{Style.RESET_ALL}")
    time.sleep(1)

if __name__ == "__main__":
    # Clear the screen first
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Show boot sequence
    simulate_boot_sequence()
    
    # Start the DOS simulator
    DOSSimulator().cmdloop()
