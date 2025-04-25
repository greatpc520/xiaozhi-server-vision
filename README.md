# 帮助小智使用视觉

目前使用的是我之前开源的另一个项目, [小智闹钟](https://github.com/XuSenfeng/xiaozhi-alarm/tree/touch), 我在这个项目移植了照相机的server, 所以你可以使用访问客户端的/jpg目录的方式获取到当前的照片, 使用的开发板是立创实战派S3

![image-20250331210358002](https://picture-01-1316374204.cos.ap-beijing.myqcloud.com/lenovo-picture/202503312103151.png), **只支持一个用户!!!!多用户的时候这个方式的同步方法会出现冲突**

## 环境

如果你的报错显示`No module named`可以使用下面两个安装一下新的module

使用原服务器的环境在输入`pip install --upgrade "volcengine-python-sdk[ark]"`和`pip install opencv-python`两个安装这两个库 原程序地址https://github.com/xinnan-tech/xiaozhi-esp32-server, 我是用的是源码安装, 没有适配其他方式, 暂时不可以在服务器使用

## 服务器部署

服务器使用两核两G的时候不建议使用本地的音频模型, 可以使用豆包的语音识别服务, https://console.volcengine.com/speech/app

![image-20250420111337108](https://picture-01-1316374204.cos.ap-beijing.myqcloud.com/lenovo-picture/202504201113273.png)

实际的安装方式和原版服务的的安装方式相同, 我使用裸机进行安装, 没有试过docker部署的方式, 使用服务器的时候注意在防火墙以及安全组里面把使用的端口打开

> 原服务器使用端口8000, 我的服务使用8003(兼容服务器的API以及server服务)

## 后台运行

```
conda activate xiaozhi-esp32-server
nohup python -u app.py > output.log 2>&1 &
```
终止程序, 使用`pa -aux`查看一下这个程序的PID, 之后使用kill命令终止这个程序
![image](https://github.com/user-attachments/assets/91c39b10-8e86-4b1c-bc0e-74fc4654aa95)



- `nohup`：忽略挂断信号（即使终端关闭，进程仍继续运行）。
- `-u`：强制 Python 不缓冲输出（避免日志延迟）。
- `> output.log`：将标准输出重定向到日志文件。
- `2>&1`：将标准错误输出合并到标准输出。
- `&`：将进程放到后台运行。
