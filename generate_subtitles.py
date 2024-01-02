# Import necessary libraries and modules
import os
import cv2
import speech_recognition as sr
from moviepy.editor import ImageSequenceClip, AudioFileClip, VideoFileClip
from tqdm import tqdm
from pydub import AudioSegment

class VideoTranscriber:
    def __init__(self, video_path):
        # Initialize the recognizer for speech recognition
        self.recognizer = sr.Recognizer()
        self.video_path = video_path
        self.audio_path = ''  # Placeholder for audio path after extraction
        self.text_array = []  # To store transcribed text
        self.fps = 0  # Frames per second

    def transcribe_video(self):
        print('Transcribing video')

        # Capture FPS and total frame count of the video
        cap = cv2.VideoCapture(self.video_path)
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        # Validate FPS value
        if self.fps == 0:
            raise ValueError("The frames per second (fps) of the video could not be determined or is zero.")

        # Transcribe the audio to text using Google's speech recognition API
        with sr.AudioFile(self.audio_path) as source:
            audio_data = self.recognizer.record(source)
            result = self.recognizer.recognize_google(audio_data, show_all=True)

            # Check if the transcription was successful
            if not result or 'alternative' not in result:
                print("Transcription failed.")
                return

            text = result['alternative'][0]['transcript']

            # Save the transcribed text to a file, with every 15 words on a new line
            with open('SubtitleGenerator.txt', 'w') as file:
                words = text.split()
                for i in range(0, len(words), 15):
                    file.write(' '.join(words[i:i + 15]) + '\n')

            print("Transcription saved to SubtitleGenerator.txt")

            # Calculate how many frames each word lasts
            words = text.split()
            total_words = len(words)
            frames_per_word = total_frames / total_words

            # Populate the text_array with text segments for each frame
            for i in range(total_frames):
                start_word = int(i / frames_per_word)
                end_word = int((i + 1) / frames_per_word)

                if end_word > total_words:
                    end_word = total_words

                segment_text = ' '.join(words[start_word:end_word])
                self.text_array.append((segment_text, i, i + 1))

    def extract_audio(self, output_audio_path='audio_output/audio.wav'):
        print('Extracting audio')
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
        # Extract audio from the video
        video = VideoFileClip(self.video_path)
        audio = video.audio
        audio.write_audiofile(output_audio_path, codec="pcm_s16le")
        self.audio_path = output_audio_path
        print('Audio extracted')

    def extract_frames(self, output_folder):
        print('Extracting frames')
        cap = cv2.VideoCapture(self.video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        N_frames = 0

        # Loop over frames and add subtitles to them
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            segment_text, start_frame, end_frame = self.text_array[N_frames]
            text = segment_text

            # Calculate position for the text
            text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
            text_x = int((frame.shape[1] - text_size[0]) / 2)
            text_y = int(height - text_size[1] - 10)

            # Overlay text on frame
            cv2.putText(frame, text, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

            # Save the frame
            cv2.imwrite(os.path.join(output_folder, str(N_frames) + ".jpg"), frame)
            N_frames += 1

        cap.release()
        print('Frames extracted')

    def create_video(self, output_video_path):
        print('Creating video')
        # Create an image folder for extracted frames
        image_folder = os.path.join(os.path.dirname(self.video_path), "frames")
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)

        self.extract_frames(image_folder)

        # List and sort the frame images
        images = [img for img in os.listdir(image_folder) if img.endswith(".jpg")]
        images.sort(key=lambda x: int(x.split(".")[0]))

        # Ensure valid FPS value
        if not self.fps or self.fps <= 0:
            raise ValueError("The frames per second (fps) value is invalid.")

        # Create video from images and set the audio
        clip = ImageSequenceClip([os.path.join(image_folder, image) for image in images], fps=self.fps)
        audio = AudioFileClip(self.audio_path)
        if audio.duration > clip.duration:
            audio = audio.subclip(0, clip.duration)
        clip = clip.set_audio(audio)
        clip.write_videofile(output_video_path, codec='libx264', audio_codec='aac')
        print("Video saved at:", output_video_path)


# Main execution
video_path = "test_videos/Test.mp4"
output_video_path = "test_videos/output.mp4"

transcriber = VideoTranscriber(video_path)
transcriber.extract_audio()
transcriber.transcribe_video()
transcriber.create_video(output_video_path)

