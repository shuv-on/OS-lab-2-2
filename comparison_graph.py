import matplotlib.pyplot as plt
import numpy as np

# ডেটা (আপনার table থেকে)
storages = ['SSD NVMe', 'HDD', 'USB 3.0']
file_types = ['Small', 'Large', 'Mixed']  # X-axis

# Baseline speeds (MB/s)
baseline_speeds = {
    'SSD NVMe': [1142.22, 310.18, 123.43],
    'HDD': [853, 165.13, 214.04],
    'USB 3.0': [1346.4, 27.01, 20.97]
}

# CPU Load speeds (MB/s)
cpu_speeds = {
    'SSD NVMe': [1079.2, 99.91, 102.59],
    'HDD': [640.44, 190.25, 160.97],
    'USB 3.0': [829.82, 21.09, 17.87]
}

# Figure তৈরি (3 subplots: SSD, HDD, USB)
fig, axes = plt.subplots(1, 3, figsize=(15, 6))
x = np.arange(len(file_types))  # [0,1,2] for Small, Large, Mixed
width = 0.35  # Bar width

for i, storage in enumerate(storages):
    ax = axes[i]

    # Baseline এবং CPU bars
    baseline_bars = ax.bar(x - width / 2, baseline_speeds[storage], width, label='Baseline', color='blue', alpha=0.7)
    cpu_bars = ax.bar(x + width / 2, cpu_speeds[storage], width, label='CPU Load', color='red', alpha=0.7)

    # Title এবং labels
    ax.set_title(f'{storage} Comparison', fontsize=12, fontweight='bold')
    ax.set_xlabel('File Type', fontsize=10)
    ax.set_ylabel('Transfer Speed (MB/s)', fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(file_types)
    ax.set_ylim(0, max(max(baseline_speeds[storage]), max(cpu_speeds[storage])) + 50)

    # Bar-এ value লেবেল যোগ করুন
    for bar, speed in zip(baseline_bars, baseline_speeds[storage]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3, f'{speed:.1f}',
                ha='center', va='bottom', fontsize=8)
    for bar, speed in zip(cpu_bars, cpu_speeds[storage]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3, f'{speed:.1f}',
                ha='center', va='bottom', fontsize=8)

    # Legend এবং grid
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

# Overall title
fig.suptitle('Baseline vs CPU Load File Transfer Speed Comparison', fontsize=16, fontweight='bold')

# Notes যোগ করুন (bottom text)
fig.text(0.5, 0.02, 'Stability: No error (all); Lag: 0.5-3.7 ms (avg); Method: pv tool over 3 runs',
         ha='center', fontsize=10, style='italic')

# Plot সেভ করুন
plt.tight_layout()
plt.savefig('comparison_transfer_plot.png', dpi=300, bbox_inches='tight')  # High-res PNG for report
plt.show()  # Screen-এ দেখান (optional)

print("Comparison plot saved as 'comparison_transfer_plot.png'. Check your current directory!")
