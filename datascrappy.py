# -*- coding: utf-8 -*-
"""
Created on Sat Feb 15 11:18:41 2020

@author: Nicolas Xiong
"""

import requests
import re
from bs4 import BeautifulSoup
import json
import datetime
import time
import sqlite3  


#连接到一个现有的数据库。如果数据库不存在，那么它就会被创建，最后将返回一个数据库对象。
db = sqlite3.connect('data.db') 
print ("成功连接数据库");

#创建一个cursor
c = db.cursor()   
 

id_Cursor = c.execute("SELECT id FROM weather_")
if len(list(id_Cursor))==0 :
    #执行SQL语句，为weather_表添加数据
    c.execute("INSERT INTO weather_ (id ,date ,time,temperature ,humidity ,air_quality) \
              VALUES (0, 0, 25, 0, 0 ,0 )");
    db.commit()
    print ("weather_表添加数据成功");

db.close()


while 1:
    now = datetime.datetime.now()
    print("抓取准备中，现在是：%d时%d分" %(now.hour,now.minute))
    time.sleep(5) 
    #两分钟抓取一次
    if now.minute % 2 == 0:
          #爬取网页
          link = 'http://www.weather.com.cn/weather/101200101.shtml'
          headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134'}
          r=requests.get(link,headers=headers)     
          response = r.content.decode('utf-8')#中文解码

          #解析网页
          soup=BeautifulSoup(response,"html.parser")#解析网页文本
          text=soup.find_all(text=re.compile("observe24h_data"))#寻找有相关内容的标签里的内容
          wheather_data=str(text).lstrip(r"['\nvar observe24h_data = ").rstrip(r";\n']")#转为字符串类型，去除非json格式数据(去头去尾) 
          json_=json.loads(wheather_data)#化json数据为字典
        
          #整理出天气数据列表
          temperature=[]
          time_=[]
          humidity=[]
          air_quality=[]
          for t in json_['od']['od2']:
              time_.append(t['od21'])#获取时间列表
              temperature.append(t['od22']) #获取温度列表
              humidity.append(t['od27']) #获取湿度列表
              air_quality.append(t['od28'])#获取空气质量列表
              
          #由于最新空气质量为空，故取前一小时数据，造成0点才可得到昨天23点的数据，故需要日期更正
          today=datetime.date.today()
          if int(time_[1]) == 23:
              today=today-datetime.timedelta(days=1)
              
          #连接到一个现有的数据库。如果数据库不存在，那么它就会被创建，最后将返回一个数据库对象。
          db = sqlite3.connect('data.db') 
          print ("成功连接数据库");

          #创建一个cursor
          c = db.cursor() 
          
          #数据写入数据库
          id_Cursor = c.execute("SELECT MAX(id) FROM weather_")  #获取weather_中的id数据
          id_tuple=id_Cursor.fetchall()[0]  #fetchall()获取id_Cursor中列表套元组格式的数据
          id=id_tuple[0]
          print("已添加id数:"+str(id_tuple[0]))
          
          data_today_Cursor=c.execute("SELECT time FROM weather_ WHERE date LIKE'"+str(today)+"'")
          status=0
          for data_today in data_today_Cursor:
              if data_today[0] == time_[1]:
                  status=1

          if status :
              print("时间数据重复，数据未写入")
          else:
              c.execute("INSERT INTO weather_ (id, date, time, temperature, humidity, air_quality) \
                         VALUES ('"+str(id+1)+"', '"+str(today)+"', '"+str(time_[1])+"', '"+str(temperature[1])+"', '"+str(humidity[1])+"', '"+str(air_quality[1])+"')");   
              db.commit()
              print("数据库写入成功")
          
          #关闭数据库连接
          db.close()
          
          #抓完后睡一段时间（睡过这一分钟）
          print("睡眠中。。。")
          time.sleep(100)































