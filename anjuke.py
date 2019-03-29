#coding:utf-8

#爬取安居客南京房源数据，并保存到数据库
import requests
from lxml import html
import MySQLdb
import time
from utils.proxy import get_proxy_ip
from utils.headers import get_user_agent

def download(url,headers=None,cookies=None,proxies=None,num_retries=3):  #支持user-agent和proxy
    #proxies = {"http": "http://10.10.1.10:3128", "https": "http://10.10.1.10:1080",}
    response=requests.get(url,headers=headers,cookies=cookies,proxies=proxies)
    if response.status_code and 500<=response.status_code<600:  # 出现服务器端错误时重试三次
        if num_retries > 0:
            response = download(url,headers,cookies,proxies,num_retries-1)
    return response

if __name__ == '__main__':

    conn = MySQLdb.connect(host='localhost',user='root',passwd='',db='renthouse',charset='utf8',port=3306) #不要写成utf-8
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS anjukehouse(
                        id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
                        city VARCHAR(32) NOT NULL,
                        title VARCHAR(128) NOT NULL,
                        location VARCHAR(128) NOT NULL,
                        room VARCHAR(128) NOT NULL ,
                        price VARCHAR(64) NOT NULL ,
                        url VARCHAR(128) NOT NULL);""")
    conn.commit()
    #seed_url = "https://nj.zu.anjuke.com/fangyuan/p{page}/"
    page = 0
    while page<50:
        try:
            user_agent = get_user_agent()
            headers = {"User-Agent": user_agent, "Referer": 'https://nanjing.anjuke.com/'}
            proxies = get_proxy_ip()
            page = page + 1
            current_url = seed_url.format(page=page)
            print current_url
            response = download(url=current_url, headers=headers, proxies=proxies)
            tree = html.fromstring(response.text)
            item_tags = tree.xpath('//div[@class="zu-itemmod  "]')  # 注意itemmod后面两个空格
            for item in item_tags:
                title = item.xpath('./div[1]/h3/a/text()')[0]
                price = item.xpath('./div[2]/p/strong/text()')[0]
                room = item.xpath('./div[1]/p')[0].text_content().strip().replace(u'\ue147', '|')
                url = item.xpath('./div[1]/h3/a')[0].attrib['href']
                location = item.xpath('./div[1]/address/a/text()')[0]
                # print title, price, room, url, location
                cursor.execute("""INSERT INTO anjukehouse(city,title,location,room,price,url)
                        VALUES('%s','%s','%s','%s','%s','%s');"""%(u'南京',title,location,room,price,url))
                conn.commit()
        except Exception as e:
            print "download page %s error: %s"%(page,e)
        time.sleep(2) # 停顿2s
    conn.close()
