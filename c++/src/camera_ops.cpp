// src/camera_ops.cpp
#include "camera_ops.h"

// 构造函数
CameraOps::CameraOps() : camera(0) {}

// 打开摄像头
bool CameraOps::open() {
    if (!camera.isOpened()) {
        std::cerr << "Error: Cannot open camera." << std::endl;
        return false;
    }
    return true;
}

// 关闭摄像头
void CameraOps::close() {
    if (camera.isOpened()) {
        camera.release();
    }
}

// 获取帧
bool CameraOps::get_frame(cv::Mat& frame) {
    if (camera.isOpened()) {
        camera >> frame;
        return !frame.empty();
    }
    return false;
}
