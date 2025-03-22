import json
import sys
import os
from file_operations.embeddings_manager import EmbeddingsManager
from file_operations.file_manager import FileManager
from file_operations.llm_manager import LLMManager
from typing import Dict, Any
import platform
from pathlib import Path
import speech_recognition as sr  # Add this import

GROQ_API_KEY = "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"

class FileAssistant:
    def __init__(self):
        self.file_manager = FileManager()
        self.embeddings_manager = EmbeddingsManager()
        self.llm_manager = LLMManager()
        self._initialize_system()

    def _initialize_system(self):
        """Initialize the system by scanning directories and creating embeddings"""
        print("🔄 Checking system state...")
        
        # Check if embeddings and directory tree already exist
        if self.embeddings_manager.load_embeddings():
            print("✅ Found existing embeddings")
            # Update embeddings with any new paths
            self._update_embeddings()
        else:
            print("⚠️ No existing embeddings found. Performing initial scan...")
            # Scan system for directory structure
            directory_tree = self.file_manager.scan_system()
            
            # Save directory tree
            self.file_manager.save_directory_tree(directory_tree)
            
            # Create embeddings for paths
            self.embeddings_manager.create_embeddings(directory_tree)
            
            print("✅ System initialized successfully!")

    def process_command(self, command: str) -> Dict:
        """Process a user command"""
        print(f"\n🔍 Processing command: {command}")
        
        # Search for similar paths
        similar_paths = self.embeddings_manager.search_paths(command)
        
        if not similar_paths:
            print("⚠️ No relevant paths found")
            return {
                "command": "",
                "explanation": "No relevant paths found for the command",
                "imports": []
            }
        
        # Process command with LLM
        result = self.llm_manager.process_query(command, similar_paths)
        
        if result["command"]:
            print(f"📝 Generated command: {result['command']}")
            print(f"ℹ️ Explanation: {result['explanation']}")
            
            # Execute the command
            success = self.execute_command(result["command"])
            if success:
                print("✅ Command executed successfully!")
                # Update embeddings with any new paths
                self._update_embeddings()
            else:
                print("❌ Command execution failed")
        else:
            print("❌ No command generated")
        
        return result

    def execute_command(self, command: str) -> bool:
        """Execute a Python command safely"""
        try:
            # Create a new namespace for execution
            namespace = {}
            
            # Add required imports
            if "os" in command:
                namespace["os"] = os
            if "shutil" in command:
                import shutil
                namespace["shutil"] = shutil
            
            # Execute the command
            exec(command, namespace)
            return True
        except Exception as e:
            print(f"Error executing command: {e}")
            return False

    def _update_embeddings(self):
        """Update embeddings with any new paths"""
        print("🔄 Checking for directory structure changes...")
        
        # Get the latest directory tree
        directory_tree = self.file_manager.scan_system()
        
        # Extract all paths from the new directory tree
        new_paths = []
        for drive, tree in directory_tree.items():
            for path, content in tree.items():
                full_path = os.path.join(drive, path)
                if full_path not in self.embeddings_manager.paths:
                    new_paths.append(full_path)
                    for dir_name in content["dirs"]:
                        new_path = os.path.join(full_path, dir_name)
                        if new_path not in self.embeddings_manager.paths:
                            new_paths.append(new_path)
                    for file_name in content["files"]:
                        new_path = os.path.join(full_path, file_name)
                        if new_path not in self.embeddings_manager.paths:
                            new_paths.append(new_path)
        
        if new_paths:
            print(f"📝 Found {len(new_paths)} new paths. Updating embeddings...")
            self.embeddings_manager.update_embeddings(new_paths)
            print("✅ Embeddings updated successfully!")
        else:
            print("✅ No new paths found. Directory structure is up to date.")

def recognize_speech():
    """Recognize speech from microphone input"""
    recognizer = sr.Recognizer()

    # Check if microphone is available
    if not sr.Microphone.list_microphone_names():
        print(json.dumps({"error": "No microphone detected"}))
        sys.exit(1)

    with sr.Microphone() as source:
        print("Listening...", file=sys.stderr)  # Send log to stderr
        recognizer.adjust_for_ambient_noise(source)

        try:
            # Increase timeout and add 'phrase_time_limit'
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
        except Exception as e:
            print(json.dumps({"error": f"Microphone error: {str(e)}"}))
            sys.exit(1)

    try:
        text = recognizer.recognize_google(audio)
        print(json.dumps({"text": text}))  # Print only JSON
        return text
    except sr.UnknownValueError:
        print(json.dumps({"error": "Could not understand the audio"}))
        return None
    except sr.RequestError as e:
        print(json.dumps({"error": f"Speech service error: {str(e)}"}))
        return None

def main():
    assistant = FileAssistant()
    print("\n🤖 File Assistant is ready! Speak your command or say 'exit' to quit.")
    
    while True:
        try:
            # Use speech recognition to get the command
            print("Say something...")
            command = recognize_speech()
            
            if command is None:
                print("⚠️ Could not recognize speech. Please try again.")
                continue
            
            if command.lower() == 'exit':
                break
            
            if command:
                assistant.process_command(command)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()