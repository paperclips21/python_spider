import requests
import time
import random
import os
from bs4 import BeautifulSoup

"""
时间：20200105
爬虫逻辑：
1. 根据初始url，得到当前分类的页面，然后通过构造url进行分页
2. 每一页会得到20个小说，点击进入当前小说页面，得到该小说每一集对应url。
3. 点击进入每一集对应 url，在页面中找到对应音频地址，下载保存

总结：
1. 单线程，能跑，效率低
2. 网站没有什么反爬措施，只要对 url 简单拉取即可
3. 考虑如何优化流程，不只是单独调用 for 循环。可能从页面解析及提取元素中进行调整
4. 考虑如何处理以便于使用数据库进行存储
"""


def get_epison(s, item_info):
    item_url = 'https://www.tingzh.com' + item_info['url']
    item_page = s.get(item_url).text
    item_soup = BeautifulSoup(item_page, 'lxml')

    # 创建保存路径
    path = f"/Users/xingyu/Downloads/audio/{item_info['name']}"
    if not os.path.exists(path):
        os.mkdir(path)

    # 拿到每一集的地址，存在 epison_url 内
    for each_epison in item_soup.select('ul.compress ul li'):
        epison_num = each_epison.select_one('a')['title']  # 当前集数，是文本形式
        epison_url = 'https://www.tingzh.com' + \
            each_epison.select_one('a')['href']

        # 访问每一集的地址，找到其对应音频文件地址
        epison_page = BeautifulSoup(s.get(epison_url).text, 'lxml')
        audio_url = str(epison_page.select_one(
            'div.combox div script:nth-child(5)'))
        audio_url = audio_url.split('(')[1].split(')')[0][1:-1]
        audio_url = audio_url.replace('%3A', ':').replace('%2F', '/')

        # 找到音频地址，下载到本地
        audio_r = s.get(audio_url).content
        with open(f"/Users/xingyu/Downloads/audio/{item_info['name']}/{epison_num}.mp3", 'wb') as f:
            f.write(audio_r)
        print(f"{item_info['name']} {epison_num} ，下载成功")


def get_item(s, page_soup, page_num):
    """
    通过每一页得到的信息，提取每一小说的详细信息
    """
    for item in page_soup.select('div.clist ul li'):
        item_info = {'name': item.select_one('a')['title'],
                     'url': item.select_one('a')['href'],
                     'author': item.select('p')[1].get_text(),
                     'type': item.select('p')[2].get_text(),
                     'oral': item.select_one('p a').get_text(),
                     'time': item.select('p')[4].get_text()}
        get_epison(s, item_info)  # 对该小说进行爬取
        print(f"第 {page_num} 页，{item_info['name']} 下载完毕")


def get_page(s, page_num_all, initial_url):
    """
    构建翻页
    """
    for page_num in range(1, page_num_all+1):
        # 构建翻页，从第一页开始
        page_url = initial_url[:-5] + f'-{page_num}.html'
        page_soup = BeautifulSoup(s.get(page_url).text, 'lxml')
        time.sleep(random.uniform(0.2, 2))  # 暂停

        get_item(s, page_soup, page_num)
        print(f"第 {page_num} 页，下载完毕")


if __name__ == "__main__":
    s = requests.Session()
    initial_url = 'https://www.tingzh.com/list/1.html'  # 只爬取第一类“玄幻”
    r = s.get(initial_url,
              headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'})
    print(f'初始 url 访问状态: {r.status_code}')
    soup = BeautifulSoup(r.text, 'lxml')

    # 从初始url提取到，总共有多少页，用于后续构建 url 翻页
    page_num_all = soup.select('div.border div.clist span a')[-1]['href']
    page_num_all = int(page_num_all.split(
        '/')[-1].split('.')[0].split('-')[-1])

    get_page(s, page_num_all, initial_url)
