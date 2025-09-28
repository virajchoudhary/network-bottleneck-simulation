#!/usr/bin/env python3
# File: analysis_tools/analyser.py (REPLACE YOUR EXISTING FILE)

import sys, os
import matplotlib.pyplot as plt
import pandas as pd
from scapy.all import rdpcap

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

def analyze_and_plot(pcap_path, log_path=None, buffer_label="Buffer Metric"):
    outdir = os.path.join(PROJECT_ROOT, "analysis_output")
    os.makedirs(outdir, exist_ok=True)
    pkts = rdpcap(pcap_path)
    pcap_name = os.path.splitext(os.path.basename(pcap_path))[0]
    suffix = "_with_buffer" if log_path and os.path.exists(log_path) else ""
    plot_filename = os.path.join(outdir, f"throughput_{pcap_name}{suffix}.png")
    
    if not pkts: 
        return
    
    times = [float(p.time) for p in pkts]
    start_time = min(times)
    duration = max(times) - start_time
    bins = int(duration) + 1
    bytes_per_bin = [0] * bins
    
    for p in pkts:
        bin_index = int(float(p.time) - start_time)
        if bin_index < bins: 
            bytes_per_bin[bin_index] += len(p)
    
    mbps = [(b * 8) / 1e6 for b in bytes_per_bin]
    time_points = list(range(bins))
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    color = 'tab:blue'
    ax1.set_xlabel('Time (seconds)', fontsize=12)
    ax1.set_ylabel('Throughput (Mbps)', fontsize=12, color=color)
    ax1.plot(time_points, mbps, color=color, linewidth=2, marker='o', markersize=4)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)
    
    if log_path and os.path.exists(log_path):
        ax2 = ax1.twinx()
        color = 'tab:red'
        ax2.set_ylabel(buffer_label, fontsize=12, color=color)
        df = pd.read_csv(log_path)
        ax2.plot(df['Timestamp'], df['BufferSize'], color=color, linestyle='--', linewidth=2)
        ax2.tick_params(axis='y', labelcolor=color)
        print(f"[INFO] Successfully plotted data from {os.path.basename(log_path)}")
    elif log_path:
        print(f"[WARNING] Log file not found: {log_path}")
    
    plt.title(f"Network Analysis - {pcap_name.replace('_', ' ').title()}", fontsize=14)
    fig.tight_layout()
    plt.savefig(plot_filename, dpi=150)
    plt.close()
    print(f"[GRAPH] Saved: {plot_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analysis_tools/analyser.py <pcap_file_name> [log_file_name] [buffer_label]")
        sys.exit(1)
        
    pcap_name = sys.argv[1]
    full_pcap_path = os.path.join(PROJECT_ROOT, 'captures', pcap_name)
    full_log_path = None
    
    if len(sys.argv) > 2:
        log_name = sys.argv[2]
        case_folder = {
            'case1': 'case1_buffer_overflow', 
            'case2': 'case2_long_queue', 
            'case3': 'case3_bandwidth_limit'
        }.get(pcap_name.split('_')[0])
        if case_folder: 
            full_log_path = os.path.join(PROJECT_ROOT, case_folder, log_name)
    
    label = sys.argv[3] if len(sys.argv) > 3 else "Buffer Metric"
    analyze_and_plot(full_pcap_path, full_log_path, label)