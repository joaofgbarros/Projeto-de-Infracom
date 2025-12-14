from socket import *
from rdt import *
import random
import time

class Player:
    def __init__(self, addr, username):
        self.addr = addr
        self.username = username
        self.play = False
        self.idle = False
        self.score = 0
        
        self.hint = False
        self.suggest = False
        self.pos = (1, 1)
    
    def reset(self):
        self.play = True
        self.hint = False
        self.suggest = False
        self.pos = (1, 1)
    
    def ganha(self):
        self.score += 1
    
    def elimina(self):
        self.play = False

    def is_idle(self):
        return self.idle

    def set_idle(self, idle): 
        self.idle = idle
    
    def is_playing(self): 
        return self.play

    def get_username(self):
        return self.username
    
    def get_addr(self):
        return self.addr

    def get_full_username(self):
        return f"<{self.username}:{self.addr}>"
    
    def get_pos(self):
        return self.pos
    
    def set_pos(self, x, y):
        self.pos = (x, y)

    def get_score(self):
        return self.score

    def get_hint(self):
        return self.hint
    
    def set_hint(self, hint):
        self.hint = hint

    def get_suggest(self):
        return self.suggest

    def set_suggest(self, suggest):
        self.suggest = suggest


class Server:
    def __init__(self, addr):
        self.addr = addr
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind(addr)
        
        self.recebedor = rdt_receiver(self.sock)
        self.enviador = rdt_sender(self.sock)

        self.nomes = set()
        self.online = {}
        self.tesouro = (3, 3)
        self.ganador = None
        self.run = False
        self.tempo_rodada = 30
    
    def envia(self, addr, msg):
        self.enviador.send(msg.encode(), addr)
    
    def broadcast(self, msg):
        for addr, player in self.online.items():
            if not player.is_idle():
                self.envia(addr, msg)

    def sorteia_tesouro(self):
        #grid 3x3
        while True:
            x = random.randint(1, 3)
            y = random.randint(1, 3)

            # nao pode comecar junto com os jogadores em 1,1
            if (x, y) != (1, 1):
                self.tesouro = (x, y)
                print("Tesouro está em ", self.tesouro, ". Shhhh...")
                return
    
    def estado(self):
        s = "[Servidor] Estado atual: " # msg q envia a cada rodada
        partes = []
        for _, player in self.online.items():
            if player.play:
                partes.append(f"{player.get_username()}{player.get_pos()}")
        return s + ", ".join(partes)

    def comanda(self, data, addr):
        cmd = data.decode().strip().split()

        if cmd[0] == 'login':
            nome = cmd[1]
            self.login(addr, nome)
            return
        
        # precisa ta logado p continuar
        if addr not in self.online:
            self.envia(addr, "[Servidor] voce precisa fazer login primeiro")
            self.envia(addr,"INPUT")
            return
        player = self.online[addr]

        if cmd[0] == 'logout':
            self.logout(player)
            return

        # Precisa estar jogando pra continuar
        if not player.is_playing():
            self.envia(addr, "[Servidor] Você foi eliminado por inatividade")
            player.set_idle(False)
        elif cmd[0] == 'move':
            dir = cmd[1]
            if self.move(player, dir) and self.ganador == None: # Se achou o tesouro, guarda ganador
                self.ganador = player
        elif cmd[0] == 'hint':
            self.hint(player)
        elif cmd[0] == 'suggest':
            self.suggest(player)
        else:
            self.envia(addr, "Não entendi esse comando :/")
            self.envia(addr, "INPUT")
        
        return
        

    def roda_rodada(self):
        self.broadcast(f"[Servidor] Rodada iniciada! Jogadores têm {self.tempo_rodada} segundos para enviar os seus movimentos.") #em um tom claro de ameaça
        for addr, player in self.online.items():
            if player.is_playing() and not player.is_idle():
                self.envia(addr, "INPUT")
                player.set_idle(True)
        
        inicio = time.time()
        while time.time() - inicio < self.tempo_rodada: #timeout de 10s pra receber os comandos
            try:
                data, addr = self.recebedor.recv()
                if data:
                    self.comanda(data, addr) # Processa o comando
                    alguem = False
                    for _, player in self.online.items():
                        if player.is_playing() and player.is_idle():
                            alguem = True
                    if not alguem: break
            except timeout:
                pass

        # elimina
        for _, player in self.online.items():
            if player.is_playing() and player.is_idle():
                player.elimina()
        
        # Envia estado
        self.broadcast(self.estado())

        # Checa se acabou (alguem chegou no tesouro, ou nao tem mais ninguem)
        alguem = False
        for _, player in self.online.items():
            if player.is_playing():
                alguem = True
        
        if not alguem or self.ganador != None:
            self.run = False
        if self.ganador != None:
            self.broadcast(f"[Servidor] O jogador {self.ganador.get_full_username()} encontrou o tesouro na posição {self.tesouro}!")
            self.ganador.ganha()

    def main(self):
        print("O servidor esta online B) e aguardando jogadores B(") #o adm esta olaine
        while True:
            if not self.online:
                try:
                    data, addr = self.recebedor.recv()
                    self.comanda(data, addr)
                except TimeoutError: pass
                continue
            
            time.sleep(3)
            print("\natencao Creuzebek, vai comecar a baixaria")
            # Reseta todo mundo pra começar uma nova rodada (todo mundo jogando, queiram ou não >:D)
            for addr, player in self.online.items():
                if not player.is_idle():
                    player.reset()
            self.sorteia_tesouro()
            self.ganador = None
            self.run = True
            while self.run:
                self.roda_rodada()

            self.broadcast("Ranking atual: ")
            for addr, player in self.online.items():
                self.broadcast(f"  O jogador {player.get_username()} está com {player.get_score()}.")

            print("acabou, Creuzebek :( acabou a baixaria)")

    def login(self, addr, username):
        # Checa se ja existe alguem nesse endereço / com esse nome
        if addr in self.online:
            self.envia(addr, "[Servidor] Você já está online!")
            self.envia(addr, "INPUT")
        else:
            tem = False
            for _, player in self.online.items():
                if player.get_username() == username:
                    tem = True
            if tem:
                self.envia(addr, "[Servidor] Já tem alguém com esse nome! >:C")
                self.envia(addr, "INPUT")
            else:
                self.envia(addr, "[Servidor] Você está online :-)")
                self.online[addr] = Player(addr, username)

    def logout(self, player):
        addr = player.get_addr()
        del self.online[addr]
        self.broadcast(f"Eita. O jogador {player.get_username()} não aguentou...")

    def move(self, player, dir):
        x, y = player.get_pos()
        addr = player.get_addr()

        if dir == "up":
            y += 1
        elif dir == "down":
            y -= 1
        elif dir == "left":
            x -= 1
        elif dir == "right":
            x += 1
        else:
            self.envia(addr, "[Servidor] Como que tu quer jogar o jogo sem saber jogar. Joga o jogo.")
            self.envia(addr, "INPUT")
            return False
        # checa se nao vai sair
        if not (1 <= x <= 3 and 1 <= y <= 3):
            self.envia(addr, "[Servidor] cuidado, voce vai sair do mapa!")
            self.envia(addr,"INPUT")
            return False
        player.set_pos(x,y)
        player.set_idle(False)

        # se achou o tesouro, avisa todos: “ O jogador <nome:porta> encontrou o tesouro na posição (x,y)!”
        return (x, y) == self.tesouro

    def hint(self, player):
        addr = player.get_addr()
        if player.get_hint():
            self.envia(addr, "[Servidor] voce ja usou hint!")
            self.envia(addr,"INPUT")
            return

        player.set_hint(True)
        player.set_idle(False)
        px, py = player.get_pos()
        tx, ty = self.tesouro

        if (ty-py) > 0 and abs((ty-py)) >= abs((tx-px)):
            self.envia(addr, "Dica: O tesouro está mais acima")
        elif (tx-px) > 0 and abs((tx-px)) >= abs((ty-py)):
            self.envia(addr, "Dica: O tesouro está mais a direita")
        elif (tx-px) < 0 and abs((tx-px)) >= abs((ty-py)):
            self.envia(addr, "Dica: O tesouro está mais a esquerda")
        else:
            self.envia(addr, "Dica: O tesouro está mais abaixo")

    def suggest(self, player):
        addr = player.get_addr()
        if player.get_suggest():
            self.envia(addr, "[Servidor] voce ja usou suggest!")
            self.envia(addr,"INPUT")
            return

        player.set_suggest(True)
        player.set_idle(False)
        px, py = player.get_pos()
        tx, ty = self.tesouro

        if ty > py:
            self.envia(addr, f"Sugestão: move up {ty-py} casas.")
        elif ty < py:
            self.envia(addr, f"Sugestão: move down {py-ty} casas.")
        elif tx > px:
            self.envia(addr, f"Sugestão: move right {tx-px} casas.")
        else:
            self.envia(addr, f"Sugestão: move left {px-tx} casas.")


if __name__ == '__main__':
    server_addr = ('localhost', 12000)
    serv = Server(server_addr)
    serv.main()
