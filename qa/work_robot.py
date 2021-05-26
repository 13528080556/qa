# @Date  : 2021/3/30
# @Author: Hugh
# @Email : 609799548@qq.com

import os
import urllib.parse

import requests


class WxWork:

    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.key = self.__get_key()

    def __get_key(self):
        query_string = {}
        for key_value in urllib.parse.urlparse(self.webhook_url).query.split('&'):
            k, v = str(key_value).split('=')
            query_string[k] = v
        return query_string['key']

    def upload(self, filepath):
        upload_url = f'https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={self.key}&type=file'
        with open(filepath, 'rb') as f:
            r = requests.post(upload_url, files={
                'media': (os.path.split(filepath)[-1], f, 'text/html')
            })
            print(r.text)
            return r.json()['media_id']

    def send_file(self, content):
        r = requests.post(self.webhook_url, json={
            'msgtype': 'file',
            "file": {
                "media_id": content
            }
        })
        print(r.text)

    def send_msg(self, message):
        requests.post(self.webhook_url, json={
            "msgtype": "text",
            "text": {
                "content": message,
            }
        })
