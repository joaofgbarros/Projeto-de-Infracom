from rdt import rdt_sender
from rdtreceptor import rdtrecebedor
from socket import *

server_ip = 'localhost'
server_port = 12000
server_addr = (server_ip, server_port)

sock = socket(AF_INET, SOCK_DGRAM)
enviador = rdt_sender(sock)
recebedor = rdtrecebedor(sock)

file_name = 'gloglo.png'
file = b''
with open(file_name, 'rb') as f:
    file = f.read()

msg = file_name.encode() + b'\r\n' + file
enviador.send_bytes(msg, server_addr)
novo = recebedor.receive_bytes()
new_name, new_file = novo.split(b'\r\n', 1)

with open(new_name.decode(), 'wb') as f:
    f.write(new_file)
