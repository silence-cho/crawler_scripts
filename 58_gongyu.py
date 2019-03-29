#coding:utf-8

#爬取58品牌公馆南京的房源信息，并保存到数据库。
#由于其网页上数字采用了特殊的字体，爬取下来的网页中字体乱码，需要进行转换，参考https://www.cnblogs.com/silence-cho/p/10202552.html
import requests
from lxml import html
import csv
import re
from fontTools.ttLib import TTFont
import base64
import MySQLdb
import time
from download import get_user_agent

def download(url,headers=None,cookies=None,proxies=None,num_retries=3):  #支持user-agent和proxy
    #proxies = {"http": "http://10.10.1.10:3128", "https": "http://10.10.1.10:1080",}
    response=requests.get(url,headers=headers,cookies=cookies,proxies=proxies)
    if response.status_code and 500<=response.status_code<600:  # 出现服务器端错误时重试三次
        if num_retries > 0:
            response = download(url,user_agent,proxies,num_retries-1)
    return response

def convertNumber(html_page):

    base_fonts = ['uni9FA4', 'uni9F92', 'uni9A4B', 'uni9EA3', 'uni993C', 'uni958F', 'uni9FA5', 'uni9476', 'uni9F64',
                  'uni9E3A']
    base_fonts2 = ['&#x' + x[3:].lower() + ';' for x in base_fonts]  # 构造成 &#x9e3a; 的形式
    pattern = '(' + '|'.join(base_fonts2) + ')'

    font_base64 = re.findall("base64,(AA.*AAAA)", response.text)[0]  # 找到base64编码的字体格式文件
    font = base64.b64decode(font_base64)
    with open('58font2.ttf', 'wb') as tf:
        tf.write(font)
    onlinefont = TTFont('58font2.ttf')
    convert_dict = onlinefont['cmap'].tables[0].ttFont.tables['cmap'].tables[0].cmap  # convert_dict数据如下：{40611: 'glyph00004', 40804: 'glyph00009', 40869: 'glyph00010', 39499: 'glyph00003'
    new_page = re.sub(pattern, lambda x: getNumber(x.group(),convert_dict), html_page)
    return new_page

def getNumber(g,convert_dict):
    key = int(g[3:7], 16)  # '&#x9ea3',截取后四位十六进制数字，转换为十进制数，即为上面字典convert_dict中的键
    number = int(convert_dict[key][-2:]) - 1  # glyph00009代表数字8， glyph00008代表数字7，依次类推
    return str(number)

def getLocation(title):
    desc = title.split()
    if u'寓' in desc[0]or u'社区' in desc[0]:
        location = desc[0].strip(u'【整租】【合租】')+desc[2]
    else:
        location=desc[1]
    return location

def getAveragePrice(price):
    price_range = price.split('-')
    if len(price_range)==2:
        average_price = (int(price_range[0])+int(price_range[1]))/2
    else:
        average_price=price
    return average_price

if __name__ == '__main__':

    conn = MySQLdb.connect(host='localhost',user='root',passwd='',db='renthouse',charset='utf8',port=3306) #不要写成utf-8
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS 58house(
                        id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
                        title VARCHAR(128) NOT NULL,
                        location VARCHAR(128) NOT NULL,
                        room VARCHAR(128) NOT NULL ,
                        price VARCHAR(64) NOT NULL ,
                        average_price VARCHAR(64) NOT NULL ,
                        url VARCHAR(768) NOT NULL);""")
    conn.commit()
    seed_url = "https://nj.58.com/pinpaigongyu/pn/{page}/"
    page = 0
    flag=True
    while flag:
        try:
            user_agent = get_user_agent()
            headers={"User_Agent":user_agent}
            page = page+1
            current_url=seed_url.format(page=page)
            print current_url
            response = download(url=current_url,headers=headers)
            new_page = convertNumber(response.text)
            tree = html.fromstring(new_page)
            li_tags = tree.xpath('//ul[@class="list"]/li')
            #print li_tags
            if (not li_tags) or page>600:
                print page
                flag=False
            for li_tag in li_tags:
                title = li_tag.xpath('.//div[@class="des strongbox"]/h2/text()')[0].strip()
                room = li_tag.xpath('.//p[@class="room"]/text()')[0].replace('\r\n', '').replace(r' ', '')
                price = li_tag.xpath('.//div[@class="money"]//b/text()')[0].strip().replace('\r\n', '').replace(r' ', '')
                url = li_tag.xpath('./a[@href]')[0].attrib['href'].strip()
                location = getLocation(title)
                average_price = getAveragePrice(price)
                cursor.execute("""INSERT INTO 58house(title,location,room,price,average_price,url) 
                        VALUES('%s','%s','%s','%s','%s','%s');"""%(title,location,room,price,average_price,url))
                conn.commit()
        except Exception as e:
            print "download page %s error: %s"%(page,e)
        time.sleep(5) # 停顿时间小于5s时会要求图形验证码
    conn.close()