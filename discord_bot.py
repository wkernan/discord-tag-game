import discord
from discord.ext import commands
import json
import asyncio
import time
from typing import Dict

from tag_game import TagGame
from dodge_mechanisms import DodgeMechanisms


class TagGameBot(commands.Bot):
    def __init__(self, config_path: str = "config.json"):
        # Create intents with message_content enabled
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents)

        # Load configuration
        with open(config_path, "r") as f:
            self.config = json.load(f)

        # Initialize game components
        self.game = TagGame(self.config)
        self.dodge_mechanisms = DodgeMechanisms()

        # Game state
        self.active_challenges: Dict[int, Dict] = {}
        self.challenge_messages: Dict[str, str] = {}

    async def setup_hook(self):
        """Setup bot commands"""
        await self.add_cog(GameCommands(self))

    async def on_ready(self):
        """Bot ready event"""
        print(f"{self.user} has connected to Discord!")
        print(f"Bot is in {len(self.guilds)} guilds")

        # Set bot status
        await self.change_presence(activity=discord.Game(name="LAN Tag Game"))

    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command!")
        else:
            await ctx.send(f"An error occurred: {error}")


class GameCommands(commands.Cog):
    def __init__(self, bot: TagGameBot):
        self.bot = bot

    @commands.command(name="join")
    async def join_game(self, ctx):
        """Join the tag game"""
        if self.bot.game.add_player(ctx.author.id, ctx.author.display_name):
            embed = discord.Embed(
                title="🎮 Player Joined!",
                description=f"{ctx.author.display_name} has joined the LAN Tag Game!",
                color=discord.Color.green(),
            )
            embed.add_field(
                name="Players", value=len(self.bot.game.players), inline=True
            )
            embed.add_field(
                name="Status", value=self.bot.game.state.value.title(), inline=True
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ You're already in the game or the game is full!")

    @commands.command(name="leave")
    async def leave_game(self, ctx):
        """Leave the tag game"""
        if self.bot.game.remove_player(ctx.author.id):
            embed = discord.Embed(
                title="👋 Player Left",
                description=f"{ctx.author.display_name} has left the LAN Tag Game!",
                color=discord.Color.red(),
            )
            embed.add_field(
                name="Players", value=len(self.bot.game.players), inline=True
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ You're not in the game!")

    @commands.command(name="start")
    @commands.has_permissions(manage_channels=True)
    async def start_game(self, ctx):
        """Start the tag game (Admin only)"""
        if self.bot.game.start_game():
            embed = discord.Embed(
                title="🚀 Game Started!",
                description="The LAN Tag Game has begun!",
                color=discord.Color.blue(),
            )
            embed.add_field(
                name="Players", value=len(self.bot.game.players), inline=True
            )
            embed.add_field(
                name="Current 'It'",
                value=self.bot.game.current_it.discord_name,
                inline=True,
            )
            embed.add_field(
                name="Duration",
                value=f"{self.bot.game.round_duration // 60} minutes",
                inline=True,
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Not enough players to start the game!")

    @commands.command(name="stop")
    @commands.has_permissions(manage_channels=True)
    async def stop_game(self, ctx):
        """Stop the tag game (Admin only)"""
        self.bot.game.stop_game()
        embed = discord.Embed(
            title="🛑 Game Stopped",
            description="The LAN Tag Game has ended!",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="status")
    async def game_status(self, ctx):
        """Show current game status"""
        status = self.bot.game.get_game_status()
        embed = discord.Embed(title="📊 Game Status", color=discord.Color.blue())
        embed.add_field(name="State", value=status["state"].title(), inline=True)
        embed.add_field(name="Players", value=status["players"], inline=True)
        embed.add_field(
            name="Current 'It'", value=status["current_it"] or "None", inline=True
        )
        embed.add_field(
            name="Active Challenges", value=status["active_challenges"], inline=True
        )
        embed.add_field(
            name="Game Time", value=f"{status['game_time']:.0f}s", inline=True
        )
        embed.add_field(
            name="Round Duration", value=f"{status['round_duration']}s", inline=True
        )
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard")
    async def show_leaderboard(self, ctx):
        """Show the current leaderboard"""
        leaderboard = self.bot.game.get_leaderboard()
        if not leaderboard:
            await ctx.send("No players in the game yet!")
            return

        embed = discord.Embed(title="🏆 Leaderboard", color=discord.Color.gold())

        for i, player in enumerate(leaderboard[:10], 1):
            status = "👑 IT" if player["is_it"] else ""
            embed.add_field(
                name=f"{i}. {player['name']} {status}",
                value=f"Score: {player['score']} | Tags: {player['tags_made']} | Dodges: {player['dodges_successful']}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command(name="tag")
    async def tag_player(self, ctx, target):
        """Tag another player"""
        # Convert mention to user ID
        if not target.startswith("<@") or not target.endswith(">"):
            await ctx.send("❌ Please mention a player with @player")
            return

        # Extract user ID from mention
        try:
            user_id = int(target.strip("<@!>"))
        except ValueError:
            await ctx.send("❌ Invalid player mention")
            return

        result = self.bot.game.attempt_tag(ctx.author.id, user_id)

        if result["success"]:
            embed = discord.Embed(
                title="🏃 Tag Attempt!",
                description=result["message"],
                color=discord.Color.orange(),
            )
            embed.add_field(name="Target", value=f"<@{user_id}>", inline=True)
            embed.add_field(name="Tagger", value=ctx.author.display_name, inline=True)
            embed.add_field(
                name="Time Limit",
                value=f"{self.bot.config['game_settings']['dodge_timeout']}s",
                inline=True,
            )

            # Create dodge challenge
            challenge = await self.bot.dodge_mechanisms.get_random_challenge()
            embed.add_field(name="Dodge Challenge", value=challenge[0], inline=False)
            embed.add_field(name="Challenge Type", value=challenge[2], inline=True)

            # Store challenge info
            self.bot.active_challenges[user_id] = {
                "challenge_id": result["challenge_id"],
                "question": challenge[0],
                "answer": challenge[1],
                "challenge_type": challenge[2],
                "start_time": time.time(),
                "timeout": self.bot.config["game_settings"]["dodge_timeout"],
            }

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {result['message']}")

    @commands.command(name="dodge")
    async def dodge_challenge(self, ctx, answer: str):
        """Attempt to dodge a tag challenge"""
        if ctx.author.id not in self.bot.active_challenges:
            await ctx.send("❌ You don't have an active challenge to dodge!")
            return

        challenge = self.bot.active_challenges[ctx.author.id]

        # Check if challenge is expired
        if time.time() - challenge["start_time"] > challenge["timeout"]:
            del self.bot.active_challenges[ctx.author.id]
            await ctx.send("❌ Challenge expired! You were tagged!")
            return

        # Validate answer
        success = self.bot.dodge_mechanisms.validate_answer(
            challenge["challenge_type"], challenge["answer"], answer
        )

        # Resolve challenge
        result = self.bot.game.resolve_dodge_challenge(
            ctx.author.id, challenge["challenge_id"], success
        )

        if result["success"]:
            embed = discord.Embed(
                title="🎯 Dodge Result",
                description=result["message"],
                color=discord.Color.green()
                if result["dodged"]
                else discord.Color.red(),
            )

            if not result["dodged"] and "new_it" in result:
                embed.add_field(name="New 'It'", value=result["new_it"], inline=True)

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {result['message']}")

        # Clean up challenge
        if ctx.author.id in self.bot.active_challenges:
            del self.bot.active_challenges[ctx.author.id]

    @commands.command(name="players")
    async def list_players(self, ctx):
        """List all players in the game"""
        if not self.bot.game.players:
            await ctx.send("No players in the game!")
            return

        embed = discord.Embed(title="👥 Players", color=discord.Color.blue())

        for player in self.bot.game.players.values():
            status = []
            if player.is_it:
                status.append("👑 IT")
            if player.is_tagged:
                status.append("🏷️ Tagged")
            if player.discord_id in self.bot.active_challenges:
                status.append("⚡ Challenged")

            status_str = " ".join(status) if status else "Ready"
            embed.add_field(
                name=player.discord_name,
                value=f"Score: {player.score} | Status: {status_str}",
                inline=True,
            )

        await ctx.send(embed=embed)

    @commands.command(name="gamehelp")
    async def show_help(self, ctx):
        """Show help information"""
        embed = discord.Embed(
            title="🎮 LAN Tag Game Help",
            description="Welcome to the LAN Tag Game! Here are the available commands:",
            color=discord.Color.blue(),
        )

        commands_info = [
            ("!join", "Join the game"),
            ("!leave", "Leave the game"),
            ("!start", "Start the game (Admin only)"),
            ("!stop", "Stop the game (Admin only)"),
            ("!status", "Show game status"),
            ("!leaderboard", "Show leaderboard"),
            ("!tag @player", "Tag another player"),
            ("!dodge answer", "Attempt to dodge a challenge"),
            ("!players", "List all players"),
            ("!gamehelp", "Show this help message"),
        ]

        for cmd, desc in commands_info:
            embed.add_field(name=cmd, value=desc, inline=False)

        embed.add_field(
            name="🎯 How to Play",
            value="1. Join the game with !join\n2. Wait for the game to start\n3. If you're 'it', tag other players with !tag @player\n4. If tagged, quickly respond with !dodge answer\n5. Complete challenges to dodge tags!",
            inline=False,
        )

        await ctx.send(embed=embed)


async def main():
    """Main function to run the bot"""
    bot = TagGameBot()

    try:
        print("🤖 Starting Discord bot...")
        await bot.start(bot.config["discord_token"])
    except KeyboardInterrupt:
        print("\n🛑 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("👋 Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
