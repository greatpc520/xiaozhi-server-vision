import openai
from config.logger import setup_logging
from core.utils.util import check_model_key
from core.providers.llm.base import LLMProviderBase
import requests
import base64
import cv2

TAG = __name__
logger = setup_logging()
#图片转base64函数
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

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

    def response(self, session_id, dialogue):
        url = 'http://192.168.248.171/jpg'  
        response = requests.get(url, timeout=2000)
        use_pic = False
        if response.status_code == 200:  
            with open('tmp/image.jpg', 'wb') as file:  
                file.write(response.content)  
                print('文件下载成功')  
                use_pic = True
        else: 
            print('文件下载失败')


        if use_pic == True:
            img = cv2.imread('tmp/image.jpg')
            flipped_img = cv2.flip(img, 1)
            cv2.imwrite('tmp/flipped_image.jpg', flipped_img)
            #输入图片路径
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
