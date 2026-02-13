import subprocess
import logging
import os

CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0

def start_ffmpeg_process(output_path:str, fps:float, width:int, height:int, input_source=None):
    """
    Запускает FFmpeg в режиме ожидания сырых кадров через PIPE (stdin).
    """
    cmd = [
        'ffmpeg',
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{width}x{height}',
        '-pix_fmt', 'bgr24',
        '-r', str(fps),
        '-i', '-'
    ]
    
    if input_source and os.path.exists(input_source):
        cmd += [
            '-i', input_source, 
            '-map', '0:v',
            '-map', '1:a?'        
            ]
    else:
        cmd += ['-map', '0:v']
    
    cmd += [
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'medium',
        '-crf', '18',
        '-c:a', 'copy',
        output_path
    ]
    
    logging.info(f'Starting FFmpeg pipe: {cmd}')
        
    return subprocess.Popen(
        cmd, 
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, 
        creationflags=CREATE_NO_WINDOW
    )


# def merge_audio(video_no_audio:str, video_with_audio:str, output_path:str):
#     """
#     Накладывает аудиодорожку из video_with_audio на видео из video_no_audio и сохраняет в output_path.
#     """
#     creationflags = CREATE_NO_WINDOW
#     try:
#         cmd = [
#             'ffmpeg', 
#             '-i', video_no_audio, 
#             '-i', video_with_audio, 
#             '-map', '0:v', 
#             '-map', '1:a', 
#             '-c', 'copy', 
#             '-y', output_path
#         ]
#         logging.info('FFmpeg process started.')
#         subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=creationflags)
#         logging.info('FFmpeg process finished successfully.')
        
#     except subprocess.CalledProcessError:
#         logging.warning('Audio stream not found or merge failed. Saving video without audio.')
#         try:
#             cmd = [
#                 'ffmpeg',
#                 '-i', video_no_audio,
#                 '-c', 'copy',
#                 '-y', output_path
#             ]
#             subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=creationflags)
#             logging.info('FFmpeg succeeded without audio.')
#         except subprocess.CalledProcessError:
#             logging.warning('Failed to save video without audio.')
            
# def merge_frames_to_video(frames_dir:str, input_path:str, output_path:str, fps:float):
#     """
#     Собирает видео из кадров в frames_dir.
#     Пытается взять аудио из input_path и наложить на итоговое видео.
#     """
#     abs_frames_dir = os.path.abspath(frames_dir).replace('\\', '/')
#     input_pattern = f'{abs_frames_dir}/frame_%08d.jpg'
    
#     logging.info(f'FFmpeg pattern: {input_pattern}')
    
#     base_args = [
#         '-c:v', 'libx264',
#         '-pix_fmt', 'yuv420p',
#         '-preset', 'medium',
#         '-crf', '23',
#         '-y', output_path
#     ]
    
#     creationflags=CREATE_NO_WINDOW
    
#     try:
#         cmd = [
#             'ffmpeg', 
#             '-framerate', str(fps),
#             '-i', input_pattern,
#             '-i', input_path,
#             '-map', '0:v',
#             '-map', '1:a',
#             '-c:a', 'copy'
#         ] + base_args
#         subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, creationflags=creationflags)
#         logging.info('FFmpeg process finished successfully.')
        
#     except subprocess.CalledProcessError as e:
#         logging.warning(f'FFmpeg process failed.')
        
#         try:
#             cmd = [
#                 'ffmpeg', 
#                 '-framerate', str(fps),
#                 '-i', input_pattern,
#             ] + base_args
#             subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=creationflags)
#             logging.info('FFmpeg succeeded without audio.')
#         except subprocess.CalledProcessError as e2:
#             error_output = e2.stderr.decode('utf-8', errors='ignore')
#             logging.error(f'FFmpeg fallback error details:\n{error_output}')