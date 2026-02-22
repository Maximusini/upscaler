import threading
import queue
import cv2
import os
import shutil
import logging
from neural_upscaler.engine.ffmpeg_wrapper import start_ffmpeg_process

class VideoUpscaleWorker:
    def __init__(self, upscaler):
        self.upscaler = upscaler
        self.read_queue = queue.Queue(maxsize=5)
        self.write_queue = queue.Queue(maxsize=5)
        self.stop_event = threading.Event()
        
    def reader_thread(self, video_path):
        video = cv2.VideoCapture(video_path)
        i = 0
        
        while video.isOpened() and not self.stop_event.is_set():
            ret, frame = video.read()
            if not ret:
                break
            
            i += 1
            while not self.stop_event.is_set():
                try:
                    self.read_queue.put((i, frame), timeout=0.1)
                    break
                except queue.Full:
                    continue

        video.release()
        
        while not self.stop_event.is_set():
            try:
                self.read_queue.put(None, timeout=0.1)
                break
            except queue.Full:
                continue
        
    def processor_thread(self):
        while not self.stop_event.is_set():
            try:
                item = self.read_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            
            if item is None:
                while not self.stop_event.is_set():
                    try:
                        self.write_queue.put(None, timeout=0.1)
                        break
                    except queue.Full:
                        continue
                break
            
            i, frame = item
            try:
                upscaled_frame = self.upscaler.process_image(frame, check_interrupt=self.stop_event.is_set)
                
                while not self.stop_event.is_set():
                    try:
                        self.write_queue.put((i, upscaled_frame), timeout=0.1)
                        break
                    except queue.Full:
                        continue
            except Exception as e:
                logging.error(f'Error processing frame {i}: {e}')
            
    def writer_thread(self, process, total_frames, progress):
        frames_written = 0
        try:
            while not self.stop_event.is_set():
                try:
                    item = self.write_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                if item is None:
                    break
                
                _, frame = item
                
                try:
                    process.stdin.write(frame.tobytes())
                    process.stdin.flush()
                    frames_written += 1

                    if progress and total_frames > 0:
                        percent = int((frames_written / total_frames) * 100)
                        
                        if progress(percent) is False:
                            self.stop_event.set()
                except (BrokenPipeError, IOError) as e:
                    logging.error(f'FFmpeg process ended unexpectedly: {e}')
                    self.stop_event.set()
                    break
        finally:
            if process.stdin:
                process.stdin.close()
                
    def process_video(self, input_path, output_path, work_dir, progress=None):
        self.stop_event.clear()
        
        
        video = cv2.VideoCapture(input_path)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video.get(cv2.CAP_PROP_FPS)
        w = int(video.get(cv2.CAP_PROP_FRAME_WIDTH)) * self.upscaler.scale
        h = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)) * self.upscaler.scale
        video.release()
        
        logging.info(f'Starting pipeline. Output: {w}x{h}, {fps} fps')
        ffmpeg_process = start_ffmpeg_process(output_path, fps, w, h, input_source=input_path)
        
        if ffmpeg_process is None:
            logging.error('Failed to start FFmpeg process.')
            return False
            
        try:
            thread_reader = threading.Thread(target=self.reader_thread, args=(input_path,))
            thread_processor = threading.Thread(target=self.processor_thread)
            thread_writer = threading.Thread(target=self.writer_thread, args=(ffmpeg_process, total_frames, progress))
            
            thread_reader.start()
            thread_processor.start()
            thread_writer.start()
            
            thread_reader.join()
            thread_processor.join()
            thread_writer.join()
            
            stdout, stderr = ffmpeg_process.communicate()
            
            if self.stop_event.is_set():
                logging.info('Video processing was stopped by user.')
                return False
            
            if ffmpeg_process.returncode != 0:
                logging.error(f'FFmpeg exited with error code {ffmpeg_process.returncode}')
                return False
            
            logging.info('Video processing completed successfully.')
            return True
            
        except Exception as e:
            logging.error(f'Error during video processing: {e}')
            self.stop_event.set()
            
            if ffmpeg_process:
                ffmpeg_process.kill()
            raise e