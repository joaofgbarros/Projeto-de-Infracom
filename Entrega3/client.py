from rdt import *
from socket import *

server_ip = 'localhost'
server_port = 12000
server_addr = (server_ip, server_port)

sock = socket(AF_INET, SOCK_DGRAM)
enviador = rdt_sender(sock)
recebedor = rdt_receiver(sock)

print("aqui tem caca ao tesouro? ciiiin")

while True:
    cmd = input("> ")

    # envia comando p servidor (login, hint, etc)
    enviador.send(cmd.encode(), server_addr)

    # recebe resposta
    resposta, _ = recebedor.recv()
    print(resposta.decode())