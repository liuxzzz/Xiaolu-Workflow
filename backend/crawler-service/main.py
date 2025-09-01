#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hello World Python Application
A simple starter project for Python development.
"""

import sys
import os
from datetime import datetime


def greet(name: str = "World") -> str:
    """
    Generate a personalized greeting message.
    
    Args:
        name (str): The name to greet. Defaults to "World".
        
    Returns:
        str: A greeting message.
    """
    return f"Hello, {name}! 🐍"


def show_system_info():
    """Display basic system information."""
    print("=" * 50)
    print("🚀 Python Hello World Application")
    print("=" * 50)
    print(f"📅 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"💻 Platform: {sys.platform}")
    print("=" * 50)


def main():
    """Main application entry point."""
    show_system_info()
    
    # Basic greeting
    print(greet())
    print(greet("Developer"))
    
    # Interactive mode
    print("\n🎯 Interactive Mode:")
    try:
        while True:
            user_input = input("\n👋 Enter your name (or 'quit' to exit): ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye! Have a great day!")
                break
            elif user_input:
                print(f"✨ {greet(user_input)}")
            else:
                print("✨ Hello there! Please enter your name.")
                
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for using the app! Goodbye!")
    except EOFError:
        print("\n\n👋 Goodbye!")


if __name__ == "__main__":
    main()
