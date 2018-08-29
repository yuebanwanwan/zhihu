# -*- coding: utf-8 -*-
import scrapy
from lxml import etree
import requests
import re
import math
from scrapy_splash import SplashRequest
from queue import Queue
from zhihu.items import ZhihuItem,FollowersItem


class AzhihuSpider(scrapy.Spider):
    name = 'azhihu'
    allowed_domains = ['zhihu.com']
    #从轮子哥的粉丝开始爬取
    base_urls = 'https://www.zhihu.com/people/excited-vczh/followers'
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75 Safari/537.36'
    }
    urlqueue = Queue()
    script = """
    function main(splash, args)
      splash.images_enabled = false
      assert(splash:go(args.url))
      assert(splash:wait(0.5))
      return {
        html = splash:html(),
      }
    end
    """
    #执行js点击查看详细资料按钮获取用户的详细资料并返回带有详细资料的html页面
    #在知乎有的用户没有详细资料故没有‘查看详细资料’按钮，splash会报js执行错误
    follower_script = """
    function main(splash, args)
      assert(splash:go(args.url))
      assert(splash:wait(0.5))
      js = "document.querySelector('.Button.ProfileHeader-expandButton.Button--plain').click()"
      splash:evaljs(js)
      assert(splash:wait(0.5))
      return {
        html = splash:html(),
      }
    end
    """

    def start_requests(self):
        self.urlqueue.put(self.base_urls)
        while self.urlqueue != None:
            response = requests.get(self.urlqueue.get(),headers = self.headers)
            if response.status_code == 200:
                html = etree.HTML(response.text)
                fllowers = html.xpath('//strong[@class="NumberBoard-itemValue"]//text()')
                reallyf = str(fllowers[1])
                #去掉数字中的非数字字符
                r2 = re.sub("\D", "", reallyf)
                #得到r3为该用户的粉丝数
                r3 = int(r2)
                #向上取整获取爬取的页面总数(包含粉丝信息的页面)
                MAX_PAGE = math.ceil(r3/2)
                for i in range(1,MAX_PAGE+1):
                    base_page_url = 'https://www.zhihu.com/people/excited-vczh/followers?page='
                    yield SplashRequest(url=base_page_url + str(i),callback=self.parse,args={'lua_source':self.script},headers=self.headers)
    def parse(self, response):
        items = response.xpath('//div[@class="List-item"]//div[@class="UserItem-title"]')
        if items:
            for item in items:
                Item = ZhihuItem()
                Item['user'] = item.xpath('.//a[@class="UserLink-link"]/text()').extract_first().strip()
                url = ''.join(item.xpath('.//a[@class="UserLink-link"]/@href').extract()).strip()
                #生成该用户粉丝列表的首页并加入Queue中等待爬取
                reallyurl = url + '/followers'
                self.urlqueue.put(reallyurl)
                yield Item
                #生成粉丝个人信息主页
                yield SplashRequest(url='https:' + url + '/activities',callback=self.parse_followers,headers=self.headers)
    def parse_followers(self,response):
        Item = FollowersItem()
        Item['username'] = response.xpath('//span[@class="ProfileHeader-name"]/text()').extract_first().strip()
        bodytest = response.xpath('//div[@class="ProfileHeader-contentBody"]')
        #如果存在个人简介
        if bodytest:
            Item['introduction'] = ''.join(response.xpath('//div[@class="ProfileHeader-contentBody"]//text()').extract()).strip()
        else:
            Item['introduction'] = response.xpath('//span[@class="ProfileHeader-tips"]/text()').extract_first().strip()
        yield Item













