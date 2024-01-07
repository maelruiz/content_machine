import tkinter
import whisper
import os
import cv2
from moviepy.editor import ImageSequenceClip, AudioFileClip, VideoFileClip, clips_array
from tqdm import tqdm
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import threading
import argparse

class VideoTranscriber:
    def __init__(self, model_path, video_path, audio_path, master):
        self.master = master
        self.master.title("Video Processor GUI")
        self.process_thread = None 
        self.original_video_path = tk.StringVar()
        self.additional_video_path = tk.StringVar()
        self.output_video_path = tk.StringVar()

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
        
        tk.Label(master, text="Text Color:").grid(row=5, column=0, sticky="e")
        self.text_color = tk.Entry(master)
        self.text_color.grid(row=5, column=1)
        self.text_color.insert(0,"0,0,255")

        tk.Label(master, text="Text Position X:").grid(row=6, column=0, sticky="e")
        self.text_x = tk.Entry(master)
        self.text_x.grid(row=6, column=1)
        self.text_x.insert(0,'int(("frame.shape[1] - text_size[0]) / 2)"')

        tk.Label(master, text="Text Position Y:").grid(row=7, column=0, sticky="e")
        self.text_y = tk.Entry(master)
        self.text_y.grid(row=7, column=1)
        self.text_y.insert(0,"int(height/2)")

        tk.Label(master, text="Text Size:").grid(row=8, column=0, sticky="e")
        self.text_size = tk.Entry(master)
        self.text_size.grid(row=8, column=1)   
        self.text_size.insert(0,2)
        
        # Create the progress bar     
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(master, variable=self.progress_var, mode="determinate")
        self.progress_bar.grid(row=3, columnspan=3, pady=10)

        # Create the process button
        tk.Button(master, text="Process Video", command=self.process_video).grid(row=4, columnspan=3, pady=10)

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

    def process_video_threaded(self):
        original_path = self.original_video_path.get()
        additional_path = self.additional_video_path.get()
        output_path = self.output_video_path.get()

        if not all([original_path, additional_path, output_path]):
            tk.messagebox.showerror("Error", "Please provide all paths.")
            return

        self.model = whisper.load_model(model_path)
        self.video_path = video_path
        self.audio_path = audio_path
        self.text_array = []
        self.fps = 0
        self.char_width = 0
        final_video_path = self.output_video_path.get()
        self.progress_var.set(0)
        self.progress_bar.start()
        tk.messagebox.showinfo("Success", "Starting process.")
        transcriber.extract_audio()
        tk.messagebox.showinfo("Success", "Finished extracting audio.")
        transcriber.transcribe_video()
        tk.messagebox.showinfo("Success", "Finished transcribing video.")
        transcriber.create_video(final_video_path)
        tk.messagebox.showinfo("Success", "Finished creating video.")
        transcriber.add_video_below(final_video_path, add_video, final_video_path)
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
        assert os.path.isfile(audio_path)
        result = self.model.transcribe(audio_path)
        print('Transcribing video')
        result = self.model.transcribe(self.audio_path)
        text = result["segments"][0]["text"]
        textsize = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        cap = cv2.VideoCapture(self.video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        asp = 16/9
        ret, frame = cap.read()
        width = frame[:, int(int(width - 1 / asp * height) / 2):width - int((width - 1 / asp * height) / 2)].shape[1]
        width = width - (width * 0.1)
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.char_width = int(textsize[0] / len(text))
                
        for j in tqdm(result["segments"]):
            lines = []
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
        video = VideoFileClip(self.video_path)
        audio = video.audio 
        audio.write_audiofile(output_audio_path)
        self.audio_path = output_audio_path
        print('Audio extracted')
    
    def extract_frames(self, output_folder):
        print('Extracting frames')
        cap = cv2.VideoCapture(self.video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        asp = width / height
        N_frames = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            #frame = frame[:, int(int(width - 1 / asp * height) / 2):width - int((width - 1 / asp * height) / 2)]
            
            for i in self.text_array:
                if N_frames >= i[1] and N_frames <= i[2]:
                    text = i[0]
                    text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                    text_x = int(self.text_x.get())
                    text_y = int(self.text_y.get())
                    text_color = tuple(map(int, self.text_color.get().split(',')))

                    cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, text_color, float(self.text_size.get()))
                    break
            
            cv2.imwrite(os.path.join(output_folder, str(N_frames) + ".jpg"), frame)
            N_frames += 1
        
        cap.release()
        print('Frames extracted')

    def create_video(self, output_video_path):
        print('Creating video')
        image_folder = os.path.join(os.path.dirname(self.video_path), "frames")
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)
        
        self.extract_frames(image_folder)
        
        print("Video being saved at:", output_video_path)
        images = [img for img in os.listdir(image_folder) if img.endswith(".jpg")]
        images.sort(key=lambda x: int(x.split(".")[0]))
        
        frame = cv2.imread(os.path.join(image_folder, images[0]))
        height, width, layers = frame.shape
        
        clip = ImageSequenceClip([os.path.join(image_folder, image) for image in images], fps=self.fps)
        audio = AudioFileClip(self.audio_path)
        clip = clip.set_audio(audio)
        clip.write_videofile(output_video_path)
        print('Video created and saved')
        
    def add_video_below(self, original_video_path, additional_video_path, output_video_path):
        original_clip = VideoFileClip(original_video_path)
        
        additional_clip = VideoFileClip(additional_video_path, audio=False)
        
        additional_clip = additional_clip.set_duration(original_clip.duration)
        
        final_clip = clips_array([[original_clip], [additional_clip]])
        
        final_clip.write_videofile(output_video_path)

# Usage


model_path = "base"
video_path = "./5minsvid.mp4"
output_video_path = "./output.mp4"
final_video_path = "./final.mp4"
audio_path = os.path.join(os.getcwd(), "audio.mp3")
add_video = "./minecraft.mp4"

parser = argparse.ArgumentParser(description="Video Processor with GUI")
parser.add_argument("--model_path", type=str, help="Path to the model", default="base")
parser.add_argument("--video_path", type=str, help="Path to the input video", default="./5minsvid.mp4")
parser.add_argument("--audio_path", type=str, help="Path to the audio file", default="")
parser.add_argument("--output_video_path", type=str, help="Path to the output video", default="./output.mp4")
parser.add_argument("--additional_video_path", type=str, help="Path to the additional video", default="./minecraft.mp4")

args = parser.parse_args()

root = tk.Tk()
transcriber = VideoTranscriber(model_path, video_path, audio_path, root)
root.mainloop()
