import random
from typing import Tuple


class DodgeMechanisms:
    def __init__(self):
        self.words = [
            "QUAKE",
            "GAMING",
            "LAN",
            "TAG",
            "DODGE",
            "PLAYER",
            "NETWORK",
            "DISCORD",
            "BOT",
            "FUN",
            "COMPETITION",
            "VICTORY",
            "CHALLENGE",
        ]

    async def math_challenge(self) -> Tuple[str, str]:
        """Generate a simple math challenge"""
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        operation = random.choice(["+", "-", "*"])

        if operation == "+":
            answer = a + b
        elif operation == "-":
            answer = a - b
        else:
            answer = a * b

        question = f"What is {a} {operation} {b}?"
        return question, str(answer)

    async def rock_paper_scissors(self) -> Tuple[str, str]:
        """Generate a rock, paper, scissors challenge"""
        choices = ["rock", "paper", "scissors"]
        bot_choice = random.choice(choices)

        # Determine what player needs to choose to win
        if bot_choice == "rock":
            player_choice = "paper"
        elif bot_choice == "paper":
            player_choice = "scissors"
        else:  # scissors
            player_choice = "rock"

        question = f"I choose {bot_choice}! Beat me!"
        return question, player_choice

    async def word_scramble(self) -> Tuple[str, str]:
        """Generate a word scramble challenge"""
        word = random.choice(self.words)
        scrambled = "".join(random.sample(word, len(word)))

        question = f"Unscramble this word: {scrambled}"
        return question, word.lower()

    async def button_mash(self) -> Tuple[str, str]:
        """Generate a button mashing challenge"""
        target_clicks = random.randint(5, 15)
        question = f"Click the button {target_clicks} times quickly!"
        return question, str(target_clicks)

    async def get_random_challenge(self) -> Tuple[str, str, str]:
        """Get a random dodge challenge"""
        challenges = [
            (self.math_challenge, "Math Challenge"),
            (self.rock_paper_scissors, "Rock, Paper, Scissors"),
            (self.word_scramble, "Word Scramble"),
            (self.button_mash, "Button Mash"),
        ]

        challenge_func, challenge_name = random.choice(challenges)
        question, answer = await challenge_func()

        return question, answer, challenge_name

    def validate_answer(self, challenge_type: str, expected: str, actual: str) -> bool:
        """Validate the player's answer"""
        actual = actual.strip().lower()
        expected = expected.lower()

        if challenge_type == "Math Challenge":
            try:
                return int(actual) == int(expected)
            except ValueError:
                return False
        elif challenge_type == "Rock, Paper, Scissors":
            valid_choices = ["rock", "paper", "scissors", "r", "p", "s"]
            if actual in valid_choices:
                # Convert shorthand to full word
                if actual == "r":
                    actual = "rock"
                elif actual == "p":
                    actual = "paper"
                elif actual == "s":
                    actual = "scissors"
                return actual == expected
            return False
        elif challenge_type == "Word Scramble":
            return actual == expected
        elif challenge_type == "Button Mash":
            try:
                return int(actual) >= int(expected)
            except ValueError:
                return False

        return False
