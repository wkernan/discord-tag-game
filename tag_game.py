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
    tag_attempts: Dict[int, int] = None  # Track attempts per target: {target_id: attempts}
    
    def __post_init__(self):
        if self.tag_attempts is None:
            self.tag_attempts = {}


class TagGame:
    def __init__(self, config: Dict):
        self.config = config
        self.state = GameState.WAITING
        self.players: Dict[int, Player] = {}
        self.current_it: Optional[Player] = None
        self.game_start_time: Optional[float] = None
        self.it_start_time: Optional[float] = None  # Track when current "it" started
        self.round_duration = config["game_settings"]["round_duration"]
        self.it_timeout = config["game_settings"]["it_timeout"]
        self.min_players = config["game_settings"]["min_players"]
        self.max_players = config["game_settings"]["max_players"]
        self.active_challenges: Dict[int, Dict] = {}
        self.last_tagged_by: Dict[int, int] = {}  # Track who each player last tagged

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
        
        # Reset all player states
        for player in self.players.values():
            player.is_it = False
            player.is_tagged = False
            player.tag_attempts.clear()

    def pause_game(self):
        """Pause the tag game"""
        self.state = GameState.PAUSED

    def resume_game(self):
        """Resume the tag game"""
        if self.state == GameState.PAUSED:
            self.state = GameState.PLAYING

    def _clear_current_it(self):
        """Clear the current 'it' player's status"""
        if self.current_it:
            self.current_it.is_it = False

    def _get_available_players(self) -> List[Player]:
        """Get list of players who are not tagged and can be 'it'"""
        return [p for p in self.players.values() if not p.is_tagged]

    def _select_random_it(self) -> Optional[Player]:
        """Select a random player to be 'it'"""
        available_players = self._get_available_players()
        if available_players:
            return random.choice(available_players)
        return None

    def _select_specific_it(self, specific_player_id: int) -> Optional[Player]:
        """Select a specific player to be 'it'"""
        if specific_player_id in self.players:
            return self.players[specific_player_id]
        return None

    def _setup_new_it_player(self, new_it: Player):
        """Set up a new 'it' player's state"""
        self.current_it = new_it
        new_it.is_it = True
        new_it.last_active = time.time()
        # Reset attempt counters for new 'it' player
        new_it.tag_attempts.clear()
        # Set start time for new 'it' player
        self.it_start_time = time.time()

    def _select_new_it(self, specific_player_id: Optional[int] = None):
        """Select a new player to be 'it'"""
        if not self.players:
            return

        # Clear current 'it' status
        self._clear_current_it()

        # Select new 'it' player
        if specific_player_id is not None:
            # Make the specific player 'it' (when they get tagged)
            new_it = self._select_specific_it(specific_player_id)
        else:
            # Select new 'it' randomly (for game start)
            new_it = self._select_random_it()

        # Set up the new 'it' player if one was found
        if new_it:
            self._setup_new_it_player(new_it)

    def _validate_game_state(self) -> Optional[Dict]:
        """Validate that the game is in the correct state for tagging"""
        if self.state != GameState.PLAYING:
            return {"success": False, "message": "Game is not active"}
        return None

    def _validate_players_exist(self, tagger_id: int, target_id: int) -> Optional[Dict]:
        """Validate that both players exist in the game"""
        if tagger_id not in self.players or target_id not in self.players:
            return {"success": False, "message": "Player not found"}
        return None

    def _validate_tagging_rules(self, tagger: Player, target: Player, tagger_id: int, target_id: int) -> Optional[Dict]:
        """Validate all tagging rules"""
        if not tagger.is_it:
            return {"success": False, "message": "You are not 'it'"}

        if target.is_it:
            return {"success": False, "message": "Cannot tag yourself"}

        if target.is_tagged:
            return {"success": False, "message": "Player is already tagged"}

        # Check if tagger is trying to tag the same person they tagged last time
        if tagger_id in self.last_tagged_by and self.last_tagged_by[tagger_id] == target_id:
            return {"success": False, "message": "You must tag a different player than your last target"}

        return None

    def _validate_attempt_limit(self, tagger: Player, target: Player, target_id: int) -> Optional[Dict]:
        """Validate that the tagger hasn't exceeded attempt limits"""
        attempts = tagger.tag_attempts.get(target_id, 0)
        if attempts >= 3:
            return {"success": False, "message": f"You've already attempted to tag {target.discord_name} 3 times. Try tagging someone else!"}
        return None

    def _track_attempt(self, tagger: Player, target_id: int) -> int:
        """Track the attempt and return remaining attempts"""
        attempts = tagger.tag_attempts.get(target_id, 0)
        tagger.tag_attempts[target_id] = attempts + 1
        return 3 - attempts - 1

    def _create_dodge_challenge(self, target_id: int, tagger_id: int) -> Dict:
        """Create a new dodge challenge"""
        challenge_id = f"{target_id}_{int(time.time())}"
        self.active_challenges[target_id] = {
            "challenge_id": challenge_id,
            "tagger_id": tagger_id,
            "start_time": time.time(),
            "timeout": self.config["game_settings"]["dodge_timeout"],
        }
        return {
            "challenge_id": challenge_id,
            "timeout": self.config["game_settings"]["dodge_timeout"]
        }

    def attempt_tag(self, tagger_id: int, target_id: int) -> Dict:
        """Attempt to tag another player"""
        # Validate game state
        state_error = self._validate_game_state()
        if state_error:
            return state_error

        # Validate players exist
        player_error = self._validate_players_exist(tagger_id, target_id)
        if player_error:
            return player_error

        tagger = self.players[tagger_id]
        target = self.players[target_id]

        # Validate tagging rules
        rules_error = self._validate_tagging_rules(tagger, target, tagger_id, target_id)
        if rules_error:
            return rules_error

        # Validate attempt limits
        limit_error = self._validate_attempt_limit(tagger, target, target_id)
        if limit_error:
            return limit_error

        # Track the attempt
        attempts_remaining = self._track_attempt(tagger, target_id)

        # Create dodge challenge
        challenge = self._create_dodge_challenge(target_id, tagger_id)

        return {
            "success": True,
            "message": f"{target.discord_name} has been tagged! They have {challenge['timeout']} seconds to dodge! (Attempt {tagger.tag_attempts[target_id]}/3, {attempts_remaining} remaining)",
            "challenge_id": challenge["challenge_id"],
            "target_id": target_id,
        }

    def _validate_challenge(self, target_id: int, challenge_id: str) -> Optional[Dict]:
        """Validate that a dodge challenge exists and is valid"""
        if target_id not in self.active_challenges:
            return {"success": False, "message": "No active challenge found"}

        challenge = self.active_challenges[target_id]
        if challenge["challenge_id"] != challenge_id:
            return {"success": False, "message": "Invalid challenge ID"}
        
        return None

    def _handle_successful_dodge(self, target: Player) -> Dict:
        """Handle the case where a player successfully dodges"""
        target.dodges_successful += 1
        target.score += 10
        
        return {
            "success": True,
            "message": f"{target.discord_name} successfully dodged! +10 points!",
            "dodged": True,
        }

    def _handle_successful_tag(self, target: Player, tagger: Player, challenge: Dict) -> Dict:
        """Handle the case where a tag is successful"""
        # Update player stats
        target.is_tagged = True
        target.tags_received += 1
        tagger.tags_made += 1
        tagger.score += 20
        target.score -= 5

        # Clear the tagger's "tagged" status since they successfully passed it on
        tagger.is_tagged = False

        # Record that the tagger successfully tagged this target
        self.last_tagged_by[challenge["tagger_id"]] = target.discord_id
        
        # Reset attempt counter for this target since tag was successful
        if target.discord_id in tagger.tag_attempts:
            del tagger.tag_attempts[target.discord_id]

        # Switch 'it' to the tagged player
        self._select_new_it(target.discord_id)

        return {
            "success": True,
            "message": f"{target.discord_name} was tagged! {tagger.discord_name} gets +20 points, {target.discord_name} loses 5 points.",
            "dodged": False,
            "new_it": self.current_it.discord_name if self.current_it else None,
        }

    def _cleanup_challenge(self, target_id: int):
        """Remove the challenge from active challenges"""
        del self.active_challenges[target_id]

    def resolve_dodge_challenge(
        self, target_id: int, challenge_id: str, success: bool
    ) -> Dict:
        """Resolve a dodge challenge"""
        # Validate the challenge
        validation_error = self._validate_challenge(target_id, challenge_id)
        if validation_error:
            return validation_error

        challenge = self.active_challenges[target_id]
        target = self.players[target_id]
        tagger = self.players[challenge["tagger_id"]]

        # Handle the result based on success/failure
        if success:
            result = self._handle_successful_dodge(target)
        else:
            result = self._handle_successful_tag(target, tagger, challenge)

        # Clean up the challenge
        self._cleanup_challenge(target_id)
        
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
        
    def _check_it_timeout_condition(self) -> bool:
        """Check if the current 'it' player has timed out"""
        if not self.current_it or not self.it_start_time:
            return False
            
        current_time = time.time()
        return current_time - self.it_start_time > self.it_timeout

    def _handle_it_timeout_penalty(self, old_it: Player):
        """Apply penalty to the timed out 'it' player"""
        old_it.score -= 10  # Penalty for not tagging anyone

    def _find_new_it_after_timeout(self, old_it: Player) -> Optional[Player]:
        """Find a new 'it' player after timeout"""
        available_players = [p for p in self.players.values() if not p.is_tagged and p != old_it]
        if available_players:
            return random.choice(available_players)
        return None

    def _setup_new_it_after_timeout(self, new_it: Player, current_time: float):
        """Set up a new 'it' player after timeout"""
        self.current_it = new_it
        new_it.is_it = True
        new_it.last_active = current_time
        new_it.tag_attempts.clear()
        self.it_start_time = current_time

    def _create_timeout_result(self, old_it: Player, new_it: Optional[Player] = None, game_ended: bool = False) -> Dict:
        """Create timeout result dictionary"""
        result = {
            "timeout": True,
            "old_it": old_it.discord_name,
            "penalty": -10
        }
        
        if game_ended:
            result["new_it"] = None
            result["game_ended"] = True
        elif new_it:
            result["new_it"] = new_it.discord_name
            
        return result

    def check_it_timeout(self) -> Optional[Dict]:
        """Check if the current 'it' player has timed out"""
        if not self._check_it_timeout_condition():
            return None
            
        current_time = time.time()
        old_it = self.current_it
        
        # Apply penalty and clear old 'it' status
        self._handle_it_timeout_penalty(old_it)
        old_it.is_it = False  # Clear the old 'it' player's status
        
        # Find new "it" player
        new_it = self._find_new_it_after_timeout(old_it)
        
        if new_it:
            # Set up new "it" player
            self._setup_new_it_after_timeout(new_it, current_time)
            return self._create_timeout_result(old_it, new_it)
        else:
            # No available players, end the game
            self.stop_game()
            return self._create_timeout_result(old_it, game_ended=True)
