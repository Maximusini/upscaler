import cv2
import os
from src.core.ffmpeg_utils import merge_audio

class VideoUpscaler:
    def __init__(self, upscaler):
        self.upscaler = upscaler
        
    def process_video(self, input_path:str, output_path:str, progress=None):
        video = cv2.VideoCapture(input_path)
        
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width  = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))

        final_height = height * self.upscaler.scale
        final_width = width * self.upscaler.scale
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('temp.mp4', fourcc, fps, (final_width, final_height))
        
        current_frame = 0
        while video.isOpened():
            ret, frame = video.read()
            
            current_frame += 1
            if (current_frame % 10) == 0:
                print(f'Обработано ', current_frame, '/', frame_count)

            if progress != None:
                percent = int(current_frame / frame_count * 100)
                progress(percent)
                
            if not ret:
                print('Видео закончилось.')
                break
            out.write(self.upscaler.process_image(frame))

        video.release()
        out.release()
                
        merge_audio('temp.mp4', input_path, output_path)
        
        os.remove('temp.mp4')
        