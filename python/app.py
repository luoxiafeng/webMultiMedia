from flask import Flask, render_template, Response, request
from icg_camera import IcgCamera  # 使用 icg_camera 文件中的 IcgCamera 类
import cv2
import os

app = Flask(__name__)

# 创建 IcgCamera 对象
icg_camera = IcgCamera()

def generate_frames(camera):
    while True:
        # 获取摄像头帧
        frame = camera.get_frame()
        if frame is None:
            break
        else:
            # 使用 yield 生成视频流
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def list_cameras():
    # 使用 OpenCV 查找所有系统中的摄像头
    camera_indices = []

    # 检查常见摄像头设备
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.read()[0]:
            camera_indices.append(f"Camera {i} - /dev/video{i}")  # 包含可能的设备路径
            cap.release()

    # Windows 下通过 dshow 接口查找摄像头
    if os.name == 'nt':  # Windows
        for i in range(10):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.read()[0]:
                camera_indices.append(f"Camera {i}")
                cap.release()

    return camera_indices

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/camera_list')
def camera_list():
    # 获取所有摄像头列表
    cameras = list_cameras()
    return render_template('camera_list.html', cameras=cameras)

@app.route('/camera_details', methods=['GET'])
def camera_details():
    # 获取摄像头参数
    camera_id = request.args.get('camera_id', 0, type=int)
    camera_obj = IcgCamera(camera_index=camera_id)
    properties = camera_obj.get_all_properties()
    camera_obj.release()  # 释放摄像头资源
    return render_template('camera_details.html', properties=properties)

@app.route('/video_feed')
def video_feed():
    # 使用 generate_frames 函数生成视频流
    return Response(generate_frames(icg_camera), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        icg_camera.release()  # 确保在程序结束时释放摄像头资源
