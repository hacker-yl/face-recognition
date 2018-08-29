# -*- coding:utf-8 -*-
'''
# coding=utf-8
import requests, bs4

# 获取html文档
def get_html(url):
    """get the content of the url"""
    response = requests.get(url)
    response.encoding = 'utf-8'
    return response.text



# 获取笑话
def get_certain_joke(html):
    """get the joke of the html"""
    soup = bs4.BeautifulSoup(html, "html.parser")
    joke_content = soup.select('div.content')[0].get_text()
    return joke_content


url_joke = "https://www.qiushibaike.com"
html = get_html(url_joke)
joke_content = get_certain_joke(html)
print(joke_content)




#Author: nulige

import os, time

last_worktime=0
last_idletime=0

def get_cpu():
        global last_worktime, last_idletime
        f=open("/proc/stat","r")
        line=""
        while not "cpu " in line: line=f.readline()
        f.close()
        spl=line.split(" ")
        worktime=int(spl[2])+int(spl[3])+int(spl[4])
        idletime=int(spl[5])
        dworktime=(worktime-last_worktime)
        didletime=(idletime-last_idletime)
        rate=float(dworktime)/(didletime+dworktime)
        last_worktime=worktime
        last_idletime=idletime
        if(last_worktime==0): return 0
        return rate

def get_mem_usage_percent():
    try:
        f = open('/proc/meminfo', 'r')
        for line in f:
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1])
            elif line.startswith('MemFree:'):
                mem_free = int(line.split()[1])
            elif line.startswith('Buffers:'):
                mem_buffer = int(line.split()[1])
            elif line.startswith('Cached:'):
                mem_cache = int(line.split()[1])
            elif line.startswith('SwapTotal:'):
                vmem_total = int(line.split()[1])
            elif line.startswith('SwapFree:'):
                vmem_free = int(line.split()[1])
            else:
                continue
        f.close()
    except:
        return None
    physical_percent = usage_percent(mem_total - (mem_free + mem_buffer + mem_cache), mem_total)
    virtual_percent = 0
    if vmem_total > 0:
        virtual_percent = usage_percent((vmem_total - vmem_free), vmem_total)
    return physical_percent, virtual_percent

def usage_percent(use, total):
    try:
        ret = (float(use) / total) * 100
    except ZeroDivisionError:
        raise Exception("ERROR - zero division error")
    return ret

statvfs = os.statvfs('/')

total_disk_space = statvfs.f_frsize * statvfs.f_blocks
free_disk_space = statvfs.f_frsize * statvfs.f_bfree
disk_usage = (total_disk_space - free_disk_space) * 100.0 / total_disk_space
disk_usage = int(disk_usage)
disk_tip = "硬盘空间使用率（最大100%）："+str(disk_usage)+"%"
print(disk_tip)

mem_usage = get_mem_usage_percent()
mem_usage = int(mem_usage[0])
mem_tip = "物理内存使用率（最大100%）："+str(mem_usage)+"%"
print(mem_tip)

cpu_usage = int(get_cpu()*100)
cpu_tip = "CPU使用率（最大100%）："+str(cpu_usage)+"%"
print(cpu_tip)

load_average = os.getloadavg()
load_tip = "系统负载（三个数值中有一个超过3就是高）："+str(load_average)
print(load_tip)'''


import cv2
import os


photopath = "venv/graduation.jpg"
classifier = os.getcwd()+'/haarcascade_frontalface_default.xml'

#读取图片
image = cv2.imread(photopath)

#灰度转换
#gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#获取人脸识别训练数据
face_casacade = cv2.CascadeClassifier(classifier)

#探测人脸
faces = face_casacade.detectMultiScale(image)

# 方框的颜色和粗细
color = (0,0,255)
strokeWeight = 1
#弹出框名字
windowName = "Object Detection"

while True:  #为了防止
    #人脸个数
    print(len(faces))
    for x, y, width, height in faces:
        cv2.rectangle(image, (x, y), (x + width, y + height), color, strokeWeight)

    #展示人脸识别效果
    cv2.imshow(windowName, image)

    #点击弹出的图片，按escape键，结束循环
    if cv2.waitKey(20) == 27:
        break

#循环结束后，退出程序。
exit()