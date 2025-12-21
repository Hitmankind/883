# RealSense人脸追踪集成使用指南

## 📋 功能概述

系统已成功集成Intel RealSense相机的人脸追踪功能。现在您可以在Web界面中直接启动RealSense模块进行人脸识别，无需手动运行Python脚本。

## ✨ 新增功能

### 🔄 双模式支持
- **Webcam模式**: 使用浏览器摄像头进行人脸检测（基于face-api.js）
- **RealSense模式**: 使用Intel RealSense相机进行高精度人脸追踪

### 🎯 一键启动
- 点击"Start Face Tracking"时，系统会自动：
  1. 启动机械臂项目中的RealSense模块
  2. 运行 `main_example.py` 脚本
  3. 选择功能15（人脸识别）
  4. 连接到指定的服务器地址

## 🚀 使用步骤

### 1. 访问机械臂页面
打开浏览器访问：`http://localhost:8000/robot-arm/`

### 2. 选择RealSense模式
1. 在页面上找到 "Tracking Mode Selection" 区域
2. 选择 "RealSense Mode" 单选按钮
3. 输入服务器地址（默认：localhost:8000）

### 3. 启动人脸追踪
1. 点击 "Start RealSense" 按钮
2. 系统会自动启动RealSense模块
3. 等待几秒钟，看到 "RealSense Face Tracking Active" 状态
4. 人脸追踪功能已激活

### 4. 连接机械臂（可选）
1. 点击 "Connect Arm" 按钮
2. 点击 "Calibrate" 校准机械臂
3. 选择 "Track Mode" 进入自动追踪模式

### 5. 停止追踪
1. 点击 "Stop Tracking" 按钮
2. 系统会自动关闭RealSense进程

## 🔧 技术实现

### 后端API接口

#### 启动RealSense追踪
```http
POST /api/start-realsense/
Content-Type: application/json

{
  "server_address": "localhost:8000"
}

Response:
{
  "status": "success",
  "message": "RealSense人脸追踪已启动，服务器地址: localhost:8000",
  "function_id": "15"
}
```

#### 停止RealSense追踪
```http
POST /api/stop-realsense/

Response:
{
  "status": "success",
  "message": "RealSense人脸追踪已停止"
}
```

### 自动执行的命令
系统会自动执行以下命令：
```bash
python "C:\Users\ZhuanZ\CCNU_Robot\Exoskeleton-Robot\RealSense\main_example.py" --server localhost:8000 --function 15
```

### 进程管理
- **启动**: 在新控制台窗口中运行RealSense脚本
- **监控**: 自动检查进程状态
- **停止**: 通过taskkill命令终止相关进程

## ⚙️ 配置选项

### 服务器地址
- 默认地址：`localhost:8000`
- 可以修改为实际的IP地址和端口
- 用于RealSense模块与Web系统的通信

### 功能ID
- 默认使用功能15（人脸识别）
- 可以在代码中修改为其他功能ID

## 🔍 故障排除

### 常见问题

1. **RealSense模块未找到**
   - 检查路径：`C:\Users\ZhuanZ\CCNU_Robot\Exoskeleton-Robot\RealSense\main_example.py`
   - 确保机械臂项目存在

2. **无法启动RealSense**
   - 检查Python环境是否正确
   - 确保RealSense SDK已安装
   - 检查是否有权限执行Python脚本

3. **进程无法停止**
   - 手动打开任务管理器
   - 查找名为 `main_example.py` 的Python进程
   - 手动结束进程

### 调试方法

1. **查看控制台日志**
   - 浏览器开发者工具的Console标签
   - 查看API请求和响应

2. **检查服务器日志**
   - Django开发服务器的输出
   - 查看是否有错误信息

3. **手动测试RealSense**
   ```bash
   cd "C:\Users\ZhuanZ\CCNU_Robot\Exoskeleton-Robot\RealSense"
   python main_example.py --server localhost:8000 --function 15
   ```

## 🎨 用户界面说明

### 模式选择区域
- 两个单选按钮：Webcam Mode 和 RealSense Mode
- 切换模式时会自动重置相关状态

### 服务器配置
- 只在RealSense模式下显示
- 输入框用于指定服务器地址

### 状态显示
- RealSense模式下显示特殊的绿色状态面板
- 包含相机图标和旋转的加载动画

### 按钮状态
- 根据当前模式动态更新按钮文本
- RealSense模式下显示 "Start RealSense"

## 🔐 安全注意事项

1. **权限控制**
   - 需要教师权限才能访问
   - CSRF保护已启用

2. **进程管理**
   - 只能终止相关的main_example.py进程
   - 不会影响其他Python进程

3. **网络通信**
   - 使用HTTPS或localhost进行通信
   - 所有API请求都有CSRF保护

## 📝 开发注意事项

### 修改RealSense路径
如果要修改RealSense项目路径，请编辑：
```python
# students/views.py 中的 start_realsense_tracking 函数
realsense_project_path = r"C:\Users\ZhuanZ\CCNU_Robot\Exoskeleton-Robot"
```

### 添加新功能
可以修改command数组来传递更多参数：
```python
command = [
    'python', main_example_path,
    '--server', server_address,
    '--function', '15',
    '--new-parameter', 'value'
]
```

## 🎯 后续改进建议

1. **实时视频流**: 集成RealSense的视频流到Web界面
2. **更多功能**: 添加对其他RealSense功能的支持
3. **配置保存**: 保存用户的服务器地址设置
4. **状态监控**: 实时显示RealSense模块的运行状态
5. **日志查看**: 在Web界面中查看RealSense模块的日志输出

---

**🎉 集成完成！**
现在您可以通过简单的Web界面操作来启动和管理RealSense人脸追踪功能了！