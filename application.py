# -*- coding: utf-8 -*-
"""
Created on Sat Jan 11 07:37:07 2020

@author: Nicolas Xiong
"""

from flask import Flask
from flask import request, url_for, redirect, flash,jsonify
from flask import render_template
from flask_sqlalchemy import SQLAlchemy  # 导入扩展类
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user
from flask_login import logout_user
from flask_login import login_required, current_user
from bs4 import BeautifulSoup
import requests#这个是用来获取其他网站的数据，与flask自带request不一样
from datetime import timedelta
import os
import sys
import click
import json
import time
import random
import re



#兼容处理
WIN = sys.platform.startswith('win') 
if WIN:  # 如果是 Windows 系统，使用三个斜线    
    prefix = 'sqlite:///' 
else:  # 否则使用四个斜线    
    prefix = 'sqlite:////'


app=Flask(__name__)
 
app.secret_key='d'     #按错误提示加的密钥
app.config['DEBUG']=True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)

#从环境变量中读取密钥，如果没有读取到，则使用默认值
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(os.path.dirname(app.root_path), os.getenv('DATABASE_FILE', 'data.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
db = SQLAlchemy(app)  # 初始化扩展，传入程序实例 app

login_manager = LoginManager(app)  # 实例化扩展类

login_manager.login_view = 'login'



@app.context_processor 
def inject_user():           #这个函数返回的变量（以字典键值对的形式）将会统一注入到每一个模板的上下文环境中，因此可以直接在模板中使用
    user = User.query.first()    
    return dict(user=user)

@app.route('/')
def navigation():
    return render_template('navigation.html')


@app.route('/plot', methods=['GET'])
def plot_():     
    return render_template('plot.html')


@app.route('/wheather')
def wheather():
    return render_template('wheather.html')


@app.route('/index', methods=['GET', 'POST'])
@login_required  # 登录保护
def index():     
    if request.method == 'POST':  # 判断是否是 POST 请求    
        if not current_user.is_authenticated:  # 如果当前用户未认证            
            return redirect(url_for('index'))  # 重定向到主页
        # 获取表单数据        
        title = request.form.get('title')  # 传入表单对应输入字段的 name 值        
        year = request.form.get('year')
      # 验证数据        
        if not title or not year or len(year) > 4 or len(title) > 60:            
            flash('Invalid input.')  # 显示错误提示            
            return redirect(url_for('index'))  # 重定向回主页 
        # 保存表单数据到数据库        
        movie = Movie(title=title, year=year)  # 创建记录        
        db.session.add(movie)  # 添加到数据库会话        
        db.session.commit()  # 提交数据库会话        
        flash('Item created.')  # 显示成功创建的提示        
        return redirect(url_for('index'))  # 重定向回主页        
    movies = Movie.query.all()  # 读取所有电影记录
    return render_template('index.html', movies=movies)

@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST']) 
@login_required  # 登录保护
def edit(movie_id):    
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':  # 处理编辑表单的提交请求        
        title = request.form['title']        
        year = request.form['year']
        if not title or not year or len(year) > 4 or len(title) > 60:            
            flash('Invalid input.')            
            return redirect(url_for('edit', movie_id=movie_id))  # 重定向回对应的编辑页面
        movie.title = title  # 更新标题        
        movie.year = year  # 更新年份        
        db.session.commit()  # 提交数据库会话        
        flash('Item updated.')        
        return redirect(url_for('index'))  # 重定向回主页
    return render_template('edit.html', movie=movie)  # 传入被编辑的电影记录

@app.route('/movie/delete/<int:movie_id>', methods=['POST'])  # 限定只接受 POST 请求
@login_required  # 登录保护
def delete(movie_id):    
    movie = Movie.query.get_or_404(movie_id)  # 获取电影记录    
    db.session.delete(movie)  # 删除对应的记录    
    db.session.commit()  # 提交数据库会话    
    flash('Item deleted.')   
    return redirect(url_for('index'))  # 重定向回主页

@app.route('/login', methods=['GET', 'POST']) 
def login():    
    if request.method == 'POST':        
        username = request.form['username']        
        password = request.form['password']
        if not username or not password:            
            flash('Invalid input.')           
            return redirect(url_for('login'))
        user = User.query.first()        # 验证用户名和密码是否一致        
        if username == user.username and user.validate_password(password):           
            login_user(user)  # 登入用户            
            flash('Login success.')           
            return redirect(url_for('index'))  # 重定向到主页
        flash('Invalid username or password.')  # 如果验证失败，显示错误消息        
        return redirect(url_for('login'))  # 重定向回登录页面
    return render_template('login.html')

@app.route('/logout') 
@login_required  # 登录保护
def logout():    
    logout_user()  # 登出用户    
    flash('Goodbye.')    
    return redirect(url_for('index'))  # 重定向回首页

@app.route('/settings', methods=['GET', 'POST']) #更新用户名
@login_required # 登录保护
def settings():    
    if request.method == 'POST':        
        name = request.form['name']
        if not name or len(name) > 20:            
            flash('Invalid input.')            
            return redirect(url_for('settings'))
        current_user.name = name        
        # current_user 会返回当前登录用户的数据库记录对象,等同于下面的用法              
        # user = User.query.first()        
        # user.name = name        
        db.session.commit()        
        flash('Settings updated.')       
        return redirect(url_for('index'))
    return render_template('settings.html')


@app.route('/weather',methods=['POST','GET'])   #用于输出传输json到前端
def weather():
    link = 'http://www.weather.com.cn/weather/101200101.shtml'
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134'}
    r=requests.get(link,headers=headers)     
    response = r.content.decode('utf-8')#中文解码
    position=re.findall('<a href="'+link+'" target="_blank">(.*)</a>',response)#获取位置信息
        
    soup=BeautifulSoup(response,"html.parser")#解析网页文本
    text=soup.find_all(text=re.compile("observe24h_data"))#寻找有相关内容的标签里的内容
    wheather_data=str(text).lstrip(r"['\nvar observe24h_data = ").rstrip(r";\n']")#转为字符串类型，去除非json格式数据(去头去尾) 
    json_=json.loads(wheather_data)
        
    #获取列表
    temperature=[]
    time_=[]
    humidity=[]
    air_quality=[]
    for t in json_['od']['od2']:
        time_.append(str(t['od21'])+'点')#获取时间列表
        temperature.append(t['od22']) #获取温度列表
        humidity.append(t['od27']) #获取湿度列表
        air_quality.append(t['od28'])#获取空气质量列表
            
    #翻转列表，重构字典格式
    dic={}
    dic['position']=position
    dic['time']=time_[::-1]#反向赋值
    dic['temperature']=temperature[::-1]  
    dic['humidity']=humidity[::-1]
    dic['air_quality']=air_quality[::-1]

    
    return jsonify(dic)  #以json字符串格式发送数据




@app.errorhandler(404)  # 传入要处理的错误代码 
def page_not_found(e):  # 接受异常对象作为参数      
    return render_template('404.html'), 404  # 返回模板和状态码

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
    
    name = 'Xiong'
    movies = [
                           {'title': 'My Neighbor Totoro', 'year': '1988'},
                           {'title': 'Dead Poets Society', 'year': '1989'},    
                           {'title': 'A Perfect World', 'year': '1993'},    
                           {'title': 'Leon', 'year': '1994'},    
                           {'title': 'Mahjong', 'year': '1996'},    
                           {'title': 'Swallowtail Butterfly', 'year': '1996'},    
                           {'title': 'King of Comedy', 'year': '1999'},    
                           {'title': 'Devils on the Doorstep', 'year': '1999'},    
                           {'title': 'WALL-E', 'year': '2008'},
                           {'title': 'The Pork of Music', 'year': '2012'}
                           ]
    
    user = User(name=name)    
    db.session.add(user)    
    for m in movies:        
         movie = Movie(title=m['title'], year=m['year'])        
         db.session.add(movie)
         
    db.session.commit()    
    click.echo('Done.')
    
@login_manager.user_loader 
def load_user(user_id):  # 创建用户加载回调函数，接受用户 ID 作为参数    
    user = User.query.get(int(user_id))  # 用 ID 作为 User 模型的主键查询对应的用户    
    return user  # 返回用户对象



class User(db.Model,UserMixin):  # 表名将会是 user（自动生成，小写处理）    
    id = db.Column(db.Integer, primary_key=True)  # 主键    
    name = db.Column(db.String(20))  # 名字
    username = db.Column(db.String(20))  # 用户名    
    password_hash = db.Column(db.String(128))  # 密码散列值
    def set_password(self, password):  # 用来设置密码的方法，接受密码作为参数        
         self.password_hash = generate_password_hash(password)  # 将生成的密码保持到对应字段
    def validate_password(self, password):  # 用于验证密码的方法，接受密码作为参数        
        return check_password_hash(self.password_hash, password)  # 返回布尔值

    
class Movie(db.Model):  # 表名将会是 movie    
    id = db.Column(db.Integer, primary_key=True)  # 主键    
    title = db.Column(db.String(60))  # 电影标题    
    year = db.Column(db.String(4))  # 电影年份
























