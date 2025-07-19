import random
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class GameState(Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    PAUSED = "paused"
    FINISHED = "finished"


@dataclass
class Player:
    discord_id: int
    discord_name: str
    lan_id: Optional[str] = None
    is_it: bool = False
    is_tagged: bool = False
    score: int = 0
    tags_made: int = 0
    tags_received: int = 0
    dodges_successful: int = 0
    last_active: float = 0


class TagGame:
    def __init__(self, config: Dict):
        self.config = config
        self.state = GameState.WAITING
        self.players: Dict[int, Player] = {}
        self.current_it: Optional[Player] = None
        self.game_start_time: Optional[float] = None
        self.round_duration = config["game_settings"]["round_duration"]
        self.tag_timeout = config["game_settings"]["tag_timeout"]
        self.min_players = config["game_settings"]["min_players"]
        self.max_players = config["game_settings"]["max_players"]
        self.active_challenges: Dict[int, Dict] = {}

    def add_player(
        self, discord_id: int, discord_name: str, lan_id: Optional[str] = None
    ) -> bool:
        """Add a player to the game"""
        if len(self.players) >= self.max_players:
            return False

        if discord_id not in self.players:
            self.players[discord_id] = Player(
                discord_id=discord_id,
                discord_name=discord_name,
                lan_id=lan_id,
                last_active=time.time(),
            )
            return True
        return False

    def remove_player(self, discord_id: int) -> bool:
        """Remove a player from the game"""
        if discord_id in self.players:
            player = self.players[discord_id]
            if player.is_it:
                self.current_it = None
            del self.players[discord_id]
            return True
        return False

    def start_game(self) -> bool:
        """Start the tag game"""
        if len(self.players) < self.min_players:
            return False

        self.state = GameState.PLAYING
        self.game_start_time = time.time()
        self._select_new_it()
        return True

    def stop_game(self):
        """Stop the tag game"""
        self.state = GameState.FINISHED
        self.current_it = None
        self.active_challenges.clear()

    def pause_game(self):
        """Pause the tag game"""
        self.state = GameState.PAUSED

    def resume_game(self):
        """Resume the tag game"""
        if self.state == GameState.PAUSED:
            self.state = GameState.PLAYING

    def _select_new_it(self):
        """Select a new player to be 'it'"""
        if not self.players:
            return

        # Remove current 'it' status
        if self.current_it:
            self.current_it.is_it = False

        # Select new 'it' randomly
        available_players = [p for p in self.players.values() if not p.is_tagged]
        if available_players:
            self.current_it = random.choice(available_players)
            self.current_it.is_it = True
            self.current_it.last_active = time.time()

    def attempt_tag(self, tagger_id: int, target_id: int) -> Dict:
        """Attempt to tag another player"""
        if self.state != GameState.PLAYING:
            return {"success": False, "message": "Game is not active"}

        if tagger_id not in self.players or target_id not in self.players:
            return {"success": False, "message": "Player not found"}

        tagger = self.players[tagger_id]
        target = self.players[target_id]

        if not tagger.is_it:
            return {"success": False, "message": "You are not 'it'"}

        if target.is_it:
            return {"success": False, "message": "Cannot tag yourself"}

        if target.is_tagged:
            return {"success": False, "message": "Player is already tagged"}

        # Create dodge challenge
        challenge_id = f"{target_id}_{int(time.time())}"
        self.active_challenges[target_id] = {
            "challenge_id": challenge_id,
            "tagger_id": tagger_id,
            "start_time": time.time(),
            "timeout": self.config["game_settings"]["dodge_timeout"],
        }

        return {
            "success": True,
            "message": f"{target.discord_name} has been tagged! They have {self.config['game_settings']['dodge_timeout']} seconds to dodge!",
            "challenge_id": challenge_id,
            "target_id": target_id,
        }

    def resolve_dodge_challenge(
        self, target_id: int, challenge_id: str, success: bool
    ) -> Dict:
        """Resolve a dodge challenge"""
        if target_id not in self.active_challenges:
            return {"success": False, "message": "No active challenge found"}

        challenge = self.active_challenges[target_id]
        if challenge["challenge_id"] != challenge_id:
            return {"success": False, "message": "Invalid challenge ID"}

        target = self.players[target_id]
        tagger = self.players[challenge["tagger_id"]]

        if success:
            # Dodge successful
            target.dodges_successful += 1
            target.score += 10
            result = {
                "success": True,
                "message": f"{target.discord_name} successfully dodged! +10 points!",
                "dodged": True,
            }
        else:
            # Tag successful
            target.is_tagged = True
            target.tags_received += 1
            tagger.tags_made += 1
            tagger.score += 20
            target.score -= 5

            # Switch 'it' to the tagged player
            self._select_new_it()

            result = {
                "success": True,
                "message": f"{target.discord_name} was tagged! {tagger.discord_name} gets +20 points, {target.discord_name} loses 5 points.",
                "dodged": False,
                "new_it": self.current_it.discord_name if self.current_it else None,
            }

        del self.active_challenges[target_id]
        return result

    def get_game_status(self) -> Dict:
        """Get current game status"""
        return {
            "state": self.state.value,
            "players": len(self.players),
            "current_it": self.current_it.discord_name if self.current_it else None,
            "active_challenges": len(self.active_challenges),
            "game_time": time.time() - self.game_start_time
            if self.game_start_time
            else 0,
            "round_duration": self.round_duration,
        }

    def get_leaderboard(self) -> List[Dict]:
        """Get current leaderboard"""
        sorted_players = sorted(
            self.players.values(),
            key=lambda p: (p.score, p.tags_made, -p.tags_received),
            reverse=True,
        )

        return [
            {
                "name": player.discord_name,
                "score": player.score,
                "tags_made": player.tags_made,
                "tags_received": player.tags_received,
                "dodges_successful": player.dodges_successful,
                "is_it": player.is_it,
            }
            for player in sorted_players
        ]

    def cleanup_expired_challenges(self):
        """Clean up expired dodge challenges"""
        current_time = time.time()
        expired_challenges = []

        for target_id, challenge in self.active_challenges.items():
            if current_time - challenge["start_time"] > challenge["timeout"]:
                expired_challenges.append(target_id)

        for target_id in expired_challenges:
            # Auto-fail expired challenges
            self.resolve_dodge_challenge(
                target_id, self.active_challenges[target_id]["challenge_id"], False
            )

    def is_game_over(self) -> bool:
        """Check if the game should end"""
        if not self.game_start_time:
            return False

        return time.time() - self.game_start_time > self.round_duration
