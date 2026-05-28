import logging
import cv2
import mediapipe as mp
import numpy as np
import time
import subprocess
import os
import pyautogui

# ---------------------- Configuration ----------------------
WALL_W = 1000
WALL_H = 600
SCREEN_W, SCREEN_H = pyautogui.size()
STARTUP_COUNTDOWN = 5
HOLD_TIME = 3.0
DEBOUNCE_TIME = 0.5
SLIDE_DELAY = 3.0
PPT_FILE = "the empact of media on young people.pptx"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# ---------------------- Main Class ----------------------
class PresentationWall:
    def __init__(self, cam_index=0):
        # MediaPipe Hand Detection
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )

        # Camera
        self.cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Camera", 640, 360)
        cv2.namedWindow("Wall", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Wall", WALL_W, WALL_H)

        self.reset_state()

        # مناطق اللمس
        self.left_area = (0, 0, WALL_W//2, WALL_H)
        self.right_area = (WALL_W//2, 0, WALL_W, WALL_H)
        self.exit_area = (0, 0, 80, 80)

    def reset_state(self):
        self.mode = "startup"
        self.corner_index = 0
        self.corner_points = []
        self.M = None
        self.perspective_ready = False
        self.holding_start = None
        self.smooth_x = None
        self.smooth_y = None
        self.start_time = time.time()
        self.last_touch_time = 0
        self.last_slide_time = 0
        self.system_started = False

    def run(self):
        ppt_process = None
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            #frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            wall = np.zeros((WALL_H, WALL_W, 3), dtype=np.uint8)

            # --- Startup countdown ---
            if self.mode == "startup":
                remaining = int(STARTUP_COUNTDOWN - (time.time() - self.start_time))
                cv2.putText(wall, f"Calibration starts in {remaining}s", (250, WALL_H//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 3)
                if remaining <= 0:
                    self.mode = "corners"

            # --- Calibration targets ---
            if self.mode == "corners":
                targets = [(50,50), (WALL_W-50,50), (WALL_W-50,WALL_H-50), (50,WALL_H-50)]
                for i, t in enumerate(targets):
                    color = (0,255,0) if i == self.corner_index else (100,100,100)
                    cv2.circle(wall, t, 30, color, 3)
                cv2.putText(wall, "Touch and HOLD the green circle", (200,40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

            # --- Hand detection ---
            if results.multi_hand_landmarks:
                for hand in results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(frame, hand, self.mp_hands.HAND_CONNECTIONS)
                    index = hand.landmark[8]
                    cam_x = int(index.x * frame.shape[1])
                    cam_y = int(index.y * frame.shape[0])
                    x, y = self.map_point(cam_x, cam_y)
                    cv2.circle(wall, (x,y), 15, (255,0,0), -1)

                    if self.mode in ["corners"]:
                        self.handle_calibration(x, y, cam_x, cam_y)

                    if self.system_started:
                        ppt_process = self.handle_touch_areas(x, y, ppt_process)

            # --- Draw exit area ---
            cv2.rectangle(wall, (self.exit_area[0], self.exit_area[1]), (self.exit_area[2], self.exit_area[3]), (0,0,255),2)
            cv2.putText(wall, "Exit", (10,40), cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,255,0),2)

            cv2.putText(frame, f"Mode: {self.mode}", (10, frame.shape[0]-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255),1)

            cv2.imshow("Camera", frame)
            cv2.imshow("Wall", wall)

            key = cv2.waitKey(1) & 0xFF
            # ESC → Exit
            if key == 27:
                break
            # X → Exit
            if cv2.getWindowProperty("Wall", cv2.WND_PROP_VISIBLE) < 1:
                break

        if ppt_process:
            ppt_process.terminate()
        self.cleanup()

    # --- Mapping ---
    def map_point(self, cam_x, cam_y):
        if self.perspective_ready and self.M is not None:
            pts = np.array([[[cam_x, cam_y]]], dtype=np.float32)
            t = cv2.perspectiveTransform(pts, self.M)
            x = int(t[0][0][0])
            y = int(t[0][0][1])
        else:
            x = int(cam_x / 1280 * WALL_W)
            y = int(cam_y / 720 * WALL_H)
        if self.smooth_x is None:
            self.smooth_x, self.smooth_y = x, y
        else:
            self.smooth_x = int(0.25*x + 0.75*self.smooth_x)
            self.smooth_y = int(0.25*y + 0.75*self.smooth_y)
        return self.smooth_x, self.smooth_y

    # --- Calibration ---
    def handle_calibration(self, x, y, cam_x, cam_y):
        targets = [(50,50),(WALL_W-50,50),(WALL_W-50,WALL_H-50),(50,WALL_H-50)]
        if self.corner_index >= len(targets):
            return
        tx, ty = targets[self.corner_index]
        dist = np.hypot(x-tx, y-ty)
        if dist < 40:
            if self.holding_start is None:
                self.holding_start = time.time()
            if time.time() - self.holding_start >= HOLD_TIME:
                self.corner_points.append([cam_x, cam_y])
                self.corner_index += 1
                self.holding_start = None
                logging.info(f"Corner {self.corner_index} captured")
                time.sleep(0.5)
        else:
            self.holding_start = None
        if self.corner_index == 4 and not self.perspective_ready:
            src = np.array(self.corner_points, dtype=np.float32)
            dst = np.array([[0,0],[WALL_W,0],[WALL_W,WALL_H],[0,WALL_H]], dtype=np.float32)
            self.M = cv2.getPerspectiveTransform(src, dst)
            self.perspective_ready = True
            self.system_started = True
            logging.info("Calibration complete")

    # --- PPT Handling ---
    def open_ppt(self):
        if os.path.exists(PPT_FILE):
            return subprocess.Popen([PPT_FILE], shell=True)
        logging.error("PPT file not found!")
        return None

    # --- Touch Areas ---
    def handle_touch_areas(self, x, y, ppt_process):
        now = time.time()
        
        # Exit area
        if self.exit_area[0] <= x <= self.exit_area[2] and self.exit_area[1] <= y <= self.exit_area[3]:
            logging.info("Exit pressed")
            if ppt_process:
                ppt_process.terminate()
            self.cleanup()
            exit(0)
        
        # تحقق من التأخير بين ضغطات السلايدات
        if now - self.last_slide_time < SLIDE_DELAY:
            return ppt_process  # لا نفعل أي شيء إذا لم يمر 3 ثواني
        
        # Left area → Previous
        if self.left_area[0] <= x <= self.left_area[2]:
            logging.info("Prev pressed")
            if ppt_process:
                pyautogui.press('left')
                self.last_slide_time = now  # تحديث الوقت بعد الضغط
            else:
                ppt_process = self.open_ppt()
                time.sleep(1)  # انتظر الملف ليتم فتحه
        
        # Right area → Next
        elif self.right_area[0] <= x <= self.right_area[2]:
            logging.info("Next pressed")
            if ppt_process:
                pyautogui.press('right')
                self.last_slide_time = now  # تحديث الوقت بعد الضغط
            else:
                ppt_process = self.open_ppt()
                time.sleep(1)  # انتظر الملف ليتم فتحه
        
        return ppt_process
    def cleanup(self):
        self.cap.release()
        cv2.destroyAllWindows()

# ---------------------- Run ----------------------
if __name__=="__main__":
    wall = PresentationWall()
    try:
        wall.run()
    except KeyboardInterrupt:
        logging.info("Interrupted by user")
        wall.cleanup()