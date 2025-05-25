from rich import print
from nmr import nmr
from datetime import datetime
import time
import os
import sys


def main():
    """Generates nmr clock output"""
    clear_terminal()
    while True:
        raw_time_string = getCurrentTime()
        [hour, minute, second] = [nmr.str_to_name(
            i) for i in splitTimeString(raw_time_string)]
        printer(f"{hour}:{minute}:{second}")
        # Introduce delay by a second to avoid millisecond flicker
        time.sleep(1)


def clear_terminal():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def printer(time_item):
    """Handles printing of the output"""
    # Overwrite line with spaces that are the length of terminal size for cleaning
    clean_line = f"\r{' ' * os.get_terminal_size().columns}\r"
    # Use rich markup and write to stdout manually
    sys.stdout.write(clean_line)
    print(
        f"[bold magenta]{time_item}[/bold magenta]", end="")
    sys.stdout.flush()


def getCurrentTime():
    """Gets the current tume"""
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    return current_time


def splitTimeString(timeStr: list):
    "Splits the time string into a list of [HH, MM, SS]"
    new_string_list = timeStr.split(sep=":")
    return new_string_list


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nClock stopped.")
