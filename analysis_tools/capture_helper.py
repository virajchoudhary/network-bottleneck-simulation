import subprocess
import sys
import os

def start_capture(case_name, port):
    """Start tshark capture"""
    output_dir = "captures"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_file = f"{output_dir}/{case_name}.pcap"
    
    # Simple tshark command for macOS
    cmd = f"tshark -i lo0 -f 'tcp port {port}' -w {output_file}"
    
    print(f"Starting capture for {case_name} on port {port}")
    print(f"Output: {output_file}")
    print(f"Command: {cmd}")
    print("Press Ctrl+C to stop")
    
    os.system(cmd)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python capture_helper.py case1|case2|case3")
        sys.exit(1)
    
    case = sys.argv[1]
    ports = {"case1": 5000, "case2": 5001, "case3": 5002}
    
    if case in ports:
        start_capture(case, ports[case])
    else:
        print("Invalid case. Use case1, case2, or case3")
