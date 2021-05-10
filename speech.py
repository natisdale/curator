# Author: Joshua Gotham
# Purpose: proof of concept speech recognition in Python

import random
import time
import speech_recognition as sr


def recognize_speech_from_mic(recognizer, microphone):

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    # response object
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    # try recognizing the speech in the recording
    # if a RequestError or UnknownValueError exception is caught,
    #     update the response object accordingly
    try:
        response["transcription"] = recognizer.recognize_google(audio)
    except sr.RequestError:
        # API Error
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        # No words detected
        response["error"] = "Unable to recognize speech"

    return response


if __name__ == "__main__":

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    
    cont = True
    while(cont):
        print("Please say a command.")
        time.sleep(3)
        while(1):
            words = recognize_speech_from_mic(recognizer, microphone)
            if words["transcription"]:
                break
            if not words["success"]:
                break
            print("I didn't catch that. What did you say?\n")
        if words["error"]:
            print("ERROR: {}".format(words["error"]))
            break

        print("You said: {}".format(words["transcription"]))
        cont = words["transcription"].lower() != "quit"