from flask import Flask, render_template, Response, jsonify, request, redirect, url_for
from icg_camera import IcgCamera
import uuid  # 确保导入 uuid 模块

app = Flask(__name__)

# 创建一个全局的 IcgCamera 对象用于视频流
icg_camera = IcgCamera()
clients = {}  # 字典用于存储客户端 ID

def add_or_get_client(client_id):
    """添加新的客户端或获取现有的客户端信息"""
    if client_id not in clients:
        clients[client_id] = {'timestamp': 0}
    return client_id

@app.route('/')
def index():
    client_id = request.args.get('client_id')
    if not client_id:
        client_id = str(uuid.uuid4())  # 如果没有提供 UUID，则生成一个新的
        clients[client_id] = {'timestamp': 0}  # 初始化客户端信息
        return redirect(url_for('index', client_id=client_id))  # 重定向并附加新生成的 UUID
    add_or_get_client(client_id)
    return render_template('index.html', client_id=client_id)

@app.route('/camera_list')
def camera_list():
    client_id = request.args.get('client_id')
    if not client_id:
        return redirect(url_for('index'))  # 没有 UUID 则重定向到首页以获取 UUID
    add_or_get_client(client_id)
    return render_template('camera_list.html', client_id=client_id)

@app.route('/get_camera_list')
def get_camera_list():
    cameras = icg_camera.detect_camdev()
    return jsonify({"cameras": cameras})

@app.route('/get_camera_properties')
def get_camera_properties():
    camera_id = request.args.get('camera_id', 0, type=int)
    camera_obj = IcgCamera(camera_index=camera_id)
    properties = camera_obj.get_all_properties()
    camera_obj.release()
    return jsonify(properties)

@app.route('/video_feed')
def video_feed():
    client_id = request.args.get('client_id')  # 获取客户端 ID
    if client_id not in clients:
        return "Client ID not recognized", 400
    response = Response(icg_camera.generate_video_stream(client_id), mimetype='multipart/x-mixed-replace; boundary=frame')
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/get_cache_status')
def get_cache_status():
    client_id = request.args.get('client_id')
    if not client_id or client_id not in icg_camera.client_states:
        return jsonify({"error": "Client ID not recognized"}), 400
    return jsonify(icg_camera.get_cache_status(client_id))

@app.route('/get_frame_rate')
def get_frame_rate():
    client_id = request.args.get('client_id')
    if not client_id or client_id not in icg_camera.client_states:
        return jsonify({"error": "Client ID not recognized"}), 400
    return jsonify(icg_camera.get_frame_rate(client_id))


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        icg_camera.release()
