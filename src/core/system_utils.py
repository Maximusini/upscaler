import onnxruntime as ort
import subprocess

def get_gpu_info():
    providers = ort.get_available_providers()
    if 'CUDAExecutionProvider' in providers:
        return 'GPU: CUDA (ONNX Detected)'
    else:
        return 'CPU (Медленно)'
    
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False