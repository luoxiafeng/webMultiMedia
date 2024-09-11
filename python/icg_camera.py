import cv2

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
