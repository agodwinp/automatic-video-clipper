import sys
from moviepy.editor import VideoFileClip
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile as wav
import av
import pandas as pd
import time
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import os

original_video = "main_2.mp4"
output_path = "/Volumes/ARUN'S USB/YouTube/Uni 2020 Tips/clips/"

def setdiff_sorted(array1,array2,assume_unique=False):
    ans = np.setdiff1d(array1,array2,assume_unique).tolist()
    if assume_unique:
        return sorted(ans)
    return ans

def process_original_video(file):
    print("- Processing original video")
    video = VideoFileClip(file)
    audio = video.audio
    audio_file = file[:-4]+"_audio.wav"
    audio.write_audiofile(audio_file, verbose=False, logger=None)
    return audio_file
    
def read_audio_file(file):
    print("- Reading audio file")
    rate, data = wav.read(file)
    left = data[:, 0]
    right = data[:, 1]
    print("- Merging stereo channels")
    signal = (left+right)/2
    print("- Plotting signal")
    time = np.linspace(0, len(signal)/rate, num=len(signal))
    plt.figure(1, figsize=(15, 8))
    plt.title("Original audio signal from video")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude (dB)")
    plt.plot(time, signal)
    plt.show()
    input("~~~ Press Enter to continue... ")
    return rate, signal

def smooth_signal(signal, rate, window=40000):
    print("- Smoothing signal")
    sma = pd.DataFrame()
    sma["sma"] = abs(signal)
    sma["sma"] = sma["sma"].rolling(window=window).mean()
    sma["sma"] = sma["sma"].fillna(0)
    print("- Plotting smoothed signal")
    print("- Prepare to choose a cutoff amplitude")
    # plot signal
    time = np.linspace(0, len(sma["sma"])/rate, num=len(sma["sma"]))
    plt.figure(1, figsize=(15, 8))
    plt.title("Smoothed audio signal from video")
    plt.xlabel("Time (s)")
    plt.ylabel("Absolute Amplitude |(dB)|")
    plt.plot(time, sma["sma"])
    plt.show()
    input("~~~ Press Enter to continue...")
    # let user choose cutoff
    cutoff = int(input("~~~ What do you want the cutoff to be? "))
    print("- Analysing signal")
    remove_idx = [i for i, v in enumerate(sma["sma"]) if v < cutoff]
    keep_idx = setdiff_sorted(range(len(signal)), remove_idx)
    # identify changepoints to return pairs of index values to cut video at
    changepoints = []
    buffer = keep_idx[0]
    print("- Identifying changepoints")
    for i, v in enumerate(keep_idx):
        if i == 0:
            changepoints.append(keep_idx[i])
            buffer = keep_idx[i]
        if i == len(keep_idx)-1:
            print("    ---> 100.00%")
        elif v == buffer+1:
            buffer = v
        elif v != buffer+1:
            changepoints.append(buffer)
            changepoints.append(v)
            buffer = v
        if i == len(keep_idx)-1:
            changepoints.append(v)
        if i%200000==0:
            print("    ---> {:.2f}%".format((i/len(keep_idx)*100)))
    # convert changpoints to seconds
    print("- Converting changepoints into seconds")
    increment = (len(signal)/rate)/len(signal)
    secs_to_keep = [i*(increment) for i in changepoints]
    reduced_length = len(keep_idx)
    original_length = len(range(0, len(signal)))
    return secs_to_keep, reduced_length, original_length

def clip_video(secs_to_keep):
    print("- Creating output video clips")
    secs_to_keep.reverse()
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    i = 0
    old_stdout = sys.stdout
    num_clips = len(secs_to_keep)/2
    while len(secs_to_keep)>0:
        print("    ---> {:.2f}%".format((i/num_clips)*100))
        start = secs_to_keep.pop(-1)
        end = secs_to_keep.pop(-1)
        sys.stdout = open(os.devnull, 'w')
        ffmpeg_extract_subclip(original_video, start, end, targetname=output_path+str(i)+".mp4")
        sys.stdout = old_stdout
        i+=1
    print("    ---> 100.00%")
    

if __name__ == "__main__":
    start = time.time()
    print("\n======== Starting video clipper! ========\n")
    audio_file = process_original_video(original_video)
    rate, signal = read_audio_file(audio_file)
    secs_to_keep, reduced_length, original_length = smooth_signal(signal, rate)
    clip_video(secs_to_keep)
    saving = 100-((reduced_length/original_length)*100)
    print("- Reduced the file size by {:.2f}%".format(saving))
    end = time.time()
    duration = end-start
    print("\n======== Finished in {:.2f} minutes! ========\n".format(duration/60))
