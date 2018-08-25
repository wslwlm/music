#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
    QQ音乐多线程下载器
    只兼容Python3
'''
import os
import re
import time
import requests
import threading
import tkinter as tk
from queue import Queue
from tkinter import messagebox
from urllib.parse import quote

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0'
}

RSTR = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'


class Mythreadmanager():
    """自定义线程池"""

    def __init__(self, threadnum=3):
        self.workqueue = Queue()
        self.threadnum = threadnum
        self.initthread()

    def initthread(self):
        for i in range(self.threadnum):
            t = Mythread(self.workqueue)
            t.start()

    def add_job(self, func, *args):
        self.workqueue.put((func, args))


class Mythread(threading.Thread):
    """自定义线程类"""

    def __init__(self, queue):
        super(Mythread, self).__init__()
        self.queue = queue

    def run(self):
        while True:
            try:
                func, args = self.queue.get(True, 60)  # 当队列60s为空则结束
            except:
                messagebox.showinfo(message='下载结束')
                break
            func(*args)
            self.queue.task_done()


# 初始化线程池处理类
manager = Mythreadmanager()


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


class QQmusic(object):
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('QQ音乐下载器')
        self.window.geometry('500x300')

        self.var = tk.StringVar()

        tk.Label(self.window, text='输入歌曲名字: ').grid(row=0, column=0, sticky=tk.E)
        tk.Label(self.window, text='输入路径(默认为 E:\music): ').grid(row=1, column=0, sticky=tk.E)
        tk.Label(self.window, text='输入下载编号(多首用逗号分隔): ').grid(row=2, column=0, sticky=tk.E)
        tk.Label(self.window, text='歌曲列表: ').grid(row=3, column=0, sticky=tk.NE)

        self.entry1 = tk.Entry(self.window, width=30)
        self.entry1.grid(row=0, column=1)

        self.entry2 = tk.Entry(self.window, width=30)
        self.entry2.grid(row=1, column=1)

        self.entry3 = tk.Entry(self.window, width=20)
        self.entry3.grid(row=2, column=1, sticky=tk.W)

        self.listbox = tk.Listbox(self.window, width=30, listvariable=self.var)
        self.listbox.grid(row=3, column=1)

        self.btn1 = tk.Button(self.window, text='获取列表', command=self.load_list)
        self.btn1.grid(row=4, column=0, sticky=tk.E)

        self.btn2 = tk.Button(self.window, text='下载歌曲', command=self.load_download)
        self.btn2.grid(row=4, column=1)

        self.headers = HEADERS
        self.songdict = dict()

        self.window.mainloop()

    def get_song_list(self):
        """
        获得音乐列表
        :return: None
        """
        url = 'https://c.y.qq.com/soso/fcgi-bin/client_search_cp?ct=24&qqmusic_ver=1298&new_json=1&remoteplace=txt.yqq.so' \
              'ng&searchid=69769591960126617&t=0&aggr=1&cr=1&catZhida=1&lossless=0&flag_qc=0&p=1&n=20&w=%s&g_tk=5381&json' \
              'pCallback=MusicJsonCallback4542853598330213&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=ut' \
              'f-8&notice=0&platform=yqq&needNewCode=0' % quote(self.entry1.get())
        try:
            r = requests.get(url, headers=HEADERS)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            songlist = eval(re.findall('MusicJsonCallback\d+\((.*)\)', r.text)[0])['data']['song']['list']
            length = len(songlist)

            presence = []
            for i in range(length):
                singer_name = songlist[i]['singer'][0]['name']
                if len(songlist[i]['singer']) > 1:
                    for j in range(1, len(songlist[i]['singer'])):
                        singer_name = singer_name + '/' + songlist[i]['singer'][j]['name']
                presence.append(str(i + 1) + '. ' + songlist[i]['title'] + '  ' + singer_name)
                self.songdict[str(i + 1)] = [songlist[i]['mid'], songlist[i]['title'], singer_name]
            self.var.set(presence)
        except:
            messagebox.showerror(message='获取列表出错')
            self.window.destroy()

    def load_list(self):
        """
        开线程执行获取列表
        :return: None
        """
        t = threading.Thread(target=self.get_song_list, args=())
        t.setDaemon(True)
        t.start()

    def get_vkey(self, mid):
        """
        获得vkey
        :param mid:
        :return: vkey
        """
        url = 'https://c.y.qq.com/base/fcgi-bin/fcg_music_express_mobile3.fcg?g_tk=5381&jsonpCallback=MusicJsonCallback18' \
              '800544520639306&loginUin=1140873504&hostUin=0&format=json&inCharset=utf8&outCharset=utf-8&notice=0&platfor' \
              'm=yqq&needNewCode=0&cid=205361747&callback=MusicJsonCallback18800544520639306&uin=0&songmid=%s&filename=%s' \
              '&guid=388566810' % (mid, 'C400' + mid + '.m4a')
        try:
            r = requests.get(url, headers=self.headers)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            return eval(re.findall('MusicJsonCallback\d+\((.*)\)', r.text)[0])['data']['items'][0]['vkey']
        except:
            messagebox.showerror(message='vkey获取失败')
            self.window.destroy()

    def download(self):
        """
        调用downloader下载器下载
        :return: None
        """
        download_ids = self.entry3.get()
        download_list = download_ids.split(',')
        msg_list = []
        for download_id in download_list:
            music_id = self.songdict[download_id][0]
            name = self.songdict[download_id][1] + r'/' + self.songdict[download_id][2]
            newname = re.sub(RSTR, '_', name)  # 有可能name中含有文件名非法字符,替换为下划线
            if self.entry2.get():
                msg_list.append(self.store_music(music_id, newname, self.entry2.get()))
            else:
                msg_list.append(self.store_music(music_id, newname))

        for index, msg in enumerate(msg_list):
            if msg:
                messagebox.showinfo(message='第' + str(index + 1) + '首' + '下载成功')
            else:
                messagebox.showerror(message='第' + str(index + 1) + '首' + '下载失败')

    def get_blocks(self, url, blocks=6):
        """
        获取文件大小并进行特定分段
        :param url:
        :param blocks:
        :return: ranges
        """
        try:
            filesize = int(requests.get(url).headers['Content-Length'])  # 获取文件大小
            print('文件大小', filesize)
            if filesize < 1000000:
                messagebox.showerror(message='此歌曲可能版权受限')
                return None
            blocksize = filesize // blocks
            ranges = []
            for i in range(0, blocks - 1):
                ranges.append((i * blocksize, (i + 1) * blocksize - 1))
            ranges.append(((blocks - 1) * blocksize, filesize - 1))
            return ranges
        except:
            messagebox.showerror(message='该歌曲不存在或版权受限')
            return None

    def store_music(self, mid, name, path='E://music', threads=6):
        """
        将分块结果传递给下载函数下载
        :param mid:
        :param name:
        :param path:
        :param threads:
        :return: None
        """
        url = 'http://dl.stream.qqmusic.qq.com/C400%s.m4a?vkey=%s&guid=388566810&' \
              'uin=0&fromtag=66' % (mid, self.get_vkey(mid))
        ranges = self.get_blocks(url, threads)
        if ranges:
            try:
                if not os.path.exists(path):
                    os.mkdir(path)
                if path[-1] != r'/':
                    path += r'/'
                realpath = path + name + '.m4a'
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
    QQmusic()
