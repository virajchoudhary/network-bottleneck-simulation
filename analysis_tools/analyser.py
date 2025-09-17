#!/usr/bin/env python3
# analysis_tools/analyzer.py

import sys, os, statistics
import matplotlib.pyplot as plt
from collections import defaultdict
from scapy.all import rdpcap, TCP, IP

def load_pcap(pcap_path: str):
    if not os.path.exists(pcap_path):
        raise FileNotFoundError(f"PCAP not found: {pcap_path}")
    print(f"[INFO] Analyzing: {pcap_path}")
    pkts = rdpcap(pcap_path)
    return pkts

def count_retransmissions(pkts):
    """Count retransmissions in the main data flow."""
    flows = defaultdict(list)
    for p in pkts:
        if IP in p and TCP in p:
            ip, tcp = p[IP], p[TCP]
            fid = (ip.src, tcp.sport, ip.dst, tcp.dport)
            if len(tcp.payload) > 0:  # Only data packets
                flows[fid].append(tcp.seq)
    
    if not flows:
        return 0, 0
    
    # Find main flow (most data packets)
    main_flow = max(flows, key=lambda k: len(flows[k]))
    seqs = flows[main_flow]
    
    # Count duplicates (retransmissions)
    seen = set()
    retx = 0
    for seq in seqs:
        if seq in seen:
            retx += 1
        else:
            seen.add(seq)
    
    return retx, len(seqs)

def calculate_throughput(pkts):
    """Calculate throughput over time in 1-second windows."""
    if not pkts:
        return [], []
    
    times = [float(p.time) for p in pkts]
    start_time = min(times)
    end_time = max(times)
    duration = end_time - start_time
    
    if duration < 1:
        return [0], [sum(len(p) for p in pkts) * 8 / 1e6]
    
    # Create 1-second bins
    bins = int(duration) + 1
    bytes_per_bin = [0] * bins
    
    for p in pkts:
        bin_index = int((float(p.time) - start_time))
        if bin_index < bins:
            bytes_per_bin[bin_index] += len(p)
    
    # Convert to Mbps
    mbps = [(b * 8) / 1e6 for b in bytes_per_bin]
    time_points = list(range(bins))
    
    return time_points, mbps

def save_plot(x, y, title, filename):
    plt.figure(figsize=(12, 6))
    plt.plot(x, y, 'b-', linewidth=2, marker='o', markersize=4)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Throughput (Mbps)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[GRAPH] Saved: {filename}")

def analyze_network_performance(pcap_path: str):
    # Create output directory
    outdir = "analysis_output"
    os.makedirs(outdir, exist_ok=True)
    
    # Load packets
    pkts = load_pcap(pcap_path)
    if not pkts:
        print("[ERROR] No packets found!")
        return
    
    print(f"[INFO] Total packets: {len(pkts)}")
    
    # Generate filename from PCAP name
    pcap_name = os.path.splitext(os.path.basename(pcap_path))[0]
    plot_filename = os.path.join(outdir, f"throughput_{pcap_name}.png")
    
    # 1. Calculate packet loss
    retransmissions, total_data = count_retransmissions(pkts)
    if total_data > 0:
        loss_rate = (retransmissions / total_data) * 100
        print(f"[LOSS] Data packets: {total_data}")
        print(f"[LOSS] Retransmissions: {retransmissions}")
        print(f"[LOSS] Loss rate: {loss_rate:.1f}%")
    else:
        print("[LOSS] No data packets found")
        loss_rate = 0
    
    # 2. Calculate throughput
    time_points, throughput = calculate_throughput(pkts)
    if throughput:
        avg_throughput = statistics.mean(throughput)
        max_throughput = max(throughput)
        min_throughput = min(throughput)
        
        print(f"[THROUGHPUT] Average: {avg_throughput:.3f} Mbps")
        print(f"[THROUGHPUT] Maximum: {max_throughput:.3f} Mbps")
        print(f"[THROUGHPUT] Minimum: {min_throughput:.3f} Mbps")
        
        # 3. Calculate stability (coefficient of variation)
        if avg_throughput > 0:
            cv = statistics.stdev(throughput) / avg_throughput
            print(f"[STABILITY] Variation coefficient: {cv:.2f}")
            if cv < 0.2:
                stability = "STABLE"
            elif cv < 0.5:
                stability = "MODERATE"
            else:
                stability = "UNSTABLE"
            print(f"[STABILITY] Assessment: {stability}")
        
        # 4. Generate throughput graph
        title = f"Network Throughput - {pcap_name.replace('_', ' ').title()}"
        save_plot(time_points, throughput, title, plot_filename)
    
    # 5. Summary
    print("\n" + "="*50)
    print("NETWORK PERFORMANCE SUMMARY")
    print("="*50)
    print(f"File: {pcap_name}")
    print(f"Loss Rate: {loss_rate:.1f}%")
    if throughput:
        print(f"Avg Throughput: {avg_throughput:.3f} Mbps")
        print(f"Stability: {stability}")
    print("="*50)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pcap_file = sys.argv[1]
    else:
        pcap_file = os.path.join("captures", "case1.pcap")
    
    try:
        analyze_network_performance(pcap_file)
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
