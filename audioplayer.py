import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import sounddevice as sd
import threading
import time
import librosa

class MP3Player:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple MP3 Player")

        # Instance variables for audio control
        self.audio_file = None
        self.is_playing = False
        self.current_position = 0  # Store current playback position
        self.audio_data = None
        self.sample_rate = None
        self.streams = []  # List to keep track of output streams
        self.volume = 0.5  # Default volume

        # Get audio devices and filter for output devices only
        self.audio_devices = sd.query_devices()
        self.device_names = []
        self.device_ids = []

        for device in self.audio_devices:
            if device['max_output_channels'] > 0 and device['hostapi'] == 0:  # Avoid ASIO devices
                self.device_names.append(device['name'])
                self.device_ids.append(device['index'])

        if not self.device_names:
            messagebox.showerror("Error", "No output audio devices found.")
            root.destroy()
            return

        # GUI Elements
        self.file_label = tk.Label(root, text="No file selected")
        self.file_label.pack(pady=10)

        self.position_label = tk.Label(root, text="Current Position: 0:00")
        self.position_label.pack(pady=10)

        self.device_vars = [tk.BooleanVar() for _ in self.device_names]  # Track selected devices

        # Create checkboxes for device selection
        self.device_checkboxes = []  # Store references to checkboxes for later access
        for index, device_name in enumerate(self.device_names):
            cb = tk.Checkbutton(root, text=device_name, variable=self.device_vars[index])
            cb.pack(anchor='w')  # Align left
            self.device_checkboxes.append(cb)  # Store reference

        self.play_button = tk.Button(root, text="Play", command=self.play)
        self.play_button.pack(pady=10)

        self.stop_button = tk.Button(root, text="Stop", command=lambda: self.stop(False))
        self.stop_button.pack(pady=10)
        self.stop_button.config(state=tk.DISABLED)

        self.select_file_button = tk.Button(root, text="Select MP3 File", command=self.load_file)
        self.select_file_button.pack(pady=10)

        self.volume_scale = tk.Scale(root, from_=0, to=100, orient='horizontal', label='Volume', command=self.change_volume)
        self.volume_scale.set(50)  # Default volume set to 50%
        self.volume_scale.pack(pady=10)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("MP3 Files", "*.mp3")])
        if file_path:
            self.stop(False)
            self.current_position = 0  # Reset position to 0 when stopped
            self.update_position_label()

            self.audio_file = file_path
            self.file_label.config(text=f"Playing: {file_path.split('/')[-1]}")
            self.load_audio()  # Load the audio data

    def load_audio(self):
        self.audio_data, self.sample_rate = librosa.load(self.audio_file, sr=None, mono=False)

        if self.audio_data.ndim == 1:  # Mono audio
            self.audio_data = np.expand_dims(self.audio_data, axis=0)  # Convert to shape (1, samples)
        elif self.audio_data.ndim > 2:
            messagebox.showerror("Error", "Unsupported audio format. Please use mono or stereo files.")
            return

        if self.audio_data.shape[0] == 1:  # If there's only one channel
            self.audio_data = np.tile(self.audio_data, (2, 1))  # Duplicate the mono channel to make stereo

        self.audio_data = self.audio_data.astype(np.float32)  # Ensure audio data is float32

    def change_volume(self, value):
        self.volume = int(value) / 100.0  # Update the volume based on the slider

    def play(self):
        if self.audio_file and not self.is_playing:
            self.is_playing = True
            self.play_button.config(state=tk.DISABLED)  # Disable Play button
            self.stop_button.config(state=tk.NORMAL)
            self.set_device_selection_state(False)  # Disable device selection
            threading.Thread(target=self.play_sound).start()

    def play_sound(self):
        try:
            selected_devices = [self.device_ids[i] for i in range(len(self.device_vars)) if self.device_vars[i].get()]
            self.streams = []  # Reset streams list

            for selected_device in selected_devices:
                stream = sd.OutputStream(samplerate=self.sample_rate, channels=self.audio_data.shape[0], device=selected_device)
                stream.start()
                self.streams.append(stream)  # Store the stream

            while self.is_playing:
                if self.streams:  # Check if there are any active streams
                    start_index = int(self.current_position / 1000 * self.sample_rate)
                    end_index = start_index + int(0.1 * self.sample_rate)

                    if start_index < self.audio_data.shape[1]:
                        for stream in self.streams:  # Write to all active streams
                            stream.write((self.audio_data[:, start_index:end_index] * self.volume).T)
                        self.current_position += 100
                    else:
                        self.stop(False)

                time.sleep(0.1)
                self.update_position_label()

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.is_playing = False
            for stream in self.streams:  # Stop all streams
                if stream is not None:
                    stream.stop()
                    stream.close()
            self.streams = []  # Reset streams list
            self.play_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.set_device_selection_state(True)  # Re-enable device selection

    def stop(self, restart):
        self.is_playing = False
        for stream in self.streams:  # Stop all streams
            if stream is not None:
                stream.stop()
                stream.close()
        self.streams = []  # Reset streams list
        self.play_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.set_device_selection_state(True)  # Re-enable device selection
        if restart:
            self.play()

    def update_position_label(self):
        # Update the position label with the current position
        minutes, seconds = divmod(self.current_position // 1000, 60)
        self.position_label.config(text=f"Current Position: {minutes}:{seconds:02d}")

    def set_device_selection_state(self, state):
        # Enable or disable device selection checkboxes
        for cb in self.device_checkboxes:
            cb.config(state=tk.NORMAL if state else tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    player = MP3Player(root)
    root.mainloop()
