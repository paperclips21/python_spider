"""
时间：20200105
目标：拉取猎聘全站展示职位数据
总结：
1. 在考虑如何存储职业分类详细数据时有考虑过，目前采用的是 list of list 形式存储于变量中。
   考虑使用其他的存储格式，如 dict of dict 是不是会更方便一些
2. 没有遇到什么反爬机制，只带上 User-Agent 就可以在原网页中提取到相应数据，抽样对比没有发现与网页展示发生偏差。
   在爬到10000+条数据的时候程序错误，原因是访问时间过长。可能是触发了反爬机制，可以考虑加上处理反爬部分的代码。
3. 总体逻辑还是比较简单，从首页拉取多层的职业分类信息，然后每个细分职业构建 Session 翻页爬取。
   但是从代码角度来看，对我们外行人员来说能用就行，还需要找时间补全基本算法与数据结构方面的知识
"""

import requests
import time
import random
import pymysql
from bs4 import BeautifulSoup


def get_position_type(city_url, headers):
    """
    通过城市首页提取出所有页面展示的职位分类表，包括其链接关系与 url，储存在 list of list 中
    """
    s = requests.Session()
    r = s.get(city_url, headers=headers)
    print(f'初始页面访问代码： {r.status_code}')

    r = s.get(city_url + 'zhaogongzuo/')
    soup = BeautifulSoup(r.text, 'lxml')

    # 第一层大分类的网址在 JS 中，不做解析
    first_li = [[each.get_text()] for each in soup.select(
        'div.info-detail ul.tab li.clearfix span')]  # 2维数组

    li = []
    for each in soup.select('div.info-detail div dl'):
        second = each.select('dt a')  # 第二层
        second_li = [[second[i].get_text(), second[i]['href']]
                     for i in range(len(second))]
        third = each.select('dd')  # 第三层
        third_li = [[[third2.select('a')[j].get_text(), third2.select(
            'a')[j]['href']] for j in range(len(third2.select('a')))] for third2 in third]
        [second_li[i].append(third_li[i])
         for i in range(len(second_li))]  # 二三层合并，结果保存在二层中
        li.append(second_li)

    # 一二层合并，结果保存在一层中
    [first_li[i].append(li[i]) for i in range(len(first_li))]
    print('职位分类获取成功')

    return first_li


def get_job_info(page_num, job_info, soup, position_1_name, position_2_name, position_2_url, position_3_name, position_3_url):
    """
    拉取当前页职位信息，存入job_info
    """
    # 直接跳过了广告推广页面，进入职位展示
    for each_job in soup.select('ul.sojob-list li'):
        job_name = each_job.select_one('span.job-name a').get_text()
        job_salary = each_job.select('div p.condition.clearfix span')[
            0].get_text()
        job_area = each_job.select('div p.condition.clearfix span')[
            1].get_text()
        job_education = each_job.select(
            'div p.condition.clearfix span')[2].get_text()
        job_exercise = each_job.select(
            'div p.condition.clearfix span')[3].get_text()
        job_publish = each_job.select_one(
            'div p.time-info.clearfix time').get_text()
        job_response = each_job.select_one(
            'div p.time-info.clearfix span').get_text()
        job_company_name = each_job.select_one('p.company-name a').get_text()
        job_company_field = each_job.select_one(
            'p.field-financing span').get_text().strip()
        job_company_feature = '-'.join([each.get_text()
                                        for each in each_job.select('p.temptation.clearfix span')])

        # 使用 execute_many() 插入，需要 list of tuples 格式
        job_info.append((position_1_name, position_2_name, position_2_url, position_3_name, position_3_url,
                         page_num, job_name, job_salary, job_area, job_education, job_exercise, job_publish,
                         job_response, job_company_name, job_company_field, job_company_feature))

    print(f'{position_2_name}, {position_3_name}, 第 {page_num} 页，抓取完毕')
    return job_info


def get_job(city_url, headers, position_1_name, position_2_name, position_2_url, position_3_name, position_3_url):
    """
    通过传入的对应三层职位信息，翻页以抓取。
    1. 使用 session 逐层进行访问保持 cookies，每个职位一个 session
    2. 构建翻页，直接在当前页面进行抓取，不进入详细职位页面
    """
    # 第一步访问 city_url
    s = requests.Session()
    r = s.get(city_url, headers=headers)
    print(f'爬取 {position_3_name} 职位，首页访问： {r.status_code}')

    # 第二步，构建翻页开始抓取
    page_num = 0  # 从第 0 页开始
    job_info = []
    while True:
        page_url = position_3_url + f'pn{page_num}/'
        r = s.get(page_url)
        print(f'{position_3_name} 第 {page_num} 页: {r.status_code}')
        soup = BeautifulSoup(r.text, 'lxml')

        # 如果为真，就还有信息，继续爬取。否则说明当前页面没有职位信息，爬取完毕
        if soup.select('ul.sojob-list li'):
            # 抓取当前页面
            job_info = get_job_info(page_num, job_info, soup, position_1_name,
                                    position_2_name, position_2_url, position_3_name, position_3_url)
            page_num += 1  # 页码记得更新
            time.sleep(random.uniform(0.1, 3))
        else:
            print(f'{position_3_name} 抓取完毕，共 {page_num} 页')  # 因为 num 从0开始计数
            return job_info


def get_headers():
    """
    使用 random 库，随机返回一个 UA 头
    """
    user_agent = ['Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:65.0) Gecko/20100101 Firefox/65.0',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15',
                  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36']

    headers = {'User-Agent': random.choice(user_agent)}

    return headers


def create_table():
    """
    在本地数据库中创建表
    """
    create_table_sql = """
    create table liepin (
    position_1_name char(100),
            position_2_name char(100),
            position_2_url char(100),
            position_3_name char(100),
            position_3_url char(100),
            page_num int,
            job_name char(100),
            job_salary char(100),
            job_area char(100),
            job_education char(100),
            job_exercise char(100),
            job_publish char(100),
            job_response char(100),
            job_company_name char(100),
            job_company_field char(100),
            job_company_feature char(100));
        """
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root',
                           password='password', database='data', cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        print('liepin 表创建完成')
    except:
        conn.rollback()
        print('liepin 表创建失败')
    finally:
        cursor.close()
        conn.close()


def insert_into_table(job_info):
    insert_into_table_sql = """insert into liepin
        (position_1_name, position_2_name, position_2_url, position_3_name, position_3_url,
        page_num, job_name, job_salary, job_area, job_education, job_exercise, job_publish,
        job_response, job_company_name, job_company_field, job_company_feature)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    conn = pymysql.connect(host='127.0.0.1', port=3306,
                           user='root', password='password', database='data')
    cursor = conn.cursor()

    cursor.executemany(insert_into_table_sql, job_info)
    conn.commit()

    cursor.close()
    conn.close()
    print('数据库插入成功')


if __name__ == "__main__":
    city_url = 'https://www.liepin.com/city-nanchang/'
    position_type_li = get_position_type(
        city_url, headers=get_headers())  # 所有细分职位的信息
    create_table()

    for each_position_1 in position_type_li:
        position_1_name = each_position_1[0]
        for each_position_2 in each_position_1[1]:
            position_2_name = each_position_2[0]
            position_2_url = each_position_2[1]
            for each_position_3 in each_position_2[2]:
                position_3_name = each_position_3[0]
                position_3_url = each_position_3[1]
                job_info = get_job(city_url, get_headers(), position_1_name, position_2_name,
                                   position_2_url, position_3_name, position_3_url)
                insert_into_table(job_info)
                print(
                    f'{position_1_name}, {position_2_name}, {position_3_name} 抓取完成')
