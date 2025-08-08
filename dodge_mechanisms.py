import random
import os
from typing import Tuple
import openai


class DodgeMechanisms:
    def __init__(self):
        pass



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
        # Only AI trivia challenge
        question, answer = await self.ai_trivia_challenge()
        return question, answer, "AI Trivia Challenge"

    def validate_answer(self, challenge_type: str, expected: str, actual: str) -> bool:
        """Validate the player's answer"""
        actual = actual.strip().lower()
        expected = expected.lower()

        # Only AI trivia challenge validation
        if challenge_type == "AI Trivia Challenge":
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
