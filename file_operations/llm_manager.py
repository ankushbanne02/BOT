import os
from typing import Dict, List, Tuple
from groq import Groq
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()

class LLMManager:
    def __init__(self):
        # Try to get API key from environment or use the hardcoded one
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
            
        self.client = Groq(api_key=api_key)
        self.system_prompt = """You are a helpful assistant that generates Python commands for file operations.
Your task is to generate executable Python commands based on user requests and the available directory structure.

Available paths will be provided as context. Use these paths to generate accurate commands.
Always use raw strings (r'path') for file paths to handle special characters correctly.
Include necessary imports (os, shutil) in the command.

IMPORTANT: Your response MUST be ONLY a valid JSON object with exactly these fields:
{
    "command": "Python command to execute",
    "explanation": "Brief explanation of what the command does",
    "imports": ["required", "imports"]
}

DO NOT include any other text, markdown formatting, or code blocks.
DO NOT explain your reasoning or provide additional context.
ONLY return the JSON object.

Example response:
{
    "command": "os.makedirs(os.path.dirname(r'C:/Users/username/Documents/notes.txt'), exist_ok=True); open(r'C:/Users/username/Documents/notes.txt', 'w').close()",
    "explanation": "Creating an empty text file in Documents folder",
    "imports": ["os"]
}"""

    def process_query(self, query: str, similar_paths: List[Tuple[str, float]]) -> Dict:
        """Process user query and generate appropriate Python command"""
        # Create context from similar paths
        context = "Available paths:\n"
        for path, distance in similar_paths:
            context += f"- {path} (similarity: {1 - distance:.2f})\n"

        # Create messages for the chat
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nUser request: {query}"}
        ]

        try:
            # Get response from Groq
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.1,  # Lower temperature for more consistent output
                max_tokens=1000
            )

            # Extract the response content
            response_content = response.choices[0].message.content.strip()
            
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', response_content)
            if json_match:
                response_content = json_match.group(0)
            
            # Try to parse the JSON response
            try:
                result = json.loads(response_content)
                # Validate required fields
                if not all(key in result for key in ["command", "explanation", "imports"]):
                    raise ValueError("Missing required fields in response")
                return result
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                print(f"Raw response: {response_content}")
                return {
                    "command": "",
                    "explanation": "Error: Invalid response format",
                    "imports": []
                }

        except Exception as e:
            print(f"Error processing query: {e}")
            return {
                "command": "",
                "explanation": f"Error: {str(e)}",
                "imports": []
            } 