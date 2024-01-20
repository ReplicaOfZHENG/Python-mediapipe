import numpy as np
import math
import cv2
import pyautogui
import mediapipe as mp


def hand_gesture_control():
    screen_width, screen_height = pyautogui.size()

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False,
                           max_num_hands=1,
                           min_detection_confidence=0.5,
                           min_tracking_confidence=0.5
                           )

    camera = cv2.VideoCapture(0)

    if camera is None or not camera.isOpened():
        print("无法打开摄像头")
        exit()

    while camera.isOpened():
        success, image = camera.read()

        if not success:
            print("无法从摄像头读取图像")
            break

        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(img)

        array_landmarks = np.zeros((21, 2))

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                for id, lm in enumerate(hand_landmarks.landmark):
                    h, w, c = image.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    array_landmarks[id, 0] = cx
                    array_landmarks[id, 1] = cy
                    cv2.circle(image, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

            angle = 45
            finger_id = identify_which_finger_point(image, array_landmarks)

            if finger_id == 1:
                angle = calculate_angle(0, 0, 100, 0, array_landmarks[8, 0], array_landmarks[8, 1],
                                        array_landmarks[7, 0], array_landmarks[7, 1])
                if 40 > angle > -40:
                    pyautogui.press('right')
                elif 50 < angle < 130:
                    pyautogui.press('up')
                elif 140 < angle or angle < -140:
                    pyautogui.press('left')
                elif -130 < angle < -50:
                    pyautogui.press('down')

            elif finger_id == 0:
                angle = calculate_angle(0, 0, 100, 0, array_landmarks[4, 0], array_landmarks[4, 1],
                                        array_landmarks[3, 0], array_landmarks[3, 1])
                if 40 > angle > -40:
                    pyautogui.press('right')
                elif 50 < angle < 130:
                    pyautogui.press('up')
                elif 140 < angle or angle < -140:
                    pyautogui.press('left')
                elif -130 < angle < -50:
                    pyautogui.press('down')

        image = cv2.flip(image, 1)
        cv2.imshow("Hand Gestures", image)

        if cv2.waitKey(1) == ord('q'):
            break

    cv2.waitKey(1)


screen_width, screen_height = pyautogui.size()
running = True


def identify_which_finger_point(image, array_landmarks):
    center_x = 0
    center_y = 0
    for i in range(21):
        center_x += array_landmarks[i, 0]
        center_y += array_landmarks[i, 1]
    center_x = int(center_x / 21)
    center_y = int(center_y / 21)
    cv2.circle(image, (center_x, center_y), 5, (0, 255, 255), cv2.FILLED)

    # 伸出手指的索引，0->大拇指, 1->食指, 2->中指, 3->无名指, 4->小拇指, 5->没有伸出手指
    point_id = 0
    # 节点与中心点的最大距离值
    dis_from_center_max = 0
    dis_from_center = 0
    # 判断各个关键节点到中心点的距离
    for i in range(1, 21):
        dis_from_center = abs(array_landmarks[i, 0] - center_x) + abs(array_landmarks[i, 1] - center_y)
        if dis_from_center > dis_from_center_max:
            dis_from_center_max = dis_from_center
            if i == 4:
                point_id = 0
            elif i == 8:
                point_id = 1
            elif i == 12:
                point_id = 2
            elif i == 16:
                point_id = 3
            elif i == 20:
                point_id = 4
            else:
                point_id = 5
    return point_id


def calculate_angle(x1, y1, x2, y2, x3, y3, x4, y4):
    dx1 = x2 - x1
    dy1 = y2 - y1

    dx2 = x4 - x3
    dy2 = y4 - y3

    dot_product = dx1 * dx2 + dy1 * dy2

    magnitude1 = math.sqrt(dx1 ** 2 + dy1 ** 2)
    magnitude2 = math.sqrt(dx2 ** 2 + dy2 ** 2)

    cosine = dot_product / (magnitude1 * magnitude2)

    angle = math.degrees(math.acos(cosine))

    cross_product = dx1 * dy2 - dx2 * dy1

    if cross_product < 0:
        angle = -angle

    return angle


# 判断鼠标位置是否靠近屏幕边缘
def is_safe(move_x, move_y):
    lx, ly = pyautogui.position()
    aim_x = lx + move_x
    aim_y = ly + move_y
    if 0 < aim_x < screen_width and 0 < aim_y < screen_height:
        return 1
    else:
        return 0
