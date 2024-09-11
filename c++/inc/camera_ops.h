// inc/camera_ops.h
#ifndef CAMERA_OPS_H
#define CAMERA_OPS_H

#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/videoio.hpp>
#include <iostream>

class CameraOps {
public:
    // 构造函数
    CameraOps();

    // 打开摄像头
    bool open();

    // 关闭摄像头
    void close();

    // 获取帧
    bool get_frame(cv::Mat& frame);

private:
    cv::VideoCapture camera; // 摄像头对象
};

#endif // CAMERA_OPS_H
