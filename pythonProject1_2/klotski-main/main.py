import sys
import os
import threading

import cv2
import pygame
from collections import OrderedDict
from hand import hand
import cam
from pygame.locals import *
import time
import random
from queue import PriorityQueue

FPS = 60  # 帧率
Shape = 3  # 游戏类型
cell_size = 200  # 方格大小
cell_gap_size = 10  # 方格间距
margin = 10  # 方格的边缘
padding = 10  # 方格的填料
left_screen_size = 300  # 左侧屏幕的大小
right_screen_size = 200  # 右侧屏幕的大小

button_size = 100
button_start_size = 300

button1_x = 800
button1_y = 20
button2_x = 800
button2_y = 160
button3_x = 800
button3_y = 300
button4_x = 950
button4_y = 50
button5_x = 950
button5_y = 200
button_start_x = 410
button_start_y = 400

step_x = 50  # 步数框的x坐标
step_y = 500  # 步数框的y坐标
step_size = 50  # 步数框的大小

org_x = 870  # 原图片的x坐标
org_y = 430  # 原图片的y坐标

screen_width = (cell_size + margin) * Shape + margin + left_screen_size + right_screen_size  # 界面宽度
screen_height = (cell_size + margin) * Shape + margin  # 界面高度

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
stop_hand_key = threading.Event()


def hand_key():
    while not stop_hand_key.is_set():
        cam.hand_gesture_control()

    cv2.destroyAllWindows()


stop_hand_click = threading.Event()


def hand_click():
    while not stop_hand_click.is_set():
        hand()

    cv2.destroyAllWindows()


def tuple_add(t1, t2):
    # 定义元组相加
    return (t1[0] + t2[0], t1[1] + t2[1])


class Logic:
    # 定义游戏规则
    def __init__(self, shape=3):
        self.board = []
        # 初始序列
        self.final_list = []
        # 最终序列
        self.before_auto_move = []
        # 字母ascii码
        self.shape = int(shape)
        # 类型 3*3
        self.operations = []
        self.tiles = OrderedDict()
        self.neighbors = [
            [1, 0],  # 右
            [-1, 0],  # 左
            [0, 1],  # 上
            [0, -1],  # 下
        ]
        # 方向列表
        self.click_dict = {'x': {}, 'y': {}}
        # 点击坐标字典
        self.step = 0
        # 记录步数
        self.init_load()
        self.selected_img = random.randint(2, 5)

    def get_final_board(self):
        # 获取最终序列
        count = 45
        final_list = []
        for i in self.board:
            count -= i
        for i in range(1, 10):
            final_list.append(i)
        final_list[count - 1] = 0
        return final_list

    def init_load(self):
        self.board = random_first_list()
        self.final_list = self.get_final_board()
        self.step = 0
        count = 0
        for x in range(self.shape):
            for y in range(self.shape):
                # 标记现在是哪个块
                mark = tuple([x, y])
                self.tiles[mark] = self.board[count]
                # 图片编号
                count += 1
        self.init_click_dict()

    def init_click_dict(self):
        # 初始化点击坐标转换下标的数据
        for row in range(self.shape):
            for column in range(self.shape):
                x = margin * (column + 1) + column * cell_size + 80
                x1 = x + cell_size
                click_x = tuple(range(x, x1))
                self.click_dict['x'][click_x] = column
                y = margin * (row + 1) + row * cell_size
                y1 = y + cell_size
                click_y = tuple(range(y, y1))
                self.click_dict['y'][click_y] = row

    def move(self, mark):
        # 移动数据
        for neighbor in self.neighbors:
            # spot等于移动目标向四个方向移动后的坐标
            spot = tuple_add(mark, neighbor)
            if spot in self.tiles and self.tiles[spot] == 0:
                # 如果移动后在范围内，并且移动后的点数字为0，则交换数据
                self.tiles[spot], self.tiles[mark] = self.tiles[mark], self.tiles[spot]
                self.operations.append(neighbor)
                self.step += 1
                break

    def click_to_move(self, x, y):
        x1 = None
        for k, v in self.click_dict['x'].items():
            if x in k:
                # 如果点击的x在九宫格范围内，则给x1附现在处于哪个行
                x1 = v
        if x1 is None:
            return

        y1 = None
        for k, v in self.click_dict['y'].items():
            if y in k:
                # 如果点击的y在九宫格范围内，则给y1附现在处于哪个列
                y1 = v
        if y1 is None:
            return
        self.move((y1, x1))

    def key_move(self, direction):
        i = list(self.tiles.values()).index(0)
        mark = list(self.tiles.keys())[i]
        (x, y) = tuple_add(mark, direction)
        if (x, y) not in self.tiles.keys():
            return
        self.move((x, y))

    def is_win(self):
        if list(self.tiles.values()) == self.final_list:
            return True
        else:
            return False


def has_answer(board):
    count = 0
    for i in range(len(board)):
        if board[i] == 0:
            continue
        for j in range(i + 1, len(board)):
            if board[j] == 0:
                continue
            if board[i] > board[j]:
                count = count + 1
    if (count % 2 == 1):
        return 0
    return 1


def random_first_list():
    list = [i for i in range(1, 10)]
    x = random.randint(0, 8)
    list[x] = 0
    random.shuffle(list)
    while (not has_answer(list)):
        random.shuffle(list)
    return list


def goBackDistance(num):
    dist = 0
    row = 0
    col = 0
    for i in range(len(num)):
        if num[i] == 0:
            continue
        else:
            row = abs((num[i] - 1) // 3 - i // 3)  # 竖直距离之差
            col = abs((num[i] - 1) % 3 - i % 3)  # 水平距离之差
            dist = dist + row + col  # 当前位置到最终位置之差

    return dist


def search(board, final):
    operation = []
    begin = tuple(board)

    Queue = PriorityQueue()
    Queue.put([goBackDistance(begin), begin, begin.index(0), 0, operation])
    vis = {begin}

    while Queue.not_empty:
        prioritynum, board, pos, steps, operation = Queue.get()

        if board == final:
            for i in range(len(operation)):
                if operation[i] == -1:
                    operation[i] = 'a'
                elif operation[i] == 1:
                    operation[i] = 'd'
                elif operation[i] == 3:
                    operation[i] = 's'
                elif operation[i] == -3:
                    operation[i] = 'w'

            return operation

        pos = board.index(0)
        for i in (-1, 1, -3, 3):
            pos0 = pos + i
            row = abs(pos0 // 3 - pos // 3)  # 竖直距离之差
            col = abs(pos0 % 3 - pos % 3)  # 水平距离之差

            if row + col != 1:
                continue
            if pos0 < 0:
                continue
            if pos0 > 8:
                continue

            newboard = list(board)
            newboard[pos0], newboard[pos] = newboard[pos], newboard[pos0]
            visboard = tuple(newboard)
            if visboard not in vis:
                vis.add(visboard)
                tup1 = operation
                tup2 = [i]
                tup1 = tup1 + tup2
                Queue.put([steps + 1 + goBackDistance(newboard), newboard, pos0, steps + 1, tup1])


def next_step(logic):
    if logic.final_list == list(logic.tiles.values()):
        return
    operations = search(list(logic.tiles.values()), logic.final_list)
    if operations[0] == 'w':
        logic.key_move((-1, 0))
    elif operations[0] == 's':
        logic.key_move((1, 0))
    elif operations[0] == 'd':
        logic.key_move((0, 1))
    elif operations[0] == 'a':
        logic.key_move((0, -1))


def last_step(logic):
    if logic.step == 0:
        return
    i = list(logic.tiles.values()).index(0)
    x, y = list(logic.tiles.keys())[i]
    x1, y1 = tuple_add((x, y), logic.operations[-1])
    logic.tiles[(x, y)], logic.tiles[(x1, y1)] = logic.tiles[(x1, y1)], logic.tiles[(x, y)]
    del logic.operations[-1]
    logic.step -= 1


# 初始化
def init_game():
    pygame.init()
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("欢迎来玩图片华容道")
    return screen


def load_img(logic, screen, path_org, path_icon):
    # path_org是原图分块所在路径
    # path_reset是按钮图片所在的路径
    surface = pygame.image.load(r'./img/beijing2.png')
    screen.blit(surface, (0, 0))

    selected_img = logic.selected_img

    # 载入九宫格
    for r in range(logic.shape):
        for c in range(logic.shape):
            num = logic.tiles[(r, c)]
            x = margin * (c + 1) + c * cell_size + 80
            y = margin * (r + 1) + r * cell_size
            if num == 0:
                img = pygame.image.load(r'./pic/0.jpg')
            else:
                img = pygame.image.load(path_org + r'/%s_%d.jpg' % (selected_img, num))
            screen.blit(img, (x, y))

    # img_org = pygame.image.load(r'.\picc\%s.jpg'%logic.c)
    img_org = pygame.image.load(r'./picc/%s.jpg' % selected_img)
    # 载入原图
    screen.blit(img_org, (org_x, org_y))
    reset_button = pygame.image.load(path_icon + r'/restart.png')
    # 载入按钮
    screen.blit(reset_button, (button1_x, button1_y))
    ret_button = pygame.image.load(path_icon + r'/start2.png')

    screen.blit(ret_button, (button3_x, button3_y))
    right_button = pygame.image.load(path_icon + r'/right.png')

    screen.blit(right_button, (button4_x, button4_y))
    left_button = pygame.image.load(path_icon + r'/left.png')

    screen.blit(left_button, (button5_x, button5_y))
    start_button = pygame.image.load(path_icon + r'/start.png')

    screen.blit(start_button, (button2_x, button2_y))


def press(is_game_over, logic, screen, clock, count, counts):
    # 监控事件
    # is_game_over为判定是否结束游戏
    # count为自定义计时事件
    # counts为从哪开始计时
    for event in pygame.event.get():
        if event.type == count and not is_game_over:
            # 计时事件
            counts += 1
            pygame.display.set_caption('图片华容道--{}s-----{}step'.format(counts, logic.step))

        if event.type == pygame.QUIT:
            stop_hand_key.set()
            gesture_thread.join()
            # 退出事件
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONUP:
            # 松开鼠标事件
            if event.button == 1 and not is_game_over:
                x, y = event.pos
                # x,y为鼠标松开时的点的坐标
                if button1_x < x < button1_x + button_size and button1_y < y < button1_y + button_size:
                    # 如果此时处于重置按钮位置，则重置
                    logic.init_load()
                    return 0
                elif button2_x < x < button2_x + button_size and button2_y < y < button2_y + button_size:
                    # auto_move(logic,screen,clock=clock
                    gesture_thread = threading.Thread(target=hand_key)
                    gesture_thread.start()
                    if cv2.waitKey(1) == ord('q'):
                        stop_hand_key.set()
                        gesture_thread.join()



                elif button3_x < x < button3_x + button_size and button3_y < y < button3_y + button_size:
                    gesture_thread = threading.Thread(target=hand_click)
                    gesture_thread.start()
                    if cv2.waitKey(1) == ord('q'):
                        stop_hand_click.set()
                        gesture_thread.join()

                elif button4_x < x < button4_x + button_size and button4_y < y < button4_y + button_size:
                    last_step(logic)

                elif button5_x < x < button5_x + button_size and button5_y < y < button5_x + button_size:
                    next_step(logic)
                else:
                    # 否则调用点击移动函数
                    logic.click_to_move(int(x), int(y))

        if event.type == pygame.KEYUP:
            # 松开键盘事件
            # wasd和上下左右分别对应上下左右移动
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                direction = (-1, 0)
                logic.key_move(direction=direction)
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                direction = (0, -1)
                logic.key_move(direction=direction)
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                direction = (1, 0)
                logic.key_move(direction=direction)
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                direction = (0, 1)
                logic.key_move(direction=direction)
            elif event.key == 13:
                # 如果按下为enter键，则重新开始
                return True
    if count:
        return counts


def game_start_surface(screen, logic, clock):
    while True:
        img_surface = pygame.image.load(r'./img/beijing2.png')
        screen.blit(img_surface, (0, 0))
        img_title = pygame.image.load(r'./img/图片华容道1.png')
        screen.blit(img_title, (0, 0))
        img = pygame.image.load(r'./img/开始游戏.png')
        screen.blit(img, (0, 0))
        img_tips = pygame.image.load(r'./img/1.jpg')
        screen.blit(img_tips,(300,0))
        pygame.display.update()
        # 更新画布
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                x, y = event.pos
                if button_start_x < x < button_start_x + button_start_size and button_start_y < y < button_start_y + button_start_size / 4:
                    return
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()


if __name__ == '__main__':
    while True:
        print("""游戏规则：
            1.点击开始游戏，进入游戏
            2.点击按钮▶️或按钮⭕，开启手势控制
            3.点击右旋按钮，重新开始本局游戏
            4.左手，中指无名指小指合上，鼠标不再动；
              食指和大拇指缩小一厘米处，鼠标单机且不松开，可以拖拽；
              食指和大拇指完全合并，双击
            5.点击向左按钮返回上一步
            6.点击向右按钮自动点击一步
            7.按下wasd和上下左右分别对应上下左右移动
            8.按下enter键重新开始
        """)
        screen = init_game()
        clock = pygame.time.Clock()
        # 创建一个对象来跟踪时间（可以控制游戏循环频率）
        logic = Logic(Shape)
        # 创建游戏规则
        count = pygame.USEREVENT + 1
        # count为人为设定的用户事件
        pygame.time.set_timer(count, 1000)
        seconds = 0
        game_start_surface(screen, logic, clock)

        while True:
            seconds = press(False, logic, screen, clock, count, seconds)
            # 初始化计时数据，监控程序
            load_img(logic, screen, path_org=r"./pic", path_icon=r"./icon")
            # 加载图片
            pygame.display.update()
            # 更新画布
            clock.tick(FPS)
