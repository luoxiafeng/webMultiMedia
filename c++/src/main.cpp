// src/main.cpp
#include "camera_ops.h"
#include <boost/asio/ip/tcp.hpp>
#include <iostream>
#include <thread>
#include "server.cpp"

using namespace std;
using tcp = boost::asio::ip::tcp;

extern CameraOps cameraOps; // 声明外部摄像头对象

int main() {
    // 打开摄像头
    if (!cameraOps.open()) {
        return 1;
    }

    // I/O 上下文
    boost::asio::io_context ioc{1};

    // 监听端口
    tcp::acceptor acceptor{ioc, {tcp::v4(), 8080}};
    std::cout << "Server started on http://localhost:8080\n";

    for (;;) {
        // 等待并接受连接
        tcp::socket socket{ioc};
        acceptor.accept(socket);

        // 处理连接会话
        std::thread{std::bind(&do_session, std::move(socket))}.detach();
    }

    // 关闭摄像头
    cameraOps.close();

    return 0;
}
