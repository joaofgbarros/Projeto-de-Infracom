from socket import *
from rdt import *

sock = socket(AF_INET, SOCK_DGRAM)
sock.bind(('localhost', 12000))
print("O servidor está pronto para receber!")

while True:
    recebedor = rdt_receiver(sock)
    dados, cliente_addr = recebedor.receive_bytes()

    partes = dados.split(b'\r\n', 1)
    nome_arq = partes[0].decode()
    dados_arq = partes[1]

    nome_processado = "server_" + nome_arq

    with open(nome_processado, 'wb') as file:
        file.write(dados_arq)
    print("Arquivo salvo!")

    print("\nEnviando arquivo de volta para o cliente!")
    arq_bytes = open(nome_processado, 'rb').read()

    enviador = rdt_sender(sock)
    resposta = nome_processado.encode() + b'\r\n' + arq_bytes
    enviador.send_bytes(resposta, cliente_addr)

    print("Enviado!")

