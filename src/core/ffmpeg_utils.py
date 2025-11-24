import subprocess

def merge_audio(video_no_audio:str, video_with_audio:str, output_path:str):
    res = subprocess.run([
        'ffmpeg', 
        '-i', video_no_audio, 
        '-i', video_with_audio, 
        '-map', '0:v',
        '-map', '1:a', 
        '-c', 'copy', 
        '-y', output_path
    ], check=True)