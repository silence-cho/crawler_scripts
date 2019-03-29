#coding: utf-8

import urllib2
import re
import random
import ssl

#基于python 2.7
# 爬取代理ip网页来动态获取可用的ip地址（地址 https://www.kuaidaili.com/free/）
def get_proxy_ip():
    context = ssl._create_unverified_context()  #访问https站点时需要
    headers={
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1'}
    url="https://www.kuaidaili.com/free/"#通过网址的翻页还可以爬取更多的代理网址
    req=urllib2.Request(url,headers=headers)
    response=urllib2.urlopen(req,context=context)
    content=response.read().decode("utf-8")
    ip_pattern=re.compile(r"\d+\.\d+\.\d+\.\d+")
    port_pattern=re.compile(r'<td data-title="PORT">(\d+)</td>')
    type_pattern = re.compile(r'<td data-title=.*>(HTTP[S]{0,1})</td>')
    ip_list=re.findall(ip_pattern,content)
    port_list=re.findall(port_pattern,content)
    type_list = re.findall(type_pattern,content)
    #print ip_list,port_list,type_list
    proxy_list=[]
    for i in range(len(ip_list)):
        ip=ip_list[i].encode('utf-8')
        port=port_list[i].encode('utf-8')
        type = type_list[i].encode('utf-8').lower()
        proxy="%s:%s"%(ip,port)
        proxy_list.append({type:proxy})
    return random.choice(proxy_list)

#基于python 3
# import requests
# def get_proxy_ip():
	# headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1'}
	# url="https://www.kuaidaili.com/free/" 			#通过网址的翻页还可以爬取更多的代理网址
	# response = requests.get(url,headers=headers)
	# content=response.text
	# ip_pattern=re.compile(r"\d+\.\d+\.\d+\.\d+")
	# port_pattern=re.compile(r'<td data-title="PORT">(\d+)</td>')
	# type_pattern = re.compile(r'<td data-title=.*>(HTTP[S]{0,1})</td>')
	# ip_list=re.findall(ip_pattern,content)
	# port_list=re.findall(port_pattern,content)
	# type_list = re.findall(type_pattern,content)
	# proxy_list=[]
	# for i in range(len(ip_list)):
		# ip=ip_list[i].encode('utf-8')
		# port=port_list[i].encode('utf-8')
		# type = type_list[i].encode('utf-8').lower()
		# proxy="%s:%s"%(ip,port)
		# proxy_list.append({type:proxy})
	# return random.choice(proxy_list)

if __name__=="__main__":
	print(get_proxy_ip())   #类似结果{'http': '111.177.176.194:9999'}
	
