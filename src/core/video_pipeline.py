import threading
import queue
import cv2
import os
import shutil
import logging
from src.core.ffmpeg_utils import merge_frames_to_video

class VideoUpscaleWorker:
    def __init__(self, upscaler):
        self.upscaler = upscaler
        self.read_queue = queue.Queue(maxsize=45)
        self.write_queue = queue.Queue(maxsize=45)
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
                if self.stop_event.is_set():
                    break
                
                upscaled_frame = self.upscaler.process_image(frame)
                
                while not self.stop_event.is_set():
                    try:
                        self.write_queue.put((i, upscaled_frame), timeout=0.1)
                        break
                    except queue.Full:
                        continue
            except Exception as e:
                logging.error(f'Error processing frame {i}: {e}')
            
    def writer_thread(self, temp_dir, total_frames, progress):
        frames_written = 0
        
        while not self.stop_event.is_set():
            try:
                item = self.write_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            
            if item is None:
                break
            
            i, frame = item
            filename = f'frame_{i:08d}.jpg'
            path = os.path.join(temp_dir, filename)
            cv2.imwrite(path, frame)
            frames_written += 1
            
            if progress and total_frames > 0:
                percent = int((frames_written / total_frames) * 100)
                
                if progress(percent) is False:
                    self.stop_event.set()
    
    def process_video(self, input_path, output_path, work_dir, progress=None):
        self.stop_event.clear()
        
        video_name = os.path.splitext(os.path.basename(input_path))[0]
        frames_dir = os.path.join(work_dir, f'{video_name}_frames')
        
        if os.path.exists(frames_dir):
            shutil.rmtree(frames_dir)
        os.makedirs(frames_dir, exist_ok=True)
        
        try:
            video = cv2.VideoCapture(input_path)
            total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = video.get(cv2.CAP_PROP_FPS)
            video.release()
            
            if total_frames == 0:
                logging.warning('Could not determine total frames. Progress bar might be inaccurate.')
            
            thread_reader = threading.Thread(target=self.reader_thread, args=(input_path,))
            thread_processor = threading.Thread(target=self.processor_thread)
            thread_writer = threading.Thread(target=self.writer_thread, args=(frames_dir, total_frames, progress))
            
            thread_reader.start()
            thread_processor.start()
            thread_writer.start()
            
            thread_reader.join()
            thread_processor.join()
            thread_writer.join()
            
            if self.stop_event.is_set():
                logging.info('Video processing was stopped by user.')
                return False
            
            logging.info('All frames processed. Starting video assembly...')
            
            merge_frames_to_video(frames_dir, input_path, output_path, fps)
            
            logging.info('Video assembly completed. Merging audio...')
            return True
            
        except Exception as e:
            logging.error(f'Error during video processing: {e}')
            self.stop_event.set()
            raise e
        finally:
            if os.path.exists(frames_dir):
                logging.info('Cleaning up temporary files...')
                shutil.rmtree(frames_dir, ignore_errors=True)