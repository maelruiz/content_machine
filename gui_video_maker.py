import tkinter
import whisper
import os
import cv2
from moviepy.editor import ImageSequenceClip, AudioFileClip, VideoFileClip, clips_array, concatenate_videoclips
from tqdm import tqdm
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import threading
import argparse
from tkterminal import Terminal

class VideoTranscriber:
    def __init__(self, master):
        self.master = master
        self.master.title("Video Processor GUI")
        self.process_thread = None 
        self.original_video_path = tk.StringVar()
        self.additional_video_path = tk.StringVar()
        self.output_video_path = tk.StringVar()
        self.transcription_stage_output = tk.StringVar()

        # Create labels and entry widgets
        tk.Label(master, text="Original Video Path:").grid(row=0, column=0, sticky="e")
        tk.Entry(master, textvariable=self.original_video_path, width=50).grid(row=0, column=1)
        tk.Button(master, text="Browse", command=self.browse_original).grid(row=0, column=2)
        tk.Label(master, text="Additional Video Path:").grid(row=1, column=0, sticky="e")
        tk.Entry(master, textvariable=self.additional_video_path, width=50).grid(row=1, column=1)
        tk.Button(master, text="Browse", command=self.browse_additional).grid(row=1, column=2)
        tk.Label(master, text="Output Video Path:").grid(row=2, column=0, sticky="e")
        tk.Entry(master, textvariable=self.output_video_path, width=50).grid(row=2, column=1)
        tk.Button(master, text="Browse", command=self.browse_output).grid(row=2, column=2)
        tk.Label(master, text="Transcription Stage Path:").grid(row=3, column=0, sticky="e")
        tk.Entry(master, textvariable=self.transcription_stage_output, width=50).grid(row=3, column=1)
        tk.Button(master, text="Browse", command=self.browse_transcription_stage_output).grid(row=3, column=2)
        
        tk.Label(master, text="Text Color:").grid(row=5, column=0, sticky="e")
        self.text_color = tk.Entry(master)
        self.text_color.grid(row=5, column=1)
        self.text_color.insert(0,"0,0,255")
        tk.Label(master, text="Text Position X:").grid(row=6, column=0, sticky="e")
        self.text_x = tk.Entry(master)
        self.text_x.grid(row=6, column=1)
        self.text_x.insert(0,'0')
        tk.Label(master, text="Text Position Y:").grid(row=7, column=0, sticky="e")
        self.text_y = tk.Entry(master)
        self.text_y.grid(row=7, column=1)
        self.text_y.insert(0,"0")
        tk.Label(master, text="Text Size:").grid(row=8, column=0, sticky="e")
        self.text_size = tk.Entry(master)
        self.text_size.grid(row=8, column=1)   
        self.text_size.insert(0,2)
        tk.Label(master, text="Text Font:").grid(row=9, column=0, sticky="e")
        self.text_font = tk.Entry(master)
        self.text_font.grid(row=9, column=1)
        self.text_font.insert(0,"0")
        tk.Label(master, text="Batch Size:").grid(row=10, column=0, sticky="e")
        self.batch_size = tk.Entry(master)
        self.batch_size.grid(row=10, column=1)
        self.batch_size.insert(0,"50")
        tk.Label(master, text="Model type:").grid(row=11, column=0, sticky="e")
        self.model_path = tk.Entry(master)
        self.model_path.grid(row=11, column=1)
        self.model_path.insert(0,"base")
        # Create the progress bar     
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(master, variable=self.progress_var, mode="determinate")
        self.progress_bar.grid(row=12, columnspan=3, pady=10)
        # Create the process button
        tk.Button(master, text="Process Video", command=self.process_video).grid(row=13, columnspan=3, pady=10)
        self.terminal = Terminal(pady=10, padx=10)
        self.terminal.shell = True
        self.terminal.linebar = True
        self.terminal.grid(row=12, column=0, columnspan=3, sticky="nsew")
    def choose_text_color(self):
        color = tkinter.colorchooser.askcolor()[1]
        self.text_color.delete(0, tk.END)
        self.text_color.insert(0, color)
    
    def browse_original(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
        self.original_video_path.set(file_path)
    def browse_additional(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
        self.additional_video_path.set(file_path)
    def browse_output(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("Video files", "*.mp4")])
        self.output_video_path.set(file_path)
    def browse_transcription_stage_output(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("Video files", "*.mp4")])
        self.transcription_stage_output.set(file_path)
    def process_video_threaded(self):
        original_path = self.original_video_path.get()
        additional_path = self.additional_video_path.get()
        output_path = self.output_video_path.get()
        if not all([original_path, additional_path, output_path]):
            tk.messagebox.showerror("Error", "Please provide all paths.")
            return
        self.model = whisper.load_model(self.model_path.get())
        self.video_path = self.original_video_path
        self.text_array = []
        self.fps = 0
        self.char_width = 0
        final_video_path = self.output_video_path.get()
        transcription_stage_output = self.transcription_stage_output.get()
        self.progress_var.set(0)
        self.progress_bar.start()
        tk.messagebox.showinfo("Success", "Starting process.")
        self.extract_audio()
        tk.messagebox.showinfo("Success", "Finished extracting audio.")
        self.transcribe_video()
        tk.messagebox.showinfo("Success", "Finished transcribing video.")
        self.create_video(transcription_stage_output)
        tk.messagebox.showinfo("Success", "Finished creating video.")
        self.add_video_below(self.transcription_stage_output.get(), self.additional_video_path.get(), final_video_path)
        tk.messagebox.showinfo("Success", "Finished adding video, output now finished and outputted at: " + final_video_path + ".")
        self.progress_bar.stop()
    def process_video(self):
        # Check if another processing thread is running
        if self.process_thread and self.process_thread.is_alive():
            tk.messagebox.showinfo("Info", "Processing is already in progress.")
            return
        # Create a new thread for video processing
        self.process_thread = threading.Thread(target=self.process_video_threaded)
        self.process_thread.start()
        
        
    def transcribe_video(self):
        assert os.path.isfile(self.original_video_path.get())
        result = self.model.transcribe(self.original_video_path.get())
        print('Transcribing video')
        result = self.model.transcribe(self.audio_path)
        text = result["segments"][0]["text"]
        textsize = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        cap = cv2.VideoCapture(self.video_path.get())
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        asp = width/height
        
        ret, frame = cap.read()
        width = frame[:, int(int(width - 1 / asp * height) / 2):width - int((width - 1 / asp * height) / 2)].shape[1]
        width = width - (width * 0.1)
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.char_width = int(textsize[0] / len(text))
                
        for j in tqdm(result["segments"]):
            lines = [1-2]
            text = j["text"]
            end = j["end"]
            start = j["start"]
            total_frames = int((end - start) * self.fps)
            start = start * self.fps
            total_chars = len(text)
            words = text.split(" ")
            i = 0
                    
            while i < len(words):
                words[i] = words[i].strip()
                if words[i] == "":
                    i += 1
                    continue
                length_in_pixels = len(words[i]) * self.char_width
                remaining_pixels = width - length_in_pixels
                line = words[i] 
                        
                while remaining_pixels > 0:
                    i += 1 
                    if i >= len(words):
                        break
                    length_in_pixels = len(words[i]) * self.char_width
                    remaining_pixels -= length_in_pixels
                    if remaining_pixels < 0:
                        continue
                    else:
                        line += " " + words[i]
                        
                line_array = [line, int(start) + 15, int(len(line) / total_chars * total_frames) + int(start) + 15]
                start = int(len(line) / total_chars * total_frames) + int(start)
                lines.append(line_array)
                self.text_array.append(line_array)
                
        cap.release()
        print('Transcription complete')
            
    def extract_audio(self, output_audio_path='./audio.mp3'):
        print('Extracting audio')
        video = VideoFileClip(self.video_path.get())
        audio = video.audio 
        audio.write_audiofile(output_audio_path)
        self.audio_path = output_audio_path
        print('Audio extracted')
    
    def extract_frames(self, output_folder, batch_size=50):
        print('Extracting frames')
        cap = cv2.VideoCapture(self.video_path.get())
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        asp = width / height
        N_frames = 0

        while True:
            frames = []
            for _ in range(batch_size):
                ret, frame = cap.read()
                if not ret:
                    break

                #frame = frame[:, int(int(width - 1 / asp * height) / 2):width - int((width - 1 / asp * height) / 2)]
                frame = cv2.resize(frame, (width, height))
                frames.append(frame)

            if not frames:
                break 

            self.process_frames(frames, N_frames, output_folder)
            N_frames += batch_size

        cap.release()
        print('Frames extracted')

    def process_frames(self, frames, start_frame, output_folder):
        for i, frame in enumerate(frames):
            for j in self.text_array:
                if start_frame + i >= j[1] and start_frame + i <= j[2]:
                    text = j[0]
                    text_size, _ = cv2.getTextSize(text, int(self.text_font.get()), 0.8, int(self.text_size.get()))
                    text_x = int(self.text_x.get())
                    text_y = int(self.text_y.get())
                    text_color = tuple(map(int, self.text_color.get().split(',')))
                    cv2.putText(frame, text, (text_x, text_y), int(self.text_font.get()), 0.75, text_color, int(self.text_size.get()))
                    break

            cv2.imwrite(os.path.join(output_folder, str(start_frame + i) + ".jpg"), frame)

    def create_video(self, output_video_path):
        print('Creating video')
        image_folder = os.path.join(os.path.dirname(self.video_path.get()), "frames")
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)

        self.extract_frames(image_folder)

        print("Video being saved at:", output_video_path)
        images = [img for img in os.listdir(image_folder) if img.endswith(".jpg")]
        images.sort(key=lambda x: int(x.split(".")[0]))

        # Resize all frames to a smaller resolution and save in batches
        batch_size = self.batch_size.get()
        clips = []

        for i in range(0, len(images), int(len(images) / int(batch_size))):
            batch_images = images[i:i+int(batch_size)]
            resized_images = [cv2.imread(os.path.join(image_folder, image)) for image in batch_images]

            clip = ImageSequenceClip(resized_images, fps=self.fps)
            clips.append(clip)

        final_clip = concatenate_videoclips(clips)
        
        # Extract audio once
        audio = AudioFileClip(self.audio_path)
        final_clip = final_clip.set_audio(audio)

        final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac")

        print('Video created and saved')

            
    def add_video_below(self, original_video_path, additional_video_path, output_video_path):
        original_clip = VideoFileClip(original_video_path)
        
        additional_clip = VideoFileClip(additional_video_path, audio=False)
        
        additional_clip = additional_clip.set_duration(original_clip.duration)
        
        final_clip = clips_array([[original_clip], [additional_clip]])
        
        final_clip.write_videofile(output_video_path)
# Usage

parser = argparse.ArgumentParser(description="Video Processor with GUI")
parser.add_argument("--model_path", type=str, help="Path to the model", default="base")
parser.add_argument("--video_path", type=str, help="Path to the input video", default="./5minsvid.mp4")
parser.add_argument("--audio_path", type=str, help="Path to the audio file", default="")
parser.add_argument("--output_video_path", type=str, help="Path to the output video", default="./output.mp4")
parser.add_argument("--additional_video_path", type=str, help="Path to the additional video", default="./minecraft.mp4")

args = parser.parse_args()

root = tk.Tk()
transcriber = VideoTranscriber(root)

root.mainloop() 
