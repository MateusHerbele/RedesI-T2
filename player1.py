import socket
from game import Game
from player import Player
from network import send_broadcast, send_unicast, ring_messages

def wait_for_user_input():
    while True:
        user_input = input("Digite 'sim' para iniciar a comunicação: ").strip().lower()
        if user_input == "sim":
            break
        else:
            print("Entrada inválida. Por favor, digite 'sim' para iniciar a comunicação.")

def dealer_routine(dealer_index, game, player, socket_sender, socket_receiver, NEXT_NODE_ADDRESS):
    # Inicializar o jogo
    while True:
        n_sub_rounds = 0
        game.initialize_deck() # Inicializa o baralho
        game.shuffle_deck() # Embaralha o baralho
        cards_to_send = game.draw_cards() # Distribui as cartas 
        if n_sub_rounds == 0:
            cards = send_broadcast(socket_sender, socket_receiver, 1, cards_to_send, NEXT_NODE_ADDRESS) # Envia as cartas para os jogadores
            n_players_alive = game.state['players_alive'].count(True)
            player.receive_cards(cards[n_players_alive-1]) # Recebe as cartas do dealer
            send_broadcast(socket_sender, socket_receiver, 2, game.state['vira'], NEXT_NODE_ADDRESS) # Envia o vira
            guesses = send_broadcast(socket_sender, socket_receiver, 3, None, NEXT_NODE_ADDRESS) # Pede os palpites
            player.make_a_guess(guesses, game.state['round'], n_players_alive) # Dealer faz o palpite
            guesses.append(player.guess)
            send_broadcast(socket_sender, socket_receiver, 4, guesses, NEXT_NODE_ADDRESS) # Envia os palpites
        # Manda a mensagem para coletar as cartas jogadas 
        # e recebe as cartas jogadas
        player.play_a_card([]) # Dealer joga uma carta
        cards_played = send_broadcast(socket_sender, socket_receiver, 5, player.card_played, NEXT_NODE_ADDRESS) 
        subround_winner = game.end_of_sub_round(cards_played) # Contabiliza quem fez a rodada
        if subround_winner != dealer_index:
            send_unicast(socket_sender, 0, (subround_winner, game), NEXT_NODE_ADDRESS) # Passa o token para quem vai "tornar"
                                                                           # E se tornar o "dealer" da próxima rodada
        n_sub_rounds += 1
        if n_sub_rounds == game.state['round']:
            round_evaluation = game.end_of_round() # Avalia a situação pós-rodada
            send_broadcast(socket_sender, 6, None, NEXT_NODE_ADDRESS) # Passa os resultados da rodada
            if round_evaluation == -1: # Ninguém ganhou
                next_dealer = game.next_dealer() # Pega o próximo dealer
                send_broadcast(socket_sender, socket_receiver, 0, (next_dealer, game), NEXT_NODE_ADDRESS) # Passa o token para o próximo dealer
                continue
            elif round_evaluation == -2: # Empate
                send_broadcast(socket_sender, socket_receiver, 7, round_evaluation, NEXT_NODE_ADDRESS)
            else: # Tem um vencedor
                send_broadcast(socket_sender, socket_receiver, 8, round_evaluation, NEXT_NODE_ADDRESS)
                break


# ----------------- Main -----------------
# CURRENT_NODE_ADDRESS = (("127.0.0.1", 21254), 0)
# NEXT_NODE_ADDRESS = (("127.0.0.1", 21255), 1)

# socket_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# socket_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# socket_receiver.bind(CURRENT_NODE_ADDRESS[0])

# token_available = True if CURRENT_NODE_ADDRESS[1] == 0 else False
# start_game = True if CURRENT_NODE_ADDRESS[1] == 0 else False
# player = Player()
# game = Game()

# wait_for_user_input()
# while True:
#     # Inicializar o jogo
#     if start_game:
#         dealer_routine(CURRENT_NODE_ADDRESS[1], game, player, socket_sender, socket_receiver)
#         start_game = False
#     # Verificar se o token está disponível
#     if token_available:
#         dealer_routine(CURRENT_NODE_ADDRESS[1], game, player, socket_sender, socket_receiver)
#     # Se não tiver, só espera as mensagens
#     else:
#         # Receber as mensagens
#         # Essa função só para quando receber o token
#         network_comunication = ring_messages(socket_sender, socket_receiver)
#         if network_comunication == 1:
#             token_available = True
#         if network_comunication == 0:
#             break # Acaba a execução do programa
def main():
    CURRENT_NODE_ADDRESS = (("127.0.0.1", 21254), 0)
    NEXT_NODE_ADDRESS = (("127.0.0.1", 21255), 1)

    socket_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    socket_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_receiver.bind(CURRENT_NODE_ADDRESS[0])

    token_available = True if CURRENT_NODE_ADDRESS[1] == 0 else False
    start_game = True if CURRENT_NODE_ADDRESS[1] == 0 else False
    player = Player()
    game = Game()

    wait_for_user_input()
    while True:
        # Inicializar o jogo
        if start_game:
            dealer_routine(CURRENT_NODE_ADDRESS[1], game, player, socket_sender, socket_receiver)
            start_game = False
        # Verificar se o token está disponível
        if token_available:
            dealer_routine(CURRENT_NODE_ADDRESS[1], game, player, socket_sender, socket_receiver)
            token_available = False  # Token usado
        # Se não tiver, só espera as mensagens
        else:
            # Receber as mensagens
            # Essa função só para quando receber o token
            network_comunication = ring_messages(socket_sender, socket_receiver)
            if network_comunication == 1:
                token_available = True
            if network_comunication == 0:
                break # Acaba a execução do programa

if __name__ == "__main__":
    main()