import cv2
import pynput
import mediapipe as mp


class HandDetector():
    def __init__(self):
        self.hand_detector = mp.solutions.hands.Hands(static_image_mode=False,
                                                      max_num_hands=2,
                                                      min_detection_confidence=0.8,
                                                      min_tracking_confidence=0.8
                                                      )
        self.drawer = mp.solutions.drawing_utils
        self.prev_positions = {'Left': {}, 'Right': {}}
        self.smoothing_factor = 0.5

    def process(self, img):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.hands_data = self.hand_detector.process(img_rgb)
        if self.hands_data.multi_hand_landmarks:
            for handlms in self.hands_data.multi_hand_landmarks:
                self.drawer.draw_landmarks(img, handlms, mp.solutions.hands.HAND_CONNECTIONS)

    def find_position(self, img):
        h, w, c = img.shape
        self.position = {'Left': {}, 'Right': {}}
        if self.hands_data.multi_hand_landmarks:
            i = 0;
            for point in self.hands_data.multi_handedness:
                score = point.classification[0].score
                if score >= 0.8:
                    label = point.classification[0].label
                    hand_lms = self.hands_data.multi_hand_landmarks[i].landmark
                    for id, lm in enumerate(hand_lms):
                        x, y = int(lm.x * w), int(lm.y * h)
                        # 应用平滑化
                        smoothed_x = self.smooth_coordinate(x, label, id, 'x')
                        smoothed_y = self.smooth_coordinate(y, label, id, 'y')

                        self.position[label][id] = (smoothed_x, smoothed_y)

                i = i + 1
        return self.position

    def smooth_coordinate(self, new_value, hand, landmark_id, axis):
        # 应用指数移动平均
        if axis == 'x':
            prev_value = self.prev_positions[hand].get((landmark_id, 'x'), new_value)
        elif axis == 'y':
            prev_value = self.prev_positions[hand].get((landmark_id, 'y'), new_value)

        smoothed_value = self.smoothing_factor * prev_value + (1 - self.smoothing_factor) * new_value

        # 更新前一个位置
        self.prev_positions[hand][(landmark_id, axis)] = smoothed_value

        return int(smoothed_value)


def hand():
    ctr = pynput.mouse.Controller()
    camera = cv2.VideoCapture(0)
    camera.set(3, 7000)
    camera.set(4, 7000)
    hand_detector = HandDetector()
    flag = 1
    num = 0
    scaling_factor = 3
    while True:
        success, image = camera.read()
        if success:
            # img = cv2.flip(image, 1)
            # img = cv2.resize(image, (500, 500))
            img = cv2.flip(image, 1)  # 屏幕反转
            hand_detector.process(img)
            position = hand_detector.find_position(img)

            # 左手，中指无名指小指合上，鼠标不再动，食指和大拇指缩小一厘米处，鼠标单机且不松开，可以拖拽，食指和大拇指完全合并，双击
            hand_L = 'Left'
            tips = [4, 8, 12, 16, 20]
            tip_data = {4: 0, 8: 0, 12: 0, 16: 0, 20: 0}

            for tip in tips:
                ltp1 = position[hand_L].get(tip, None)  # 左手显示关节坐标
                ltp2 = position[hand_L].get(tip - 2, None)
                ltp_8 = position[hand_L].get(8, None)
                ltp_4 = position[hand_L].get(4, None)
                ltp_0 = position[hand_L].get(0, None)

                if ltp1 and ltp2:

                    cv2.circle(img, (ltp_8[0], ltp_8[1]), 7, (0, 255, 255), cv2.FILLED)  # 食指
                    # cv2.circle(img, (ltp_12[0], ltp_12[1]), 7, (0, 255, 255), cv2.FILLED)  # 中指
                    cv2.line(img, (ltp_8[0], ltp_8[1]), (ltp_4[0], ltp_4[1]), (255, 255, 255), 3)  # 食指中指之间的线

                    t_1 = int((ltp_4[0] + ltp_8[0]) / 2)
                    t_2 = int((ltp_4[1] + ltp_8[1]) / 2)
                    cv2.circle(img, (t_1, t_2), 7, (255, 0, 255), cv2.FILLED)  # 食指和中指中间的点

                    print(ltp_4[1] - ltp_8[1])
                    if (flag == 1) and (ltp_4[1] - ltp_8[1]) <= 20:
                        ctr.click(pynput.mouse.Button.left, 2)
                        flag = 0
                    if (flag == 1) and (ltp_4[1] - ltp_8[1]) <= 50 and (ltp_4[1] - ltp_8[1]) >= 30:
                        # pyautogui.click()
                        ctr.press(pynput.mouse.Button.left)
                        flag = 0

                    if (flag == 0) and (ltp_4[1] - ltp_8[1]) > 50:
                        ctr.release(pynput.mouse.Button.left)
                        flag = 1
                    cv2.circle(img, (ltp1[0], ltp1[1]), 7, (255, 255, 0), cv2.FILLED)
                    cv2.circle(img, (ltp2[0], ltp2[1]), 5, (255, 0, 0), cv2.FILLED)
                    if tip == 4:
                        if ltp1[0] > ltp2[0]:
                            tip_data[tip] = 1
                        else:
                            tip_data[tip] = 0
                    else:
                        if ltp1[1] > ltp2[1]:
                            tip_data[tip] = 0
                        else:
                            tip_data[tip] = 1
                    if int(list(tip_data.values()).count(1)) > 2:
                        ctr.position = ((ltp_0[0] - 300) * 3, (ltp_0[1] - 400) * 3)

            # 右手
            hand_R = 'Right'
            tips = [4, 8, 12, 16, 20]
            tip_data = {4: 0, 8: 0, 12: 0, 16: 0, 20: 0}
            for tip in tips:
                ltp1 = position[hand_R].get(tip, None)  # 右手显示关节坐标
                ltp2 = position[hand_R].get(tip - 2, None)
                ltp_8 = position[hand_R].get(8, None)
                ltp_4 = position[hand_R].get(4, None)
                ltp_0 = position[hand_R].get(0, None)

                if ltp1 and ltp2:
                    cv2.circle(img, (ltp_8[0], ltp_8[1]), 7, (0, 255, 255), cv2.FILLED)  # 食指
                    # cv2.circle(img, (ltp_12[0], ltp_12[1]), 7, (0, 255, 255), cv2.FILLED)  # 中指
                    cv2.line(img, (ltp_8[0], ltp_8[1]), (ltp_4[0], ltp_4[1]), (255, 255, 255), 3)  # 食指中指之间的线

                    t_1 = int((ltp_4[0] + ltp_8[0]) / 2)
                    t_2 = int((ltp_4[1] + ltp_8[1]) / 2)
                    cv2.circle(img, (t_1, t_2), 7, (255, 0, 255), cv2.FILLED)  # 食指和中指中间的点

                    print(ltp_4[1] - ltp_8[1])

                    if (flag == 1) and (ltp_4[1] - ltp_8[1]) <= 20:
                        ctr.click(pynput.mouse.Button.left, 2)
                        flag = 0
                    if (flag == 1) and 50 >= (ltp_4[1] - ltp_8[1]) >= 30:
                        # pyautogui.click()
                        ctr.press(pynput.mouse.Button.left)
                        flag = 0

                    if (flag == 0) and (ltp_4[1] - ltp_8[1]) > 50:
                        ctr.release(pynput.mouse.Button.left)
                        flag = 1
                    cv2.circle(img, (ltp1[0], ltp1[1]), 7, (255, 255, 0), cv2.FILLED)
                    cv2.circle(img, (ltp2[0], ltp2[1]), 5, (255, 0, 0), cv2.FILLED)

                    if tip == 4:
                        if ltp1[0] > ltp2[0]:
                            tip_data[tip] = 1
                        else:
                            tip_data[tip] = 0
                    else:
                        if ltp1[1] > ltp2[1]:
                            tip_data[tip] = 0
                        else:
                            tip_data[tip] = 1
                    if int(list(tip_data.values()).count(1)) > 2:
                        ctr.position = ((ltp_0[0] - 300) * 3, (ltp_0[1] - 400) * 3)
            cv2.imshow('Video', img)
        k = cv2.waitKey(1)
        if k == ord('q') or cv2.waitKey(1) & 0xFF == 27:
            break

    camera.release()
    cv2.destroyAllWindows()
