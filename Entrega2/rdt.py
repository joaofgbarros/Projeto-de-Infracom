from socket import *
from random import random

class rdt:
    acks = [b'ACK0', b'ACK1']
    pkts = [b'PKT0', b'PKT1']
    buffer_size = 1024
    lost_pkt_probability = 0.2

    def __init__(self, socket: socket):
        self.socket = socket

    def udt_send(self, data, dest):
        # Simula perda de pacotes
        if random() > type(self).lost_pkt_probability:
            self.socket.sendto(data, dest)


class rdt_sender(rdt):
    def __init__(self, socket: socket):
        super().__init__(socket)
        self.seqnum = 0 # Número de sequência
        self.timeout = 0.1
    
    # Separa em chunks, e envia
    def send_bytes(self, data, dest):
        print(f"Enviando {len(data)} bytes")
        # Coloca timeout no recv() do socket
        self.socket.settimeout(self.timeout)
        for i in range(0, len(data), type(self).buffer_size-4):
            # número de sequência + Chunk dos dados
            msg = type(self).pkts[self.seqnum] + data[i:i+type(self).buffer_size-4]
            # Envia msg
            self.send(msg, dest)
            # Flipa o número de sequência
            self.seqnum = 1 - self.seqnum
        # Envia mesagem final (sem corpo) 
        self.send(type(self).pkts[self.seqnum], dest)

    # Envia um pacote e recebe o ack correspondente
    def send(self, msg, dest):
        self.udt_send(msg, dest)
        recvd = False
        while not recvd:
            # Assume que enviou bem. Espera o ACK
            try:
                ack = self.socket.recv(type(self).buffer_size)
                # Se for o ack certo, recvd = True, e sai do loop. Se não, ignora
                recvd = (ack == type(self).acks[self.seqnum])
                if recvd: print("Recebi o ACK certo >:D")
                else: print("Recebi o ACK errado >:C")
            except:
                print("Timeout! Retransmitindo...")
                self.udt_send(msg, dest)

class rdt_receiver(rdt):
    def __init__(self, socket: socket):
        super().__init__(socket)
        self.numesperado = 0
        self.ultimo_addr = None

    def extrai_pacote(pctdata):
        cabeca = pctdata[:4]
        if cabeca == b'PKT0':
            return 0, pctdata[4:]
        elif cabeca == b'PKT1':
            return 1, pctdata[4:]
        
        return -1, b''

    def receive_bytes(self):
        data_recebida = b''

        self.socket.settimeout(None) # pra remover o timeout do socket (importante)
    
        while True:
            pkts, addr = self.socket.recvfrom(type(self).buffer_size)
            seqnum, data = type(self).extrai_pacote(pkts)
            self.ultimo_addr = addr #salvando endereco

            if seqnum == -1:
                print("Recebi um pacote com erro! B(")
                continue
            
            print("Recebi um pacote! XD")
            if seqnum == self.numesperado:
                # acumula payload
                data_recebida += data

                # envia ack
                ack_pkts = type(self).acks[seqnum]
                print("Enviando ACK!")
                type(self).udt_send(ack_pkts, addr)
                self.numesperado = 1 - self.numesperado
                if len(data) == 0:
                    # Pacote sem corpo: é o último.
                    print("Isso quer dizer que acabou ne? :(")
                    print("Mas vai que tem mais coisa ne! :)")
                    # Tenta receber mais um pacote (cajo o ack se perca)
                    self.socket.settimeout(0.5)
                    try:
                        while True:
                            # Tenta receber
                            pkts, addr = self.socket.recvfrom(type(self).buffer_size)
                            self.ultimo_addr = addr
                            # Se recebeu, restransmite ACK
                            seqnum, data = type(self).extrai_pacote(pkts)
                            if seqnum != -1:
                                #recebeu algo!!! e sem erro!
                                ack_pkts = type(self).acks[seqnum]
                                type(self).udt_send(ack_pkts, addr)
                                print("Eu recebi. Eu recebi algo. B')")
                    except:
                        # Deu timeout, então acabou
                        print("Eu nao recebi nada... A transmissao de dados acabou!")
                        break
            else:
                # pacote fora de ordem, so envia ack
                ack_pkts = type(self).acks[seqnum]
                type(self).udt_send(ack_pkts, addr)
                print("Recebi um pacote fora de ordem! Reenviando ACK")
        
        return data_recebida, self.ultimo_addr
