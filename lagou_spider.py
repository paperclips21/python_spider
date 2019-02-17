#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 17 15:42:23 2019
目标：抓取拉勾招聘信息
流程：访问首页获取每个职位对应url，然后通过修改url进行翻页抓取
重点：session会话维持、ip代理设置
@author: xingyu
"""

import requests
from bs4 import BeautifulSoup
import time
import random

def get_index(index_url):
    '''
    通过拉勾首页获取各职位对应名称及url
    因为对首页只是一次访问即可获取，不做headers/cookies设置
    '''
    r = requests.get(index_url)
    soup_index = BeautifulSoup(r.text, 'lxml')
    
    position_list = [] # 保存各职位名称+url
    for each_first in soup_index.select('#sidebar > div > .menu_box'):
        first_name = each_first.select_one('h2').get_text().strip(' \n') # 第一分类名称

        for each_second in each_first.select('div.menu_sub.dn > dl'):
            second_name = each_second.select_one('dt > span').get_text() # 第二分类名称

            for each_third in each_second.select('dd > a'):
                third_name = each_third.get_text() # 职位名称
                third_url = each_third['href'] # 职位url
                position_list.append([first_name, second_name, third_name, third_url])
    
    return position_list

def choose_ua():
    '''
    每次调用此函数随机返回一个UA
    '''
    ua = [
        'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
        'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
        'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
        'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E) QQBrowser/6.9.11079.201',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1',
        'Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.9.168 Version/11.50',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; Tablet PC 2.0; .NET4.0E)',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'
    ]
    return random.choice(ua)

def get_position(position_list):
    '''
    根据从首页获得的各职位对应url，对每个职位进行翻页保存职位信息
    创建会话，每个职位有1次会话
    '''
    position_info = []
    
    for positions_url in [position_list[i][3] for i in range(len(position_list))]:
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Host': 'www.lagou.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': choose_ua() # 每个职位，随机选择一个User-Agent
        }

        s = requests.Session()
        s.headers.update(headers) # 需要设置headers信息，否则返回登陆页面
        s.proxies = { # 代理池
                'HTTP': 'http://110.52.235.241:9999',
                'HTTP': 'http://121.61.1.2:9999',
                'HTTP': 'http://61.184.40.41:9999',
                'HTTPS': 'https://111.177.190.225:9999',
                'HTTPS': 'https://125.123.143.208:9999'
            }
        s.get('http://www.lagou.com') # 第一步先访问首页，获得cookies
        time.sleep(1)

        for pn in range(1, 31, 1):
            r = s.get(positions_url + str(pn) + '/') # 循环进行翻页访问
            time.sleep(random.uniform(1.2, 3.4))
            if len(r.text)<2000: break # 如果翻页完毕，退出当前职位爬取
            soup_positon = BeautifulSoup(r.text, 'lxml')

            for each_position in soup_positon.select('#s_position_list > ul > li'):
                position_id = each_position['data-positionid'] # 职位id
                position_salary = each_position['data-salary'] # 薪资
                position_name = each_position['data-positionname'] # 职位名称
                position_url = each_position.select_one('.position_link')['href'] # 职位url
                position_area = each_position.select_one('.add > em').get_text() # 工作地点
                position_publishtime = each_position.select_one('.format-time').get_text() # 发布时间
                position_requ = each_position.select_one('div.position > div.p_bot > div.li_b_l').get_text().split('\n')[-2] # 职位要求
                position_desc = each_position.select_one('div.li_b_r').get_text() # 职位描述
                position_tags = each_position.select_one('div.list_item_bot > div.li_b_l').get_text('/') # 职位tags

                hr_id = each_position['data-hrid'] # HRid
                company_name = each_position['data-company'] # 供职公司
                company_id = each_position['data-companyid'] # 公司id
                company_url = each_position.select_one('.company_name > a')['href'] # 公司url
                company_desc = each_position.select_one('div.industry').get_text().strip() # 公司行业描述

                position_info.append([position_id, position_salary, position_name, position_url, position_area, position_publishtime, position_requ, position_desc, position_tags, 
                                     hr_id, company_name, company_id, company_url, company_desc])
                print(pn, position_name, 'done')
                
        if len(position_info) >= 4000: break # 爬取四千条数据即终止
    
    return position_info


position_list = get_index('http://www.lagou.com') # 首页获取每个职位url
position_info = get_position(position_list) # 循环抓取数据