#!/usr bin/env python3
# -*- coding: utf-8 -*-

'''
    Python多线程解析下载网易云音乐
    只兼容Python3
'''
import os
import re
import time
import requests
import tkinter as tk
import codecs
import random
import base64
import string
import threading
from queue import Queue
from Crypto.Cipher import AES
from tkinter import messagebox

RSTR = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'


class MythreadManager(object):
    """
    线程池管理者
    """

    def __init__(self, threadnum=3):
        self.threadnum = threadnum
        self.workqueue = Queue()
        self.initMythread()

    def initMythread(self):
        for i in range(self.threadnum):
            t = Mythread(self.workqueue)
            t.start()

    def add_job(self, func, *args):
        self.workqueue.put((func, args))


class Mythread(threading.Thread):
    """
    自定义线程类
    """

    def __init__(self, queue):
        super(Mythread, self).__init__()
        self.queue = queue

    def run(self):
        while True:
            try:
                func, args = self.queue.get(True, 60)  # 确定阻塞时间
            except:
                break
            func(*args)
            self.queue.task_done()


# 创建线程池对象
manager = MythreadManager()


def tdownload(url, startpos, endpos, f):
    """
    下载函数
    :param url:
    :param startpos:
    :param endpos:
    :param f:
    :return: None
    """
    print('start thread: %s at %s' % (threading.current_thread().getName(), time.time()))
    headers = {'Range': 'bytes=%s-%s' % (startpos, endpos)}  # 关键逻辑,只取特定片段
    print('Start:%s,end:%s' % (startpos, endpos))
    req = requests.get(url, headers=headers)
    f.seek(startpos)
    f.write(req.content)
    print('end thread: %s at %s' % (threading.current_thread().getName(), time.time()))
    f.close()


class Wyy_data(object):
    def __init__(self, headers):
        """
        初始化一些参数
        :param query:
        :param headers:
        """
        self.window = tk.Tk()
        self.window.title('网易云音乐搜索下载')
        self.window.geometry('600x300')
        self.var = tk.StringVar()

        tk.Label(self.window, text='请输入你想下载的歌曲名字: ').grid(row=0, column=0, sticky=tk.E)
        tk.Label(self.window, text='请输入存储文件夹(默认为 E:\music): ').grid(row=1, column=0, sticky=tk.E)
        tk.Label(self.window, text='请输入你想下载的歌曲编号(如果是多首请用逗号分隔):').grid(row=2, column=0, sticky=tk.W)

        self.listbox = tk.Listbox(self.window, listvariable=self.var, height=10, width=40)
        self.listbox.grid(row=3, column=1)

        self.entry1 = tk.Entry(self.window, width=20)
        self.entry1.grid(row=0, column=1, sticky=tk.W)

        self.entry2 = tk.Entry(self.window, width=10)
        self.entry2.grid(row=2, column=1, sticky=tk.W)

        self.entry3 = tk.Entry(self.window, width=20)
        self.entry3.grid(row=1, column=1, sticky=tk.W)

        self.btn1 = tk.Button(self.window, text='得到歌曲列表', command=self.load_list)
        self.btn1.grid(row=4, column=0, sticky=tk.E)

        self.btn2 = tk.Button(self.window, text='点击下载歌曲', command=self.load_download)
        self.btn2.grid(row=4, column=1, sticky=tk.E)

        self.headers = headers
        self.song_dict = {}
        self.second_param = '010001'
        self.third_param = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d' \
                           '2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee25' \
                           '5932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
        self.forth_param = '0CoJUm6Qyw8W8jud'

        self.window.mainloop()

    def pad(self, msg):
        """
        填充的padding算法
        :param msg:
        :return: 填充后的值
        """
        padding = 16 - len(msg.encode()) % 16
        return msg + padding * chr(padding)

    def get_rand(self):
        """
        获得随机十六位字符串
        :return: 十六位字符串
        """
        return ''.join(random.sample(string.ascii_letters + string.digits, 16))

    def aes_encrypt(self, msg, key, iv='0102030405060708'):
        """
        AES加密
        :param msg:
        :param key:
        :param iv:
        :return: 加密后的text
        """
        msg = self.pad(msg)
        iv = iv.encode('utf-8')
        key = key.encode('utf-8')
        msg = msg.encode('utf-8')
        cryptor = AES.new(key, AES.MODE_CBC, iv)
        text = cryptor.encrypt(msg)
        text = base64.b64encode(text)
        return text

    def get_params(self, rand):
        """
        获得params参数
        :param rand:
        :return: params
        """
        query = '{"hlpretag":"<span class=\\"s-fc7\\">","hlposttag":"</span>","s":"%s","type":"1","offset":"0",' \
                '"total":"true","limit":"30","csrf_token":""}' % self.entry1.get()
        text = self.aes_encrypt(query, self.forth_param)
        params = self.aes_encrypt(text.decode('utf-8'), rand)
        return params

    def rsa_encrypt(self, text):
        """
        RSA加密
        :param text:
        :return: None
        """
        text = text[::-1].encode('utf-8')
        rs = int(codecs.encode(text, 'hex_codec'), 16) ** int(self.second_param, 16) % int(self.third_param, 16)
        return format(rs, 'x').zfill(256)

    def encrypt(self):
        """
        进行参数加密
        :return: data
        """
        rand = self.get_rand()
        params = self.get_params(rand)
        encSecKey = self.rsa_encrypt(rand)
        data = {
            'params': params,
            'encSecKey': encSecKey
        }
        return data

    def get_data(self):
        """
        下载歌曲
        :return: None
        """
        url = 'https://music.163.com/weapi/cloudsearch/get/web?csrf_token='
        data = self.encrypt()
        req = requests.post(url, headers=self.headers, data=data).json()
        # print(req)
        if not req['result']['songCount']:
            messagebox.showerror(message='没有歌曲信息')
            self.window.destroy()
        else:
            songs = req['result']['songs']
            count = 0
            for song in songs:
                count += 1
                self.song_dict[str(count)] = [str(song['id']), song['name'], song['ar'][0]['name']]

    def get_list(self):
        """
        获得歌曲列表
        :return: None
        """
        self.get_data()
        presence = []
        for key, value in self.song_dict.items():
            presence.append(key + '. ' + value[1] + ' ' + value[2])

        self.var.set(presence)

    def load_list(self):
        """
        开线程执行获取列表
        :return: None
        """
        t = threading.Thread(target=self.get_list, args=())
        t.setDaemon(True)
        t.start()

    def download(self):
        """
        调用downloader下载器下载
        :return: None
        """
        download_ids = self.entry2.get()
        download_list = download_ids.split(',')
        msg_list = []
        for download_id in download_list:
            music_id = self.song_dict[download_id][0]
            name = self.song_dict[download_id][1] + ' ' + self.song_dict[download_id][2]
            newname = re.sub(RSTR, '_', name)  # 有可能name中含有文件名非法字符,替换为下划线
            if self.entry3.get():
                msg_list.append(self.thread_download(music_id, newname, self.entry3.get()))
            else:
                msg_list.append(self.thread_download(music_id, newname))

        for msg in msg_list:
            if msg:
                messagebox.showinfo(message='下载成功')
            else:
                messagebox.showerror(message='下载失败')

        self.window.destroy()

    def get_blocks(self, url, blocks=6):
        """
        获取文件大小并进行特定分段
        :param url:
        :param blocks:
        :return: blocks
        """
        try:
            filesize = int(requests.get(url).headers['Content-Length'])  # 获取文件大小
            print('文件大小', filesize)
            blocksize = filesize // blocks
            ranges = []
            for i in range(0, blocks - 1):
                ranges.append((i * blocksize, (i + 1) * blocksize - 1))
            ranges.append(((blocks - 1) * blocksize, filesize - 1))
            return ranges
        except:
            messagebox.showerror(message='该歌曲不存在或版权受限')
            return None

    def thread_download(self, id, rename, filepath='E://music', threads=6):
        """
        多线程下载音乐
        :param id:
        :param rename:
        :param filepath:
        :param threads:
        :return: None
        """
        url = 'http://music.163.com/song/media/outer/url?id=' + id + '.mp3'
        ranges = self.get_blocks(url, threads)
        if ranges:
            try:
                if not os.path.exists(filepath):
                    os.mkdir(filepath)
                if filepath[-1] != r'/':
                    filepath += r'/'
                realpath = filepath + rename + '.mp3'
                with open(realpath, 'wb+') as f:
                    fileno = f.fileno()
                    for i in range(threads):
                        dup = os.dup(fileno)  # 文件句柄复制,以免多线程同用一句柄出错
                        fd = os.fdopen(dup, 'wb+', -1)
                        manager.add_job(tdownload, *(url, ranges[i][0], ranges[i][1], fd))  # 创建线程

                return True
            except:
                return False
        else:
            return False

    def load_download(self):
        """
        开一线程执行下载
        :return: None
        """
        t = threading.Thread(target=self.download, args=())
        t.setDaemon(True)
        t.start()


if __name__ == '__main__':
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'music.163.com',
        'Origin': 'http://music.163.com',
        'Referer': 'https://music.163.com/search/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75 Safari/537.36',
    }
    # query = '{"hlpretag":"<span class=\\"s-fc7\\">","hlposttag":"</span>","s":"%s","type":"1","offset":"0","total":"true","limit":"30","csrf_token":""}'

    Wyy_data(headers)
