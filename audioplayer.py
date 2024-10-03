import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pygame
import sounddevice as sd
import threading

class AudioPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MP3 Player with Audio Device Selection")
        self.audio_file = None
        self.loop = False
        self.is_playing = False

        # Initialize pygame for audio playback
        pygame.mixer.init()

        # Set up GUI layout
        self.setup_gui()

    def setup_gui(self):
        # File selection button
        self.file_button = ttk.Button(self.root, text="Select MP3 File", command=self.select_file)
        self.file_button.pack(pady=10)

        # Listbox for selecting multiple audio devices
        self.device_listbox = tk.Listbox(self.root, selectmode=tk.MULTIPLE, height=10, width=50)
        self.device_listbox.pack(pady=10)
        self.populate_device_list()

        # Start and Stop buttons
        self.start_button = ttk.Button(self.root, text="Start", command=self.start_audio)
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = ttk.Button(self.root, text="Stop", command=self.stop_audio)
        self.stop_button.pack(side=tk.LEFT, padx=10)

        # Loop checkbox
        self.loop_var = tk.BooleanVar()
        self.loop_checkbutton = ttk.Checkbutton(self.root, text="Loop", variable=self.loop_var)
        self.loop_checkbutton.pack(pady=10)

    def populate_device_list(self):
        # Query available audio devices
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            self.device_listbox.insert(tk.END, f"Device {i}: {device['name']}")

    def select_file(self):
        # Open file dialog to select MP3 file
        file_path = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
        if file_path:
            self.audio_file = file_path
            messagebox.showinfo("File Selected", f"MP3 file '{self.audio_file}' selected.")

    def start_audio(self):
        if self.audio_file is None:
            messagebox.showwarning("No File", "Please select an MP3 file first!")
            return

        # Get selected audio devices
        selected_devices = self.device_listbox.curselection()
        if not selected_devices:
            messagebox.showwarning("No Devices", "Please select at least one audio device.")
            return

        # Play audio on a separate thread to keep the GUI responsive
        self.loop = self.loop_var.get()
        self.is_playing = True
        threading.Thread(target=self.play_audio, daemon=True).start()

    def play_audio(self):
        # Load the MP3 file using pygame mixer
        pygame.mixer.music.load(self.audio_file)
        pygame.mixer.music.play(loops=-1 if self.loop else 0)

        # Keep playing until the user stops it
        while pygame.mixer.music.get_busy() and self.is_playing:
            pass

    def stop_audio(self):
        self.is_playing = False
        pygame.mixer.music.stop()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioPlayerApp(root)
    root.mainloop()
