from socket import *
import math

# Informações do servidor
server_name = 'localhost' 
server_port = 12000

file_name = "gloglo.png"
# file_name = input("Me diga o nome do arquivo: ")
buffer_size = 1024

client_socket = socket(AF_INET, SOCK_DGRAM)

# Le o arquivo
file = open(file_name, 'rb')
file_bytes = file.read()
file.close()

# Envia arquivo (nome, pacotes, mensagem final)
print('Enviando', len(file_bytes), 'bytes em', math.ceil(len(file_bytes)/buffer_size), 'pacotes')
client_socket.sendto(file_name.encode(), (server_name, server_port)) 
for i in range(0, len(file_bytes), buffer_size):
    msg = file_bytes[i:i+buffer_size]
    client_socket.sendto(msg, (server_name, server_port))
client_socket.sendto(b'DONE', (server_name, server_port))

# Recebe o arquivo de volta
print("Tentando receber de volta")
msg, server_addr = client_socket.recvfrom(buffer_size)
new_name = "recebido_" + msg.decode()
with open(new_name, 'wb') as file:
    msg = b''
    while msg != b'DONE':
        file.write(msg)
        msg, server_addr = client_socket.recvfrom(buffer_size)
print("Recebido", new_name)

client_socket.close()
