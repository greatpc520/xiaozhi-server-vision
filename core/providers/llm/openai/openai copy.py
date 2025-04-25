import openai
from config.logger import setup_logging
from core.utils.util import check_model_key
from core.providers.llm.base import LLMProviderBase
import base64
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from core.handle.iotHandle import send_iot_conn
import asyncio
import threading
import time
from PIL import Image


TAG = __name__
logger = setup_logging()
#图片转base64函数
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
def mirror_image(input_path, output_path, direction='horizontal'):
    """
    实现图片镜像（水平或垂直翻转）
    
    参数：
        input_path (str): 输入图片路径
        output_path (str): 输出图片路径
        direction (str): 翻转方向，'horizontal'（默认）或'vertical'
    """
    try:
        with Image.open(input_path) as img:
            # 选择翻转方式
            if direction == 'horizontal':
                flipped_img = img.transpose(Image.FLIP_LEFT_RIGHT)
            elif direction == 'vertical':
                flipped_img = img.transpose(Image.FLIP_TOP_BOTTOM)
            else:
                raise ValueError("方向参数错误，必须是 'horizontal' 或 'vertical'")
            
            # 保留原始图片模式（如RGB/RGBA）
            if img.mode in ('RGBA', 'LA'):
                flipped_img.save(output_path, format='PNG')  # 保留透明度通道
            else:
                flipped_img.save(output_path)
            
            print(f"镜像成功！保存至 {output_path}")
            
    except Exception as e:
        print(f"处理失败: {str(e)}")

class LLMProvider(LLMProviderBase):
    def __init__(self, config):
        self.model_name = config.get("model_name")
        self.api_key = config.get("api_key")
        if 'base_url' in config:
            self.base_url = config.get("base_url")
        else:
            self.base_url = config.get("url")
        self.max_tokens = config.get("max_tokens", 500)
        print("self.api_key", self.api_key)
        check_model_key("LLM", self.api_key)
        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        # 启动HTTP服务器
        self._start_http_server()


    def _start_http_server(self):
        """使用http.server实现图片上传服务"""
        # 创建上传目录
        self.upload_dir = "tmp"  # 保持与原有代码一致
        os.makedirs(self.upload_dir, exist_ok=True)

        class ImageUploadHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                if self.path != '/upload':
                    logger.bind(tag=TAG).error(404, "Endpoint not found")
                    return

                try:
                    content_length = int(self.headers.get('Content-Length', 0))
                except ValueError:
                    logger.bind(tag=TAG).error(400, "Invalid Content-Length")
                    return

                if content_length <= 0:
                    logger.bind(tag=TAG).error(400, "Empty request body")
                    return

                # 循环读取以确保获取所有数据
                image_data = bytearray()
                remaining = content_length
                while remaining > 0:
                    chunk = self.rfile.read(min(remaining, 8192))  # 每次读取8KB
                    if not chunk:
                        break  # 连接中断，数据不完整
                    image_data.extend(chunk)
                    remaining -= len(chunk)
                
                # 检查实际接收长度
                if remaining != 0:
                    logger.bind(tag=TAG).error(400, f"数据不完整，预期 {content_length} 字节，收到 {len(image_data)} 字节")
                    return

                # 保存文件
                try:
                    # 保存为固定文件名
                    fixed_path = os.path.join(self.server.upload_dir, "image_now.jpg")
                    with open(fixed_path, 'wb') as f:
                        f.write(image_data)

                    # 保存为固定文件名
                    fixed_path = os.path.join(self.server.upload_dir, "image.jpg")
                    with open(fixed_path, 'wb') as f:
                        f.write(image_data)
                    print(f"图片已保存: tmp/image_now.jpg")
                except Exception as e:
                    logger.bind(tag=TAG).error(500, f"保存失败: {str(e)}")


        # 创建服务器实例
        server_address = ('', 8003)
        self.httpd = HTTPServer(server_address, ImageUploadHandler)
        # 传递上传目录给handler
        self.httpd.upload_dir = self.upload_dir

        # 在独立线程中启动服务器
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = True  # 守护线程
        self.server_thread.start()
        print(f"[HTTP Server] Started on port 8003, upload dir: {self.upload_dir}")
        

    def response(self, session_id, dialogue, conn = None):
        use_pic = False
        # 处理图片上传
        try:
            # if conn is not None:
            #     url = f"http://{conn.client_ip}/jpg"
            # else:
            #     url = 'http://192.168.248.171/jpg'  # 改成你自己的板子ip
            # # 发送请求
            # response = requests.get(url, timeout=1000)
            # use_pic = False
            # if response.status_code == 200:  
            #     with open('tmp/image.jpg', 'wb') as file:  
            #         file.write(response.content)  
            #         print('文件下载成功')
            #         use_pic = True
            # else: 
            #     print('文件下载失败')
            print("begin to take photo")
            asyncio.run(send_iot_conn(conn, "Camera", "take_photo", {}))
            # 这里可以添加代码来处理图片上传
            print("begin to upload photo")
            # 开启服务器, 获取图片
            # 2. 等待并检查图片上传（最多等待5秒）
            print("等待图片上传...")
            start_time = time.time()
            while not os.path.exists('tmp/image.jpg'):
                time.sleep(0.2)
                if time.time() - start_time > 5:
                    print("等待图片超时")
                    break
            
            # 3. 检查结果
            if os.path.exists('tmp/image.jpg'):
                use_pic = True
                logger.bind(tag=TAG).info("图片上传验证成功")
            else:
                logger.bind(tag=TAG).error("未检测到上传的图片")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in response generation: {e}")
            return "【图片服务响应异常】"
        
        if use_pic == True:
            mirror_image('tmp/image.jpg', 'tmp/flipped_image.jpg')
            image_path = "tmp/flipped_image.jpg"
            #原图片转base64
            base64_image = encode_image(image_path)
        
            last_message = dialogue[-1]
            content_text = last_message.get("content", "")
            content_img = [
                {"type": "text", "text": content_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    },
                },
            ]
            dialogue[-1]["content"] = content_img
        try:
            responses = self.client.chat.completions.create(
                model=self.model_name,
                messages=dialogue,
                stream=True,
                max_tokens=self.max_tokens,
            )

            is_active = True
            for chunk in responses:
                try:
                    # 检查是否存在有效的choice且content不为空
                    delta = chunk.choices[0].delta if getattr(chunk, 'choices', None) else None
                    content = delta.content if hasattr(delta, 'content') else ''
                except IndexError:
                    content = ''
                if content:
                    # 处理标签跨多个chunk的情况
                    if '<think>' in content:
                        is_active = False
                        content = content.split('<think>')[0]
                    if '</think>' in content:
                        is_active = True
                        content = content.split('</think>')[-1]
                    if is_active:
                        print("content", content, end="")
                        yield content

        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in response generation: {e}")

        # 删除临时图片
        if os.path.exists('tmp/image.jpg'):
            os.remove('tmp/image.jpg')

    def response_with_functions(self, session_id, dialogue, functions=None):
        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=dialogue,
                stream=True,
                tools=functions
            )

            for chunk in stream:
                yield chunk.choices[0].delta.content, chunk.choices[0].delta.tool_calls

        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in function call streaming: {e}")
            yield {"type": "content", "content": f"【OpenAI服务响应异常: {e}】"}
