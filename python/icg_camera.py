import cv2
import os
import time

class IcgCamera:
    def __init__(self, camera_index=0):
        # 初始化摄像头对象
        self.camera = cv2.VideoCapture(camera_index)

    def get_frame(self):
        # 获取摄像头帧
        success, frame = self.camera.read()
        if not success:
            return None
        # 编码为 JPEG 格式
        ret, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()

    def release(self):
        # 释放摄像头资源
        self.camera.release()

    def reset_camera(self):
        # 复位摄像头
        self.release()
        time.sleep(1)  # 稍作等待，确保摄像头释放
        self.camera = cv2.VideoCapture(0)  # 重新初始化摄像头

    def get_all_properties(self):
        # 获取摄像头的所有参数信息属性
        properties = {
            'CAP_PROP_FRAME_WIDTH': self.camera.get(cv2.CAP_PROP_FRAME_WIDTH),
            'CAP_PROP_FRAME_HEIGHT': self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT),
            'CAP_PROP_FPS': self.camera.get(cv2.CAP_PROP_FPS),
            'CAP_PROP_BRIGHTNESS': self.camera.get(cv2.CAP_PROP_BRIGHTNESS),
            'CAP_PROP_CONTRAST': self.camera.get(cv2.CAP_PROP_CONTRAST),
            'CAP_PROP_SATURATION': self.camera.get(cv2.CAP_PROP_SATURATION),
            'CAP_PROP_HUE': self.camera.get(cv2.CAP_PROP_HUE),
            'CAP_PROP_GAIN': self.camera.get(cv2.CAP_PROP_GAIN),
            'CAP_PROP_EXPOSURE': self.camera.get(cv2.CAP_PROP_EXPOSURE),
        }
        return properties

    def detect_camdev(self):
        # 使用 OpenCV 查找所有系统中的摄像头
        camera_indices = []

        # 检查常见摄像头设备
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.read()[0]:
                camera_indices.append({"name": f"Camera {i} - /dev/video{i}", "index": i})
                cap.release()

        # Windows 下通过 dshow 接口查找摄像头
        if os.name == 'nt':  # Windows
            for i in range(10):
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.read()[0]:
                    camera_indices.append({"name": f"Camera {i}", "index": i})
                    cap.release()

        return camera_indices

    def generate_video_stream(self):
        # 生成摄像头的视频流
        timeout = 5  # 设置超时时间为5秒
        no_frame_start_time = None

        while True:
            frame = self.get_frame()
            if frame is None:
                print('No frame received')
                if no_frame_start_time is None:
                    no_frame_start_time = time.time()  # 记录第一次未收到帧的时间

                # 检查超时时间
                elif time.time() - no_frame_start_time > timeout:
                    print('No frame for 5 seconds, resetting camera...')
                    self.reset_camera()  # 超时后重置摄像头
                    no_frame_start_time = None  # 重置计时器
                continue
            else:
                no_frame_start_time = None  # 重置计时器
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
