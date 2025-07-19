# 🎮 Discord Tag Game

A fun Discord bot-powered tag game! Players join through Discord, and when someone is tagged, they get a chance to dodge through various mini-challenges.

## 🚀 Features

- **Discord Integration**: Full Discord bot with rich embeds and commands
- **Dodge Challenges**: Multiple types of challenges to dodge tags:
  - Math problems
  - Rock, Paper, Scissors
  - Word scrambles
  - Button mashing
- **Scoring System**: Points for successful tags and dodges
- **Leaderboard**: Track player performance
- **Real-time Game Status**: See who's "it" and active challenges

## 🛠️ Setup

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Discord server where you can invite bots

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/discord-tag-game.git
   cd discord-tag-game
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration**:
   ```bash
   cp config.example.json config.json
   ```

3. **Configure the bot**:
   - Edit `config.json` with your Discord bot token and server information
   - Replace `YOUR_DISCORD_BOT_TOKEN_HERE` with your actual bot token
   - Replace `YOUR_GUILD_ID_HERE` with your Discord server ID
   - Replace `YOUR_TAG_CHANNEL_ID_HERE` with the channel ID where the game will be played

4. **Create a Discord Bot**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to the "Bot" section and create a bot
   - Copy the bot token to your `config.json`
   - Enable the following intents:
     - Message Content Intent
     - Server Members Intent (optional)

5. **Invite the bot to your server**:
   - Go to OAuth2 > URL Generator
   - Select "bot" scope
   - Select permissions: Send Messages, Embed Links, Use Slash Commands
   - Use the generated URL to invite the bot

### Running the Game

1. **Start the bot**:
   ```bash
   python run_game.py
   ```

2. **Join the game**:
   - In your Discord server, use `!join` to join the game
   - Have other players join with the same command

3. **Start the game**:
   - An admin can use `!start` to begin the game
   - A random player will be chosen as "it"

## 🎯 How to Play

### Basic Commands

- `!join` - Join the game
- `!leave` - Leave the game
- `!start` - Start the game (Admin only)
- `!stop` - Stop the game (Admin only)
- `!status` - Show current game status
- `!leaderboard` - Show player rankings
- `!tag @player` - Tag another player (only if you're "it")
- `!dodge answer` - Attempt to dodge a challenge
- `!players` - List all players
- `!gamehelp` - Show help information

### Game Flow

1. **Join Phase**: Players join the game with `!join`
2. **Start Phase**: Admin starts the game with `!start`
3. **Playing Phase**: 
   - One player is randomly chosen as "it"
   - "It" can tag other players with `!tag @player`
   - Tagged players get a dodge challenge
   - Players have 10 seconds to complete the challenge with `!dodge answer`
   - If successful, they dodge and get points
   - If failed, they become "it" and the tagger gets points
4. **End Phase**: Game ends after the configured duration or when stopped

### Dodge Challenges

When tagged, players must complete one of these challenges:

1. **Math Challenge**: Solve a simple math problem
   - Example: "What is 5 + 3?" → Answer: "8"

2. **Rock, Paper, Scissors**: Beat the bot's choice
   - Example: "I choose rock! Beat me!" → Answer: "paper"

3. **Word Scramble**: Unscramble a word
   - Example: "Unscramble this word: KEAUQ" → Answer: "quake"

4. **Button Mash**: Click a button multiple times quickly
   - Example: "Click the button 10 times quickly!" → Answer: "10"

### Scoring

- **Successful Tag**: +20 points for the tagger, -5 points for the tagged
- **Successful Dodge**: +10 points for the dodger
- **Failed Dodge**: Tagged player becomes "it"

## ⚙️ Configuration

Edit `config.json` to customize game settings:

```json
{
    "discord_token": "YOUR_BOT_TOKEN",
    "guild_id": "YOUR_SERVER_ID",
    "tag_channel_id": "YOUR_CHANNEL_ID",
    "game_settings": {
        "tag_timeout": 300,        // Time limit for tags (seconds)
        "dodge_timeout": 10,       // Time limit for dodge challenges (seconds)
        "min_players": 2,          // Minimum players to start
        "max_players": 20,         // Maximum players allowed
        "round_duration": 600      // Game duration (seconds)
    }
}
```

## 🔧 Technical Details

### Architecture

- **`tag_game.py`**: Core game logic and state management
- **`dodge_mechanisms.py`**: Challenge generation and validation
- **`discord_bot.py`**: Discord bot interface and commands
- **`run_game.py`**: Launcher script with error handling

### Discord Integration

The game uses Discord's bot API for all interactions:
- Players join through Discord commands
- Game state is managed in Discord
- All challenges and scoring happen through Discord
- No external network discovery needed

## 🐛 Troubleshooting

### Common Issues

1. **Bot not responding**:
   - Check that the bot token is correct
   - Ensure the bot has proper permissions
   - Verify the bot is online
   - Make sure Message Content Intent is enabled in Discord Developer Portal

2. **Commands not working**:
   - Check that the bot has the required permissions
   - Verify the channel ID is correct
   - Ensure the bot prefix is "!"
   - Try restarting the bot

3. **Privileged intents errors**:
   - Enable Message Content Intent in Discord Developer Portal
   - Make sure bot has proper permissions in your server

### Debug Mode

To enable debug logging, add this to the top of `discord_bot.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

Feel free to contribute to this project! Some ideas for improvements:

- Additional dodge challenge types
- Team-based gameplay
- Tournament mode
- Web interface for game management
- Mobile app companion

## 📝 License

This project is open source and available under the MIT License.

## 🎉 Have Fun!

Enjoy playing Discord Tag with your friends! The game is designed to be simple but engaging, perfect for Discord servers and gaming communities. 