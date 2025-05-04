"""
Simple text editor for the DOS-Simulator
"""
import os
import sys
import curses
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init()

def draw_interface(stdscr, text_lines, current_line, current_col, status=""):
    """Draw the editor interface"""
    height, width = stdscr.getmaxyx()
    
    # Clear screen
    stdscr.clear()
    
    # Draw top bar
    stdscr.addstr(0, 0, " DOS-Simulator Editor ".center(width, "="))
    
    # Calculate visible lines
    max_lines = height - 3  # Accounting for header, status, and command line
    start_line = max(0, current_line - max_lines // 2)
    end_line = min(start_line + max_lines, len(text_lines))
    
    # Draw text
    for i, line in enumerate(text_lines[start_line:end_line], start=start_line):
        if i == current_line:
            # Current line highlight
            line_display = line[:width-1]
            stdscr.addstr(i - start_line + 1, 0, line_display)
            
            # Draw cursor position
            cursor_y = i - start_line + 1
            cursor_x = min(current_col, len(line))
            stdscr.move(cursor_y, cursor_x)
        else:
            # Normal line
            line_display = line[:width-1]
            stdscr.addstr(i - start_line + 1, 0, line_display)
    
    # Draw status bar
    help_text = " ^S Save | ^Q Quit "
    if status:
        status_text = f" {status} "
    else:
        status_text = f" Line: {current_line+1}, Col: {current_col+1} "
    
    remaining_space = width - len(status_text) - len(help_text)
    status_bar = status_text + " " * remaining_space + help_text
    
    stdscr.addstr(height-1, 0, status_bar[:width-1], curses.A_REVERSE)
    
    # Update the screen
    stdscr.refresh()

def insert_char(text_lines, current_line, current_col, char):
    """Insert a character at the current position"""
    line = text_lines[current_line]
    text_lines[current_line] = line[:current_col] + char + line[current_col:]
    return current_col + 1

def delete_char(text_lines, current_line, current_col):
    """Delete the character at the current position"""
    if current_col > 0:
        line = text_lines[current_line]
        text_lines[current_line] = line[:current_col-1] + line[current_col:]
        return current_col - 1
    elif current_line > 0:
        # Backspace at beginning of line merges with previous line
        prev_line = text_lines[current_line-1]
        curr_line = text_lines[current_line]
        current_col = len(prev_line)
        text_lines[current_line-1] = prev_line + curr_line
        text_lines.pop(current_line)
        return current_col, current_line - 1
    return current_col

def handle_enter(text_lines, current_line, current_col):
    """Split the line at the current position"""
    line = text_lines[current_line]
    text_lines[current_line] = line[:current_col]
    text_lines.insert(current_line + 1, line[current_col:])
    return 0, current_line + 1

def editor_main(stdscr, initial_content=""):
    """Main editor function"""
    # Setup
    curses.curs_set(1)  # Show cursor
    stdscr.clear()
    
    # Initialize text content
    text_lines = initial_content.split('\n')
    if not text_lines:
        text_lines = [""]
    
    # Initial cursor position
    current_line = 0
    current_col = 0
    
    # Status message
    status = ""
    
    # Main loop
    while True:
        # Draw the interface
        draw_interface(stdscr, text_lines, current_line, current_col, status)
        
        # Get input
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            # Handle Ctrl+C
            status = "Press Ctrl+Q to quit"
            continue
        
        # Clear status after any key
        status = ""
        
        # Handle input
        if key == curses.KEY_UP:
            # Move up
            if current_line > 0:
                current_line -= 1
                current_col = min(current_col, len(text_lines[current_line]))
        
        elif key == curses.KEY_DOWN:
            # Move down
            if current_line < len(text_lines) - 1:
                current_line += 1
                current_col = min(current_col, len(text_lines[current_line]))
        
        elif key == curses.KEY_LEFT:
            # Move left
            if current_col > 0:
                current_col -= 1
            elif current_line > 0:
                # Go to end of previous line
                current_line -= 1
                current_col = len(text_lines[current_line])
        
        elif key == curses.KEY_RIGHT:
            # Move right
            if current_col < len(text_lines[current_line]):
                current_col += 1
            elif current_line < len(text_lines) - 1:
                # Go to beginning of next line
                current_line += 1
                current_col = 0
        
        elif key == curses.KEY_HOME:
            # Go to beginning of line
            current_col = 0
        
        elif key == curses.KEY_END:
            # Go to end of line
            current_col = len(text_lines[current_line])
        
        elif key == curses.KEY_BACKSPACE or key == 127:
            # Backspace
            if current_col > 0:
                current_col = delete_char(text_lines, current_line, current_col)
            elif current_line > 0 and isinstance(current_col, int):
                # At beginning of line, merge with previous line
                result = delete_char(text_lines, current_line, current_col)
                if isinstance(result, tuple):
                    current_col, current_line = result
                else:
                    current_col = result
        
        elif key == curses.KEY_DC:
            # Delete
            if current_col < len(text_lines[current_line]):
                line = text_lines[current_line]
                text_lines[current_line] = line[:current_col] + line[current_col+1:]
            elif current_line < len(text_lines) - 1:
                # At end of line, merge with next line
                next_line = text_lines[current_line + 1]
                text_lines[current_line] += next_line
                text_lines.pop(current_line + 1)
        
        elif key == 10 or key == 13:
            # Enter
            current_col, current_line = handle_enter(text_lines, current_line, current_col)
        
        elif key == 19:
            # Ctrl+S to save
            status = "File saved"
            return '\n'.join(text_lines)
        
        elif key == 17:
            # Ctrl+Q to quit
            return None if status != "File saved" else '\n'.join(text_lines)
        
        elif 32 <= key <= 126:
            # Printable character
            current_col = insert_char(text_lines, current_line, current_col, chr(key))
        
        elif key == 9:
            # Tab (insert 4 spaces)
            for _ in range(4):
                current_col = insert_char(text_lines, current_line, current_col, ' ')

def edit_text(initial_content=""):
    """
    Launch the text editor with initial content
    Returns the edited content or None if cancelled
    """
    try:
        return curses.wrapper(editor_main, initial_content)
    except Exception as e:
        # If curses fails, provide a fallback
        print(f"{Fore.RED}Error starting editor: {str(e)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Falling back to simple editor mode...{Style.RESET_ALL}")
        return simple_editor(initial_content)

def simple_editor(initial_content=""):
    """Simple fallback editor if curses fails"""
    print(f"{Fore.CYAN}==== DOS-Simulator Simple Editor ===={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Enter text, one line at a time. Type '.exit' on a new line to finish.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Type '.cancel' to cancel editing.{Style.RESET_ALL}")
    
    # Show initial content with line numbers
    if initial_content:
        print(f"\nCurrent content:")
        for i, line in enumerate(initial_content.split('\n'), 1):
            print(f"{i:3d}: {line}")
    
    print("\nEnter new content:")
    
    lines = []
    line_num = 1
    
    while True:
        try:
            line = input(f"{line_num:3d}: ")
            if line == '.exit':
                return '\n'.join(lines)
            elif line == '.cancel':
                return None
            
            lines.append(line)
            line_num += 1
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Type '.exit' to save or '.cancel' to discard changes.")
