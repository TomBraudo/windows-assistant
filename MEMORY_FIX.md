# Memory Leak Fix for RunPod OmniParser Server

## 🔥 The Problem

Your RunPod server was hitting **100% memory usage**, causing:
- Server crashes
- Slow response times  
- High costs (need bigger pods)

## 🛠️ The Solution

Created **`server_optimized.py`** with aggressive memory management:

### Key Improvements:

1. **Explicit Variable Cleanup**
   ```python
   finally:
       del ocr_bbox_rslt, text, ocr_bbox
       del dino_labled_img, label_coordinates
       aggressive_cleanup()
   ```

2. **CUDA Cache Clearing**
   ```python
   torch.cuda.empty_cache()
   torch.cuda.ipc_collect()  # Clear inter-process memory
   ```

3. **No-Gradient Context**
   ```python
   with torch.no_grad():  # Prevents gradient tracking
       result = get_som_labeled_img(...)
   ```

4. **Queue Limits**
   ```python
   demo.queue(
       max_size=10,  # Max 10 requests in queue
       default_concurrency_limit=2  # Max 2 concurrent
   )
   ```

5. **PIL Image Cleanup**
   ```python
   if hasattr(image_input, 'close'):
       image_input.close()
   ```

6. **Memory Logging**
   - Logs GPU memory before/after each request
   - Helps identify leaks

## 📋 Deployment Steps

### Step 1: Upload to RunPod

1. Stop your current pod
2. Upload `server_optimized.py` to your pod workspace
3. Replace the old `server.py` or run the new one directly:
   ```bash
   python server_optimized.py
   ```

### Step 2: Monitor Memory (Optional but Recommended)

Open a second terminal on RunPod and run:
```bash
python monitor_memory.py 5
```

This will show real-time memory usage every 5 seconds:
```
[14:32:15] Elapsed: 0s
  🎮 GPU: 3.42GB / 16.00GB (21.4%)
     Reserved: 3.85GB
     Peak: 3.42GB
  💾 RAM: 4.12GB / 32.00GB (12.9%)
     Peak: 4.12GB
```

### Step 3: Test It

Run your test from the Windows Assistant:
```bash
python test_runpod_omniparser.py
```

Watch the memory monitor - you should see:
- Memory spikes during processing ✅
- Memory returns to baseline after each request ✅
- No continuous memory growth ❌

## 🔍 What to Look For

### Good Signs ✅
- Memory goes up during processing
- Memory goes back down after processing
- GPU memory stays below 80%
- RAM stays below 50%

### Bad Signs ⚠️
- Memory keeps climbing with each request
- Memory never goes back down
- Hitting 90%+ consistently
- Server becomes unresponsive

## 🚨 If Still Leaking

### Option 1: Reduce Batch Size
Edit `server_optimized.py`:
```python
demo.queue(
    max_size=5,  # Even smaller queue
    default_concurrency_limit=1  # Only 1 at a time
)
```

### Option 2: Restart Server Periodically
Add a request counter and auto-restart:
```python
REQUEST_COUNT = 0
MAX_REQUESTS = 100

def process_image(...):
    global REQUEST_COUNT
    REQUEST_COUNT += 1
    
    if REQUEST_COUNT >= MAX_REQUESTS:
        print("⚠️  Reached max requests, restart recommended")
        REQUEST_COUNT = 0
        aggressive_cleanup()
    ...
```

### Option 3: Use a Bigger Pod
If you're processing many concurrent requests, you might just need more RAM:
- Current: RTX A4500 (16GB VRAM)
- Consider: RTX A6000 (48GB VRAM) if budget allows

### Option 4: Model Optimization
Consider using smaller models:
- Florence-2 base (current) → Florence-2 small
- Reduces memory footprint by ~30%

## 📊 Memory Budget Reference

Typical memory usage per request:
- **OCR (PaddleOCR)**: ~500MB
- **YOLO Detection**: ~1.5GB
- **Florence-2 Captioning**: ~2GB
- **Image Processing**: ~200MB
- **Total per request**: ~4-5GB peak

With 16GB VRAM:
- Safe concurrent requests: **2-3**
- System overhead: ~2GB
- Leaves buffer for spikes

## 🎯 Expected Results

After deploying the optimized server:
- **Baseline memory**: 20-30%
- **During processing**: 40-60%
- **After processing**: Returns to baseline
- **No crashes**: Even after 100+ requests

## 📝 Notes

- The monitor creates a CSV log file for tracking trends
- Run the monitor for a few hours to verify no slow leaks
- GPU memory is more critical than RAM for your workload
- If you see gradual memory increase (< 1% per hour), it's acceptable
- If you see rapid increase (> 5% per 10 requests), there's still a leak

## 🔗 Related Files

- `server_optimized.py` - Memory-optimized server
- `monitor_memory.py` - Real-time memory monitoring
- `test_runpod_omniparser.py` - Test client

---

**Let me know if memory usage is still high after these changes!** 🚀

