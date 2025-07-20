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
        self.challenge_channels: Dict[int, int] = {}  # Store channel ID for each challenge

    async def setup_hook(self):
        """Setup bot commands"""
        await self.add_cog(GameCommands(self))

    async def on_ready(self):
        """Bot ready event"""
        print(f"{self.user} has connected to Discord!")
        print(f"Bot is in {len(self.guilds)} guilds")

        # Set bot status
        await self.change_presence(activity=discord.Game(name="LAN Tag Game"))
        
        # Start timeout monitoring
        self.loop.create_task(self.monitor_it_timeout())
        
        # Start the challenge timeout monitor
        self.loop.create_task(self.monitor_challenge_timeouts())

    async def monitor_challenge_timeouts(self):
        """Monitor active challenges and auto-resolve timeouts"""
        print("🔍 Challenge timeout monitor started")
        while True:
            try:
                current_time = time.time()
                expired_challenges = []
                
                # Debug: Print active challenges
                if self.active_challenges:
                    print(f"🔍 Monitoring {len(self.active_challenges)} active challenges")
                    for player_id, challenge in self.active_challenges.items():
                        time_elapsed = current_time - challenge["start_time"]
                        time_remaining = challenge["timeout"] - time_elapsed
                        print(f"  Player {player_id}: {time_elapsed:.1f}s elapsed, {time_remaining:.1f}s remaining")
                        
                        if time_elapsed > challenge["timeout"]:
                            expired_challenges.append(player_id)
                            print(f"  ⏰ Player {player_id} challenge expired!")
                
                # Resolve expired challenges
                for player_id in expired_challenges:
                    print(f"🔄 Resolving timeout for player {player_id}")
                    await self.resolve_timeout_challenge(player_id)
                
                # Wait before next check
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"❌ Error in challenge timeout monitor: {e}")
                await asyncio.sleep(5)  # Wait longer on error

    async def resolve_timeout_challenge(self, player_id: int):
        """Resolve a challenge that has timed out"""
        print(f"🔄 Starting timeout resolution for player {player_id}")
        
        if player_id not in self.active_challenges:
            print(f"❌ Player {player_id} not found in active challenges")
            return
            
        challenge = self.active_challenges[player_id]
        print(f"📋 Challenge details: {challenge}")
        
        # Auto-fail the challenge (player didn't respond in time)
        result = self.game.resolve_dodge_challenge(
            player_id, challenge["challenge_id"], False
        )
        print(f"🎯 Resolve result: {result}")
        
        # Send timeout message to the channel
        channel_id = self.challenge_channels.get(player_id)
        print(f"📢 Channel ID for timeout message: {channel_id}")
        
        if channel_id:
            channel = self.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="⏰ Challenge Timeout!",
                    description=f"<@{player_id}> didn't respond in time and was tagged!",
                    color=discord.Color.red(),
                )
                if "new_it" in result:
                    embed.add_field(name="New 'It'", value=result["new_it"], inline=True)
                await channel.send(embed=embed)
                print(f"✅ Timeout message sent to channel {channel_id}")
            else:
                print(f"❌ Could not find channel {channel_id}")
        else:
            print(f"❌ No channel ID found for player {player_id}")
        
        # Clean up
        del self.active_challenges[player_id]
        if player_id in self.challenge_channels:
            del self.challenge_channels[player_id]
        print(f"🧹 Cleaned up challenge data for player {player_id}")

    async def monitor_it_timeout(self):
        """Monitor for 'it' player timeouts"""
        while True:
            try:
                if self.game.state.value == "playing" and self.game.current_it:
                    timeout_result = self.game.check_it_timeout()
                    print(f"🔍 IT timeout result: {timeout_result}")
                    if timeout_result:
                        # Find a channel to send the timeout message
                        for guild in self.guilds:
                            for channel in guild.text_channels:
                                if channel.permissions_for(guild.me).send_messages:
                                    embed = discord.Embed(
                                        title="⏰ 'It' Player Timeout!",
                                        description=f"{timeout_result['old_it']} didn't tag anyone within 5 minutes!",
                                        color=discord.Color.orange()
                                    )
                                    embed.add_field(name="Penalty", value=f"{timeout_result['penalty']} points", inline=True)
                                    
                                    if timeout_result.get("game_ended"):
                                        embed.add_field(name="Game Status", value="Game ended - no available players", inline=True)
                                    elif timeout_result["new_it"]:
                                        embed.add_field(name="New 'It'", value=timeout_result["new_it"], inline=True)
                                    
                                    await channel.send(embed=embed)
                                    break
                            break
                
                await asyncio.sleep(5)  # Check every 30 seconds
            except Exception as e:
                print(f"❌ Error in 'it' timeout monitor: {e}")
                await asyncio.sleep(5)

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
        
        # Add attempt information if someone is "it"
        if self.bot.game.current_it:
            it_player = self.bot.game.current_it
            
            # Show time remaining for "it" player
            if self.bot.game.it_start_time:
                time_elapsed = time.time() - self.bot.game.it_start_time
                time_remaining = max(0, self.bot.game.it_timeout - time_elapsed)
                minutes = int(time_remaining // 60)
                seconds = int(time_remaining % 60)
                embed.add_field(name="'It' Time Remaining", value=f"{minutes}:{seconds:02d}", inline=True)
            
            if it_player.tag_attempts:
                attempts_info = []
                for target_id, attempts in it_player.tag_attempts.items():
                    if target_id in self.bot.game.players:
                        target_name = self.bot.game.players[target_id].discord_name
                        attempts_info.append(f"{target_name}: {attempts}/3")
                if attempts_info:
                    embed.add_field(name="Tag Attempts", value="\n".join(attempts_info), inline=False)
        
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
            
            # Store channel for timeout notifications
            self.bot.challenge_channels[user_id] = ctx.channel.id

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
        if ctx.author.id in self.bot.challenge_channels:
            del self.bot.challenge_channels[ctx.author.id]

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

    @commands.command(name="attempts")
    async def show_attempts(self, ctx):
        """Show current 'it' player's tag attempts"""
        if not self.bot.game.current_it:
            await ctx.send("❌ No one is currently 'it'!")
            return
            
        it_player = self.bot.game.current_it
        if not it_player.tag_attempts:
            await ctx.send(f"🎯 {it_player.discord_name} hasn't attempted to tag anyone yet!")
            return
            
        embed = discord.Embed(
            title=f"🎯 {it_player.discord_name}'s Tag Attempts",
            color=discord.Color.orange()
        )
        
        for target_id, attempts in it_player.tag_attempts.items():
            if target_id in self.bot.game.players:
                target_name = self.bot.game.players[target_id].discord_name
                attempts_remaining = 3 - attempts
                embed.add_field(
                    name=f"Target: {target_name}",
                    value=f"Attempts: {attempts}/3 ({attempts_remaining} remaining)",
                    inline=True
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
            ("!attempts", "Show current 'it' player's tag attempts"),
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
