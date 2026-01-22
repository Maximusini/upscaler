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
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False
    
def get_vram_limit():
    default_vram = 2 * 1024 * 1024 * 1024
    
    if sys.platform != 'win32':
        return default_vram
    
    try:
        if sys.platform == 'win32':
            cmd = ['powershell', '-Command', 'Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty AdapterRAM']
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
            output = subprocess.check_output(cmd, startupinfo=startupinfo, text=True)
        
            rams = [int(x) for x in re.findall(r'\d+', output)]
            
            if rams:
                return max(rams)
    except Exception as e:
        print(f'Ошибка определения VRAM через PowerShell: {e}')
        
        try:
            cmd_wmic = 'wmic path win32_VideoController get AdapterRAM'
            output = subprocess.check_output(cmd_wmic, shell=True).decode()
            rams = [int(x) for x in re.findall(r'\d+', output)]
            if rams:
                return max(rams)
        except:
            pass
    
    print('Не удалось определить VRAM, используем 2GB')
    
    return default_vram