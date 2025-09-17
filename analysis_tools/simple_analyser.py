#!/usr/bin/env python3
import sys

def analyze_pcap(pcap_file):
    """Simple PCAP analysis without scapy"""
    print(f"Analyzing: {pcap_file}")
    print("For detailed analysis, use: wireshark " + pcap_file)
    print("\nBasic Wireshark filters to use:")
    print("- tcp.analysis.retransmission (find retransmissions)")
    print("- tcp.analysis.lost_segment (find lost packets)")
    print("- io,stat,1 (I/O graph with 1-second intervals)")
    print("\nLook for:")
    print("- High retransmission rates (indicates problems)")
    print("- Uneven throughput (indicates bottlenecks)")
    print("- Connection resets (indicates failures)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_analyzer.py <pcap_file>")
        sys.exit(1)
    
    analyze_pcap(sys.argv[1])
