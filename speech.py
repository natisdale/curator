# Author: Joshua Gotham
# Purpose: proof of concept speech recognition in Python

import random
import time
import threading
import speech_recognition as sr
from PIL import Image, ImageTk
import requests
import tkinter as tk
import os
from io import BytesIO

cont = True
pause = False

def recognize_speech_from_mic():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    # response object
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    # try recognizing speech
    # if a RequestError or UnknownValueError exception is caught,
    # update response and return
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

def listen():
    global cont
    global pause
    while(cont):
        print("Please say a command.")
        while(1):
            words = recognize_speech_from_mic()
            if words["transcription"]:
                break
            if not words["success"]:
                break
            print("I didn't catch that. What did you say?")
        if words["error"]:
            print("ERROR: {}".format(words["error"]))
            break
        print("You said: {}".format(words["transcription"]))
        word = words["transcription"].lower()
        if(word == "quit"):
            cont = False
        elif (word == "pause"):
            pause = True
        elif (word == "play"):
            pause = False 


def play():
    root = tk.Tk()
    root.title("MET Test")
    img1 = "https://i.imgur.com/sxgudbo.jpg"
    img2 = "https://i.imgur.com/HEYyG6t.jpg"
    img3 = "https://i.imgur.com/u1DokH7.jpg"
    img4 = "https://i.imgur.com/vTO84Hy.jpg"
    img5 = "https://i.imgur.com/Cg9Vgy2.jpg"
    img6 = "https://i.imgur.com/mFJyggj.jpg"
    images = [img1, img2, img3, img4, img5, img6]
    photos = [ImageTk.PhotoImage(Image.open(BytesIO(requests.get(x).content))) for x in images]
    panel = tk.Label()
    panel.photos = photos 
    panel.counter = 0
    panel.subcounter = 0
    def next_pic():
        if(not pause):
            panel['image'] = panel.photos[panel.counter%len(panel.photos)]
            if(panel.subcounter == 9):
                panel.after(500, next_pic)
                panel.subcounter = 0
                panel.counter += 1
            else:
                panel.after(500, next_pic)
                panel.subcounter += 1
            if(not cont):
                root.destroy()
                root.quit()
                return
        else:
            panel.after(500, next_pic)
    panel.pack(side="bottom", fill="both", expand="yes")
    next_pic()
    root.mainloop()

if __name__ == "__main__":
    # Creates recognizer and microphone instances
    t1 = threading.Thread(target=listen)
    t2 = threading.Thread(target=play)
    t1.start()
    t2.start()
    t1.join()
    print("T1 joined")
    t2.join()
    print("T2 joined")
    exit()
    
    