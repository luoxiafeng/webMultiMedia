# app.py
from flask import Flask, render_template, Response, jsonify, request
from app_mgr import AppManager
from icg_camera import IcgCamera
import uuid

app = Flask(__name__)
app_mgr = AppManager()

@app.route('/')
def index():
    client_id = request.args.get('client_id')
    client_ip = request.remote_addr  # 获取客户端 IP 地址
    if not client_id:
        client_id = str(uuid.uuid4())
    client_id = app_mgr.add_or_get_client(client_id, client_ip)  # 记录 client_id 和 IP
    client_ip = app_mgr.get_client_ip(client_id)
    return render_template('index.html', client_id=client_id, client_ip=client_ip)

@app.route('/camera_list')
def camera_list():
    client_id = request.args.get('client_id')
    client_ip = request.remote_addr
    if not client_id:
        client_id = str(uuid.uuid4())
    client_id = app_mgr.add_or_get_client(client_id, client_ip)
    client_ip = app_mgr.get_client_ip(client_id)
    return render_template('camera_list.html', client_id=client_id, client_ip=client_ip)

@app.route('/get_camera_list')
def get_camera_list():
    cameras = IcgCamera.detect_camdev()
    return jsonify({"cameras": cameras})

@app.route('/get_camera_properties')
def get_camera_properties():
    ''' camera_id = request.args.get('camera_id', 0, type=int)
    camera_obj = IcgCamera(camera_index=camera_id)
    properties = camera_obj.get_all_properties()
    camera_obj.release()
    return jsonify(properties) '''

@app.route('/video_feed')
def video_feed():
    client_id = request.args.get('client_id')
    client_ip = request.remote_addr
    if not client_id:
        client_id = str(uuid.uuid4())
    client_id = app_mgr.add_or_get_client(client_id, client_ip)

    icg_camera = app_mgr.get_camera()
    response = Response(icg_camera.generate_video_stream(client_id), mimetype='multipart/x-mixed-replace; boundary=frame')
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/get_cache_status')
def get_cache_status():
    client_id = request.args.get('client_id')
    return jsonify(app_mgr.get_camera().get_cache_status(client_id))

@app.route('/get_frame_rate')
def get_frame_rate():
    client_id = request.args.get('client_id')
    return jsonify(app_mgr.get_camera().get_frame_rate(client_id))

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        app_mgr.release_resources()
