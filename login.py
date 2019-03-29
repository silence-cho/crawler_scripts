#coding:utf-8



import requests
from bs4 import BeautifulSoup


#1. 登陆抽屉热搜榜,并点赞
'''
自动登录抽屉热搜榜流程：先访问主页，获取cookie1，然后携带用户名，密码和cookie1访问登陆页面对cookie1授权，随后就能利用cookie1直接访问个人主页等。
注意真正起作用的是cookie1里面gpsd': '2c805bc26ead2dfcc09ef738249abf65，第二次进行登陆时对这个值进行了认证，
随后就能利用cookie1进行访问了，进行登录时也会返回cookie2，但cookie2并不起作用
'''

def login_chouti():
	#访问首页
	response=requests.get(
		url="https://dig.chouti.com/",
		headers={"User-Agent":"Mozilla/5.0 (Windows NT 6.1; rv:62.0) Gecko/20100101 Firefox/62.0"}
	)
	cookie_dict = response.cookies.get_dict()
	print(cookie_dict)

	#登录页面，发送post
	response2= requests.post(
		url="https://dig.chouti.com/login",
		data={
			"oneMonth":"1",
			"password":"你自己的密码",
			"phone":"8618626429847",
		},
		headers={"User-Agent":"Mozilla/5.0 (Windows NT 6.1; rv:62.0) Gecko/20100101 Firefox/62.0"},
		cookies=cookie_dict,
	)

	#携带cookie，访问首页，显示为登录状态
	response3= requests.get(
		url="https://dig.chouti.com/",
		headers={"User-Agent":"Mozilla/5.0 (Windows NT 6.1; rv:62.0) Gecko/20100101 Firefox/62.0"},
		cookies = cookie_dict
	)

	#携带cookie，进行点赞，返回推送成功
	response4 = requests.post(
		url="https://dig.chouti.com/link/vote?linksId=22650731",  #换成你需要点赞的url
		headers={"User-Agent":"Mozilla/5.0 (Windows NT 6.1; rv:62.0) Gecko/20100101 Firefox/62.0"},
		cookies = cookie_dict
	)
	print(response4.text)  #{"result":{"code":"9999", "message":"推荐成功", "data":{"jid":"cdu_53961215992","likedTime":"1539697099953000","lvCount":"13","nick":"silence624","uvCount":"1","voteTime":"小于1分钟前"}}}

#2. 登陆github,并打印出所有的版本仓库名
#需要cookie和跨站伪造请求token值进行登陆
def login_github():
	response1 = requests.get(
		url="https://github.com/login",   #url为https://github.com/时拿到的cookie不行
		headers={"User-Agent":"Mozilla/5.0 (Windows NT 6.1; rv:62.0) Gecko/20100101 Firefox/62.0"},

	)
	cookie_dict = response1.cookies.get_dict()  #拿到cookie
	#print(cookie_dict)
	soup = BeautifulSoup(response1.text,features='html.parser')
	tag = soup.find(name='input',attrs={"name":"authenticity_token"})
	authenticity_token = tag.attrs.get('value')    # 从前端页面拿到跨站伪造请求token值
	#print(authenticity_token)
	response = requests.post(
		url='https://github.com/session',
		data={
			"authenticity_token":authenticity_token,
			"commit":"Sign+in",
			"login":"xxxxx",
			"password":"xxx",
			"utf8":""
		},
		headers={"User-Agent":"Mozilla/5.0 (Windows NT 6.1; rv:62.0) Gecko/20100101 Firefox/62.0"},
		cookies = cookie_dict,
	)
	c2=response.cookies.get_dict()
	cookie_dict.update(c2)    #自动登录，对cookie值进行更新

	r = requests.get(url="https://github.com/settings/repositories",cookies=cookie_dict)   #利用更新后的cookie保持会话，拿到仓库名
	soup2 = BeautifulSoup(r.text,features='html.parser')
	tags = soup2.find_all(name='a',attrs={'class':'mr-1'})
	for item in tags:
		print(item.get_text())  #打印版本仓库名称
	
if __name__=="__main__":
	login_chouti()
	login_github()