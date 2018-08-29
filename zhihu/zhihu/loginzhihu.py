import scrapy
import time
import json
from PIL import Image




def start_requests(self):
    """请求登录页面"""
    return [scrapy.Request(url="https://www.zhihu.com/signup", callback=self.get_captcha)]


def get_captcha(self, response):
    """这一步主要是获取验证码"""
    post_data = {
        "email": "lq574343028@126.com",
        "password": "lq534293223",
        "captcha": "",  # 先把验证码设为空,这样知乎就会提示输入验证码
    }
    t = str(int(time.time() * 1000))
    #  这里是关键,这也是我找了好久才找到的方法,这就是知乎每次的验证码图片的url
    captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
    return [scrapy.FormRequest(url=captcha_url, meta={"post_data": post_data}, callback=self.after_get_captcha)]


def after_get_captcha(self, response):
    """把验证码存放到本地,手工输入"""
    with open("E:/outback/zhihu/zhihu/utils/captcha.png", "wb") as f:
        f.write(response.body)
    try:
        # 这一句就是让程序自动打打图片
        img = Image.open("E:/outback/zhihu/zhihu/utils/captcha.png")
        img.show()
    except:
        pass
    captcha = input("input captcha")
    post_data = response.meta.get("post_data", {})
    post_data["captcha"] = captcha
    post_url = "https://www.zhihu.com/login/email"
    return [scrapy.FormRequest(url=post_url, formdata=post_data,
                               callback=self.check_login)]


def check_login(self, response):
    """验证是否登录成功"""
    text_json = json.loads(response.text)
    if "msg" in text_json and text_json["msg"] == "登录成功":
        yield scrapy.Request("https://www.zhihu.com/", dont_filter=True, callback=self.start_get_info)
    else:
        # 如果不成功就再登录一次
        return [scrapy.Request(url="https://www.zhihu.com/signup", callback=self.get_captcha)]


def start_get_info(self, response):
    """登录成功后就可以去请求用户信息"""
    yield scrapy.Request(url=self.user_url.format(user="liu-qian-chi-24", include=self.user_query),
                         callback=self.parse_user)