import onnxruntime as ort
import subprocess
import psutil
import logging

try:
    import GPUtil
except ImportError:
    GPUtil = None

def get_gpu_info():
    """
    Возвращает информацию о текущем графическом процессоре.
    Порядок проверки: 
    """
    providers = ort.get_available_providers()
    
    if 'CUDAExecutionProvider' in providers:
        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    return f'GPU: {gpus[0].name}, memory: {gpus[0].memoryTotal} MB'
            except:
                pass
        return 'GPU: CUDA (NVIDIA)'
    
    elif 'DmlExecutionProvider' in providers:
        return 'GPU: DirectML (AMD/Intel/NVIDIA)'
       
    else:
        return 'CPU'
    
def check_ffmpeg():
    """
    Проверяет наличие FFmpeg в системе (нужен для видео).
    """
    try:
        creation_flags = 0x08000000 if psutil.WINDOWS else 0
        subprocess.run(
            ['ffmpeg', '-version'], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags
        )
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        logging.error(f'Error checking FFmpeg: {e}')
        return False
    
def get_vram_limit():
    """
    Рассчитывает безопасный лимит памяти (в байтах) для тайлинга.
    """
    GB_TO_BYTES = 1024 ** 3
    
    if GPUtil:
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                total_vram = gpus[0].memoryTotal * 1024 * 1024
                safe_limit = int(total_vram * 0.9)
                
                logging.info(f'NVIDIA GPU detected: {gpus[0].name}, VRAM: {total_vram / GB_TO_BYTES:.2f} GB, Safe limit: {safe_limit / GB_TO_BYTES:.2f} GB')
                return safe_limit
        except Exception as e:
            logging.error(f'Error getting VRAM limit: {e}')
    
    try:
        memory = psutil.virtual_memory()
        available_ram = memory.available
        
        target_limit = int(available_ram * 0.8)
        logging.info(f"Using RAM-based limit strategy. Free RAM: {available_ram / GB_TO_BYTES:.2f} GB. Limit set to: {target_limit / GB_TO_BYTES:.2f} GB")
        
        return target_limit
    except Exception as e:
        logging.error(f'Error getting RAM limit: {e}')
        return 2 * GB_TO_BYTES