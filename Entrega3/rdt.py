from socket import *
from random import random

class rdt:
    acks = [b'ACK0', b'ACK1'] # ACKS
    pkts = [b'PKT0', b'PKT1'] # Números de Sequência
    buffer_size = 1024
    lost_pkt_probability = 0.05

    def __init__(self, socket: socket):
        self.socket = socket

    def udt_send(self, data, dest):
        # Simula perda de pacotes
        if random() > type(self).lost_pkt_probability:
            self.socket.sendto(data, dest)

class rdt_sender(rdt):
    def __init__(self, socket: socket):
        super().__init__(socket)
        self.nums = dict() # Números de sequência. Mapeia addr -> seqnum

    # Envia um pacote e recebe o ack correspondente
    def send(self, msg, dest, timeout=0.1):
        # Insere endereço destino se for novo
        if dest not in self.nums:
            self.nums[dest] = 0
        
        # Monta mensagem e envia
        pkt = type(self).pkts[self.nums[dest]] + msg
        self.socket.settimeout(timeout)
        self.udt_send(pkt, dest)
        recvd = False
        while not recvd:
            # Assume que enviou bem. Espera o ACK
            try:
                ack, addr = self.socket.recvfrom(type(self).buffer_size)
                # Se for o ack certo, recvd = True, e sai do loop. Se não, ignora
                recvd = (ack == type(self).acks[self.nums[dest]])
            except TimeoutError:
                # Pacote perdido? Reenvia
                self.udt_send(pkt, dest)
        self.nums[dest] = 1 - self.nums[dest] # Flipa

class rdt_receiver(rdt):
    def __init__(self, socket: socket):
        super().__init__(socket)
        self.nums = dict() # Dicionario para manter seqnum esperado de todos do clientes / do servidor

    def extrai_pacote(pctdata):
        cabeca = pctdata[:4]
        if cabeca == b'PKT0':
            return 0, pctdata[4:]
        elif cabeca == b'PKT1':
            return 1, pctdata[4:]
        
        return -1, b'' # Bronca

    def recv(self, timeout=0.1):
        self.socket.settimeout(timeout) 
        receba = True
        while receba:
            # Recebe pacote
            pkts, addr = self.socket.recvfrom(type(self).buffer_size)
            # Extrai os dados
            seqnum, data = type(self).extrai_pacote(pkts)

            if seqnum == -1: # Bronca
                return
            
            # Adiciona no dicionário se é endereço novo
            if addr not in self.nums:
                self.nums[addr] = seqnum
            
            if seqnum == self.nums[addr]:
                # Envia ack e sai do loop (pra retornar)
                ack_pkts = type(self).acks[seqnum]
                self.udt_send(ack_pkts, addr)
                self.nums[addr] = 1 - self.nums[addr] # Flipa
                receba = False
            else:
                # pacote fora de ordem, so envia ack e espera outro
                ack_pkts = type(self).acks[seqnum]
                self.udt_send(ack_pkts, addr)
            
        # Retorna dados (e endereço)
        return data, addr
