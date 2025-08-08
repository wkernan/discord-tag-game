import random
import os
from typing import Tuple
import openai


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

    async def ai_trivia_challenge(self) -> Tuple[str, str]:
        """Generate an AI-powered trivia challenge"""
        try:
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Generate a trivia question using ChatGPT
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a trivia game master specializing in challenging questions. Generate a single difficult trivia question with a clear, specific answer. The question should be challenging but not impossible. Focus on history, science, geography, literature, or obscure facts. Respond in this exact format: 'QUESTION: [your question here] ANSWER: [the correct answer here]'"
                    },
                    {
                        "role": "user",
                        "content": "Give me a challenging trivia question that would stump most people but has a definitive answer."
                    }
                ],
                max_tokens=200,
                temperature=0.8
            )
            
            # Parse the response
            content = response.choices[0].message.content
            lines = content.split('\n')
            
            question = ""
            answer = ""
            
            for line in lines:
                if line.startswith("QUESTION:"):
                    question = line.replace("QUESTION:", "").strip()
                elif line.startswith("ANSWER:"):
                    answer = line.replace("ANSWER:", "").strip()
            
            # Fallback if parsing fails
            if not question or not answer:
                question = "What year did the Berlin Wall fall?"
                answer = "1989"
            
            return question, answer.lower()
            
        except Exception as e:
            # Fallback to challenging trivia questions if AI fails
            fallback_questions = [
                ("What year did the Berlin Wall fall?", "1989"),
                ("What is the chemical symbol for gold?", "au"),
                ("Who wrote 'Pride and Prejudice'?", "jane austen"),
                ("What is the largest organ in the human body?", "skin"),
                ("In what year did World War II end?", "1945"),
                ("What is the capital of Australia?", "canberra"),
                ("Who painted the Mona Lisa?", "leonardo da vinci"),
                ("What is the smallest prime number?", "2"),
                ("What is the chemical formula for water?", "h2o"),
                ("Who was the first President of the United States?", "george washington"),
                ("What is the largest ocean on Earth?", "pacific"),
                ("What year did Columbus discover America?", "1492"),
                ("What is the square root of 144?", "12"),
                ("Who wrote 'Romeo and Juliet'?", "william shakespeare"),
                ("What is the hardest natural substance on Earth?", "diamond")
            ]
            return random.choice(fallback_questions)

    async def get_random_challenge(self) -> Tuple[str, str, str]:
        """Get a random dodge challenge"""
        challenges = [
            (self.math_challenge, "Math Challenge"),
            (self.rock_paper_scissors, "Rock, Paper, Scissors"),
            (self.word_scramble, "Word Scramble"),
            (self.ai_trivia_challenge, "AI Trivia Challenge"),
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
        elif challenge_type == "AI Trivia Challenge":
            # For AI trivia, we do a more flexible comparison
            # Check if the answer contains the expected answer or vice versa
            actual_words = set(actual.split())
            expected_words = set(expected.split())
            
            # Check for exact match first
            if actual == expected:
                return True
            
            # Check if any word from expected is in actual
            for word in expected_words:
                if word in actual_words:
                    return True
            
            # Check if any word from actual is in expected
            for word in actual_words:
                if word in expected_words:
                    return True
            
            return False

        return False
