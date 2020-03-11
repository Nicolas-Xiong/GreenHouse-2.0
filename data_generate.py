# -*- coding: utf-8 -*-
"""
Created on Sat Feb 15 11:18:41 2020

@author: Nicolas Xiong
"""

import numpy as np
import json
import datetime
import time
import sqlite3  
import random


def parameter_create():   #参数生成函数
    temperature_min = random.randint(5,15)
    temperature_max = random.randint(25,35)
    temperature_A = (temperature_max - temperature_min)/2
    temperature_B = (temperature_max + temperature_min)/2
    
    humidity_min = random.randint(50,60)
    humidity_max = random.randint(90,100)
    humidity_A = (humidity_max - humidity_min)/2
    humidity_B = (humidity_max + humidity_min)/2
    
    lux_B = random.randint(1000,2500)
    lux_max = random.randint(50000,80000)
    lux_A = lux_max -lux_B 

    co2_B = random.randint(500,700)
    co2_min = random.randint(100,300)
    co2_A = co2_B - co2_min
    return {'temperature':[temperature_A,temperature_B],'humidity':[humidity_A,humidity_B],'lux':[lux_A,lux_B],'co2':[co2_A,co2_B]}

def limit(mi,ma,data):   #数据大小限制函数
    if data < mi:
        data = mi
    if data > ma:
        data = ma
    return data


#连接到一个现有的数据库。如果数据库不存在，那么它就会被创建，最后将返回一个数据库对象。
db = sqlite3.connect('data.db') 
print ("成功连接数据库");

#创建一个cursor
c = db.cursor()   
 
#Greenhouse_data表为空则添加虚拟数据，否则跳过
id_Cursor = c.execute("SELECT MAX(id) FROM greenhouse_data_day")
day = id_Cursor.fetchall()   #筛选出来必须立马赋值
id_Cursor1 = c.execute("SELECT MAX(id) FROM greenhouse_data_hour")
hour = id_Cursor1.fetchall()  #筛选出来必须立马赋值

print(day)
print(hour)

#初始化数据
time_forge = datetime.datetime(2020,1,1,0,0,0,0)  #虚拟时间
time_forge_recorder = time_forge  #虚拟时间记录
parameter = parameter_create()  #参数创建
id_recorder = day[0][0]  #greenhouse_data_day中最大的id

if not day[0][0]:
    print('Greenhouse_data_day表为空，开始添加过往数据')
    id_recorder = 0
    
    #加速时间
    while 1:  
        time_now = datetime.datetime.now()
        id_recorder = id_recorder + 1
        if time_forge.day - time_forge_recorder.day:  #过一天改变一次模型的参数
            time_forge_recorder = time_forge  #跟新虚拟时间记录
            parameter = parameter_create()  #跟新参数
        
        temperature = parameter['temperature'][0]*np.sin(np.pi*time_forge.hour/12 - np.pi/2) + parameter['temperature'][1]
        temperature_l =limit(0,40,temperature+ random.randint(-1,1))
    
        humidity = parameter['humidity'][0]*np.sin(np.pi*time_forge.hour/12 + np.pi/2) + parameter['humidity'][1]
        humidity_l = limit(0,100,humidity + random.randint(-5,5))
    
        
        if time_forge.hour >= 6 and time_forge.hour < 18:
                lux = parameter['lux'][0]*np.sin(np.pi*time_forge.hour/12 - np.pi/2) + parameter['lux'][1] + random.randint(-1000,1000)
                co2 = parameter['co2'][0]*np.sin(np.pi*time_forge.hour/12 + np.pi/2) + parameter['co2'][1] + random.randint(-50,50)
        else :
                lux = parameter['lux'][1] + random.randint(-1000,1000)
                co2 = parameter['co2'][1]+ random.randint(-50,50)
        lux_l = limit(0,80000,lux)
        lux_l = lux_l/1000
        co2_l = limit(0,800,co2)
        
        c.execute("INSERT INTO greenhouse_data_day (id ,date ,time,temperature ,humidity ,lux ,co2) VALUES ("+str(id_recorder)+", '"+str(time_forge.date())+"', '"+str(time_forge.hour)+"', '"+str(temperature_l)+"', '"+str(humidity_l)+"' ,'"+str(lux_l)+"' ,'"+str(co2_l)+"')");
              
        if time_forge.year == time_now.year and time_forge.month == time_now.month and time_forge.day == time_now.day and time_forge.hour == time_now.hour:
            break  
        time_forge = time_forge + datetime.timedelta(hours=1)  #循环一次虚拟时间加一小时
        print(time_forge)
         
    #提交数据
    db.commit()
    print ("Greenhouse_data_day表添加过往数据成功");

if not hour[0][0]:
    print('Greenhouse_data_hour表为空，开始添加初始化数据')
    c.execute("INSERT INTO greenhouse_data_hour (id ,temperature_hour ,humidity_hour ,lux_hour ,co2_hour) VALUES (1 ,0 ,0 ,0 ,0)");
    
    #提交数据
    db.commit()
    print ("Greenhouse_data_hour表添加初始化数据成功");

#关闭数据库连接
db.close()


now = datetime.datetime.now() 
minute_recorder = now  #记录开始运行时的时期，之后每分钟跟新一次
hour_recorder = now #记录开始运行时的时期，之后每小时跟新一次
date_recorder = now#记录开始运行时的日期

#正常时间
while 1:
    print("数据生成准备中，现在是：%d时%d分" %(now.hour,now.minute))
    time.sleep(10) 
    now = datetime.datetime.now()
    if now.minute - minute_recorder.minute :  #过一分钟生成一次数据
          minute_recorder = now  #跟新记录时间
          print('分钟记录跟新')
          
          if now.day - date_recorder.day :  #过一天改变一次模型的参数
              date_recorder = now #跟新日期记录
              parameter = parameter_create()  #每日跟新参数
              print('日期记录和参数跟新')
          
          #生成从此刻起，前一个小时每分钟的数据
          hour_before = now - datetime.timedelta(hours=1)  
          x=[]
          while 1:
              hour_before = hour_before + datetime.timedelta(minutes=1)
              x.append(float(hour_before.hour + hour_before.minute/60))
              if hour_before.hour == now.hour and hour_before.minute == now.minute:
                  break  
          x = np.asarray(x)  #将列表变为numpy数组
    
          temperature = parameter['temperature'][0]*np.sin(np.pi*x/12 - np.pi/2) + parameter['temperature'][1]
          temperature_c = [limit(0,40,tem + random.randint(-1,1)) for tem in temperature]
    
          humidity = parameter['humidity'][0]*np.sin(np.pi*x/12 + np.pi/2) + parameter['humidity'][1]
          humidity_c = [limit(0,100,hum + random.randint(-5,5)) for hum in humidity]
    
          lux_c=[]
          co2_c=[]
          for x_ in x:
                if x_ >= 6 and x_ < 18:
                    lux = parameter['lux'][0]*np.sin(np.pi*x_/12 - np.pi/2) + parameter['lux'][1] + random.randint(-1000,1000)
                    co2 = parameter['co2'][0]*np.sin(np.pi*x_/12 + np.pi/2) + parameter['co2'][1] + random.randint(-50,50)
                else :
                    lux = parameter['lux'][1] + random.randint(-1000,1000)
                    co2 = parameter['co2'][1]+ random.randint(-50,50)
                lux = limit(0,80000,lux)
                co2 = limit(0,800,co2)
                lux_c.append(lux/1000)
                co2_c.append(co2)
                
                
          db = sqlite3.connect('data.db') 
          print ("成功连接数据库");

          #创建一个cursor
          c = db.cursor()   
          
          #跟新greenhouse_data_hour中的存储内容
          c.execute("UPDATE greenhouse_data_hour SET temperature_hour = '"+str(temperature_c)+"' ,humidity_hour = '"+str(humidity_c)+"',lux_hour = '"+str(lux_c)+"',co2_hour = '"+str(co2_c)+"' where id=1")      
        
          #提交数据
          db.commit()
          print ("Greenhouse_data_hour表跟新数据成功");
        
          if now.hour - hour_recorder.hour :  #每过一小时生成一次对应数据
              id_recorder = id_recorder + 1
              hour_recorder = now
              print('小时记录跟新')
              
              temperature = parameter['temperature'][0]*np.sin(np.pi*now.hour/12 - np.pi/2) + parameter['temperature'][1]
              temperature_l =limit(0,40,temperature+ random.randint(-1,1))
    
              humidity = parameter['humidity'][0]*np.sin(np.pi*now.hour/12 + np.pi/2) + parameter['humidity'][1]
              humidity_l = limit(0,100,humidity + random.randint(-5,5))
    
        
              if now.hour >= 6 and now.hour < 18:
                  lux = parameter['lux'][0]*np.sin(np.pi*now.hour/12 - np.pi/2) + parameter['lux'][1] + random.randint(-1000,1000)
                  co2 = parameter['co2'][0]*np.sin(np.pi*now.hour/12 + np.pi/2) + parameter['co2'][1] + random.randint(-50,50)
              else :
                  lux = parameter['lux'][1] + random.randint(-1000,1000)
                  co2 = parameter['co2'][1]+ random.randint(-50,50)
              lux_l = limit(0,80000,lux)
              lux_l = lux_l/1000
              co2_l = limit(0,800,co2)
        
              c.execute("INSERT INTO greenhouse_data_day (id ,date ,time,temperature ,humidity ,lux ,co2) VALUES ("+str(id_recorder)+", '"+str(now.date())+"', '"+str(now.hour)+"', '"+str(temperature_l)+"', '"+str(humidity_l)+"' ,'"+str(lux_l)+"' ,'"+str(co2_l)+"')");
              
              #提交数据
              db.commit()
              print ("Greenhouse_data_day表添加数据成功");
            
          #关闭数据库连接
          db.close()
            
            
        































