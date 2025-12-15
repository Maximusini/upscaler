import torch
import subprocess

def get_gpu_info():
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        return f'GPU: {name}'
    else:
        return 'CPU (Медленно)'
    
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False