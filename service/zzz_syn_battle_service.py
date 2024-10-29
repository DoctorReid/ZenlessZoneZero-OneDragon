import requests
import logging
from datetime import datetime
from zzz_save_battle_class import save_battle
from zzz_data_model import get_battle_by_name

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def file_name_tool(file_name):
    # 找到第一个 '.' 的位置
    dot_index = file_name.find('.')
    if dot_index != -1:
        # 如果找到了 '.', 则将 '.' 及其后面的内容全部清空
        file_name = file_name[:dot_index]
    else:
        # 如果没有找到 '.', 则原样返回文件名
        file_name = file_name
    return file_name


class SynBattle:
    def __init__(self):
        self.group_id = 861603314

    async def fetch_data(self):
        url = "http://127.0.0.1:3000/get_group_files_by_folder"
        payload = {
            "group_id": self.group_id,
            "folder_id": "/2c49ee6b-a94b-4b26-9143-8bf86c795a8b"
        }
        try:
            logging.info("------------------------------")
            logging.info(f"[{datetime.now()}] 自动检查群文件是否发生变更...")
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                res = response.json()['data']['files']
                updated = False  # 标志变量，用于跟踪是否有文件被更新
                for data in res:
                    creation_date = datetime.fromtimestamp(data['modify_time'])
                    file_name = file_name_tool(data['file_name'])
                    battle = get_battle_by_name(file_name)
                    if (battle is None) or (battle.battle_url is None) or (creation_date > battle.creation_date):
                        logging.info(f"[{datetime.now()}] 发现配置【{data['file_name']}】存在差异，开始同步")
                        await self.getFileUrl(data['file_id'], data['busid'],
                                              file_name, data['uploader_name'],
                                              datetime.fromtimestamp(data['modify_time']))
                        logging.info(f"[{datetime.now()}] 同步完成")
                        updated = True  # 设置标志变量为 True 表示有文件被更新
                if not updated:
                    logging.info(f"[{datetime.now()}] 未发现更新，等待下一次检查...")
        except Exception as e:
            logging.error(e)

    async def getFileUrl(self, file_id, busid, file_name, uploader_name, creation_date):
        url = "http://127.0.0.1:3000/get_group_file_url"
        payload = {
            "group_id": self.group_id,
            "file_id": file_id,
            "busid": busid
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                url = response.json()['data']['url']
                await save_battle(file_name, url, uploader_name, creation_date)
        except Exception as e:
            logging.error(e)
