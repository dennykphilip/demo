from flask import Flask, render_template, jsonify, redirect, request, url_for
import os
import time
from PIL import Image
import matplotlib.pyplot as plt
import pronouncing
from gtts import gTTS
import pygame
import speech_recognition as sr
from matplotlib.widgets import Button

app = Flask(__name__)

pygame.mixer.init()
recognizer = sr.Recognizer()

phoneme_groups = {
    'closed': {'m', 'b', 'p'},
    'slight': {'d', 'e', 'g', 'h', 'k', 'l', 'n', 'ng', 's', 'ue'},
    'teeth': {'air', 'ch', 'ee', 'f', 'r', 't', 'th', 'v', 'x', 'y', 'z'},
    'wide': {'a', 'ae', 'ear', 'er', 'i', 'ie', 'u'},
    'round': {'j', 'oi', 'oo', 'or', 'q', 'sh', 'w', 'zh'},
    'open': {'ar', 'aw', 'o', 'oa', 'ou'}
}

messages = {
    "welcome": "Welcome to the interview. Let's get started!",
    "thankyou": "Thank you for your time. This concludes the interview."
}

questions = {
    "Tell me about yourself.": ["experience", "skills", "learning", "data"],
    "Why do you want to become a data analyst?": ["insights", "curiosity", "problem-solving", "impact"],
    # Add more questions as needed
}

@app.route('/')
def dashboard():
    return render_template('dash.html')

@app.route('/start_interview', methods=['POST'])
def start_interview():
    """Trigger the interview process."""
    fig, img_display = initialize_image_display()
    conduct_interview(img_display)
    return jsonify({'status': 'Interview completed'})


def conduct_interview(img_display):
    """Run the interview process and return questions and answers."""
    play_message_with_phonemes(messages["welcome"], "welcome", img_display)

    results = []  # To store question-answer pairs
    for i, (question, _) in enumerate(questions.items(), 1):
        print(f"Question: {question}")
        play_message_with_phonemes(question, f"question_{i}", img_display)

        answer = listen_with_image(img_display)
        if answer:
            print(f"Answer: {answer}")
            results.append({'question': question, 'answer': answer})  # Append to results

    play_message_with_phonemes(messages["thankyou"], "thankyou", img_display)
    return jsonify({'status': 'Interview completed', 'results': results})

def generate_audio(text, audio_file):
    """Generate audio from text."""
    try:
        tts = gTTS(text=text, lang='en')
        tts.save(audio_file)
        pygame.mixer.music.load(audio_file)
    except Exception as e:
        print(f"Error generating audio: {e}")

def extract_phonemes(text):
    """Extract phonemes from the given text."""
    words = text.split()
    phonemes = []
    for word in words:
        pronunciations = pronouncing.phones_for_word(word)
        if pronunciations:
            phonemes.extend(pronunciations[0].split())
        else:
            phonemes.extend(list(word.lower()))
    return phonemes

def group_phonemes(phonemes):
    """Group phonemes by category."""
    grouped = []
    for phoneme in phonemes:
        for group, members in phoneme_groups.items():
            if phoneme in members:
                grouped.append(group)
                break
    return grouped

def initialize_image_display():
    """Initialize a figure with an image display and a close button."""
    fig = plt.figure(figsize=(6, 6))  # Adjust size for image
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)  # Add border

    # Create axis for the image display
    ax_img = fig.add_subplot(111)
    ax_img.axis('off')  # Hide axes

    img_display = ax_img.imshow(Image.new('RGB', (800, 800)))  # Placeholder image

    plt.ion()  # Enable interactive mode
    plt.show()
    return fig, img_display

def update_image(image_path, img_display):
    """Update the image displayed."""
    if os.path.exists(image_path):
        img = Image.open(image_path)
        img_display.set_data(img)  # Update displayed image
        plt.draw()
        plt.pause(0.001)
    else:
        print(f"Image not found: {image_path}")

def display_group_images(groups, total_duration, img_display):
    """Display phoneme group images during playback."""
    image_dir = r'C:\Users\phili\PycharmProjects\virtualRecruiter\phonemes'
    group_duration = total_duration / len(groups)

    for i, group in enumerate(groups):
        target_time = i * group_duration * 1000
        while pygame.mixer.music.get_pos() < target_time:
            time.sleep(0.01)
        image_path = os.path.join(image_dir, f"{group}.jpg")
        update_image(image_path, img_display)

def play_message_with_phonemes(text, label, img_display):
    """Play message with phoneme images."""
    audio_file = f"{label}.mp3"
    generate_audio(text, audio_file)

    phonemes = extract_phonemes(text)
    phoneme_groups_list = group_phonemes(phonemes)
    audio_length = pygame.mixer.Sound(audio_file).get_length()

    pygame.mixer.music.play()
    display_group_images(phoneme_groups_list, total_duration=audio_length, img_display=img_display)

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

def listen_with_image(img_display):
    """Display 'closed' image while listening."""
    closed_mouth_image = r'C:\Users\phili\PycharmProjects\virtualRecruiter\phonemes\closed.jpg'
    update_image(closed_mouth_image, img_display)

    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
        except sr.RequestError:
            print("Network error.")
        except sr.WaitTimeoutError:
            print("Listening timed out.")
    return None


if __name__ == '__main__':
    app.run(debug=True)