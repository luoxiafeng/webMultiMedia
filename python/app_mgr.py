# app_mgr.py
from icg_camera import IcgCamera

class AppManager:
    def __init__(self):
        # 初始化全局的 IcgCamera 对象用于视频流
        self.icg_camera = IcgCamera()
        self.client_ids = {}  # 用于管理客户端ID和IP地址
    
    def get_camera(self):
        return self.icg_camera

    def add_or_get_client(self, client_id, ip_address):
        if client_id not in self.client_ids:
            self.client_ids[client_id] = ip_address  # 仅记录 IP 地址
        return client_id

    def release_resources(self):
        # 释放所有资源
        if self.icg_camera:
            self.icg_camera.release()

    def get_client_ip(self, client_id):
        return self.client_ids.get(client_id)
