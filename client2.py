import pygame
import socket
import math

WINDOW_WIDTH = 600
WINDOW_HEIGHT = 600
ROW_NUM = 6
COLUMN_NUM = 7
RADIOS = WINDOW_WIDTH/15
SPACE = 5

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)

FRAME_RATE = 24
MAX_TIME = 120  # in seconds

LEFT = 1
HEIGHT_RECT = RADIOS * 2
WIDTH_RECT = RADIOS * (2 * COLUMN_NUM + 1)
MYPLAYERNUM = 2

OPEN_SCREEN = "Open.png"
INSTRUCTIONS = "Instructions.png"
WAIT = "Wait.png"
IP = "127.0.0.1"
PORT = 8820


def draw_board(screen):
    """Draw the board"""
    screen.fill(BLUE)
    pygame.draw.rect(screen, BLACK, pygame.Rect(0, 0, WIDTH_RECT, HEIGHT_RECT))
    pos = [RADIOS, RADIOS * 3 + SPACE]
    for col in range(COLUMN_NUM):
        for row in range(ROW_NUM):
            pygame.draw.circle(screen, BLACK, tuple(pos), RADIOS)
            pos[1] += (RADIOS * 2 + SPACE)  # change the next position
        pos[1] = RADIOS * 3 + SPACE  # change the next position
        pos[0] += (RADIOS * 2 + SPACE)
    pygame.display.flip()


def draw_image(screen, image1):
    img = pygame.image.load(image1)
    screen.blit(img, (0, 0))
    pygame.display.flip()


def draw_status(status, screen):
    font = pygame.font.SysFont("comicsansms", 45)
    text_surface = font.render(status, True, CYAN)
    screen.blit(text_surface, (0, 0))
    pygame.display.flip()


def main():
    # open socket with the server
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Init screen
    pygame.init()
    size = (WINDOW_WIDTH, WINDOW_HEIGHT)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Connect 4")
    draw_image(screen, OPEN_SCREEN)  # open screen
    clock = pygame.time.Clock()

    start_game = False
    instructions = False
    while (not start_game) and (not instructions):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT:
                if 35 <= event.pos[0] <= 170 and 500 <= event.pos[1] <= 580:  # play button
                    start_game = True
                elif 420 <= event.pos[0] <= 590 and 500 <= event.pos[1] <= 580:  # instructions button
                    draw_image(screen, INSTRUCTIONS)
                    instructions = True
    if instructions:  # print instructions
        while not start_game:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT:
                    if 210 <= event.pos[0] <= 370 and 420 <= event.pos[1] <= 485:  # play button
                        start_game = True
    # Game loop:
    my_socket.connect((IP, PORT))
    data = my_socket.recv(1024).decode().split("|")  # start/wait
    print(data)
    if data[0] == "WAIT":  # Print the wait screen to the player
        draw_image(screen, WAIT)
        data = my_socket.recv(1024).decode().split("|")  # to receive the start message

    if data[0] == "ENDTIME":  # The waiting time (30 seconds) left
        print("Opponent's time went out")
        draw_status("Opponent's time went out", screen)
        my_socket.send("END|".encode())

    if data[0] == "START":
        draw_board(screen)
        done = False
        while not done:
            data = my_socket.recv(1024).decode().split("|")
            print(data)
            my_turn = False
            got_enemy_turn = False
            if data[0] == "TURN":
                if int(data[1]) == MYPLAYERNUM:
                    my_turn = True
            finish = False
            frame_count = 0
            while not finish:
                # Print the timer on screen:
                pygame.draw.rect(screen, BLACK, pygame.Rect(0, 0, WIDTH_RECT/3, HEIGHT_RECT/2))
                total_seconds = MAX_TIME - (frame_count // FRAME_RATE)
                if total_seconds < 0:
                    total_seconds = 0
                minutes = total_seconds // 60  # Divide by 60 to get total minutes
                seconds = total_seconds % 60  # Use modulus (remainder) to get seconds
                font = pygame.font.SysFont("comicsansms", 25)  # font for timer
                output_string = "Time left: {0:02}:{1:02}".format(minutes, seconds)
                text = font.render(output_string, True, WHITE)
                screen.blit(text, [0, 0])
                frame_count += 1
                clock.tick(FRAME_RATE)  # Limit frames per second
                pygame.display.flip()
                if "00:00" in output_string:  # the time is over
                    finish = True
                    done = True
                    my_socket.send("TIMEOVER|".encode())
                    draw_status("YOUR TIME ENDED!", screen)
                    print("MY TIME ENDED!")
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        my_socket.send("END|".encode())
                        done = True
                        finish = True
                        exit()
                    pygame.mouse.set_visible(False)
                    made_move = False
                    occupied = False

                    if my_turn:
                        if event.type == pygame.MOUSEMOTION:
                            pygame.draw.rect(screen, BLACK, (0, 0, WIDTH_RECT, HEIGHT_RECT))
                            pygame.draw.circle(screen, YELLOW, (event.pos[0], RADIOS), RADIOS)
                        pygame.display.update()

                        while event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT and not made_move and not occupied:
                            col_num = math.floor(event.pos[0] / (RADIOS*2))  # player's input- the column number
                            my_socket.send(("ISVALID|" + str(col_num) + "|" + str(MYPLAYERNUM)).encode())
                            answer = my_socket.recv(1024).decode()
                            print("answer", answer)

                            if answer.split("|")[0] == "VALID":
                                row_num = ROW_NUM - int(answer.split("|")[1])
                                pygame.draw.circle(screen, YELLOW, (col_num*(2*RADIOS+SPACE)+RADIOS, row_num*(2*RADIOS+SPACE)+RADIOS), RADIOS)  # the x correct place
                                pygame.display.flip()
                                made_move = True
                                my_turn = False
                                got_enemy_turn = False

                            elif answer.split("|")[0] == "OCCUPIED" and not occupied:
                                occupied = True

                            elif answer.split("|")[0] == "WIN":
                                print("IM THE WINNER")
                                draw_status("YOU ARE THE WINNER!", screen)
                                row_num = ROW_NUM - int(answer.split("|")[1])
                                pygame.draw.circle(screen, RED, (col_num*(2*RADIOS+SPACE)+RADIOS, row_num*(2*RADIOS+SPACE)+RADIOS), RADIOS)  # the x correct place
                                pygame.display.flip()
                                made_move = True
                                done = True
                                finish = True
                                my_socket.send("END|".encode())

                    else:
                        if event.type == pygame.MOUSEMOTION:
                            pygame.draw.rect(screen, BLACK, (0, 0, WIDTH_RECT, HEIGHT_RECT))
                            pygame.draw.circle(screen, YELLOW, (event.pos[0], RADIOS), RADIOS)
                        pygame.display.update()
                        if not got_enemy_turn:
                            my_socket.send(("WHATENEMY|"+str(MYPLAYERNUM)).encode())
                            data = my_socket.recv(1024).decode().split("|")
                            print("data", data)

                            if data[0] == "STOPGAME":
                                if data[1] == "TIMEOVER":
                                    draw_status("OPPONENT'S TIME OVER", screen)
                                else:
                                    draw_status("OTHER OPPONENT LEFT", screen)
                                my_socket.send("END|".encode())
                                done = True
                                finish = True
                                got_enemy_turn = True
                                my_turn = True
                                print("The other opponent left")

                            elif data[0] == "ENEMYTURN":
                                if data[3] == "True":
                                    my_socket.send("END|".encode())
                                    draw_status("YOU ARE THE LOSER!", screen)
                                    print("IM THE LOSER")
                                    done = True
                                    finish = True
                                got_enemy_turn = True
                                my_turn = True
                                col = int(data[2])
                                row = ROW_NUM - int(data[1])
                                print("enemy turn:", col, "", row)
                                pygame.draw.circle(screen, RED, (col * (2 * RADIOS + SPACE) + RADIOS, row * (2 * RADIOS + SPACE) + RADIOS), RADIOS)  # not sure about the row!!!!
                                pygame.display.flip()
    pygame.time.wait(3000)
    my_socket.close()


if __name__ == "__main__":
    main()
