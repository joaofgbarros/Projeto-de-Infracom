from socket import *
from random import random

class rdt_sender:
    acks = [b'ACK0', b'ACK1']
    pkts = [b'PKT0', b'PKT1']
    buffer_size = 1024
    lost_pkt_probability = 0.2
    
    def __init__(self, socket: socket):
        self.socket = socket
        self.seqnum = 0
    
    def send_bytes(self, data, dest):
        # Envia os chunks
        self.socket.settimeout(0.1)
        for i in range(0, len(data), type(self).buffer_size-4):
            # Chunk dos dados + número de sequência
            msg = type(self).pkts[self.seqnum] + data[i:i+type(self).buffer_size-4]
            self.send(msg, dest)
            print("Recebi o ACK bom >:D")
            self.seqnum = 1 - self.seqnum
        self.send(type(self).pkts[self.seqnum], dest)

    def send(self, msg, dest):
        self.udt_send(msg, dest)
        recvd = False
        while not recvd:
            # Assume que enviou. Agora, quero o meu ACK.
            try:
                ack = self.socket.recv(type(self).buffer_size)
                recvd = (ack == type(self).acks[self.seqnum])
            except:
                print("Timeout! Retransmitindo...")
                self.udt_send(msg, dest)


    def udt_send(self, data, dest):
        # nao falta adicionar o random :-) ;)
        if random() <= lost_pkt_probability
            print("Simulando a perda do pacote...")
        else:
            self.socket.sendto(data, dest)
