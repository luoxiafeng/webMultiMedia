import cv2
import os
import time
import threading
import platform
import subprocess
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from uuid import uuid4

@dataclass
class Frame:
    id: int
    buffer: bytes
    timestamp: int  # 添加时间戳（毫秒）
    read_count: int = 0
    lock: Lock = field(default_factory=Lock)  # 每个帧有自己的锁

class IcgCamera:
    def __init__(self, max_length=10):  # 缓存大小修改为35
        self.camera = None  # 初始化时不打开摄像头
        self.frame_list = [None] * max_length  # 初始化固定长度的链表
        self.max_length = max_length  # 链表最大长度
        self.insert_index = 0  # 插入索引，控制循环插入
        self.thread = None  # 用于帧插入的线程
        self.running = False  # 线程运行控制标志
        self.client_states = {}  # 字典：客户端ID -> { 'frame_pos': int, 'timestamp': int }

    def start_framebuffer(self):
        # 检查并初始化摄像头
        if self.is_camera_in_use():
            print("Camera is already in use by another process or object, releasing it before re-initializing...")
            self.release()  # 先尝试释放摄像头

        # 尝试重新初始化摄像头
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            raise RuntimeError("Failed to initialize the camera. Please check the camera connection.")

        # 开启帧插入线程
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._insert_frames)
            self.thread.start()

    def is_camera_in_use(self):
        # 尝试打开摄像头以检查是否被占用
        temp_camera = cv2.VideoCapture(0)
        if temp_camera.isOpened():
            temp_camera.release()  # 如果成功打开，说明未被占用
            return False
        else:
            return True  # 如果无法打开，说明可能被占用

    def stop_framebuffer(self):
        # 停止帧插入线程
        if self.running:
            self.running = False
            self.thread.join()
        if self.camera is not None and self.camera.isOpened():
            self.camera.release()  # 确保摄像头被释放

    def _insert_frames(self):
        # 向链表插入新帧，运行于线程中
        frame_id = 0
        while self.running:
            frame = self.get_frame_data()
            if frame is not None:
                timestamp = int(time.time() * 1000)  # 获取当前时间戳（毫秒）
                new_frame = Frame(id=frame_id, buffer=frame, timestamp=timestamp)

                # 获取当前插入位置的节点，如果为空则直接插入，否则加锁后插入
                current_node = self.frame_list[self.insert_index]
                if current_node is not None:
                    with current_node.lock:  # 对当前节点加锁
                        self.frame_list[self.insert_index] = new_frame
                else:
                    self.frame_list[self.insert_index] = new_frame  # 插入新帧

                self.insert_index = (self.insert_index + 1) % self.max_length  # 更新插入索引，实现循环
                frame_id += 1

    def get_frame_data(self):
        # 获取摄像头帧数据
        success, frame = self.camera.read()
        if not success:
            print(f"Failed to get frame.")
            return None
        ret, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()

    def get_frame(self, frame_pos, current_timestamp, client_id):
        # 从指定链表节点的下一个节点获取 frame 数据
        if all(frame is None for frame in self.frame_list):
            print(f"[{client_id}] Frame list is empty.")
            # 检查线程是否已启动，如果未启动则启动线程
            if not self.running:
                print(f"[{client_id}] Frame buffer thread is not running. Starting thread...")
                self.start_framebuffer()  # 启动帧插入线程
            return None, frame_pos  # 返回当前帧位置

        # 计算下一个帧的位置，如果到了链表尾部，则下一个位置就是链表头部
        next_pos = (frame_pos + 1) % self.max_length  
        frame = self.frame_list[next_pos]

        if frame is None or frame.timestamp <= current_timestamp:
            print(f"[{client_id}] Waiting for new frames or outdated frame detected...")
            return None, frame_pos

        # 检查当前节点是否有写锁，如果有则等待
        while frame.lock.locked():
            time.sleep(0.001)  # 等待写锁释放

        # 读取帧数据时加锁
        with frame.lock:
            frame.read_count += 1  # 增加读取计数
            return frame, next_pos

    def release(self):
        # 停止帧插入线程并释放摄像头资源
        self.stop_framebuffer()  # 停止帧插入线程
        if self.camera is not None and self.camera.isOpened():
            self.camera.release()  # 释放摄像头资源

    def reset_camera(self):
        # 复位摄像头
        self.release()
        time.sleep(1)  # 等待摄像头释放
        self.camera = cv2.VideoCapture(0)  # 重新初始化摄像头
        self.start_framebuffer()  # 重新启动帧插入线程

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
    
    @staticmethod
    def detect_camdev():
        # 获取当前操作系统
        system = platform.system().lower()
        camera_indices = []

        if system == 'linux':
            # Linux 系统：通过检查 /dev 目录下的 video 设备
            video_devices = [f for f in os.listdir('/dev') if f.startswith('video')]
            for index, device in enumerate(video_devices):
                camera_indices.append({"name": f"Camera {index} - /dev/{device}", "index": index})

        elif system == 'windows':
            # Windows 系统：通过 DirectShow 枚举摄像头设备
            try:
                # 使用 PowerShell 调用 DirectShow 接口获取设备列表
                result = subprocess.run(
                    ["powershell.exe", 
                     "-Command", 
                     "Get-WmiObject Win32_PnPEntity | Where-Object { $_.Name -match 'Camera|Imaging' } | Select-Object Name"],
                    capture_output=True, text=True, check=True)
                
                devices = result.stdout.splitlines()
                for i, device in enumerate(devices):
                    device_name = device.strip()
                    if device_name:
                        camera_indices.append({"name": f"Camera {i} - {device_name}", "index": i})
            except subprocess.CalledProcessError as e:
                print(f"Error detecting cameras on Windows: {e}")

        else:
            print(f"Unsupported system: {system}")

        return camera_indices

    def generate_video_stream(self, client_id):
        # 使用链表中的帧生成视频流

        # 初始化当前客户端的帧位置为链表头（最早插入的帧）和初始时间戳
        if client_id not in self.client_states:
            self.client_states[client_id] = {'frame_pos': 0, 'timestamp': 0}  # 初始化为链表头，即最早的帧和初始时间戳

        frame_interval = 1 / 30  # 设置帧间隔为 1/30 秒
        last_time = time.time()

        while True:
            current_time = time.time()
            elapsed_time = current_time - last_time

            if elapsed_time < frame_interval:
                time.sleep(frame_interval - elapsed_time)

            last_time = time.time()

            # 获取当前客户端的帧位置和时间戳
            frame_pos = self.client_states[client_id]['frame_pos']
            current_timestamp = self.client_states[client_id]['timestamp']

            # 从链表中获取下一个帧的数据
            frame, frame_pos = self.get_frame(frame_pos, current_timestamp, client_id)
            if frame is None:
                print(f"[{client_id}] Waiting for valid frames...")
                continue

            # 更新客户端的帧位置和时间戳
            self.client_states[client_id]['frame_pos'] = frame_pos
            self.client_states[client_id]['timestamp'] = frame.timestamp

            # 生成视频流
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n'+ frame.buffer + b'\r\n')
            
    
    # 在 IcgCamera 类中修改方法
    def get_cache_status(self, client_id):
        """根据 client_id 获取链表中帧的ID和时间戳"""
        # 获取指定客户端的状态
        client_state = self.client_states.get(client_id, None)
        if not client_state:
            return []
        frame_pos = client_state['frame_pos']
        cache_status = [{"id": frame.id, "timestamp": frame.timestamp} 
                        for frame in self.frame_list if frame is not None]
        return cache_status

    def get_frame_rate(self, client_id):
        """根据 client_id 获取帧率数据"""
        client_state = self.client_states.get(client_id, None)
        if not client_state:
            return []
        # 假设帧率是通过时间戳差异计算得到的
        timestamps = [frame.timestamp for frame in self.frame_list if frame is not None]
        if len(timestamps) < 2:
            return []
        intervals = [t2 - t1 for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
        frame_rates = [1000 / interval for interval in intervals]  # 将时间间隔转换为帧率（帧/秒）
        return frame_rates[-15:]  # 只返回最近的15个数据点

