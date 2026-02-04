import subprocess
import logging

def merge_audio(video_no_audio:str, video_with_audio:str, output_path:str):
    try:
        cmd = [
            'ffmpeg', 
            '-i', video_no_audio, 
            '-i', video_with_audio, 
            '-map', '0:v', 
            '-map', '1:a', 
            '-c', 'copy', 
            '-y', output_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        
    except subprocess.CalledProcessError:
        logging.warning('Audio stream not found or merge failed. Saving video without audio.')
        try:
            subprocess.run([
                'ffmpeg', '-i', video_no_audio, '-c', 'copy', '-y', output_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logging.error(f'Critical ffmpeg error: {e}')