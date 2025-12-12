from socket import *
from rdt import *
import random
import threading
import time

sock = socket(AF_INET, SOCK_DGRAM)
sock.bind(('localhost', 12000))
print("O servidor HuntCin está pronto para receber!")

recebedor = rdt_receiver(sock)
enviador = rdt_sender(sock)

# estado atual do jogo

usuarios = {}          # nome → addr ; usuarios online, pra saber a porta endereco
enderecos = {}         # addr → nome ; contrario: pega porta e sabe usuario q mandou
pos = {}               # nome → (x,y) ; posicao do usuario no grid
usou_hint = {}         # nome → ja usou sim ou nao (so pode 1)
usou_suggest = {}      # nome → booleano tb
tesouro = None         # (x, y) ; posicao do tesouro
ociosos = {}           # nome -> addr ; usado para saber se o servidor está a espera de um ACK de um usuário especifico

# funcoes pro jogo

def envia(addr, msg):
    enviador.send(msg.encode(), addr)
    
def broadcast(msg):
    for _, addr in usuarios.items():
      if _, addr not in ociosos.items(): 
        envia(addr, msg)    
    
def sorteia_tesouro():
    global tesouro
    #grid 3x3
    while True:
        x = random.randint(1, 3)
        y = random.randint(1, 3)

        # nao pode comecar junto com os jogadores em 1,1
        if (x, y) != (1, 1):
            tesouro = (x, y)
            return

def estado():
    s = "[Servidor] Estado atual: " # msg q envia a cada rodada
    partes = []
    for nome, (x,y) in pos.items():
        partes.append(f"{nome}({x},{y})")
    return s + ", ".join(partes)

###

while True:
    
    data, addr = recebedor.recv()
    if (_, addr in ociosos.items()):
        del ociosos[usuarios[addr]]
    cmd = data.decode().strip().split()

    #recebendo comandos

    # login
    if cmd[0] == "login":
        nome = cmd[1]

        if nome in usuarios:
            envia(addr, "alguem ja usou esse nome! seja mais original") # nao pode nome repetido
            continue
        
        usuarios[nome] = addr
        enderecos[addr] = nome

        # valores iniciais
        pos[nome] = (1,1)
        usou_hint[nome] = False
        usou_suggest[nome] = False

        if tesouro is None:
            sorteia_tesouro()

        envia(addr, "voce esta online!")
        ociosos[nome] = addr
        continue

    # precisa ta logado p continuar
    if addr not in enderecos:
        envia(addr, "voce precisa fazer login primeiro")
        continue

    nome = enderecos[addr]

    # logout
    if cmd[0] == "logout": # remove o usuario
        del usuarios[nome]
        del enderecos[addr]
        del pos[nome]
        envia(addr, "voce deslogou")
        continue

    # move (incrementa as coordenadas. tem que impedir de "sair" do grid  
    if cmd[0] == "move":
        direcao = cmd[1]

        x, y = pos[nome]

        if direcao == "up":
            y += 1
        elif direcao == "down":
            y -= 1
        elif direcao == "left":
            x -= 1
        elif direcao == "right":
            x += 1

        # checa se nao vai sair
        if not (1 <= x <= 3 and 1 <= y <= 3):
            envia(addr, "cuidado, voce vai sair do mapa!")
            ociosos[nome] = addr
            continue

        pos[nome] = (x,y)

        # se achou o tesouro, avisa todos: “ O jogador <nome:porta> encontrou o tesouro na posição (x,y)!”
        if (x,y) == tesouro:
            broadcast(f"O jogador {nome} encontrou o tesouro na posição {tesouro}!")
            for nome, (x,y) in pos.items():
                pos[nome] = (1,1)
            for nome, _ in usou_hint:
                del usou_hint[nome]
            for nome, _ in usou_suggest:
                del usou_suggest[nome]
            sorteia_tesouro()

        broadcast(estado()) # fim da rodada, mostra estado
        continue


    # para os recursos especiais, ja que a funcao dos dois eh a mesma de informar uma direcao do tesouro,
    # ambos comparam as coordenadas do usuario aas do tesouro, mas possuem prioridade diferente sobre qual direcao dizer
    # por exemplo, se o jogador esta em (1,1) e o tesouro em(2,2), a hint vera logo que X(tesouro) > X(user) e 
    # dira pro jogador ir para direita. ja o suggest vera primeiro que Y(tesouro) > Y(user), e sugere  UP.
    # dessa forma, os dois recursos so devolvem a mesma direcao se ela for a unica que precisa ser tomada (reto) ate o tesouro.
    
    # hint dica, printa ex: “O tesouro está mais acima.”
    """
    if cmd[0] == "hint":
        if usou_hint[nome]:
            envia(addr, "voce ja usou hint!")
            ociosos[nome] = addr
            continue

        usou_hint[nome] = True #hint usada
        px, py = pos[nome]
        tx, ty = tesouro

        if (ty-py) > 0 and abs((ty-py)) >= abs((tx-px)):
            envia(addr, "O tesouro está mais acima")
            ociosos[nome] = addr
        elif (tx-px) > 0 and abs((tx-px)) >= abs((ty-py)):
            envia(addr, "O tesouro está mais a direita")
            ociosos[nome] = addr
        elif (tx-px) < 0 and abs((tx-px)) >= abs((ty-py)):
            envia(addr, "O tesouro está mais a esquerda")
            ociosos[nome] = addr
        else (ty-py) < 0 and abs((tx-px)) >= abs((ty-py)):
            envia(addr, "O tesouro está mais abaixo")
            ociosos[nome] = addr
        continue
    """
    
    # sugestao, printa ex: “Sugestão: move up.”
    if cmd[0] == "suggest":
        if usou_suggest[nome]:
            envia(addr, "voce ja usou suggest!")
            ociosos[nome] = addr
            continue

        usou_suggest[nome] = True #agora ja usou

        px, py = pos[nome]
        tx, ty = tesouro

        if ty > py:
            envia(addr, "Sugestão: move up.")
            ociosos[nome] = addr
        elif ty < py:
            envia(addr, "Sugestão: move down.")
            ociosos[nome] = addr
        elif tx > px:
            envia(addr, "Sugestão: move right.")
            ociosos[nome] = addr
        else:
            envia(addr, "Sugestão: move left.")
            ociosos[nome] = addr
        continue
    
