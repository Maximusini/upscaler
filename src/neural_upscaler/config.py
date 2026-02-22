import os
import json
from PySide6.QtCore import QStandardPaths

class ConfigManager():
    def __init__(self):
        path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
        os.makedirs(path, exist_ok=True)
        self.config_path = os.path.join(path, 'settings.json')
    
    def save_config(self, data):
        with open(self.config_path, 'w') as file:
            json.dump(data, file, indent=4)
            
    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as file:
                return json.load(file)
        else:
            return {}