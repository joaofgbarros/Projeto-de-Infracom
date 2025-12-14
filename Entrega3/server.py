from socket import *
from rdt import *
import random
import time

sock = socket(AF_INET, SOCK_DGRAM)
sock.bind(('localhost', 12000))
print("O servidor HuntCin está pronto para receber!")

recebedor = rdt_receiver(sock)
enviador = rdt_sender(sock)

# estado atual do jogo

usuarios = {}               # nome → addr ; usuarios online, pra saber a porta endereco
enderecos = {}              # addr → nome ; contrario: pega porta e sabe usuario q mandou
pos = {}                    # nome → (x,y) ; posicao do usuario no grid
usou_hint = {}              # nome → ja usou sim ou nao (so pode 1)
usou_suggest = {}           # nome → booleano tb
tesouro = None              # (x, y) ; posicao do tesouro
ociosos = {}                # nome -> addr ; usado para saber se o servidor está a espera de um ACK de um usuário especifico
ranking = {}                # nome -> int ; usado para saber a pontuação do usuário

# controle das rodadas

rodada_ativa = False        # flag pra indicar se tem uma rodada rodando
tempo_rodada = 10           # 10 segundos por rodada
jogadores_jogando = set()   # jogadores que enviaram movimento nessa rodada

# funcoes pro jogo

def envia(addr, msg):
    enviador.send(msg.encode(), addr)
    
def broadcast(msg):
    for _, addr in usuarios.items():
       if _ not in ociosos:
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

def elimina(nome, motivo): #me de motivo pra ir embora
    if nome in usuarios and motivo == "eliminado":
        addr = usuarios[nome]
        envia(addr, f"Voce foi {motivo} B(") #avisando o perdedor
        #removendo o perdedor
        if nome in pos:
            del pos[nome]
        if nome in usou_hint:
            del usou_hint[nome]
        if nome in usou_suggest:
            del usou_suggest[nome]

        #termina de humilhar completamente o cara avisando os outros
        broadcast(f"{nome} foi {motivo} XD")
        return True
    if nome in usuarios and motivo == "desconectado":
        addr = usuarios[nome]
        envia(addr, f"Voce foi {motivo} B(") #avisando o perdedor
        #removendo o perdedor
        if nome in usuarios:
            del usuarios[nome]
        if addr in enderecos:
            del enderecos[addr]
        if nome in pos:
            del pos[nome]
        if nome in usou_hint:
            del usou_hint[nome]
        if nome in usou_suggest:
            del usou_suggest[nome]

        #termina de humilhar completamente o cara avisando os outros
        broadcast(f"{nome} foi {motivo} XD")
        return True
    return False

def comanda(data, addr):
    cmd = data.decode().strip().split()
    #recebendo comandos

    # login
    if cmd[0] == "login":
        nome = cmd[1]

        if nome in usuarios:
            envia(addr, "alguem ja usou esse nome! seja mais original") # nao pode nome repetido
            envia(addr,"INPUT")
            return
        
        usuarios[nome] = addr
        enderecos[addr] = nome
        ranking[nome] = 0

        # valores iniciais
        pos[nome] = (1,1)
        usou_hint[nome] = False
        usou_suggest[nome] = False

        if tesouro is None:
            sorteia_tesouro()

        envia(addr, "voce esta online!")
        #ociosos[nome] = addr
        return

    # precisa ta logado p continuar
    if addr not in enderecos:
        envia(addr, "voce precisa fazer login primeiro")
        envia(addr,"INPUT")
        return

    nome = enderecos[addr]

    # logout
    if cmd[0] == "logout": # remove o usuario
        elimina(nome, "desconectado") #uma eliminacao voluntaria
        envia(addr, "voce deslogou")
        envia(addr,"INPUT")
        return
    
    if rodada_ativa:
        if cmd[0] in ["move", "hint", "suggest"]:
            jogadores_jogando.add(nome)

        # move (incrementa as coordenadas. tem que impedir de "sair" do grid)
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
            else:
                envia("Como que tu quer jogar o jogo sem saber jogar. Joga o jogo.")
                envia("INPUT")
                return
            # checa se nao vai sair
            if not (1 <= x <= 3 and 1 <= y <= 3):
                envia(addr, "cuidado, voce vai sair do mapa!")
                envia(addr,"INPUT")
                #ociosos[nome] = addr
                return
            pos[nome] = (x,y)
            del ociosos[nome]

            # se achou o tesouro, avisa todos: “ O jogador <nome:porta> encontrou o tesouro na posição (x,y)!”
            if (x,y) == tesouro:
                broadcast(f"O jogador {nome} encontrou o tesouro na posição {tesouro}!")
                ranking[nome] = ranking[nome] + 1
                for nome, (x,y) in pos.items():
                    pos[nome] = (1,1)
                usou_hint.clear()
                usou_suggest.clear()
                return "achooou" #força o fim da rodada
            
            return


        # para os recursos especiais, ja que a funcao dos dois eh a mesma de informar uma direcao do tesouro,
        # ambos comparam as coordenadas do usuario aas do tesouro, mas possuem prioridade diferente sobre qual direcao dizer
        # por exemplo, se o jogador esta em (1,1) e o tesouro em(2,2), a hint vera logo que X(tesouro) > X(user) e 
        # dira pro jogador ir para direita. ja o suggest vera primeiro que Y(tesouro) > Y(user), e sugere  UP.
        # dessa forma, os dois recursos so devolvem a mesma direcao se ela for a unica que precisa ser tomada (reto) ate o tesouro.
        
        # hint dica, printa ex: “O tesouro está mais acima.”

        if cmd[0] == "hint":
            if usou_hint[nome]:
                envia(addr, "voce ja usou hint!")
                envia(addr,"INPUT")
                #ociosos[nome] = addr
                return

            usou_hint[nome] = True #hint usada
            px, py = pos[nome]
            tx, ty = tesouro

            if (ty-py) > 0 and abs((ty-py)) >= abs((tx-px)):
                envia(addr, "O tesouro está mais acima")
                #ociosos[nome] = addr
            elif (tx-px) > 0 and abs((tx-px)) >= abs((ty-py)):
                envia(addr, "O tesouro está mais a direita")
                #ociosos[nome] = addr
            elif (tx-px) < 0 and abs((tx-px)) >= abs((ty-py)):
                envia(addr, "O tesouro está mais a esquerda")
                #ociosos[nome] = addr
            else:
                envia(addr, "O tesouro está mais abaixo")
                #ociosos[nome] = addr
            del ociosos[nome]
            return
        
        # sugestao, printa ex: “Sugestão: move up.”
        if cmd[0] == "suggest":
            if usou_suggest[nome]:
                envia(addr, "voce ja usou suggest!")
                envia(addr,"INPUT")
                #ociosos[nome] = addr
                return

            usou_suggest[nome] = True #agora ja usou

            px, py = pos[nome]
            tx, ty = tesouro

            if ty > py:
                envia(addr, "Sugestão: move up.")
                #ociosos[nome] = addr
            elif ty < py:
                envia(addr, "Sugestão: move down.")
                #ociosos[nome] = addr
            elif tx > px:
                envia(addr, "Sugestão: move right.")
                #ociosos[nome] = addr
            else:
                envia(addr, "Sugestão: move left.")
                #ociosos[nome] = addr
            del ociosos[nome]
            return
    #nao ta tendo rodada e o cara ta querendo jogar, ô bixin ansioso
    envia(addr, "Espera comecar a rodada primeiro, danado")
    
def roda_rodada():
    global rodada_ativa, tesouro

    print("\natencao Creuzebek, vai comecar a baixaria")
    rodada_ativa = True
    jogadores_jogando.clear()

    if tesouro is None:
        sorteia_tesouro()

    broadcast(f"Rodada iniciada! Voce tem {tempo_rodada} segundos para enviar seu movimento.") #em um tom claro de ameaça
    broadcast("INPUT") #sinal pros clientes enviarem os seus comandos
    for nome, addr in usuarios.items():
        ociosos[nome] = addr
    inicio = time.time()
    achou = False

    while time.time() - inicio < tempo_rodada and not achou and ociosos: #timeout de 10s pra receber os comandos
        try:
            data, addr = recebedor.recv()
            sock.settimeout(0.1)
            if data:
                resultado = comanda(data, addr)
                if resultado == "achooou":
                    achou = True
        except timeout:
            pass
    #acabou a rodada
    rodada_ativa = False

    eliminados = []
    for nome in list(usuarios.keys()):
        if nome not in jogadores_jogando:
            eliminados.append(nome)
    
    #eliminando os eliminados B)
    for nome in eliminados:
        elimina(nome, "eliminado")

    if usuarios:
        broadcast(estado())
        broadcast("Ranking atual: ")
        for nome, addr in usuarios.items():
         broadcast(f"O jogador {nome} está com {ranking[nome]}.")
    
    else:
        broadcast("Isso significa que todo mundo foi eliminado né? Que bando de incompetentes")
    
    print("acabou, Creuzebek :( acabou a baixaria)")

###
print("O servidor esta online B) e aguardando jogadores B(") #o adm esta olaine
while True:
    if usuarios and not rodada_ativa:
        #precisa de uma pausa de tempo entre as rodadas?
        roda_rodada()
    try:
        sock.settimeout(0.1)
        data, addr = recebedor.recv()
        if data:
            comanda(data, addr)
    except timeout:
        continue
