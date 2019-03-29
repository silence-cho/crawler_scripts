#coding:utf-8

#一个完整的网页爬虫，支持重试，延迟，缓存，回调函数，递归深度，url去重

import requests
import re
import urlparse
from datetime import datetime,timedelta
import time
import hashlib
import os
import pickle
import zlib
from pymongo import MongoClient
from bson.binary import Binary


#下载器
#num_retries 爬取失败时重试次数
#delay 同一个域名爬取时延迟时间
#支持下载内容进行缓存
class Downloader(object):
    def __init__(self,user_agent=None, proxies=None, num_retries=3,delay=5,cache=None):
        self.user_agent = user_agent
        self.proxies = proxies
        self.num_retries=num_retries
        self.throttle = Throttle(delay)
        self.cache = cache

    def __call__(self, url):
        result = None
        try:
            result = self.cache[url]  #从缓存中获取结果
        except KeyError:
            pass
        else:
            if self.num_retries>0 and 500<=result['code']<None:
                result = None
        if result==None:
            self.throttle.wait(url)
            response = self.download(url,self.user_agent,self.proxies,self.num_retries)
            result={'html':response.text,'code':response.status_code}
            if self.cache:
                self.cache[url]=result   #将结果保存到缓存
        return result['html']

    def download(self,url, user_agent, proxies, num_retries):
        response = requests.get(url, headers={'User-Agent': user_agent}, proxies=proxies)
        if response.status_code and 500 <= response.status_code < 600:  # 出现服务器端错误时重试三次
            if num_retries > 0:
                response = self.download(url, user_agent, proxies, num_retries - 1)
        return response

#同一个域名的下载延迟
class Throttle(object):
    def __init__(self,delay):
        self.delay = delay
        self.domains={}

    def wait(self,url):
        domain = urlparse.urlparse(url).netloc  #提取网址的域名
        last_accessed = self.domains.get(domain)
        if self.delay>0 and last_accessed!=None:
            sleep_secs = self.delay-(datetime.now()-last_accessed).seconds
            if sleep_secs>0:
                time.sleep(sleep_secs)
        self.domains[domain]=datetime.now()

#以MongoCache作为缓存系统
class MongoCache(object):
    def __init__(self,client=None,expires=timedelta(days=30)):
        self.client =MongoClient('127.0.0.1',27017) if client is None else client
        self.db = self.client.cache #连接cache数据库，没有则创建
        self.collection = self.db.webpage #webpage集合，没有则创建（集合相当于表）
        self.collection.create_index('timestamp',expireAfterSeconds=expires.total_seconds())

    def __getitem__(self, url):
        record = self.collection.find_one({'_id':url})
        if record:
            return pickle.loads(zlib.decompress(record['result']))
        else:
            raise KeyError(url + 'does not exist!')
    def __setitem__(self, url, result):
        record={'result':Binary(zlib.compress(pickle.dumps(result))),'timestamp':datetime.utcnow()}
        #mongoDB 存储文件，将数据转化为二进制再存储
        self.collection.update({'_id':url},{'$set':record},upsert=True)
		
#以磁盘作为cache		
class DiskCache(object):
    def __init__(self,cache_dir='cache',expires=timedelta(days=30)):
        self.cache_dir = cache_dir
        self.expires = expires  #缓存有效期30天
　　　　 if not os.path.exists(self.cache_dir):
        　　os.makedirs(self.cache_dir)

    def url_to_path(self,url):  #对url进行hash摘要计算，以其为文件名
        h = hashlib.md5()
        h.update(url)
        return h.hexdigest()

    def __getitem__(self, url):
        path = os.path.join(self.cache_dir, self.url_to_path(url))
        if os.path.exists(path):
            with open(path,'rb') as f:
                result,timestamp = pickle.loads(zlib.decompress(f.read()))
            if datetime.utcnow()>timestamp+self.expires:  #判断缓存是否过期
                raise KeyError(url+'has expired!')
            return result
        else:
            raise KeyError(url+'does not exist!')

    def __setitem__(self, url, result):
        path = os.path.join(self.cache_dir,self.url_to_path(url))
        timestamp = datetime.utcnow()
        data = pickle.dumps((result,timestamp))  #加上时间戳，判断缓存是否过期
        with open(path,'wb') as f:
            f.write(zlib.compress(data))  #压缩，减少内存

#使用上述下载器进行整站爬取
#max_depth: 爬取url最大递归深度
#callback: 对下载的网页进行处理的回调函数
def link_carwl(start_url,link_regex,max_depth=5,callback=None,user_agent=None, proxies=None, num_retries=3,delay=5,cache=None):
    url_queue = [start_url]
    seen = {start_url:0}
    down = Downloader(user_agent=user_agent, proxies=proxies, num_retries=num_retries,delay=delay,cache=cache)
    while url_queue:
        url = url_queue.pop()
        html = down(url)
        if callback!=None:
            callback(url,html)
        depth = seen[url]
        if depth<max_depth:
            for link in get_links(html):
                if re.match(link_regex,link):
                    #urlparse.urljoin(url,link)  #link可能为相对路径
                    if link not in seen:   #不访问重复的url
                        seen[link] =depth+1  #在url的深度基础上加一
                        url_queue.append(link)
# url提取
def get_links(html):
    webpage_regex = re.compile('<a[^>]+href=["\'](.*?)["\']', re.IGNORECASE)  # ["\']匹配单引号或双引号
    return webpage_regex.findall(html)

if __name__ == '__main__':
    link_carwl('https://nj.lianjia.com/ershoufang/',r'https://nj.lianjia.com/ershoufang/.*',max_depth=1,cache=MongoCache())
    d = Downloader(cache=MongoCache())
    print(d.cache['https://nj.lianjia.com/ershoufang/']['html'])
