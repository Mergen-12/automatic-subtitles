import speech_recognition as sr
import pysrt
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from datetime import timedelta
import os

change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

# Specify input and output paths
input_video_path = "test.mp4"
output_path = "output"
audio_file_path = os.path.join(output_path, "audio.wav")
srt_file_path = os.path.join(output_path, "test_subtitles.srt")
output_video_file = os.path.join(output_path, "test_subtitled.mp4")

# Function to extract audio from the video
def extract_audio(input_video_path, output_audio_path):
    video_clip = VideoFileClip(input_video_path)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(output_audio_path)
    audio_clip.close()

# Initialize an empty list to store subtitles
subtitles = []
# Function to transcribe audio using Google Speech Recognition

recognizer = sr.Recognizer()

# Load the audio file
audio_clip = sr.AudioFile(audio_file_path)

with audio_clip as source:
        # Adjust for ambient noise
    recognizer.adjust_for_ambient_noise(source)
    audio = recognizer.record(source)

    # Perform speech-to-text
    try:
        text = recognizer.recognize_google(audio)
        sentences = text.split()  # Split text into sentences

        subtitles.extend(sentences)
    except sr.UnknownValueError:
        print("Could not understand audio")

# Convert wav to audio_segment
audio_segment = AudioSegment.from_wav(audio_file_path)
# print("Audio Duration (seconds):", audio_segment.duration_seconds)
# Normalize audio_segment to -20dBFS 
normalized_sound = audio_segment.set_frame_rate(44100).set_channels(1)
normalized_sound = normalized_sound - normalized_sound.dBFS + 20.0


# Print detected non-silent chunks, which in our case would be spoken words.
nonsilent_data = detect_nonsilent(normalized_sound, min_silence_len=500, silence_thresh=-20, seek_step=1)
# print("Non-silent chunks:", nonsilent_data)
# Convert ms to seconds and create SRT timestamps
max_segment_duration = 6
timestamps = []
for chunks in nonsilent_data:
    start_time = chunks[0] / 1000
    end_time = chunks[1] / 1000

    # Calculate the number of segments needed
    num_segments = int((end_time - start_time) / max_segment_duration) + 1

    # Adjust timestamps for each segment
    for i in range(num_segments):
        segment_start = start_time + i * max_segment_duration
        segment_end = min(start_time + (i + 1) * max_segment_duration, end_time)

        timestamps.append((segment_start, segment_end))

# print(subtitles)
# Calculate the average number of subtitles per chunk
average_subtitles_per_chunk = len(subtitles) / len(timestamps)

# Create SRT subtitle file
with open(srt_file_path, 'w') as srt_file:
    subtitle_number = 1
    space = 1
    for timestamp in timestamps:
        start_time_str = str(timedelta(seconds=timestamp[0]))
        end_time_str = str(timedelta(seconds=timestamp[1]))
        
        if 1 < space:
            srt_file.write ('\n')
            srt_file.write ('\n')
        space+=1
        srt_file.write(str(subtitle_number) + '\n')
        srt_file.write(start_time_str.replace('.', ',')[:-3] + ' --> ' + end_time_str.replace('.', ',')[:-3] + '\n')

        # Calculate the range of subtitles to assign to this chunk
        start_subtitle_idx = int((subtitle_number - 1) * average_subtitles_per_chunk)
        end_subtitle_idx = int(subtitle_number * average_subtitles_per_chunk)

        # Assign subtitles to the chunk
        for i in range(start_subtitle_idx, min(end_subtitle_idx, len(subtitles))):
            srt_file.write(subtitles[i].strip() + ' ')

        subtitle_number += 1


    # print("Timestamps:", timestamps)
    # Calculate the total duration of the audio (in seconds)
    audio_duration = audio_segment.duration_seconds

def time_to_seconds(time_obj):
    return time_obj.hours * 3600 + time_obj.minutes * 60 + time_obj.seconds + time_obj.milliseconds / 1000


def create_subtitle_clips(subtitles, videosize,fontsize=24, font='Arial', color='yellow', debug = False):
    subtitle_clips = []

    for subtitle in subtitles:
        start_time = time_to_seconds(subtitle.start)
        end_time = time_to_seconds(subtitle.end)
        duration = end_time - start_time

        video_width, video_height = videosize
        
        text_clip = TextClip(subtitle.text, fontsize=fontsize, font=font, color=color, bg_color = 'black',size=(video_width*3/4, None), method='caption').set_start(start_time).set_duration(duration)
        subtitle_x_position = 'center'
        subtitle_y_position = video_height* 4 / 5 

        text_position = (subtitle_x_position, subtitle_y_position)                    
        subtitle_clips.append(text_clip.set_position(text_position))

    return subtitle_clips

# Load video and SRT file
video = VideoFileClip(input_video_path)
subtitles = pysrt.open(srt_file_path)

# Create subtitle clips
subtitle_clips = create_subtitle_clips(subtitles, video.size)

# Add subtitles to the video
final_video = CompositeVideoClip([video] + subtitle_clips)

# Write output video file
final_video.write_videofile(output_video_file)
