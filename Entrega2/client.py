from rdt import *
from socket import *

server_ip = 'localhost'
server_port = 12000
server_addr = (server_ip, server_port)

sock = socket(AF_INET, SOCK_DGRAM)
enviador = rdt_sender(sock)
recebedor = rdt_receiver(sock)

# file_name = 'poema.txt'
file_name = input("Qual o nome do arquivo? ")
file = b''
with open(file_name, 'rb') as f:
    file = f.read()

msg = file_name.encode() + b'\r\n' + file
print("Vou enviar o arquivo!")
enviador.send_bytes(msg, server_addr)
print("\nVou receber um arquivo!")
novo, _ = recebedor.receive_bytes()
new_name, new_file = novo.split(b'\r\n', 1)

with open("recebido_" + new_name.decode(), 'wb') as f:
    f.write(new_file)
print(len(new_file))
