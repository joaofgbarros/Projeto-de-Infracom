from socket import *

def cria_ack(seqnum):
    return b'ACK0' if seqnum == 0 else b'ACK1'

def extrai_pacote(pctdata):
    cabeca = pctdata[:4]
    if cabeca == b'PKT0':
        return 0, pctdata[4:]
    elif cabeca == b'PKT1':
        return 1, pctdata[4:]
    
    return -1, b''

class rdtrecebedor:
    def __init__(self, socket: socket):
        self.socket = socket
        self.numesperado = 0
    
    def receive_bytes(self):
        data_recebida = b''

        self.socket.settimeout(None) #pra remover o timeout do socket (importante)
    
        while True:
            pkts, addr = self.socket.recvfrom(1024)
            seqnum, data = extrai_pacote(pkts)

            if seqnum == -1:
                print("Recebi um pacote com erro! B(")
                continue

            print("Recebi um pacote! XD")
            if seqnum == self.numesperado:
                data_recebida += data

                #envia ack
                ack_pkts = cria_ack(seqnum)
                self.socket.sendto(ack_pkts, addr)
                print("Enviando ACK!")
                self.numesperado = 1 - self.numesperado
                if len(data) == 0:
                    print("Isso quer dizer que acabou ne? :(")
                    print("Mas vai que tem mais coisa ne! :)")
                    self.socket.settimeout(0.5)
                    try:
                        while True:
                            pkts, addr = self.socket.recvfrom(1024)
                            seqnum, data = extrai_pacote(pkts)

                            if seqnum != -1:
                                #recebeu algo!!! e sem erro!
                                ack_pkts = cria_ack(1 - self.numesperado)
                                self.socket.sendto(ack_pkts, addr)
                                print("Eu recebi. Eu recebi algo. B')")

                    except:
                        print("Eu nao recebi. Acabou a transmissao.")
                        break
            else:
                #pacote fora de ordem
                ultimo_pacote_bom = 1 - self.numesperado
                ack_pkts = cria_ack(ultimo_pacote_bom)
                self.socket.sendto(ack_pkts, addr)
                print("Recebi um pacote fora de ordem! Reenviando ACK")
        
        self.socket.settimeout(None)
        return data_recebida
