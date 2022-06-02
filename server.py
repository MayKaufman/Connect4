import socket
import numpy
import threading
import time

IP = "0.0.0.0"
PORT = 8820
ROW_NUM = 6
COLUMN_NUM = 7
MAX_TIME = 10  # max waiting time (in seconds)
server_exit = False
turn = 1
board = numpy.zeros((ROW_NUM, COLUMN_NUM))
last_turn = []  # [row,col,True/False- if win]
lock = threading.Lock()
is_win = False
num_of_connected_players = 0
exit_reason = ""  # default: other opponent left


def get_new_board():
    return numpy.zeros((ROW_NUM, COLUMN_NUM))


def is_valid_move(board, col):
    """Check if the move is validate"""
    return board[ROW_NUM - 1][col] == 0


def do_move(board, row, col, player_num):
    """Update the board with the new player's move"""
    board[row][col] = player_num


def get_free_row(board, col):
    """Returns the next free row-depending on the column"""
    for row in range(ROW_NUM):
        if board[row][col] == 0:
            return row


def check_win(board, player_num):
    """Check if the player won: vertical, horizontal and diagonals"""
    # Check vertical:
    for col in range(COLUMN_NUM):
        for row in range(ROW_NUM - 3):
            if board[row][col] == player_num and board[row + 1][col] == player_num and \
                    board[row + 2][col] == player_num and board[row + 3][col] == player_num:
                return True

    # Check horizontal:
    for col in range(COLUMN_NUM - 3):
        for row in range(ROW_NUM):
            if board[row][col] == player_num and board[row][col + 1] == player_num and \
                    board[row][col + 2] == player_num and board[row][col + 3] == player_num:
                return True

    # Check diagonals:
    for col in range(COLUMN_NUM - 3):
        for row in range(ROW_NUM - 3):
            if board[row][col] == player_num and board[row + 1][col + 1] == player_num and \
                    board[row + 2][col + 2] == player_num and board[row + 3][col + 3] == player_num:
                return True

    for col in range(COLUMN_NUM - 3):
        for row in range(3, ROW_NUM):
            if board[row][col] == player_num and board[row - 1][col + 1] == player_num and \
                    board[row - 2][col + 2] == player_num and board[row - 3][col + 3] == player_num:
                return True


def print_board(board):
    print(numpy.flip(board, 0))  # why flip?


def handle_client(client_socket):
    global server_exit
    global exit_reason
    global turn
    global board
    global last_turn
    global is_win
    global num_of_connected_players

    lock.acquire()
    num_of_connected_players += 1
    lock.release()
    count_time = 0
    if num_of_connected_players != 2:
        client_socket.send("WAIT|".encode())
        while num_of_connected_players != 2 and count_time != MAX_TIME:  # A loop just to wait until other opponent will connect
            count_time += 1
            time.sleep(1)

    if count_time == MAX_TIME:  # to check if player waits more than 30 seconds- end game
        server_exit = True
        client_socket.send("ENDTIME|".encode())
    else:
        client_socket.send("START|".encode())

    client_socket.send(("TURN|" + str(turn)).encode())

    while not server_exit:
        data = client_socket.recv(1024).decode().split("|")
        print("received data", data)
        if data[0] == "END" or data[0] == "TIMEOVER":
            exit_reason = data[0]
            server_exit = True
            lock.acquire()
            if turn == 1:
                turn = 2
            else:
                turn = 1
            lock.release()
        elif data[0] == "ISVALID" and int(data[2]) == turn:  # check if the turn is for the right player
            col = int(data[1])
            row = get_free_row(board, col)
            if is_valid_move(board, col):  # int(data[1]) = col
                do_move(board, row, col, turn)
                print_board(board)

                if check_win(board, turn):
                    client_socket.send(("WIN|" + str(row) + "|" + str(turn)).encode())
                    is_win = True
                else:
                    client_socket.send(("VALID|" + str(row)).encode())
                lock.acquire()
                last_turn = [row, col, is_win]
                if turn == 1:
                    turn = 2
                else:
                    turn = 1
                lock.release()

            else:
                client_socket.send(("OCCUPIED|".encode()))
        if data[0] == "WHATENEMY":  # the enemy did his turn already
            while int(data[1]) != turn:  # A loop just to wait until other opponent will finish his move
                nothing = 1
            if server_exit:
                client_socket.send(("STOPGAME|"+exit_reason).encode())
                print("STOPGAME|"+exit_reason)
            else:
                client_socket.send(("ENEMYTURN|" + str(last_turn[0]) + "|" + str(last_turn[1]) + "|" + str(last_turn[2])).encode())
    client_socket.close()


def main():
    global server_exit
    threads = []
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, PORT))
    server_socket.listen(5)
    try:
        while not server_exit:
            client_socket, client_address = server_socket.accept()
            print('Connected to: ' + client_address[0] + ':' + str(client_address[1]))
            t = threading.Thread(target=handle_client, args=(client_socket,))
            t.start()
            threads.append(t)
    except KeyboardInterrupt:  # The server want to exit
        server_exit = True
    except():
        print("Error in socket")

    for t in threads:
        t.join()
    server_socket.close()


if __name__ == "__main__":
    main()
