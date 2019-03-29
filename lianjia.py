#coding:utf-8

#爬取链家南京房源数据，并保存到数据库
import requests
from lxml import html
import time
from utils.proxy import get_proxy_ip
from utils.headers import get_user_agent
import MySQLdb

def download(url,headers=None,cookies=None,proxies=None,num_retries=3):  #支持user-agent和proxy
    response=requests.get(url,headers=headers,cookies=cookies,proxies=proxies)
    if response.status_code and 500<=response.status_code<600:  # 出现服务器端错误时重试三次
        if num_retries > 0:
            response = download(url,headers,cookies,proxies,num_retries-1)
    return response

def getLocation(title):
    desc = title.split()

    if u'合租' in desc[0] or u'整租' in desc[0]:
        try:
            location = desc[2]
        except IndexError as e:
            print e
            location = desc[0]
    else:
        location=desc[0]
    return location

if __name__ == '__main__':

    conn = MySQLdb.connect(host='localhost',user='root',passwd='',db='renthouse',charset='utf8',port=3306) #不要写成utf-8
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS lianjiahouse(
                        id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
                        city VARCHAR(32) NOT NULL,
                        title VARCHAR(128) NOT NULL,
                        location VARCHAR(128) NOT NULL,
                        room VARCHAR(128) NOT NULL ,
                        price VARCHAR(64) NOT NULL ,
                        url VARCHAR(128) NOT NULL);""")
    conn.commit()
    #seed_url = "https://nj.lianjia.com/zufang/pg{page}/"
    page = 0
    while page<100:
        try:
            user_agent = get_user_agent()
            headers={"User-Agent":user_agent}
            proxies = get_proxy_ip()
            page = page+1
            current_url=seed_url.format(page=page)
            print current_url
            response = download(url=current_url,headers=headers,proxies=proxies)
            tree = html.fromstring(response.text)
            item_tags = tree.xpath('//div[@class="content__list"]/div')
            for item in item_tags:
                title = item.xpath('./div/p[1]/a/text()')[0].strip()
                room = item.xpath('./div/p[2]')[0].text_content().strip().replace('\n', '').replace(r' ', '')
                price = item.xpath('./div/span/em/text()')[0].strip()
                url = "https://nj.lianjia.com" + item.xpath('./div/p[1]/a')[0].attrib['href'].strip()
                location = getLocation(title)
                # print title, price, room, url, location

                cursor.execute("""INSERT INTO lianjiahouse(city,title,location,room,price,url)
                        VALUES('%s','%s','%s','%s','%s','%s');"""%(u'南京',title,location,room,price,url))
                conn.commit()
        except Exception as e:
            print "download page %s error: %s"%(page,e)
            # raise
        time.sleep(2) # 停顿2s
    conn.close()


