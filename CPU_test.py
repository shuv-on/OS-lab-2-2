import subprocess
import time
import csv
import os
import sys
import re  # Speed extract-এর জন্য regex
import signal  # Kill process-এর জন্য

# Configuration
source_dir = '/home/shuvon/test_files'  # Source path
dest_ssd = '/home/shuvon/test_dest'  # SSD dest
dest_hdd = '/mnt/Academic/test_dest'  # HDD dest
dest_usb3 = '/media/shuvon/Falcon/test_dest'  # USB 3.0 dest
destinations = [dest_ssd, dest_hdd, dest_usb3]  # SSD + HDD + USB
storages = ['SSD NVMe', 'HDD', 'USB 3.0']  # Labels
runs = 3  # প্রতি file type-এ run সংখ্যা
csv_file = 'cpu_baseline_all.csv'  # Output CSV
sudo_password = 'shuvon@7979'  # আপনার sudo password (lab-এর জন্য; security risk!)

# File types and sizes
file_types = {
    'Small': {'file': 'small_file.bin', 'size_mb': 10},
    'Large': {'file': 'large_file.bin', 'size_mb': 1024},
    'Mixed': {'files': ['mixed_small_{}.bin'.format(i) for i in range(1, 11)] + ['large_file.bin'], 'size_mb': 1124}
    # Total size
}


def clear_cache():
    """Cache clear করুন variability কমাতে (password দিয়ে)"""
    try:
        # sync without sudo
        subprocess.run(['sync'], check=True)
        # drop_caches with sudo -S (password pipe)
        p = subprocess.Popen(['echo', sudo_password], stdout=subprocess.PIPE)
        subprocess.run(['sudo', '-S', 'sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'], stdin=p.stdout, check=True)
        p.wait()
        print("Cache cleared successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Cache clear failed: {e}. Continuing without.")
        # Continue anyway


def start_cpu_load():
    """CPU load start করুন (stress --cpu 4 --timeout 30s background)"""
    cmd = ['stress', '--cpu', '4', '--timeout', '30s']
    result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"CPU load started (PID: {result.pid})")
    return result.pid


def stop_cpu_load(pid):
    """CPU load stop করুন"""
    try:
        subprocess.run(['kill', str(pid)], check=True)
        print(f"CPU load stopped (PID: {pid})")
    except subprocess.CalledProcessError:
        print("CPU load already stopped.")


def copy_with_pv(source, dest, size_mb, is_mixed=False):
    """pv দিয়ে copy, speed capture করুন"""
    if is_mixed:
        # Mixed-এর জন্য loop
        total_time = 0
        for src in source:
            full_src = os.path.join(source_dir, src)
            full_dest = os.path.join(dest, src)
            start = time.time()
            size_arg = '10M' if 'mixed_small' in src else '1G'
            cmd = ['pv', '-s', size_arg, full_src]
            with open(full_dest, 'wb') as f:
                subprocess.run(cmd, stdout=f, check=True)
            end = time.time()
            total_time += end - start
        avg_speed = size_mb / total_time if total_time > 0 else 0
        return avg_speed, 'No'
    else:
        full_src = os.path.join(source_dir, source)
        full_dest = os.path.join(dest, source)
        start = time.time()
        cmd = ['pv', '-s', '{}M'.format(size_mb), full_src]
        with open(full_dest, 'wb') as f:
            # stdout to file, stderr to PIPE for progress
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, check=True)
            # Speed extract from stderr (last [XXX MiB/s])
            stderr_output = result.stderr
            lines = stderr_output.split('\n')
            speed_match = re.search(r'\[(\d+\.?\d*)MiB/s\]', lines[-1]) if lines else None
            speed = float(speed_match.group(1)) if speed_match else (size_mb / (time.time() - start))
        end = time.time()
        avg_speed = size_mb / (end - start)
        return avg_speed, 'No'  # Stability assume No


def measure_lag():
    """Lag মাপুন"""
    start = time.time()
    subprocess.run(['echo', 'test'], capture_output=True)
    end = time.time()
    return round((end - start) * 1000, 1)  # ms


def clean_dest(dest, file_type):
    """পুরানো ফাইল মুছুন"""
    if file_type == 'Mixed':
        for f in file_types['Mixed']['files']:
            try:
                os.remove(os.path.join(dest, f))
            except OSError:
                pass  # Ignore if not exist
    else:
        try:
            os.remove(os.path.join(dest, file_types[file_type]['file']))
        except OSError:
            pass  # Ignore if not exist


# CSV header
with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Process Type', 'Storage Device', 'File Type', 'Avg Transfer Speed (MB/s)', 'Stability (Error?)',
                     'Avg Responsiveness (Lag ms)', 'Notes'])

# Main loop
process_type = 'CPU Load'  # Background CPU condition
for idx, dest in enumerate(destinations):
    storage = storages[idx]
    if not os.path.exists(dest):
        print(f"Warning: {dest} does not exist! Create it first.")
        continue
    clear_cache()  # প্রতি storage-এর আগে cache clear
    for file_type, info in file_types.items():
        speeds = []
        lags = []
        for run in range(1, runs + 1):
            print(f"Running {run}/{runs} for {storage} - {file_type} under CPU load...")
            clean_dest(dest, file_type)  # Clean before copy
            # Start CPU load
            pid = start_cpu_load()
            # Copy
            if file_type == 'Mixed':
                source = info['files']
            else:
                source = info['file']
            speed, stability = copy_with_pv(source, dest, info['size_mb'], is_mixed=(file_type == 'Mixed'))
            # Stop CPU load
            stop_cpu_load(pid)
            speeds.append(speed)
            # Lag
            lag = measure_lag()
            lags.append(lag)
            print(f"Run {run}: Speed {speed:.2f} MB/s, Lag {lag} ms")

        avg_speed = sum(speeds) / runs
        avg_lag = sum(lags) / runs
        notes = f"pv real-time avg over {runs} runs under CPU load (stress --cpu 4). Stability: {stability}"

        # CSV write
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([process_type, storage, file_type, f"{avg_speed:.2f}", stability, f"{avg_lag:.1f}", notes])

        print(f"{storage} {file_type} Avg under CPU: {avg_speed:.2f} MB/s, Avg Lag: {avg_lag:.1f} ms")

print(f"CPU load baseline complete! Check {csv_file} for data.")
