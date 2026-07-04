import os
import psutil
import time

def get_system_resources() -> dict:
    """
    Returns the current global CPU and RAM usage percentage,
    along with available RAM in GB.
    """
    try:
        cpu = psutil.cpu_percent(interval=None)
        ram_info = psutil.virtual_memory()
        
        # Process memory
        process = psutil.Process(os.getpid())
        process_ram = process.memory_info().rss / (1024 * 1024 * 1024) # in GB
        
        return {
            "cpu_percent": cpu,
            "ram_percent": ram_info.percent,
            "ram_available_gb": ram_info.available / (1024 * 1024 * 1024),
            "ram_total_gb": ram_info.total / (1024 * 1024 * 1024),
            "process_ram_gb": process_ram
        }
    except Exception:
        return {
            "cpu_percent": 0.0,
            "ram_percent": 0.0,
            "ram_available_gb": 0.0,
            "ram_total_gb": 0.0,
            "process_ram_gb": 0.0
        }

class ResourceTracker:
    """
    Tracks the resource consumption before and after running inference.
    """
    def __init__(self):
        self.start_resources = get_system_resources()
        self.start_time = time.time()
        
    def get_metrics(self) -> dict:
        """
        Calculates and returns metrics comparing current resources with start state.
        """
        end_resources = get_system_resources()
        duration = time.time() - self.start_time
        
        # Calculate RAM change
        ram_delta = end_resources["process_ram_gb"] - self.start_resources["process_ram_gb"]
        
        return {
            "duration_sec": duration,
            "cpu_peak_percent": max(self.start_resources["cpu_percent"], end_resources["cpu_percent"]),
            "ram_peak_percent": max(self.start_resources["ram_percent"], end_resources["ram_percent"]),
            "process_ram_delta_mb": ram_delta * 1024,
            "current_process_ram_gb": end_resources["process_ram_gb"]
        }
