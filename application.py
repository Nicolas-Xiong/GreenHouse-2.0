# -*- coding: utf-8 -*-
"""
Created on Sat Jan 11 07:37:07 2020

@author: Nicolas Xiong
"""

from flask import Flask
from flask import request, url_for, redirect,jsonify,Response,send_from_directory
from flask import render_template
from flask_sqlalchemy import SQLAlchemy# 导入扩展类
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user
from flask_login import logout_user
from flask_login import login_required, current_user
import requests  #这个是用来获取其他网站的数据，与flask自带request不一样
import numpy as np
import pandas as pd
import datetime 
import os
import sys
import click
import json
import random
import re
import cv2
import logging



#兼容处理
WIN = sys.platform.startswith('win') 
if WIN:  # 如果是 Windows 系统，使用三个斜线    
    prefix = 'sqlite:///' 
else:  # 否则使用四个斜线    
    prefix = 'sqlite:////'


app=Flask(__name__)
 
app.secret_key='d'     #按错误提示加的密钥
app.config['DEBUG']=True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = datetime.timedelta(seconds=1)

#从环境变量中读取密钥，如果没有读取到，则使用默认值
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
#设置数据库路径
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(os.path.dirname(app.root_path), os.getenv('DATABASE_FILE', 'data.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
db = SQLAlchemy(app)  # 初始化扩展，传入程序实例 app

login_manager = LoginManager(app)  # 实例化扩展类

login_manager.login_view = 'login'

logging.basicConfig(filename="flask_log.txt",format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@app.context_processor 
def inject_user():           #这个函数返回的变量（以字典键值对的形式）将会统一注入到每一个模板的上下文环境中，因此可以直接在模板中使用
    user=current_user    #当前用户信息
    return dict(user=user)

@app.route('/navigation_2', methods=['GET'])    #一小时内的数据
def navigation_2():
    return render_template('navigation_2.html')
@app.route('/data_hour',methods=['GET'])
def data_hour():
    hour_data = Greenhouse_data_hour.query.all()[0]
    #eval去除字符串的引号并执行内部内容
    dic={'temperature':eval(hour_data.Temperature_hour),'humidity':eval(hour_data.Humidity_hour),'lux':eval(hour_data.Lux_hour),'co2':eval(hour_data.Co2_hour)}
 
    return jsonify(dic)

@app.route('/navigation_2_2', methods=['GET'])   #一天内的数据
def navigation_2_2():
    return render_template('navigation_2_2.html')
@app.route('/data_day',methods=['GET'])
def data_day():  
    max_id = db.session.query(func.max(Greenhouse_data_day.id)).all()[0][0] #获取最大id值
    before_id = max_id - 24
    
    time_=[]
    temperature=[]
    humidity=[]
    lux=[]
    co2=[]
    while before_id != max_id:
          before_id = before_id + 1
          day_date = Greenhouse_data_day.query.filter(Greenhouse_data_day.id == before_id).all()[0]
          time_.append(day_date.Time+'点')
          temperature.append(int(float(day_date.Temperature)))
          humidity.append(int(float(day_date.Humidity)))
          lux.append('%.2f' % float(day_date.Lux))
          co2.append(int(float(day_date.Co2)))
    
    dic={'time':time_,'temperature':temperature,'humidity':humidity,'lux':lux,'co2':co2}
    
    return jsonify(dic)

@app.route('/video', methods=['GET'])    #视频窗口一
def video():
    return render_template('video.html')

@app.route('/video_2', methods=['GET']) #视频窗口二
def video_2():
    return render_template('video_2.html')

@app.route('/video_3', methods=['GET'])  #视频窗口三
def video_3():
    return render_template('video_3.html')

@app.route('/video_4', methods=['GET'])  #视频窗口四
def video_4():
    return render_template('video_4.html')

@app.route('/weather_true', methods=['GET','POST'])
def weather_true():
    location_id="CN101200101" #默认显示武汉的天气情况
    location_cn="武汉"
    if current_user.is_authenticated:  #以下操作需要登录，否则无法查询current_user.city_id 
        if current_user.city_id:      #如果有上次查询，显示上次查询城市
            location_id = current_user.city_id
            location_cn = current_user.city_cn
        if request.method == 'POST':    #如果有post方式的请求
            city_cn_post = request.form['search']
            city = City_data.query.filter(City_data.city_cn==city_cn_post).all()  #.all 输出列表
            if city:   #如果数据库里面查到了用户搜索的城市，显示该城市天气数据
                location_id=city[0].city_id
                location_cn=city_cn_post
                current_user.city_id=city[0].city_id
                current_user.city_cn=city_cn_post
                db.session.commit() 
            else:    #否则返回查询前的城市天气数据
                data_now = weather_data_get(weather_type='now',location=location_id)
                data_forecast = weather_data_get(weather_type='forecast',location=location_id)
                data_lifestyle = weather_data_get(weather_type='lifestyle',location=location_id)
                return render_template('weather.html',now=data_now,forecast=data_forecast,lifestyle=data_lifestyle,location_cn=location_cn,status_error=1)
            
    data_now = weather_data_get(weather_type='now',location=location_id)
    data_forecast = weather_data_get(weather_type='forecast',location=location_id)
    data_lifestyle = weather_data_get(weather_type='lifestyle',location=location_id)
    return render_template('weather.html',now=data_now,forecast=data_forecast,lifestyle=data_lifestyle,location_cn=location_cn)

@app.route('/temperature', methods=['GET', 'POST'])   #温度历史数据
def temperature():
    today = datetime.date.today()
    status=0
    date = today - datetime.timedelta(days=1) 
    if request.method == 'POST':         #如果是post方式的请求
        date_post = request.form['date']
        if date_post :
            d=list(date_post)
            date_datetime=datetime.date(int(d[0]+d[1]+d[2]+d[3]),int(d[5]+d[6]),int(d[8]+d[9]))
            if date_datetime >= datetime.date(2020,1,1) and date_datetime <= date:
                date = date_datetime
            else:
                status = 1
        else :
            status = 2
    day_date = Greenhouse_data_day.query.filter(Greenhouse_data_day.Date==str(date)).all()
    
    time_=[]
    temperature=[]
    humidity=[]
    lux=[]
    co2=[]
    for d in day_date:
        time_.append(d.Time+'点')
        temperature.append(int(float(d.Temperature)))
        humidity.append(int(float(d.Humidity)))
        lux.append('%.2f' % float(d.Lux))
        co2.append(int(float(d.Co2)))
    
    dic={'date':date,'time':time_,'temperature':temperature,'humidity':humidity,'lux':lux,'co2':co2}
    return render_template('temperature.html',data=dic,status=status)


@app.route('/temperature/download',methods=['GET'])   #温度数据数据下载
def temperature_download():  
    path = os.getcwd()  # 获取当前目录
    
    #获取某列数据
    date = Greenhouse_data_day.query.with_entities(Greenhouse_data_day.Date)  
    time = Greenhouse_data_day.query.with_entities(Greenhouse_data_day.Time)
    temperature = Greenhouse_data_day.query.with_entities(Greenhouse_data_day.Temperature)
    
    date_list = [d[0] for d in date]
    time_list = [ti[0]+' 点' for ti in time]
    temperature_list = [str(round(eval(te[0])))+' ℃' for te in temperature]  #round四舍六入五留双
    data = pd.DataFrame([date_list,time_list,temperature_list])
    data_T = pd.DataFrame(data.values.T,index=None)  #矩阵转置
    data_T.columns = ['日期','时间','温度'] #设置列标
    writer = pd.ExcelWriter('temperature.xlsx')
    data_T.to_excel(writer,index = None)  #不输出行标
    writer.save()
    
    return send_from_directory(path,filename="temperature.xlsx",as_attachment=True)
    

@app.route('/humidity', methods=['GET', 'POST'])   #湿度历史数据
def humidity():
    today = datetime.date.today()
    status=0
    date = today - datetime.timedelta(days=1) 
    if request.method == 'POST':         #如果是post方式的请求
        date_post = request.form['date']
        if date_post :
            d=list(date_post)
            date_datetime=datetime.date(int(d[0]+d[1]+d[2]+d[3]),int(d[5]+d[6]),int(d[8]+d[9]))
            if date_datetime >= datetime.date(2020,1,1) and date_datetime <= date:
                date = date_datetime
            else:
                status = 1
        else :
            status = 2
    day_date = Greenhouse_data_day.query.filter(Greenhouse_data_day.Date==str(date)).all()
    
    time_=[]
    temperature=[]
    humidity=[]
    lux=[]
    co2=[]
    for d in day_date:
        time_.append(d.Time+'点')
        temperature.append(int(float(d.Temperature)))
        humidity.append(int(float(d.Humidity)))
        lux.append('%.2f' % float(d.Lux))
        co2.append(int(float(d.Co2)))
        
    dic={'date':date,'time':time_,'temperature':temperature,'humidity':humidity,'lux':lux,'co2':co2}    
    
    return render_template('humidity.html',data=dic,status=status)

@app.route('/humidity/download',methods=['GET'])   #湿度数据数据下载
def humidity_download():  
    path = os.getcwd()  # 获取当前目录
    
    #获取某列数据
    date = Greenhouse_data_day.query.with_entities(Greenhouse_data_day.Date)  
    time = Greenhouse_data_day.query.with_entities(Greenhouse_data_day.Time)
    humidity = Greenhouse_data_day.query.with_entities(Greenhouse_data_day.Humidity)
    
    date_list = [d[0] for d in date]
    time_list = [ti[0]+' 点' for ti in time]
    humidity_list = [str(round(eval(hu[0])))+' %' for hu in humidity]  #round四舍六入五留双
    data = pd.DataFrame([date_list,time_list,humidity_list])
    data_T = pd.DataFrame(data.values.T,index=None)  #矩阵转置
    data_T.columns = ['日期','时间','湿度'] #设置列标
    writer = pd.ExcelWriter('humidity.xlsx')
    data_T.to_excel(writer,index = None)  #不输出行标
    writer.save()
    
    return send_from_directory(path,filename="humidity.xlsx",as_attachment=True)


@app.route('/lux', methods=['GET', 'POST'])   #光照度历史数据
def lux():
    today = datetime.date.today()
    status=0
    date = today - datetime.timedelta(days=1)
    if request.method == 'POST':         #如果是post方式的请求
        date_post = request.form['date']
        if date_post :
            d=list(date_post)
            date_datetime=datetime.date(int(d[0]+d[1]+d[2]+d[3]),int(d[5]+d[6]),int(d[8]+d[9]))
            if date_datetime >= datetime.date(2020,1,1) and date_datetime <= date:
                date = date_datetime
            else:
                status = 1
        else :
            status = 2
    day_date = Greenhouse_data_day.query.filter(Greenhouse_data_day.Date==str(date)).all()
    
    time_=[]
    temperature=[]
    humidity=[]
    lux=[]
    co2=[]
    for d in day_date:
        time_.append(d.Time+'点')
        temperature.append(int(float(d.Temperature)))
        humidity.append(int(float(d.Humidity)))
        lux.append('%.2f' % float(d.Lux))
        co2.append(int(float(d.Co2)))
    
    dic={'date':date,'time':time_,'temperature':temperature,'humidity':humidity,'lux':lux,'co2':co2}
    
    return render_template('lux.html',data=dic,status=status)

@app.route('/lux/download',methods=['GET'])   #光照度数据数据下载
def lux_download():  
    path = os.getcwd()  # 获取当前目录
    
    #获取某列数据
    date = Greenhouse_data_day.query.with_entities(Greenhouse_data_day.Date)  
    time = Greenhouse_data_day.query.with_entities(Greenhouse_data_day.Time)
    lux = Greenhouse_data_day.query.with_entities(Greenhouse_data_day.Lux)
    
    date_list = [d[0] for d in date]
    time_list = [ti[0]+' 点' for ti in time]
    lux_list = [str(round(eval(lu[0]),2))+' klux' for lu in lux]  #round四舍六入五留双
    data = pd.DataFrame([date_list,time_list,lux_list])
    data_T = pd.DataFrame(data.values.T,index=None)  #矩阵转置
    data_T.columns = ['日期','时间','湿度'] #设置列标
    writer = pd.ExcelWriter('lux.xlsx')
    data_T.to_excel(writer,index = None)  #不输出行标
    writer.save()
    
    return send_from_directory(path,filename="lux.xlsx",as_attachment=True)

@app.route('/carbon', methods=['GET', 'POST'])   #CO2历史数据
def carbon():
    today = datetime.date.today()
    status=0
    date = today - datetime.timedelta(days=1)
    if request.method == 'POST':         #如果是post方式的请求
        date_post = request.form['date']
        if date_post :
            d=list(date_post)
            date_datetime=datetime.date(int(d[0]+d[1]+d[2]+d[3]),int(d[5]+d[6]),int(d[8]+d[9]))
            if date_datetime >= datetime.date(2020,1,1) and date_datetime <= date:
                date = date_datetime
            else:
                status = 1
        else :
            status = 2
    day_date = Greenhouse_data_day.query.filter(Greenhouse_data_day.Date==str(date)).all()
    
    time_=[]
    temperature=[]
    humidity=[]
    lux=[]
    co2=[]
    for d in day_date:
        time_.append(d.Time+'点')
        temperature.append(int(float(d.Temperature)))
        humidity.append(int(float(d.Humidity)))
        lux.append('%.2f' % float(d.Lux))
        co2.append(int(float(d.Co2)))
    
    dic={'date':date,'time':time_,'temperature':temperature,'humidity':humidity,'lux':lux,'co2':co2}
    
    return render_template('carbon.html',data=dic,status=status)

@app.route('/carbon/download',methods=['GET'])   #CO2数据数据下载
def carbon_download():  
    path = os.getcwd()  # 获取当前目录
    
    #获取某列数据
    date = Greenhouse_data_day.query.with_entities(Greenhouse_data_day.Date)  
    time = Greenhouse_data_day.query.with_entities(Greenhouse_data_day.Time)
    carbon = Greenhouse_data_day.query.with_entities(Greenhouse_data_day.Co2)
    
    date_list = [d[0] for d in date]
    time_list = [ti[0]+' 点' for ti in time]
    carbon_list = [str(round(eval(ca[0])))+' ppm' for ca in carbon]  #round四舍六入五留双
    data = pd.DataFrame([date_list,time_list,carbon_list])
    data_T = pd.DataFrame(data.values.T,index=None)  #矩阵转置
    data_T.columns = ['日期','时间','CO2含量'] #设置列标
    writer = pd.ExcelWriter('carbon.xlsx')
    data_T.to_excel(writer,index = None)  #不输出行标
    writer.save()
    
    return send_from_directory(path,filename="carbon.xlsx",as_attachment=True)

@app.route('/profile', methods=['GET']) #显示简介
def profile():
    users=User.query.filter(User.id!=1).all()
    return render_template('profile.html',users=users)

@app.route('/settings', methods=['GET', 'POST']) #更新用户名
@login_required # 登录保护
def settings():    
    if request.method == 'POST':         #如果是post方式的请求
        username = request.form['username']
        profile = request.form['profile']
        goback = request.form['submit']
        if goback=='返回':             
            return redirect(url_for('navigation_2'))
        if len(username)>20 or len(profile)>100:
            return render_template('settings.html',status_error=2)  #用户名或者简介过长
        if not username or not profile: 
            if not username and not profile:                  
                return render_template('settings.html',status_error=1)   #什么也没有改
            elif username :
                if len(User.query.filter(User.username==username).all()): 
                    return render_template('settings.html',status_error=3)  #用户名已被注册
                current_user.username = username 
                db.session.commit() 
                return render_template('settings.html',status_=1)  #更改了用户名
            elif profile:
                current_user.profile = profile   
                db.session.commit() 
                return render_template('settings.html',status_=2)  #更改了简介 
        current_user.username = username 
        current_user.profile = profile  
        db.session.commit()
        return render_template('settings.html',status_=3)  #更改了用户名和简介 
    return render_template('settings.html')

@app.route('/', methods=['GET', 'POST'])   #登录函数
def login():    
    if request.method == 'POST':        
        username = request.form['username']        
        password = request.form['password']
        visitor = request.form['submit']
        if visitor=='游客':            #游客登录  
            logout_user() #若已经登录则会登出
            return redirect(url_for('navigation_2'))
        if not username or not password or len(username)>20:   #未输入或者输入过长     
            #flash('无效的输入')           
            return render_template('login.html',status_error=1) 
        if len(User.query.filter(User.username==username).all()):            #.all输出为列表
            user = User.query.filter(User.username==username).all()[0]       # 验证用户名和密码是否一致  
        else:
            user=None
        if user!=None and user.validate_password(password):      
            login_user(user)  # 登入用户            
            #flash('登录成功')           
            return redirect(url_for('navigation_2'))  #登录成功  
        #flash('用户名或密码错误')  # 如果验证失败，显示错误消息        
        return render_template('login.html',status_error=2)  # 用户名或者密码错误
    return render_template('login.html') 

@app.route('/sign_up', methods=['GET','POST'])   #注册函数
def sign_up():
    if request.method == 'POST': 
        email = request.form['email']    
        username = request.form['username']
        password = request.form['password']
        sex = request.form['sex']
        if not email or not username or not password or len(email)>20 or len(username)>20:            
            return render_template('sign_up.html',status_error=1)  #未输入或者输入过长 
        if len(User.query.filter(User.email==email).all()): 
            return render_template('sign_up.html',status_error=3)  #邮箱已被注册
        if len(User.query.filter(User.username==username).all()): 
            return render_template('sign_up.html',status_error=4)  #用户名已被注册
        if sex !='男' and sex !='女':
            return render_template('sign_up.html',status_error=2)  #性别选择错误
        elif sex == '男':
            number = random.randint(1,6)
        else:
            number = random.randint(7,12)
        password_hash=generate_password_hash(password)
        date=datetime.date.today()
        authority='用户'
        profile='嗨，我是'+username+'，这个网站的'+authority 
        user = User(username=username, password_hash=password_hash,number=number,email=email,authority=authority,date=date,profile=profile)        
        db.session.add(user)  #添加用户到数据库
        db.session.commit()  # 提交数据库会话
        login_user(user)  # 登入用户
        return redirect(url_for('navigation_2'))  #登录成功
    return render_template('sign_up.html')

@app.route('/forgot_password', methods=['GET','POST'])  #修改密码函数
def forgot_password():
    if request.method == 'POST': 
        email = request.form['email']        
        password1 = request.form['password1']
        password2 = request.form['password2']
        if not email or not password1 or not password2 or len(email)>20:            
            return render_template('forgot_password.html',status_error=1) 
        if password1 != password2:
            return render_template('forgot_password.html',status_error=3) 
        if len(User.query.filter(User.email==email).all()):            #.all输出为列表
            user = User.query.filter(User.email==email).all()[0]       # 验证用户名和密码是否一致  
            user.password_hash=generate_password_hash(password1) #修改密码
            db.session.commit()  # 提交数据库会话
            login_user(user)  # 登入用户 
            return redirect(url_for('navigation_2'))  #登录成功
        return render_template('forgot_password.html',status_error=2) 
    return render_template('forgot_password.html')


@app.route('/404', methods=['GET'])   #404页面
def _404():
    return render_template('404.html')
@app.errorhandler(404)  # 传入要处理的错误代码 
def page_not_found(e):  # 接受异常对象作为参数      
    return render_template('404.html'), 404  # 返回模板和状态码

@app.route('/logout')      #登出
@login_required  # 登录保护
def logout():    
    logout_user()  # 登出用户       
    return redirect(url_for('login'))  # 重定向回首页


@app.cli.command()  # 注册为命令 
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项 
def initdb(drop):    
    """Initialize the database."""    
    if drop:  # 判断是否输入了选项        
        db.drop_all()    
    db.create_all()    
    click.echo('Initialized database.')  # 输出提示信息
        
@app.cli.command() 
@click.option('--username', prompt=True, help='The username used to login.') 
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.') 
def admin(username, password):    
    """Create user."""    
    db.create_all()
    user = User.query.first()    
    if user is not None:        
        click.echo('Updating user...')        
        user.username = username        
        user.set_password(password)  # 设置密码    
    else:        
        click.echo('Creating user...')        
        user = User(username=username, name='Admin')        
        user.set_password(password)  # 设置密码        
        db.session.add(user)
    db.session.commit()  # 提交数据库会话    
    click.echo('Done.')


@app.cli.command() 
def forge():    
    """Generate fake data."""    
    db.create_all()
    
    #添加城市数据到数据库
    csv_data = pd.read_csv("china-city-list.csv")
    for i in range(1,3241):
        city_data = City_data(city_id=csv_data.iloc[i,][0], city_cn=csv_data.iloc[i,][2]) 
        db.session.add(city_data)
    
    
    #添加初始用户数据
    users=[
             {'username':'熊子臣','password':'12345678','number':'0','email':'3494775639@qq.xyz','authority':'管理员'},
             {'username':'张三','password':'12345678','number':'1','email':'3494775639@qq.com','authority':'用户'},
             {'username':'李四','password':'12345678','number':'5','email':'','authority':'用户'}
        ]
    for u in users:     
         password_hash=generate_password_hash(u['password'])
         date=datetime.date.today()
         profile='嗨，我是'+u['username']+'，这个网站的'+u['authority']
         user = User(username=u['username'], password_hash=password_hash,number=u['number'],email=u['email'],authority=u['authority'],date=date,profile=profile)        
         db.session.add(user)
         
         
    db.session.commit()    
    click.echo('Done.')
    
@login_manager.user_loader 
def load_user(user_id):  # 创建用户加载回调函数，接受用户 ID 作为参数    
    user = User.query.get(int(user_id))  # 用 ID 作为 User 模型的主键查询对应的用户    
    return user  # 返回用户对象



class User(db.Model,UserMixin):  # 表名将会是 user（自动生成，小写处理）    
    id = db.Column(db.Integer, primary_key=True)  # 主键    
    username = db.Column(db.String(20))  # 用户名    
    password_hash = db.Column(db.String(128))  # 密码散列值
    number = db.Column(db.String(20))   #图片编号
    email = db.Column(db.String(20)) #邮箱
    authority = db.Column(db.String(20)) #权限
    date = db.Column(db.String(20)) #注册日期
    profile = db.Column(db.Text)  #简介 长文本
    city_id = db.Column(db.String(20))  # 最后一次查询的城市id数据 
    city_cn = db.Column(db.String(20))  # 最后一次查询的城市中文名称
    def set_password(self, password):  # 用来设置密码的方法，接受密码作为参数        
         self.password_hash = generate_password_hash(password)  # 将生成的密码保持到对应字段
    def validate_password(self, password):  # 用于验证密码的方法，接受密码作为参数        
        return check_password_hash(self.password_hash, password)  # 返回布尔值

class Greenhouse_data_day(db.Model):  #以天计数的表   
    id = db.Column(db.Integer, primary_key=True)  # 主键   
    Date = db.Column(db.String(10))  #日期
    Time = db.Column(db.String(4))  # 时间    
    Temperature = db.Column(db.String(10))  # 温度
    Humidity = db.Column(db.String(10))  # 湿度
    Lux = db.Column(db.String(10))  # 光照度
    Co2 = db.Column(db.String(10))  #CO2含量
    
class Greenhouse_data_hour(db.Model):  #以小时计数的表
    id = db.Column(db.Integer, primary_key=True)  # 主键      
    Temperature_hour = db.Column(db.String(600))  # 温度
    Humidity_hour = db.Column(db.String(600))  # 湿度
    Lux_hour = db.Column(db.String(600))  # 光照度
    Co2_hour = db.Column(db.String(600))  #CO2含量
    
class City_data(db.Model):  # 表名将会是 city_data   
    id = db.Column(db.Integer, primary_key=True)  # 主键    
    city_id = db.Column(db.String(20))  # 城市id数据    
    city_cn = db.Column(db.String(10))  # 城市中文名称

class VideoCamera():   #视频获取处理类
    source_site="http://ivi.bupt.edu.cn/hls/cctv1hd.m3u8"
    def __init__(self):
        self.cap = cv2.VideoCapture(self.source_site) 
    
    def __del__(self):
        self.cap.release()
    
    def get_frame(self):
        success, image = self.cap.read()
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()
    
def gen(camera):   #视频传递函数
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def weather_data_get(weather_type,location):     #天气数据获取函数
    link ="https://free-api.heweather.net/s6/weather/"+weather_type+"?location="+location+"&key=002960780ab5402ba6c28bf9857d9594"
    headers={'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'}
    night_exist=['100','103','104','300','301','406','407']  #有夜间标志的图标编号
    lifestyle_dict={'comf':'舒适度指数','cw':'洗车指数','drsg':'穿衣指数','flu':'感冒指数','sport':'运动指数','trav':'旅游指数','uv':'紫外线指数','air':'空气污染扩散条件指数','ac':'空调开启指数','ag':'过敏指数','gl':'太阳镜指数','mu':'化妆指数','airc':'晾晒指数','ptfc':'交通指数','fsh':'钓鱼指数','spi':'防晒指数'}
    
    r= requests.get(link,headers=headers)  #实况天气获取与处理
    text=r.text
    dictionary=json.loads(text)
    request_data = dictionary['HeWeather6'][0]
    #print(request_data['status'])
    app.logger.info(request_data['status'])   #输出通知日志
    if request_data['status'] != 'ok':
        app.logger.error(request_data['status'])   #输出错误日志
        return 'status_error'
    
    if weather_type == 'now':
        data_now=request_data['now']
        time_now = datetime.datetime.now()  #为夜间标志添加  n
        if time_now.hour <6 or time_now.hour>=18:
            for n1 in night_exist:
                 if data_now['cond_code'] == n1:
                     data_now['cond_code']=data_now['cond_code']+'n'
        return data_now
    
    if weather_type == 'forecast':
        data_forecast=request_data['daily_forecast']
        i=0          #为夜间标志添加  n
        for li in data_forecast:
            for n2 in night_exist:
                if li['cond_code_n'] == n2:
                    data_forecast[i]['cond_code_n']=data_forecast[i]['cond_code_n']+'n'
            i=i+1
        return data_forecast
            
    if weather_type == 'lifestyle':
        data_lifestyle=request_data['lifestyle']
        j=0
        for st in data_lifestyle:
            data_lifestyle[j]['type']=lifestyle_dict[data_lifestyle[j]['type']]
            j=j+1
        return data_lifestyle
    app.logger.error('error')
    return 'error'

def limit(mi,ma,data):   #数据大小限制函数
    if data < mi:
        data = mi
    if data > ma:
        data = ma
    return data
















