from socket import *

server_port = 12000

buffer_size = 1024

server_socket = socket(AF_INET, SOCK_DGRAM)

server_socket.bind(('', server_port))

print("O servidor está pronto para receber")

while True:
    # Recebe o nome do arquivo
    msg, client_address = server_socket.recvfrom(buffer_size)
    old_name = msg.decode()
    print("Recebendo", old_name)
    file_name = "server_" + old_name
    with open(file_name, 'wb') as file:
        msg = b''
        while msg != b'DONE':
            file.write(msg)
            msg, client_address = server_socket.recvfrom(buffer_size)

    # Envia o arquivo de volta
    file_bytes = open(file_name, 'rb').read()
    print("Enviando", file_name, f"({len(file_bytes)} bytes) de volta")
    server_socket.sendto(file_name.encode(), client_address) 
    for i in range(0, len(file_bytes), buffer_size):
        msg = file_bytes[i:i+buffer_size]
        server_socket.sendto(msg, client_address)
    server_socket.sendto(b'DONE', client_address)
