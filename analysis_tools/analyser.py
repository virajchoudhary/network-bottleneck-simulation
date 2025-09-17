#!/usr/bin/env python3
# analysis_tools/analyzer.py
import sys, os, math, statistics
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from scapy.all import rdpcap, TCP, IP  # pip install scapy

def load_pcap(pcap_path: str):
    if not os.path.exists(pcap_path):
        raise FileNotFoundError(f"PCAP not found: {pcap_path}")
    print(f"[INFO] Loading PCAP: {pcap_path}")
    pkts = rdpcap(pcap_path)
    print(f"[INFO] Total packets: {len(pkts)}")
    return pkts

def count_retransmissions(pkts) -> int:
    """Approximate retransmissions: repeated TCP seq per flow."""
    seen = defaultdict(set)
    retx = 0
    for p in pkts:
        if IP in p and TCP in p:
            ip = p[IP]; tcp = p[TCP]
            fid = (ip.src, tcp.sport, ip.dst, tcp.dport)
            seq = tcp.seq
            if seq in seen[fid]:
                retx += 1
            else:
                seen[fid].add(seq)
    return retx

def throughput_series(pkts, window=1.0):
    """Return (times, Mbps) using window-second bins."""
    times = [float(p.time) for p in pkts]
    if not times: return [], []
    t0, t1 = min(times), max(times)
    n = int((t1 - t0) / window) + 1
    bins = [t0 + i * window for i in range(n)]
    bytes_in = [0] * n
    for p in pkts:
        idx = int((float(p.time) - t0) // window)
        if 0 <= idx < n:
            bytes_in[idx] += len(p)
    mbps = [(b * 8) / (1e6 * window) for b in bytes_in]
    rel_times = [b - t0 for b in bins]
    return rel_times, mbps

def coarse_rtt(pkts):
    """Coarse RTT: match data segments to first cumulative ACK on the reverse flow."""
    data_by_flow = defaultdict(list)
    ack_by_rev = defaultdict(list)
    for p in pkts:
        if IP in p and TCP in p:
            ip, tcp = p[IP], p[TCP]
            fid = (ip.src, tcp.sport, ip.dst, tcp.dport)
            rev = (ip.dst, tcp.dport, ip.src, tcp.sport)
            t = float(p.time)
            if len(tcp.payload) > 0:
                data_by_flow[fid].append((t, tcp.seq, len(tcp.payload)))
            ack_by_rev[rev].append((t, tcp.ack))

    if not data_by_flow: return []
    # Choose dominant data flow
    fid = max(data_by_flow, key=lambda k: len(data_by_flow[k]))
    rev = (fid[2], fid[3], fid[0], fid[1])
    acks = sorted(ack_by_rev.get(rev, []))
    if not acks: return []

    rtts = []
    a_ptr = 0
    for t_data, seq, plen in data_by_flow[fid]:
        want = seq + plen
        while a_ptr < len(acks) and acks[a_ptr][1] < want:
            a_ptr += 1
        if a_ptr < len(acks):
            t_ack = acks[a_ptr][0]
            if t_ack >= t_data:
                rtts.append(t_ack - t_data)
    return rtts

def save_plot(x, y, title, xl, yl, path):
    plt.figure(figsize=(10, 4))
    plt.plot(x, y, lw=1.5)
    plt.title(title)
    plt.xlabel(xl); plt.ylabel(yl)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"[PLOT] Saved: {path}")

def analyze(pcap_path: str, outdir="analysis_output"):
    os.makedirs(outdir, exist_ok=True)
    pkts = load_pcap(pcap_path)

    # Packet loss via retransmissions
    tcp_total = sum(1 for p in pkts if TCP in p)
    retx = count_retransmissions(pkts)
    loss_pct = (retx / tcp_total * 100.0) if tcp_total else 0.0
    print(f"[LOSS] TCP packets: {tcp_total}")
    print(f"[LOSS] Retransmissions: {retx}")
    print(f"[LOSS] Approx packet loss: {loss_pct:.2f}%")

    # Throughput vs time
    ts, mbps = throughput_series(pkts, window=1.0)
    if ts:
        save_plot(ts, mbps, "Throughput vs Time", "Time (s)", "Throughput (Mbps)",
                  os.path.join(outdir, "throughput3_fixed.png"))
        avg = statistics.mean(mbps) if mbps else 0.0
        print(f"[TPUT] Avg: {avg:.2f} Mbps  Max: {max(mbps):.2f}  Min: {min(mbps):.2f}")

    # RTT / Latency trend (coarse)
    rtts = coarse_rtt(pkts)
    if rtts:
        ms = [r * 1000 for r in rtts]
        save_plot(range(len(ms)), ms, "RTT Samples (coarse)", "Sample #", "RTT (ms)",
                  os.path.join(outdir, "rtt.png"))
        print(f"[RTT] Avg: {statistics.mean(ms):.2f} ms  p95: {np.percentile(ms,95):.2f}  Max: {max(ms):.2f}")
    else:
        print("[RTT] Not enough data/acks to estimate")

    # Instability indicator (CV of throughput)
    if mbps:
        cv = (statistics.pstdev(mbps) / (statistics.mean(mbps) or 1))
        print(f"[VAR] Throughput CV: {cv:.2f}")
        if cv > 0.5:
            print("[VAR] High instability: consistent with overload/buffer issues.")
        elif cv > 0.2:
            print("[VAR] Moderate variability.")
        else:
            print("[VAR] Stable.")

    print(f"[DONE] Results saved in: {outdir}")

if __name__ == "__main__":
    # Default to captures/case1.pcap if no argument provided
    default_pcap = os.path.join("captures", "case3_fixed.pcap")
    pcap = sys.argv[1] if len(sys.argv) > 1 else default_pcap
    analyze(pcap)
