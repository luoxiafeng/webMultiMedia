# 打印 CONDA_PREFIX 的值
$(info CONDA_PREFIX is $(CONDA_PREFIX))

# 定义编译器 - 使用 Conda 环境中的 g++
CXX = $(CONDA_PREFIX)/Library/mingw-w64/bin/g++

# 定义编译选项 - 添加 OpenCV 头文件路径
CXXFLAGS = -I$(CONDA_PREFIX)/Library/include/opencv2 -I./inc -std=c++17

# 定义链接选项 - 添加 OpenCV 库路径
LDFLAGS = -L$(CONDA_PREFIX)/Library/lib -lopencv_core -lopencv_imgcodecs -lopencv_highgui -lopencv_videoio -lboost_system -lboost_thread -lpthread

# 源文件
SRCS = src/main.cpp src/server.cpp src/camera_ops.cpp

# 生成的可执行文件
TARGET = beast_camera_stream

# 编译规则
$(TARGET): $(SRCS)
	$(info Compiling with $(CXX))
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRCS) $(LDFLAGS)

# 清理生成文件
clean:
	rm -f $(TARGET)
