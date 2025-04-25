# 代码来自whyour/qinglong/develop/sample/notify.py, 感谢原作者的贡献
import base64
import copy
import hashlib
import hmac
import json
import re
import smtplib
import threading
import time
import urllib.parse

from io import BytesIO
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from typing import Optional

from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.utils.log_utils import log

import requests

class Push():

    _default_push_config = {
        'BARK_PUSH': '',                    # bark IP 或设备码，例：https://api.day.app/DxHcxxxxxRxxxxxxcm/
        'BARK_ARCHIVE': '',                 # bark 推送是否存档
        'BARK_GROUP': '',                   # bark 推送分组
        'BARK_SOUND': '',                   # bark 推送声音
        'BARK_ICON': '',                    # bark 推送图标
        'BARK_LEVEL': '',                   # bark 推送时效性
        'BARK_URL': '',                     # bark 推送跳转URL

        'CONSOLE': False,                   # 控制台输出

        'DD_BOT_SECRET': '',                # 钉钉机器人的 DD_BOT_SECRET
        'DD_BOT_TOKEN': '',                 # 钉钉机器人的 DD_BOT_TOKEN

        'FSKEY': '',                        # 飞书机器人的 FSKEY

        'ONEBOT_URL': '',                   # OneBot 的推送地址，以send_msg结尾
        'ONEBOT_USER': '',                  # OneBot 的推送对象，QQ号
        'ONEBOT_GROUP': '',                 # OneBot 的推送对象，群号
        'ONEBOT_TOKEN': '',                 # OneBot 的 access_token，可选

        'GOTIFY_URL': '',                   # gotify地址,如https://push.example.de:8080
        'GOTIFY_TOKEN': '',                 # gotify的消息应用token
        'GOTIFY_PRIORITY': 0,               # 推送消息优先级,默认为0

        'IGOT_PUSH_KEY': '',                # iGot 聚合推送的 IGOT_PUSH_KEY

        'SERVERCHAN_PUSH_KEY': '',          # server 酱的 PUSH_KEY，兼容旧版与 Turbo 版

        'DEER_KEY': '',                     # PushDeer 的 PUSHDEER_KEY
        'DEER_URL': '',                     # PushDeer 的 PUSHDEER_URL

        'CHAT_URL': '',                     # synology chat url
        'CHAT_TOKEN': '',                   # synology chat token

        'PUSH_PLUS_TOKEN': '',              # pushplus 推送的用户令牌
        'PUSH_PLUS_USER': '',               # pushplus 推送的群组编码
        'PUSH_PLUS_TEMPLATE': 'html',       # pushplus 发送模板，支持html,txt,json,markdown,cloudMonitor,jenkins,route,pay
        'PUSH_PLUS_CHANNEL': 'wechat',      # pushplus 发送渠道，支持wechat,webhook,cp,mail,sms
        'PUSH_PLUS_WEBHOOK': '',            # pushplus webhook编码，可在pushplus公众号上扩展配置出更多渠道
        'PUSH_PLUS_CALLBACKURL': '',        # pushplus 发送结果回调地址，会把推送最终结果通知到这个地址上
        'PUSH_PLUS_TO': '',                 # pushplus 好友令牌，微信公众号渠道填写好友令牌，企业微信渠道填写企业微信用户id

        'WE_PLUS_BOT_TOKEN': '',            # 微加机器人的用户令牌
        'WE_PLUS_BOT_RECEIVER': '',         # 微加机器人的消息接收者
        'WE_PLUS_BOT_VERSION': 'pro',       # 微加机器人的调用版本

        'QMSG_KEY': '',                     # qmsg 酱的 QMSG_KEY
        'QMSG_TYPE': '',                    # qmsg 酱的 QMSG_TYPE

        'QYWX_ORIGIN': '',                  # 企业微信代理地址

        'QYWX_AM': '',                      # 企业微信应用

        'QYWX_KEY': '',                     # 企业微信机器人

        'DISCORD_BOT_TOKEN': '',            # Discord 机器人的 Token
        'DISCORD_USER_ID': '',              # Discord 接收消息的用户ID

        'TG_BOT_TOKEN': '',                 # tg 机器人的 TG_BOT_TOKEN，例：1407203283:AAG9rt-6RDaaX0HBLZQq0laNOh898iFYaRQ
        'TG_USER_ID': '',                   # tg 机器人的 TG_USER_ID，例：1434078534
        'TG_API_HOST': '',                  # tg 代理 api
        'TG_PROXY_AUTH': '',                # tg 代理认证参数
        'TG_PROXY_HOST': '',                # tg 机器人的 TG_PROXY_HOST
        'TG_PROXY_PORT': '',                # tg 机器人的 TG_PROXY_PORT

        'AIBOTK_KEY': '',                   # 智能微秘书 个人中心的apikey 文档地址：http://wechat.aibotk.com/docs/about
        'AIBOTK_TYPE': '',                  # 智能微秘书 发送目标 room 或 contact
        'AIBOTK_NAME': '',                  # 智能微秘书  发送群名 或者好友昵称和type要对应好

        'SMTP_SERVER': '',                  # SMTP 发送邮件服务器，形如 smtp.exmail.qq.com:465
        'SMTP_SSL': 'false',                # SMTP 发送邮件服务器是否使用 SSL，填写 true 或 false
        'SMTP_EMAIL': '',                   # SMTP 收发件邮箱，通知将会由自己发给自己
        'SMTP_PASSWORD': '',                # SMTP 登录密码，也可能为特殊口令，视具体邮件服务商说明而定
        'SMTP_NAME': '',                    # SMTP 收发件人姓名，可随意填写

        'PUSHME_KEY': '',                   # PushMe 的 PUSHME_KEY
        'PUSHME_URL': '',                   # PushMe 的 PUSHME_URL

        'CHRONOCAT_QQ': '',                 # QQ 号
        'CHRONOCAT_TOKEN': '',              # CHRONOCAT 的token
        'CHRONOCAT_URL': '',                # CHRONOCAT的url地址

        'WEBHOOK_URL': '',                  # 自定义通知 请求地址
        'WEBHOOK_BODY': '',                 # 自定义通知 请求体
        'WEBHOOK_HEADERS': '',              # 自定义通知 请求头
        'WEBHOOK_METHOD': '',               # 自定义通知 请求方法
        'WEBHOOK_CONTENT_TYPE': '',         # 自定义通知 content-type

        'NTFY_URL': '',                     # ntfy地址,如https://ntfy.sh
        'NTFY_TOPIC': '',                   # ntfy的消息应用topic
        'NTFY_PRIORITY':'3',                # 推送消息优先级,默认为3

        'WXPUSHER_APP_TOKEN': '',           # wxpusher 的 appToken 官方文档: https://wxpusher.zjiecode.com/docs/ 管理后台: https://wxpusher.zjiecode.com/admin/
        'WXPUSHER_TOPIC_IDS': '',           # wxpusher 的 主题ID，多个用英文分号;分隔 topic_ids 与 uids 至少配置一个才行
        'WXPUSHER_UIDS': '',                # wxpusher 的 用户ID，多个用英文分号;分隔 topic_ids 与 uids 至少配置一个才行
    }


    def __init__(self, ctx: OneDragonContext):
        self.ctx: OneDragonContext = ctx
        self.push_config = copy.deepcopy(Push._default_push_config)


    def bark(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        使用 Bark 推送消息。
        """
        
        log.info("Bark 服务启动")

        if self.push_config.get("BARK_PUSH").startswith("http"):
            url = f'{self.push_config.get("BARK_PUSH")}'
        else:
            url = f'https://api.day.app/{self.push_config.get("BARK_PUSH")}'

        bark_params = {
            "BARK_DEVICE_KEY": "device_key",
            "BARK_ARCHIVE": "isArchive",
            "BARK_GROUP": "group",
            "BARK_SOUND": "sound",
            "BARK_ICON": "icon",
            "BARK_LEVEL": "level",
            "BARK_URL": "url",
        }
        data = {
            "title": title,
            "body": content,
        }
        for pair in filter(
            lambda pairs: pairs[0].startswith("BARK_")
            and pairs[0] != "BARK_PUSH"
            and pairs[1]
            and bark_params.get(pairs[0]),
            self.push_config.items(),
        ):
            data[bark_params.get(pair[0])] = pair[1]
        headers = {"Content-Type": "application/json;charset=utf-8"}
        response = requests.post(
            url=url, data=json.dumps(data), headers=headers, timeout=15
        ).json()

        if response["code"] == 200:
            log.info("Bark 推送成功！")
        else:
            log.error("Bark 推送失败！")


    def console(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        使用 控制台 推送消息。
        """
        print(f"{title}\n{content}")


    def dingding_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        使用 钉钉机器人 推送消息。
        """
        
        log.info("钉钉机器人 服务启动")

        timestamp = str(round(time.time() * 1000))
        secret_enc = self.push_config.get("DD_BOT_SECRET").encode("utf-8")
        string_to_sign = "{}\n{}".format(timestamp, self.push_config.get("DD_BOT_SECRET"))
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(
            secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        url = f'https://oapi.dingtalk.com/robot/send?access_token={self.push_config.get("DD_BOT_TOKEN")}&timestamp={timestamp}&sign={sign}'
        headers = {"Content-Type": "application/json;charset=utf-8"}
        data = {"msgtype": "text", "text": {"content": f"{title}\n{content}"}}
        response = requests.post(
            url=url, data=json.dumps(data), headers=headers, timeout=15
        ).json()

        if not response["errcode"]:
            log.info("钉钉机器人 推送成功！")
        else:
            log.error("钉钉机器人 推送失败！")


    def feishu_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        使用 飞书机器人 推送消息。
        """
        
        log.info("飞书 服务启动")

        url = f'https://open.feishu.cn/open-apis/bot/v2/hook/{self.push_config.get("FSKEY")}'
        data = {"msg_type": "text", "content": {"text": f"{title}\n{content}"}}
        response = requests.post(url, data=json.dumps(data)).json()

        if response.get("StatusCode") == 0 or response.get("code") == 0:
            log.info("飞书 推送成功！")
        else:
            log.error(f"飞书 推送失败！错误信息如下：\n{response}")


    def one_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        使用 OneBot 推送消息。
        """
        
        log.info("OneBot 服务启动")

        url = self.push_config.get("ONEBOT_URL").rstrip("/")
        user_id = self.push_config.get("ONEBOT_USER")
        group_id = self.push_config.get("ONEBOT_GROUP")
        token = self.push_config.get("ONEBOT_TOKEN")

        if not url.endswith("/send_msg"):
                url += "/send_msg"

        headers = {'Content-Type': "application/json"}
        message = [{"type": "text", "data": {"text": f"{title}\n{content}"}}]
        if image:
            image.seek(0)
            image_base64 = base64.b64encode(image.getvalue()).decode('utf-8')
            message.append({"type": "image", "data": {"file": f'base64://{image_base64}'}})
        data_private = {"message": message}
        data_group = {"message": message}

        if token != "":
            headers["Authorization"] = f"Bearer {token}"

        if user_id != "":
            data_private["message_type"] = "private"
            data_private["user_id"] = user_id
            response_private = requests.post(url, data=json.dumps(data_private), headers=headers).json()

            if response_private["status"] == "ok":
                log.info("OneBot 私聊推送成功！")
            else:
                log.error("OneBot 私聊推送失败！")
        
        if group_id != "":
            data_group["message_type"] = "group"
            data_group["group_id"] = group_id
            response_group = requests.post(url, data=json.dumps(data_group), headers=headers).json()

            if response_group["status"] == "ok":
                log.info("OneBot 群聊推送成功！")
            else:
                log.error("OneBot 群聊推送失败！")


    def gotify(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        使用 gotify 推送消息。
        """
        
        log.info("gotify 服务启动")

        url = f'{self.push_config.get("GOTIFY_URL")}/message?token={self.push_config.get("GOTIFY_TOKEN")}'
        data = {
            "title": title,
            "message": content,
            "priority": self.push_config.get("GOTIFY_PRIORITY"),
        }
        response = requests.post(url, data=data).json()

        if response.get("id"):
            log.info("gotify 推送成功！")
        else:
            log.error("gotify 推送失败！")


    def iGot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        使用 iGot 推送消息。
        """
        
        log.info("iGot 服务启动")

        url = f'https://push.hellyw.com/{self.push_config.get("IGOT_PUSH_KEY")}'
        data = {"title": title, "content": content}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(url, data=data, headers=headers).json()

        if response["ret"] == 0:
            log.info("iGot 推送成功！")
        else:
            log.error(f'iGot 推送失败！{response["errMsg"]}')


    def serverchan(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        通过 ServerChan 推送消息。
        """
        
        log.info("Server 酱 服务启动")

        data = {"text": title, "desp": content.replace("\n", "\n\n")}

        match = re.match(r"sctp(\d+)t", self.push_config.get("SERVERCHAN_PUSH_KEY"))
        if match:
            num = match.group(1)
            url = f'https://{num}.push.ft07.com/send/{self.push_config.get("SERVERCHAN_PUSH_KEY")}.send'
        else:
            url = f'https://sctapi.ftqq.com/{self.push_config.get("SERVERCHAN_PUSH_KEY")}.send'

        response = requests.post(url, data=data).json()

        if response.get("errno") == 0 or response.get("code") == 0:
            log.info("Server 酱 推送成功！")
        else:
            log.error(f'Server 酱 推送失败！错误码：{response["message"]}')


    def pushdeer(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        通过PushDeer 推送消息
        """
        
        log.info("PushDeer 服务启动")
        data = {
            "text": title,
            "desp": content,
            "type": "markdown",
            "pushkey": self.push_config.get("DEER_KEY"),
        }
        url = "https://api2.pushdeer.com/message/push"
        if self.push_config.get("DEER_URL"):
            url = self.push_config.get("DEER_URL")

        response = requests.post(url, data=data).json()

        if len(response.get("content").get("result")) > 0:
            log.info("PushDeer 推送成功！")
        else:
            log.error(f"PushDeer 推送失败！错误信息：{response}")


    def chat(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        通过Chat 推送消息
        """
        
        log.info("chat 服务启动")
        data = "payload=" + json.dumps({"text": title + "\n" + content})
        url = self.push_config.get("CHAT_URL") + self.push_config.get("CHAT_TOKEN")
        response = requests.post(url, data=data)

        if response.status_code == 200:
            log.info("Chat 推送成功！")
        else:
            log.error(f"Chat 推送失败！错误信息：{response}")


    def pushplus_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        通过 pushplus 推送消息。
        """
        
        log.info("PUSHPLUS 服务启动")

        url = "https://www.pushplus.plus/send"
        data = {
            "token": self.push_config.get("PUSH_PLUS_TOKEN"),
            "title": title,
            "content": content,
            "topic": self.push_config.get("PUSH_PLUS_USER"),
            "template": self.push_config.get("PUSH_PLUS_TEMPLATE"),
            "channel": self.push_config.get("PUSH_PLUS_CHANNEL"),
            "webhook": self.push_config.get("PUSH_PLUS_WEBHOOK"),
            "callbackUrl": self.push_config.get("PUSH_PLUS_CALLBACKURL"),
            "to": self.push_config.get("PUSH_PLUS_TO"),
        }
        body = json.dumps(data).encode(encoding="utf-8")
        headers = {"Content-Type": "application/json"}
        response = requests.post(url=url, data=body, headers=headers).json()

        code = response["code"]
        if code == 200:
            log.info("PUSHPLUS 推送请求成功，可根据流水号查询推送结果:" + response["data"])
            log.info(
                "注意：请求成功并不代表推送成功，如未收到消息，请到pushplus官网使用流水号查询推送最终结果"
            )
        elif code == 900 or code == 903 or code == 905 or code == 999:
            log.info(response["msg"])

        else:
            url_old = "http://pushplus.hxtrip.com/send"
            headers["Accept"] = "application/json"
            response = requests.post(url=url_old, data=body, headers=headers).json()

            if response["code"] == 200:
                log.info("PUSHPLUS(hxtrip) 推送成功！")

            else:
                log.error("PUSHPLUS 推送失败！")


    def weplus_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        通过 微加机器人 推送消息。
        """
        
        log.info("微加机器人 服务启动")

        template = "txt"
        if len(content) > 800:
            template = "html"

        url = "https://www.weplusbot.com/send"
        data = {
            "token": self.push_config.get("WE_PLUS_BOT_TOKEN"),
            "title": title,
            "content": content,
            "template": template,
            "receiver": self.push_config.get("WE_PLUS_BOT_RECEIVER"),
            "version": self.push_config.get("WE_PLUS_BOT_VERSION"),
        }
        body = json.dumps(data).encode(encoding="utf-8")
        headers = {"Content-Type": "application/json"}
        response = requests.post(url=url, data=body, headers=headers).json()

        if response["code"] == 200:
            log.info("微加机器人 推送成功！")
        else:
            log.error("微加机器人 推送失败！")


    def qmsg_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        使用 qmsg 推送消息。
        """
        
        log.info("qmsg 服务启动")

        url = f'https://qmsg.zendee.cn/{self.push_config.get("QMSG_TYPE")}/{self.push_config.get("QMSG_KEY")}'
        payload = {"msg": f'{title}\n{content.replace("----", "-")}'.encode("utf-8")}
        response = requests.post(url=url, params=payload).json()

        if response["code"] == 0:
            log.info("qmsg 推送成功！")
        else:
            log.error(f'qmsg 推送失败！{response["reason"]}')


    def wecom_app(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        通过 企业微信 APP 推送消息。
        """
        QYWX_AM_AY = re.split(",", self.push_config.get("QYWX_AM"))
        if 4 < len(QYWX_AM_AY) > 5:
            log.info("QYWX_AM 设置错误!!")
            return
        log.info("企业微信 APP 服务启动")

        corpid = QYWX_AM_AY[0]
        corpsecret = QYWX_AM_AY[1]
        touser = QYWX_AM_AY[2]
        agentid = QYWX_AM_AY[3]
        try:
            media_id = QYWX_AM_AY[4]
        except IndexError:
            media_id = ""
        if self.push_config.get("QYWX_ORIGIN"):
            origin = self.push_config.get("QYWX_ORIGIN")
        else:
            origin = "https://qyapi.weixin.qq.com"
        wx = self.WeCom(corpid, corpsecret, agentid, origin)
        # 如果没有配置 media_id 默认就以 text 方式发送
        if not media_id:
            message = title + "\n\n" + content
            response = wx.send_text(message, touser)
        else:
            response = wx.send_mpnews(title, content, media_id, touser)

        if response == "ok":
            log.info("企业微信推送成功！")
        else:
            log.error(f"企业微信推送失败！错误信息如下：\n{response}")


    class WeCom:
        def __init__(self, corpid, corpsecret, agentid, origin):
            self.CORPID = corpid
            self.CORPSECRET = corpsecret
            self.AGENTID = agentid
            self.ORIGIN = origin

        def get_access_token(self):
            url = f"{self.ORIGIN}/cgi-bin/gettoken"
            values = {
                "corpid": self.CORPID,
                "corpsecret": self.CORPSECRET,
            }
            req = requests.post(url, params=values)
            data = json.loads(req.text)
            return data["access_token"]

        def send_text(self, message, touser="@all"):
            send_url = (
                f"{self.ORIGIN}/cgi-bin/message/send?access_token={self.get_access_token()}"
            )
            send_values = {
                "touser": touser,
                "msgtype": "text",
                "agentid": self.AGENTID,
                "text": {"content": message},
                "safe": "0",
            }
            send_msges = bytes(json.dumps(send_values), "utf-8")
            respone = requests.post(send_url, send_msges)
            respone = respone.json()
            return respone["errmsg"]

        def send_mpnews(self, title, message, media_id, touser="@all"):
            send_url = (
                f"{self.ORIGIN}/cgi-bin/message/send?access_token={self.get_access_token()}"
            )
            send_values = {
                "touser": touser,
                "msgtype": "mpnews",
                "agentid": self.AGENTID,
                "mpnews": {
                    "articles": [
                        {
                            "title": title,
                            "thumb_media_id": media_id,
                            "author": "Author",
                            "content_source_url": "",
                            "content": message.replace("\n", "<br/>"),
                            "digest": message,
                        }
                    ]
                },
            }
            send_msges = bytes(json.dumps(send_values), "utf-8")
            respone = requests.post(send_url, send_msges)
            respone = respone.json()
            return respone["errmsg"]


    def wecom_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        通过 企业微信机器人 推送消息。
        """
        
        log.info("企业微信机器人服务启动")

        origin = "https://qyapi.weixin.qq.com"
        if self.push_config.get("QYWX_ORIGIN"):
            origin = self.push_config.get("QYWX_ORIGIN")

        url = f"{origin}/cgi-bin/webhook/send?key={self.push_config.get('QYWX_KEY')}"
        headers = {"Content-Type": "application/json;charset=utf-8"}
        data = {"msgtype": "text", "text": {"content": f"{title}\n{content}"}}
        response = requests.post(
            url=url, data=json.dumps(data), headers=headers, timeout=15
        ).json()

        if response["errcode"] == 0:
            log.info("企业微信机器人推送成功！")
        else:
            log.error("企业微信机器人推送失败！")


    def discord_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        使用 Discord Bot 推送消息。
        """
        
        log.info("Discord Bot 服务启动")

        base_url = "https://discord.com/api/v9"
        headers = {
            "Authorization": f"Bot {self.push_config.get('DISCORD_BOT_TOKEN')}",
            "User-Agent": "OneDragon"
        }

        create_dm_url = f"{base_url}/users/@me/channels"
        dm_headers = headers.copy()
        dm_headers["Content-Type"] = "application/json"
        dm_payload = json.dumps({"recipient_id": self.push_config.get('DISCORD_USER_ID')})
        response = requests.post(create_dm_url, headers=dm_headers, data=dm_payload, timeout=15)
        response.raise_for_status()
        channel_id = response.json().get("id")
        if not channel_id or channel_id == "":
            log.error(f"Discord 私聊频道建立失败")
            return

        message_url = f"{base_url}/channels/{channel_id}/messages"
        message_payload_dict = {"content": f"{title}\n{content}"}

        files = None
        if image:
            image.seek(0)
            files = {'file': ('image.png', image, 'image/png')}
            data = {'payload_json': json.dumps(message_payload_dict)}
            if "Content-Type" in headers:
                del headers["Content-Type"]
        else:
            headers["Content-Type"] = "application/json"
            data = json.dumps(message_payload_dict)

        response = requests.post(message_url, headers=headers, data=data, files=files, timeout=30)
        response.raise_for_status()
        log.info("Discord Bot 推送成功！")


    def telegram_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        使用 telegram 机器人 推送消息。
        """
        
        log.info("Telegram 服务启动")

        if self.push_config.get("TG_API_HOST"):
            url = f"{self.push_config.get('TG_API_HOST')}/bot{self.push_config.get('TG_BOT_TOKEN')}/sendMessage"
        else:
            url = (
                f"https://api.telegram.org/bot{self.push_config.get('TG_BOT_TOKEN')}/sendMessage"
            )
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "chat_id": str(self.push_config.get("TG_USER_ID")),
            "text": f"{title}\n{content}",
            "disable_web_page_preview": "true",
        }
        proxies = None
        if self.push_config.get("TG_PROXY_HOST") and self.push_config.get("TG_PROXY_PORT"):
            if self.push_config.get("TG_PROXY_AUTH") != "" and "@" not in self.push_config.get(
                "TG_PROXY_HOST"
            ):
                self.push_config["TG_PROXY_HOST"] = (
                    self.push_config.get("TG_PROXY_AUTH")
                    + "@"
                    + self.push_config.get("TG_PROXY_HOST")
                )
            proxyStr = "http://{}:{}".format(
                self.push_config.get("TG_PROXY_HOST"), self.push_config.get("TG_PROXY_PORT")
            )
            proxies = {"http": proxyStr, "https": proxyStr}
        response = requests.post(
            url=url, headers=headers, params=payload, proxies=proxies
        ).json()

        if response["ok"]:
            log.info("Telegram 推送成功！")
        else:
            log.error("Telegram 推送失败！")


    def aibotk(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        使用 智能微秘书 推送消息。
        """
        
        log.info("智能微秘书 服务启动")

        if self.push_config.get("AIBOTK_TYPE") == "room":
            url = "https://api-bot.aibotk.com/openapi/v1/chat/room"
            data = {
                "apiKey": self.push_config.get("AIBOTK_KEY"),
                "roomName": self.push_config.get("AIBOTK_NAME"),
                "message": {"type": 1, "content": f"{title}\n{content}"},
            }
        else:
            url = "https://api-bot.aibotk.com/openapi/v1/chat/contact"
            data = {
                "apiKey": self.push_config.get("AIBOTK_KEY"),
                "name": self.push_config.get("AIBOTK_NAME"),
                "message": {"type": 1, "content": f"{title}\n{content}"},
            }
        body = json.dumps(data).encode(encoding="utf-8")
        headers = {"Content-Type": "application/json"}
        response = requests.post(url=url, data=body, headers=headers).json()
        if response["code"] == 0:
            log.info("智能微秘书 推送成功！")
        else:
            log.error(f'智能微秘书 推送失败！{response["error"]}')


    def smtp(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        使用 SMTP 邮件 推送消息。
        """
        
        log.info("SMTP 邮件 服务启动")

        message = MIMEText(content, "plain", "utf-8")
        message["From"] = formataddr(
            (
                Header(self.push_config.get("SMTP_NAME"), "utf-8").encode(),
                self.push_config.get("SMTP_EMAIL"),
            )
        )
        message["To"] = formataddr(
            (
                Header(self.push_config.get("SMTP_NAME"), "utf-8").encode(),
                self.push_config.get("SMTP_EMAIL"),
            )
        )
        message["Subject"] = Header(title, "utf-8")

        try:
            smtp_server = (
                smtplib.SMTP_SSL(self.push_config.get("SMTP_SERVER"))
                if self.push_config.get("SMTP_SSL") == "true"
                else smtplib.SMTP(self.push_config.get("SMTP_SERVER"))
            )
            smtp_server.login(
                self.push_config.get("SMTP_EMAIL"), self.push_config.get("SMTP_PASSWORD")
            )
            smtp_server.sendmail(
                self.push_config.get("SMTP_EMAIL"),
                self.push_config.get("SMTP_EMAIL"),
                message.as_bytes(),
            )
            smtp_server.close()
            log.info("SMTP 邮件 推送成功！")
        except Exception as e:
            log.error(f"SMTP 邮件 推送失败！{e}")


    def pushme(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        使用 PushMe 推送消息。
        """
        
        log.info("PushMe 服务启动")

        url = (
            self.push_config.get("PUSHME_URL")
            if self.push_config.get("PUSHME_URL")
            else "https://push.i-i.me/"
        )
        data = {
            "push_key": self.push_config.get("PUSHME_KEY"),
            "title": title,
            "content": content,
            "date": self.push_config.get("date") if self.push_config.get("date") else "",
            "type": self.push_config.get("type") if self.push_config.get("type") else "",
        }
        response = requests.post(url, data=data)

        if response.status_code == 200 and response.text == "success":
            log.info("PushMe 推送成功！")
        else:
            log.error(f"PushMe 推送失败！{response.status_code} {response.text}")


    def chronocat(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        使用 CHRONOCAT 推送消息。
        """

        log.info("CHRONOCAT 服务启动")

        user_ids = re.findall(r"user_id=(\d+)", self.push_config.get("CHRONOCAT_QQ"))
        group_ids = re.findall(r"group_id=(\d+)", self.push_config.get("CHRONOCAT_QQ"))

        url = f'{self.push_config.get("CHRONOCAT_URL")}/api/message/send'
        headers = {
            "Content-Type": "application/json",
            "Authorization": f'Bearer {self.push_config.get("CHRONOCAT_TOKEN")}',
        }

        for chat_type, ids in [(1, user_ids), (2, group_ids)]:
            if not ids:
                continue
            for chat_id in ids:
                data = {
                    "peer": {"chatType": chat_type, "peerUin": chat_id},
                    "elements": [
                        {
                            "elementType": 1,
                            "textElement": {"content": f"{title}\n{content}"},
                        }
                    ],
                }
                response = requests.post(url, headers=headers, data=json.dumps(data))
                if response.status_code == 200:
                    if chat_type == 1:
                        log.info(f"QQ个人消息:{ids}推送成功！")
                    else:
                        log.info(f"QQ群消息:{ids}推送成功！")
                else:
                    if chat_type == 1:
                        log.error(f"QQ个人消息:{ids}推送失败！")
                    else:
                        log.error(f"QQ群消息:{ids}推送失败！")


    def ntfy(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        通过 Ntfy 推送消息
        """

        def encode_rfc2047(text: str) -> str:
            """将文本编码为符合 RFC 2047 标准的格式"""
            encoded_bytes = base64.b64encode(text.encode("utf-8"))
            encoded_str = encoded_bytes.decode("utf-8")
            return f"=?utf-8?B?{encoded_str}?="

        log.info("ntfy 服务启动")
        priority = "3"
        if not self.push_config.get("NTFY_PRIORITY"):
            log.info("ntfy 服务的NTFY_PRIORITY 未设置!!默认设置为3")
        else:
            priority = self.push_config.get("NTFY_PRIORITY")

        # 使用 RFC 2047 编码 title
        encoded_title = encode_rfc2047(title)

        data = content.encode(encoding="utf-8")
        headers = {"Title": encoded_title, "Priority": priority}  # 使用编码后的 title

        url = self.push_config.get("NTFY_URL") + "/" + self.push_config.get("NTFY_TOPIC")
        response = requests.post(url, data=data, headers=headers)
        if response.status_code == 200:  # 使用 response.status_code 进行检查
            log.info("Ntfy 推送成功！")
        else:
            log.error(f"Ntfy 推送失败！错误信息：{response.text}")


    def wxpusher_bot(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        通过 wxpusher 推送消息。
        支持的环境变量:
        - WXPUSHER_APP_TOKEN: appToken
        - WXPUSHER_TOPIC_IDS: 主题ID, 多个用英文分号;分隔
        - WXPUSHER_UIDS: 用户ID, 多个用英文分号;分隔
        """

        url = "https://wxpusher.zjiecode.com/api/send/message"

        # 处理topic_ids和uids，将分号分隔的字符串转为数组
        topic_ids = []
        if self.push_config.get("WXPUSHER_TOPIC_IDS"):
            topic_ids = [
                int(id.strip())
                for id in self.push_config.get("WXPUSHER_TOPIC_IDS").split(";")
                if id.strip()
            ]

        uids = []
        if self.push_config.get("WXPUSHER_UIDS"):
            uids = [
                uid.strip()
                for uid in self.push_config.get("WXPUSHER_UIDS").split(";")
                if uid.strip()
            ]

        # topic_ids uids 至少有一个
        if not topic_ids and not uids:
            log.info("wxpusher 服务的 WXPUSHER_TOPIC_IDS 和 WXPUSHER_UIDS 至少设置一个!!")
            return

        log.info("wxpusher 服务启动")

        data = {
            "appToken": self.push_config.get("WXPUSHER_APP_TOKEN"),
            "content": f"<h1>{title}</h1><br/><div style='white-space: pre-wrap;'>{content}</div>",
            "summary": title,
            "contentType": 2,
            "topicIds": topic_ids,
            "uids": uids,
            "verifyPayType": 0,
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(url=url, json=data, headers=headers).json()

        if response.get("code") == 1000:
            log.info("wxpusher 推送成功！")
        else:
            log.error(f"wxpusher 推送失败！错误信息：{response.get('msg')}")


    def parse_headers(self, headers) -> dict:
        if not headers:
            return {}

        parsed = {}
        lines = headers.split("\n")

        for line in lines:
            i = line.find(":")
            if i == -1:
                continue

            key = line[:i].strip().lower()
            val = line[i + 1 :].strip()
            parsed[key] = parsed.get(key, "") + ", " + val if key in parsed else val

        return parsed


    def parse_string(self, input_string, value_format_fn=None) -> dict:
        matches = {}
        pattern = r"(\w+):\s*((?:(?!\n\w+:).)*)"
        regex = re.compile(pattern)
        for match in regex.finditer(input_string):
            key, value = match.group(1).strip(), match.group(2).strip()
            try:
                value = value_format_fn(value) if value_format_fn else value
                json_value = json.loads(value)
                matches[key] = json_value
            except:
                matches[key] = value
        return matches


    def parse_body(self, body, content_type, value_format_fn=None) -> str:
        if not body or content_type == "text/plain":
            return value_format_fn(body) if value_format_fn and body else body

        parsed = self.parse_string(body, value_format_fn)

        if content_type == "application/x-www-form-urlencoded":
            data = urllib.parse.urlencode(parsed, doseq=True)
            return data

        if content_type == "application/json":
            data = json.dumps(parsed)
            return data

        return parsed


    def custom_notify(self, title: str, content: str, image: Optional[BytesIO]) -> None:
        """
        通过 自定义通知 推送消息。
        """
        
        log.info("自定义通知服务启动")

        url = self.push_config.get("WEBHOOK_URL")
        method = self.push_config.get("WEBHOOK_METHOD")
        content_type = self.push_config.get("WEBHOOK_CONTENT_TYPE")
        body = self.push_config.get("WEBHOOK_BODY")
        headers = self.push_config.get("WEBHOOK_HEADERS")

        if "$title" not in url and "$title" not in body:
            log.info("请求头或者请求体中必须包含 $title 和 $content")
            return

        headers = self.parse_headers(headers)
        body = self.parse_body(
            body,
            content_type,
            lambda v: v.replace("$title", title.replace("\n", "\\n")).replace(
                "$content", content.replace("\n", "\\n")
            ),
        )
        formatted_url = url.replace(
            "$title", urllib.parse.quote_plus(title)
        ).replace("$content", urllib.parse.quote_plus(content))
        response = requests.request(
            method=method, url=formatted_url, headers=headers, timeout=15, data=body
        )

        if response.status_code == 200:
            log.info("自定义通知推送成功！")
        else:
            log.error(f"自定义通知推送失败！{response.status_code} {response.text}")


    def add_notify_function(self) -> list:
        notify_function = []
        if self.push_config.get("BARK_PUSH"):
            notify_function.append(self.bark)
        if self.push_config.get("CONSOLE"):
            notify_function.append(self.console)
        if self.push_config.get("DD_BOT_TOKEN") and self.push_config.get("DD_BOT_SECRET"):
            notify_function.append(self.dingding_bot)
        if self.push_config.get("FSKEY"):
            notify_function.append(self.feishu_bot)
        if self.push_config.get("ONEBOT_URL"):
            notify_function.append(self.one_bot)
        if self.push_config.get("GOTIFY_URL") and self.push_config.get("GOTIFY_TOKEN"):
            notify_function.append(self.gotify)
        if self.push_config.get("IGOT_PUSH_KEY"):
            notify_function.append(self.iGot)
        if self.push_config.get("SERVERCHAN_PUSH_KEY"):
            notify_function.append(self.serverchan)
        if self.push_config.get("DEER_KEY"):
            notify_function.append(self.pushdeer)
        if self.push_config.get("CHAT_URL") and self.push_config.get("CHAT_TOKEN"):
            notify_function.append(self.chat)
        if self.push_config.get("PUSH_PLUS_TOKEN"):
            notify_function.append(self.pushplus_bot)
        if self.push_config.get("WE_PLUS_BOT_TOKEN"):
            notify_function.append(self.weplus_bot)
        if self.push_config.get("QMSG_KEY") and self.push_config.get("QMSG_TYPE"):
            notify_function.append(self.qmsg_bot)
        if self.push_config.get("QYWX_AM"):
            notify_function.append(self.wecom_app)
        if self.push_config.get("QYWX_KEY"):
            notify_function.append(self.wecom_bot)
        if self.push_config.get("DISCORD_BOT_TOKEN") and self.push_config.get("DISCORD_USER_ID"):
            notify_function.append(self.discord_bot)
        if self.push_config.get("TG_BOT_TOKEN") and self.push_config.get("TG_USER_ID"):
            notify_function.append(self.telegram_bot)
        if (
            self.push_config.get("AIBOTK_KEY")
            and self.push_config.get("AIBOTK_TYPE")
            and self.push_config.get("AIBOTK_NAME")
        ):
            notify_function.append(self.aibotk)
        if (
            self.push_config.get("SMTP_SERVER")
            and self.push_config.get("SMTP_SSL")
            and self.push_config.get("SMTP_EMAIL")
            and self.push_config.get("SMTP_PASSWORD")
            and self.push_config.get("SMTP_NAME")
        ):
            notify_function.append(self.smtp)
        if self.push_config.get("PUSHME_KEY"):
            notify_function.append(self.pushme)
        if (
            self.push_config.get("CHRONOCAT_URL")
            and self.push_config.get("CHRONOCAT_QQ")
            and self.push_config.get("CHRONOCAT_TOKEN")
        ):
            notify_function.append(self.chronocat)
        if self.push_config.get("WEBHOOK_URL") and self.push_config.get("WEBHOOK_METHOD"):
            notify_function.append(self.custom_notify)
        if self.push_config.get("NTFY_TOPIC"):
            notify_function.append(self.ntfy)
        if self.push_config.get("WXPUSHER_APP_TOKEN") and (
            self.push_config.get("WXPUSHER_TOPIC_IDS") or self.push_config.get("WXPUSHER_UIDS")
        ):
            notify_function.append(self.wxpusher_bot)
        if not notify_function:
            log.info(f"无推送渠道，请检查通知设置是否正确")
        return notify_function


    def send(self, content: str, image: Optional[BytesIO] = None, test_method: Optional[str] = None) -> None:

        for config_key in self.push_config:
            config_value = getattr(self.ctx.push_config, config_key.lower(), None)
            if config_value is None:
                continue
            if test_method and test_method not in config_key:
                continue
            self.push_config[config_key] = config_value

        title = self.ctx.push_config.custom_push_title

        notify_function = self.add_notify_function()
        ts = [
            threading.Thread(target=mode, args=(title, content, image), name=mode.__name__)
            for mode in notify_function
        ]
        [t.start() for t in ts]
        [t.join() for t in ts]


def main():
    Push.send("content")

if __name__ == "__main__":
    main()
