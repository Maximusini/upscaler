import re
import sys
import onnxruntime as ort
import subprocess

def get_gpu_info():
    providers = ort.get_available_providers()
    if 'DmlExecutionProvider' in providers:
        return 'GPU: DirectML (DirectX 12)'
    elif 'CUDAExecutionProvider' in providers:
        return 'GPU: CUDA'
    else:
        return 'CPU (Медленно)'
    
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False
    
def get_vram_limit():
    try:
        if sys.platform == 'win32':
            cmd = 'wmic path win32_VideoController get AdapterRam'
            result = subprocess.check_output(cmd, shell=True).decode()
            rams = [int(x) for x in re.findall(r'\d+', result)]
            if rams:
                return max(rams)
    except Exception as e:
        print(f'Не удалось определить VRAM: {e}')
    
    return 2 * 1024**3