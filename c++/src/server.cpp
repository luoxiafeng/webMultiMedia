// src/server.cpp
#include "camera_ops.h"
#include <boost/beast/core.hpp>
#include <boost/beast/http.hpp>
#include <boost/beast/version.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/asio/strand.hpp>
#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/videoio.hpp>
#include <filesystem>
#include <iostream>
#include <memory>
#include <string>
#include <thread>
#include <vector>

namespace beast = boost::beast;         
namespace http = beast::http;           
namespace net = boost::asio;            
using tcp = net::ip::tcp;               
using namespace std;
namespace fs = std::filesystem;

// 全局摄像头操作对象
CameraOps cameraOps;

// 从文件系统中读取文件并返回 HTTP 响应
http::response<http::string_body> handle_file_request(const std::string& target) {
    std::string path = "public" + target; // 构建文件路径
    if (target == "/") {
        path = "public/index.html"; // 默认访问 index.html
    }

    if (!fs::exists(path)) {
        // 返回 404 错误
        http::response<http::string_body> res{http::status::not_found, 11};
        res.set(http::field::content_type, "text/html");
        res.body() = "404 - Not Found";
        res.prepare_payload();
        return res;
    }

    // 读取文件内容
    std::ifstream file(path);
    std::stringstream buffer;
    buffer << file.rdbuf();

    // 构造响应
    http::response<http::string_body> res{http::status::ok, 11};
    res.set(http::field::content_type, "text/html");
    res.body() = buffer.str();
    res.prepare_payload();
    return res;
}

// 处理视频流请求
void handle_stream(tcp::socket& socket) {
    beast::flat_buffer buffer;
    while (true) {
        cv::Mat frame;
        if (!cameraOps.get_frame(frame)) break; // 获取帧失败则退出

        // 编码为 JPEG
        std::vector<uchar> buf;
        cv::imencode(".jpg", frame, buf);

        // 构造 HTTP 头
        http::response<http::vector_body<uchar>> res{
            http::status::ok, 11
        };
        res.set(http::field::server, "Boost.Beast");
        res.set(http::field::content_type, "image/jpeg");
        res.body() = std::move(buf);
        res.prepare_payload();

        // 发送响应
        beast::http::write(socket, res);

        // 控制帧率
        cv::waitKey(1);
    }
}

// 会话管理
void do_session(tcp::socket socket) {
    beast::flat_buffer buffer;

    try {
        for (;;) {
            // 读取 HTTP 请求
            http::request<http::string_body> req;
            http::read(socket, buffer, req);

            // 路由请求
            if (req.target() == "/video_feed") {
                // 处理视频流请求
                handle_stream(socket);
            } else {
                // 处理静态文件请求
                auto res = handle_file_request(std::string(req.target()));
                beast::http::write(socket, res);
            }
        }
    } catch (std::exception const& e) {
        std::cerr << "Session error: " << e.what() << "\n";
    }
}
