#!/usr/bin/env python3
"""
LAN Tag Game Launcher
Simple script to run the Discord bot with proper error handling
"""

import asyncio
import sys
import json
import os
from discord_bot import TagGameBot

def check_config():
    """Check if configuration file exists and is valid"""
    if not os.path.exists("config.json"):
        print("❌ config.json not found!")
        print("Please create a config.json file with your Discord bot settings.")
        print("See README.md for setup instructions.")
        return False
        
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            
        required_fields = ["discord_token", "guild_id", "tag_channel_id"]
        for field in required_fields:
            if field not in config or config[field] == f"YOUR_{field.upper()}_HERE":
                print(f"❌ Please configure {field} in config.json")
                return False
                
        return True
    except json.JSONDecodeError:
        print("❌ Invalid JSON in config.json")
        return False
    except Exception as e:
        print(f"❌ Error reading config.json: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import discord
        import asyncio
        import socket
        import threading
        import random
        import json
        import datetime
        import uuid
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

async def main():
    """Main launcher function"""
    print("🎮 LAN Tag Game Launcher")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        return
        
    # Check configuration
    if not check_config():
        return
        
    print("✅ Configuration and dependencies OK")
    print("🚀 Starting Discord Tag Game...")
    print("Press Ctrl+C to stop the game")
    print("-" * 40)
    
    try:
        # Create and run the bot
        bot = TagGameBot()
        await bot.start(bot.config["discord_token"])
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        if 'bot' in locals():
            bot.lan_discovery.stop()
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        if 'bot' in locals():
            bot.lan_discovery.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1) 