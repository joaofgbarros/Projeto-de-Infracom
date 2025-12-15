# Projeto de Infracom - Terceira Entrega
Terceira Entrega do projeto da disciplina de Infraestrutura da Comunicação.
Nesta entrega, foi implementado o HuntCIn: um jogo multiplayer implementado utilizando sockets UDP com transmissão confiável via protocolo RDT 3.0.

O objetivo é ser o primeiro a encontrar um tesouro escondido em um grid 3x3 com as jogadas possíveis.

## Como executar
### 1. Executar o servidor
- Abra o terminal dentro da pasta do projeto (`Entrega3/`)
- Execute o servidor
```bash
python server.py
```

### 2. Executar o cliente
- Abra outro terminal dentro da pasta do projeto (`Entrega3/`)
- Execute o cliente
```bash
python client.py
```

### 3. No cliente
- Faça login com um nome de usuário
```
> login <username>
```
- Quando a rodada começar, digite um dos comandos disponíveis:
    - `move right`: move o jogador uma casa para direita;
    - `move up`: move o jogador uma casa para cima;
    - `move left`: move o jogador uma casa para esquerda;
    - `move down`: move o jogador uma casa para baixo;
    - `hint`: pede ao servidor uma dica;
    - `suggest`: pede ao servidor uma sugestão de movimento.


## Integrantes do grupo
- Analía Eizmendi Camêlo
- Gledson Daniel Borges Campelo
- João Fernando Gama Barros
- João Victor Grangeiro Costa
