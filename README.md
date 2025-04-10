# 帮助小智使用视觉

目前使用的是我之前开源的另一个项目, [小智闹钟](https://github.com/XuSenfeng/xiaozhi-alarm/tree/touch), 我在这个项目移植了照相机的server, 所以你可以使用访问客户端的/jpg目录的方式获取到当前的照片

![image-20250331210358002](https://picture-01-1316374204.cos.ap-beijing.myqcloud.com/lenovo-picture/202503312103151.png)

## 环境
使用原服务器的环境在输入`pip install --upgrade "volcengine-python-sdk[ark]"`和`pip install opencv-python`两个安装这两个库
原程序地址https://github.com/xinnan-tech/xiaozhi-esp32-server, 我是用的是源码安装, 没有适配其他方式, 暂时不可以在服务器使用
