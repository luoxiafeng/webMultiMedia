from flask import Flask, render_template, Response, jsonify, request
from icg_camera import IcgCamera
import uuid  # 确保导入 uuid 模块

app = Flask(__name__)

# 创建一个全局的 IcgCamera 对象用于视频流
icg_camera = IcgCamera()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/camera_list')
def camera_list():
    return render_template('camera_list.html')

@app.route('/get_camera_list')
def get_camera_list():
    # 使用 IcgCamera 的 detect_camdev 方法获取摄像头列表
    cameras = icg_camera.detect_camdev()
    return jsonify({"cameras": cameras})

@app.route('/get_camera_properties')
def get_camera_properties():
    camera_id = request.args.get('camera_id', 0, type=int)
    camera_obj = IcgCamera(camera_index=camera_id)
    properties = camera_obj.get_all_properties()
    camera_obj.release()  # 释放摄像头资源
    return jsonify(properties)

@app.route('/video_feed')
def video_feed():
    # 为每个请求生成一个唯一的 client_id
    client_id = str(uuid.uuid4())  # 使用 UUID 生成唯一的 client_id
    # 调用 generate_video_stream 并传递 client_id
    response = Response(icg_camera.generate_video_stream(client_id), mimetype='multipart/x-mixed-replace; boundary=frame')
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"  # 避免缓存
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        icg_camera.release()  # 确保在程序结束时释放摄像头资源
