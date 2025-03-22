import speech_recognition as sr
import json
import sys

def recognize_speech():
    recognizer = sr.Recognizer()

    # Debugging: Check if the microphone is accessible
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
    except sr.UnknownValueError:
        print(json.dumps({"error": "Could not understand the audio"}))
    except sr.RequestError as e:
        print(json.dumps({"error": f"Speech service error: {str(e)}"}))

if __name__ == "__main__":
    recognize_speech()
