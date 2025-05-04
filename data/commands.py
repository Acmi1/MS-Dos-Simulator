"""
Command implementations for the DOS Simulator
"""
import os
import sys
import time
import random
import shlex
import subprocess
from colorama import Fore, Style
from datetime import datetime

import editor
from utils import format_file_size, parse_path, is_batch_file, run_batch_file

class DOSCommands:
    """Class that implements DOS-like commands"""
    
    def __init__(self, filesystem):
        """Initialize with the virtual filesystem"""
        self.filesystem = filesystem
    
    def do_DIR(self, args):
        """
        Display files and directories in the current directory.
        Usage: DIR [path] [/W] [/P]
        Options:
          /W - Wide list format
          /P - Pause after each screen of information
        """
        # Parse arguments
        arg_list = shlex.split(args) if args else []
        
        # Extract options and path
        path = "."
        wide_format = False
        page_display = False
        
        for arg in arg_list:
            if arg.startswith('/'):
                if arg.upper() == '/W':
                    wide_format = True
                elif arg.upper() == '/P':
                    page_display = True
            else:
                path = arg
        
        # Get directory contents
        try:
            path_info = self.filesystem.resolve_path(path)
            if not path_info or path_info['type'] != 'dir':
                return f"{Fore.RED}Invalid path: {path}{Style.RESET_ALL}"
            
            files = self.filesystem.list_directory(path)
            
            # Get the directory we're showing
            display_path = self.filesystem.get_full_path(path)
            
            # Output header
            result = [f"\n Volume in drive C is DOS-SIMULATOR"]
            result.append(f" Directory of {display_path}\n")
            
            # Calculate totals
            total_files = 0
            total_dirs = 0
            total_size = 0
            
            if wide_format:
                # Wide format (names only, multiple columns)
                file_names = []
                for file in files:
                    name_ext = file['name']
                    if file['type'] == 'dir':
                        name_ext = f"[{name_ext}]"
                        total_dirs += 1
                    else:
                        total_files += 1
                        total_size += file['size']
                    file_names.append(f"{name_ext:<12}")
                
                # Display in columns (5 entries per row)
                for i in range(0, len(file_names), 5):
                    row = file_names[i:i+5]
                    result.append("".join(row))
            else:
                # Standard format with details
                for file in files:
                    date_str = datetime.fromtimestamp(file['modified']).strftime('%m-%d-%Y')
                    time_str = datetime.fromtimestamp(file['modified']).strftime('%I:%M%p').lower()
                    
                    if file['type'] == 'dir':
                        # Directory entry
                        result.append(f"{date_str}  {time_str}    {Fore.CYAN}<DIR>          {file['name']}{Style.RESET_ALL}")
                        total_dirs += 1
                    else:
                        # File entry
                        size_str = f"{file['size']:>14,}"
                        result.append(f"{date_str}  {time_str}    {size_str} {file['name']}")
                        total_files += 1
                        total_size += file['size']
            
            # Summary line
            result.append(f"{' ':8}{total_files} File(s)    {format_file_size(total_size)}")
            result.append(f"{' ':8}{total_dirs} Dir(s)     {format_file_size(self.filesystem.get_free_space())} free")
            
            # Handle paging if requested
            if page_display:
                output = "\n".join(result)
                lines = output.split("\n")
                
                # Show 25 lines at a time
                for i in range(0, len(lines), 25):
                    print("\n".join(lines[i:i+25]))
                    if i + 25 < len(lines):
                        input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            else:
                return "\n".join(result)
            
        except Exception as e:
            return f"{Fore.RED}Error listing directory: {str(e)}{Style.RESET_ALL}"
    
    def do_CD(self, args):
        """
        Change the current directory.
        Usage: CD [path]
        CD without arguments displays the current directory.
        """
        if not args:
            # Display current directory
            return f" {self.filesystem.get_current_path()}"
        
        try:
            success = self.filesystem.change_directory(args)
            if not success:
                return f"{Fore.RED}Invalid directory: {args}{Style.RESET_ALL}"
        except Exception as e:
            return f"{Fore.RED}Error changing directory: {str(e)}{Style.RESET_ALL}"
    
    def do_CHDIR(self, args):
        """Alias for CD command."""
        return self.do_CD(args)
    
    def do_MKDIR(self, args):
        """
        Create a directory.
        Usage: MKDIR <directory>
        """
        if not args:
            return f"{Fore.RED}Missing parameter - directory name{Style.RESET_ALL}"
        
        try:
            success = self.filesystem.create_directory(args)
            if not success:
                return f"{Fore.RED}Unable to create directory: {args}{Style.RESET_ALL}"
        except Exception as e:
            return f"{Fore.RED}Error creating directory: {str(e)}{Style.RESET_ALL}"
    
    def do_MD(self, args):
        """Alias for MKDIR command."""
        return self.do_MKDIR(args)
    
    def do_RMDIR(self, args):
        """
        Remove a directory (must be empty).
        Usage: RMDIR <directory>
        """
        if not args:
            return f"{Fore.RED}Missing parameter - directory name{Style.RESET_ALL}"
        
        try:
            success = self.filesystem.remove_directory(args)
            if not success:
                return f"{Fore.RED}Unable to remove directory: {args}{Style.RESET_ALL}"
        except Exception as e:
            return f"{Fore.RED}Error removing directory: {str(e)}{Style.RESET_ALL}"
    
    def do_RD(self, args):
        """Alias for RMDIR command."""
        return self.do_RMDIR(args)
    
    def do_TYPE(self, args):
        """
        Display the contents of a text file.
        Usage: TYPE <filename>
        """
        if not args:
            return f"{Fore.RED}Missing parameter - filename{Style.RESET_ALL}"
        
        try:
            content = self.filesystem.read_file(args)
            if content is None:
                return f"{Fore.RED}File not found: {args}{Style.RESET_ALL}"
            return content
        except Exception as e:
            return f"{Fore.RED}Error reading file: {str(e)}{Style.RESET_ALL}"
    
    def do_COPY(self, args):
        """
        Copy a file from one location to another.
        Usage: COPY <source> <destination>
        """
        arg_list = shlex.split(args) if args else []
        if len(arg_list) < 2:
            return f"{Fore.RED}Syntax error - Incorrect parameter format{Style.RESET_ALL}"
        
        source = arg_list[0]
        destination = arg_list[1]
        
        try:
            success = self.filesystem.copy_file(source, destination)
            if not success:
                return f"{Fore.RED}Unable to copy file: {source} to {destination}{Style.RESET_ALL}"
            return f"        1 file(s) copied"
        except Exception as e:
            return f"{Fore.RED}Error copying file: {str(e)}{Style.RESET_ALL}"
    
    def do_DEL(self, args):
        """
        Delete a file.
        Usage: DEL <filename>
        """
        if not args:
            return f"{Fore.RED}Missing parameter - filename{Style.RESET_ALL}"
        
        try:
            success = self.filesystem.delete_file(args)
            if not success:
                return f"{Fore.RED}Unable to delete file: {args}{Style.RESET_ALL}"
        except Exception as e:
            return f"{Fore.RED}Error deleting file: {str(e)}{Style.RESET_ALL}"
    
    def do_ERASE(self, args):
        """Alias for DEL command."""
        return self.do_DEL(args)
    
    def do_REN(self, args):
        """
        Rename a file.
        Usage: REN <oldname> <newname>
        """
        arg_list = shlex.split(args) if args else []
        if len(arg_list) < 2:
            return f"{Fore.RED}Syntax error - Incorrect parameter format{Style.RESET_ALL}"
        
        oldname = arg_list[0]
        newname = arg_list[1]
        
        try:
            success = self.filesystem.rename_file(oldname, newname)
            if not success:
                return f"{Fore.RED}Unable to rename file: {oldname} to {newname}{Style.RESET_ALL}"
        except Exception as e:
            return f"{Fore.RED}Error renaming file: {str(e)}{Style.RESET_ALL}"
    
    def do_RENAME(self, args):
        """Alias for REN command."""
        return self.do_REN(args)
    
    def do_CLS(self, args):
        """Clear the screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def do_EDIT(self, args):
        """
        Edit a text file.
        Usage: EDIT <filename>
        """
        if not args:
            return f"{Fore.RED}Missing parameter - filename{Style.RESET_ALL}"
        
        filename = args.strip()
        
        # Check if file exists, if not create a new one
        content = self.filesystem.read_file(filename) or ""
        
        # Launch the text editor
        new_content = editor.edit_text(content)
        
        # Save the file if editor returned content
        if new_content is not None:
            try:
                self.filesystem.write_file(filename, new_content)
                return f"File {filename} saved successfully."
            except Exception as e:
                return f"{Fore.RED}Error saving file: {str(e)}{Style.RESET_ALL}"
    
    def do_DATE(self, args):
        """
        Display or set the system date.
        Usage: DATE [MM-DD-YYYY]
        """
        if not args:
            current_date = datetime.now().strftime('%a %m-%d-%Y')
            return f"Current date is: {current_date}\nEnter new date (MM-DD-YYYY): [Press ENTER to keep current date]"
        
        return "Date functionality is simulated in this environment."
    
    def do_TIME(self, args):
        """
        Display or set the system time.
        Usage: TIME [HH:MM:SS]
        """
        if not args:
            current_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            return f"Current time is: {current_time}\nEnter new time (HH:MM:SS): [Press ENTER to keep current time]"
        
        return "Time functionality is simulated in this environment."
    
    def do_VER(self, args):
        """Display the DOS-Simulator version."""
        from config import VERSION
        return f"\nDOS-Simulator [Version {VERSION}]\n(c) 2023 DOS-Simulator Team. All rights reserved."
    
    def do_VOL(self, args):
        """Display the disk volume label."""
        return " Volume in drive C is DOS-SIMULATOR\n Volume Serial Number is 1337-42AB"
    
    def do_ECHO(self, args):
        """
        Display a message or toggle command echoing.
        Usage: ECHO [message]
        """
        if not args:
            return "ECHO is on."
        elif args.upper() == "OFF":
            return "ECHO is now off (simulated)"
        elif args.upper() == "ON":
            return "ECHO is now on (simulated)"
        else:
            return args
    
    def do_PROMPT(self, args):
        """
        Change the command prompt.
        Usage: PROMPT [text]
        
        Note: In this simulator, this is just simulated.
        """
        return "Command prompt customization simulated in this environment."
    
    def do_PATH(self, args):
        """
        Display or set the command path.
        Usage: PATH [directory;directory;...]
        """
        return "Path is simulated in this environment."
    
    def do_MEM(self, args):
        """Display memory usage information."""
        total_mem = random.randint(600, 640) * 1024
        free_mem = random.randint(400, total_mem) 
        
        result = [
            "\nMemory Type       Total       Used       Free",
            "----------------  --------   --------   --------",
            f"Conventional      {total_mem:8,}   {total_mem-free_mem:8,}   {free_mem:8,}",
            f"Upper                 0          0          0",
            f"Reserved          131072     131072          0",
            f"Extended               0          0          0",
            "----------------  --------   --------   --------",
            f"Total memory:    {total_mem+131072:8,}   {total_mem-free_mem+131072:8,}   {free_mem:8,}",
            "",
            f"Total under 1 MB:   {total_mem:8,}",
            "",
            "Largest executable program size:     {free_mem:8,}",
            "Largest free upper memory block:          0",
            f"MS-DOS is resident in the high memory area."
        ]
        
        return "\n".join(result)
    
    def do_TREE(self, args):
        """
        Display the directory structure graphically.
        Usage: TREE [drive:][path] [/F]
        """
        show_files = '/F' in args.upper() if args else False
        path = args.split(' ')[0] if args and not args.startswith('/') else '.'
        
        try:
            # Resolve the path
            path_info = self.filesystem.resolve_path(path)
            if not path_info or path_info['type'] != 'dir':
                return f"{Fore.RED}Invalid path: {path}{Style.RESET_ALL}"
            
            # Get the full path for display
            display_path = self.filesystem.get_full_path(path)
            
            result = [f"Directory PATH listing for volume C:", f"Volume serial number is 1337-42AB"]
            result.append(display_path)
            
            # Tree generation
            tree_result = self.filesystem.generate_tree(path, show_files)
            result.extend(tree_result)
            
            return "\n".join(result)
        except Exception as e:
            return f"{Fore.RED}Error generating tree: {str(e)}{Style.RESET_ALL}"
    
    def do_HELP(self, args):
        """
        Get help for DOS commands.
        Usage: HELP [command]
        """
        # This will be handled by the main class do_help method
        pass
    
    def do_EXIT(self, args):
        """Exit the DOS simulator."""
        # This will be handled by the main class do_exit method
        pass
    
    def do_QUIT(self, args):
        """Exit the DOS simulator."""
        # This will be handled by the main class do_quit method
        pass
    
    def do_SYS(self, args):
        """
        Display system information.
        Usage: SYS
        """
        cpu_model = "Intel(R) 8086 CPU @ 8MHz"
        ram = f"{random.randint(600, 640)} KB"
        
        result = [
            f"\nDOS-Simulator System Information:",
            f"---------------------------------",
            f"Processor:      {cpu_model}",
            f"Memory:         {ram}",
            f"Operating System: DOS-Simulator",
            f"System Uptime:  {random.randint(0, 24)} hours, {random.randint(0, 59)} minutes"
        ]
        
        return "\n".join(result)
        
    def do_ATTRIB(self, args):
        """
        Display or change file attributes.
        Usage: ATTRIB [+R|-R] [+A|-A] [+S|-S] [+H|-H] [file]
        """
        return "File attribute functionality simulated in this environment."
        
    def do_FIND(self, args):
        """
        Search for a text string in a file.
        Usage: FIND [/V] [/C] [/N] [/I] "string" [file(s)]
        """
        arg_list = shlex.split(args) if args else []
        
        if len(arg_list) < 2:
            return f"{Fore.RED}FIND: Parameter format not correct{Style.RESET_ALL}"
        
        # Extract options and search string
        search_string = None
        filename = None
        case_insensitive = False
        invert_search = False
        count_only = False
        show_line_numbers = False
        
        for i, arg in enumerate(arg_list):
            if arg.startswith('/'):
                if arg.upper() == '/I':
                    case_insensitive = True
                elif arg.upper() == '/V':
                    invert_search = True
                elif arg.upper() == '/C':
                    count_only = True
                elif arg.upper() == '/N':
                    show_line_numbers = True
            elif search_string is None and arg.startswith('"') and arg.endswith('"'):
                search_string = arg.strip('"')
            elif search_string is None:
                search_string = arg
            elif filename is None:
                filename = arg
        
        if not search_string or not filename:
            return f"{Fore.RED}FIND: Invalid parameters{Style.RESET_ALL}"
            
        try:
            content = self.filesystem.read_file(filename)
            if content is None:
                return f"{Fore.RED}FIND: File not found - {filename}{Style.RESET_ALL}"
            
            lines = content.split('\n')
            matches = []
            match_count = 0
            
            for i, line in enumerate(lines, 1):
                is_match = search_string in line
                if case_insensitive:
                    is_match = search_string.lower() in line.lower()
                
                if invert_search:
                    is_match = not is_match
                
                if is_match:
                    match_count += 1
                    if not count_only:
                        if show_line_numbers:
                            matches.append(f"[{i}]{line}")
                        else:
                            matches.append(line)
            
            if count_only:
                return f"FIND: {match_count} line(s) matched"
            else:
                result = [f"---------- {filename}"]
                result.extend(matches)
                return "\n".join(result)
                
        except Exception as e:
            return f"{Fore.RED}FIND: Error searching file: {str(e)}{Style.RESET_ALL}"
                
    def do_MORE(self, args):
        """
        Display output one screen at a time.
        Usage: MORE < [filename] or command | MORE
        """
        if not args:
            return f"{Fore.RED}File not found - {args}{Style.RESET_ALL}"
        
        try:
            content = self.filesystem.read_file(args)
            if content is None:
                return f"{Fore.RED}File not found - {args}{Style.RESET_ALL}"
            
            lines = content.split('\n')
            
            # Display 25 lines at a time
            for i in range(0, len(lines), 25):
                chunk = lines[i:i+25]
                print("\n".join(chunk))
                
                if i + 25 < len(lines):
                    input(f"{Fore.YELLOW}-- More --{Style.RESET_ALL}")
            
        except Exception as e:
            return f"{Fore.RED}Error reading file: {str(e)}{Style.RESET_ALL}"
    
    def do_SORT(self, args):
        """
        Sort the contents of a text file.
        Usage: SORT [/R] [filename]
        
        Options:
          /R - Sort in reverse order
        """
        arg_list = args.split() if args else []
        reverse = False
        filename = None
        
        for arg in arg_list:
            if arg.upper() == '/R':
                reverse = True
            else:
                filename = arg
        
        if not filename:
            return f"{Fore.RED}Required parameter missing{Style.RESET_ALL}"
        
        try:
            content = self.filesystem.read_file(filename)
            if content is None:
                return f"{Fore.RED}File not found - {filename}{Style.RESET_ALL}"
            
            lines = content.split('\n')
            lines.sort(reverse=reverse)
            
            return '\n'.join(lines)
            
        except Exception as e:
            return f"{Fore.RED}Error sorting file: {str(e)}{Style.RESET_ALL}"
    
    def do_SET(self, args):
        """
        Display or set environment variables.
        Usage: SET [variable=[string]]
        """
        return "Environment variables simulated in this environment."
    
    def do_LABEL(self, args):
        """
        Create, change, or delete the volume label of a disk.
        Usage: LABEL [drive:][label]
        """
        return "Disk label functionality simulated in this environment."
    
    def do_FORMAT(self, args):
        """
        Format a disk for use with DOS.
        Usage: FORMAT drive: [/Q] [/U] [/V:label]
        """
        return "Disk formatting simulated in this environment."
    
    def do_XCOPY(self, args):
        """
        Copy files and directories.
        Usage: XCOPY source [destination] [/A | /M] [/D[:date]] [/P] [/S [/E]]
        """
        return "XCOPY functionality simulated in this environment."

    def do_CREATE(self, args):

        """
        Create files and directories.
        
        """

        return "CREATE functionality simulated in this environment."


    def execute_command(self, command):
        """Execute a DOS command"""
        cmd_parts = command.strip().split(' ', 1)
        cmd_name = cmd_parts[0].upper()
        args = cmd_parts[1] if len(cmd_parts) > 1 else ""
        
        if hasattr(self, f"do_{cmd_name}"):
            command_func = getattr(self, f"do_{cmd_name}")
            return command_func(args)
        else:
            return f"{Fore.RED}Bad command or file name{Style.RESET_ALL}"
