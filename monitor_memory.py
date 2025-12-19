"""
Real-time memory monitor for OmniParser server.
Run this while your server is running to track memory usage.
"""

import torch
import time
import os
from datetime import datetime

def get_gpu_memory():
    """Get GPU memory usage in GB"""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0) / 1024**3
        reserved = torch.cuda.memory_reserved(0) / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        return allocated, reserved, total
    return 0, 0, 0

def get_system_memory():
    """Get system RAM usage"""
    try:
        import psutil
        mem = psutil.virtual_memory()
        used_gb = mem.used / 1024**3
        total_gb = mem.total / 1024**3
        percent = mem.percent
        return used_gb, total_gb, percent
    except ImportError:
        return None, None, None

def monitor_memory(interval=5, duration=None):
    """
    Monitor memory usage continuously.
    
    Args:
        interval: Seconds between checks (default: 5)
        duration: Total seconds to run (None = forever)
    """
    print("="*70)
    print("🔍 MEMORY MONITOR STARTED")
    print("="*70)
    print(f"Checking every {interval} seconds")
    print("Press Ctrl+C to stop\n")
    
    # Try to import psutil for system memory
    try:
        import psutil
        has_psutil = True
    except ImportError:
        print("⚠️  psutil not installed - system RAM monitoring disabled")
        print("   Install with: pip install psutil\n")
        has_psutil = False
    
    start_time = time.time()
    max_gpu_used = 0
    max_ram_used = 0
    
    log_file = f"memory_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            elapsed = time.time() - start_time
            
            # GPU Memory
            gpu_allocated, gpu_reserved, gpu_total = get_gpu_memory()
            gpu_percent = (gpu_allocated / gpu_total * 100) if gpu_total > 0 else 0
            max_gpu_used = max(max_gpu_used, gpu_allocated)
            
            # System RAM
            if has_psutil:
                ram_used, ram_total, ram_percent = get_system_memory()
                if ram_used is not None:
                    max_ram_used = max(max_ram_used, ram_used)
            else:
                ram_used, ram_total, ram_percent = None, None, None
            
            # Display
            print(f"[{current_time}] Elapsed: {int(elapsed)}s")
            print(f"  🎮 GPU: {gpu_allocated:.2f}GB / {gpu_total:.2f}GB ({gpu_percent:.1f}%)")
            print(f"     Reserved: {gpu_reserved:.2f}GB")
            print(f"     Peak: {max_gpu_used:.2f}GB")
            
            if has_psutil and ram_used is not None:
                print(f"  💾 RAM: {ram_used:.2f}GB / {ram_total:.2f}GB ({ram_percent:.1f}%)")
                print(f"     Peak: {max_ram_used:.2f}GB")
                
                # Warning if RAM is too high
                if ram_percent > 90:
                    print(f"  ⚠️  WARNING: RAM usage is very high ({ram_percent:.1f}%)!")
            
            # Warning if GPU is too high
            if gpu_percent > 90:
                print(f"  ⚠️  WARNING: GPU memory usage is very high ({gpu_percent:.1f}%)!")
            
            print()
            
            # Log to file
            with open(log_file, "a") as f:
                f.write(f"{current_time},{elapsed:.0f},{gpu_allocated:.3f},{gpu_reserved:.3f},{gpu_percent:.1f}")
                if ram_used is not None:
                    f.write(f",{ram_used:.3f},{ram_percent:.1f}")
                f.write("\n")
            
            # Check duration
            if duration and elapsed >= duration:
                break
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n" + "="*70)
        print("🛑 MONITORING STOPPED")
        print("="*70)
        print(f"Peak GPU usage: {max_gpu_used:.2f}GB")
        if has_psutil and max_ram_used > 0:
            print(f"Peak RAM usage: {max_ram_used:.2f}GB")
        print(f"Log saved to: {log_file}")
        print("="*70)

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    interval = 5
    duration = None
    
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except:
            print("Usage: python monitor_memory.py [interval_seconds] [duration_seconds]")
            print("Example: python monitor_memory.py 5 300  # Check every 5s for 5 minutes")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
        except:
            duration = None
    
    monitor_memory(interval, duration)

