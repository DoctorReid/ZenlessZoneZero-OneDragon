from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableView, QLineEdit, QPushButton,
                               QAbstractItemView, QHeaderView, QLabel, QFileDialog, QMessageBox, QInputDialog)
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem
import requests
import os


def find_project_root(start_path, marker='src'):
    """
    从给定路径开始，递归地向上查找项目根目录。

    :param start_path: 开始查找的路径
    :param marker: 标识项目根目录的文件或目录名称
    :return: 项目根目录的绝对路径
    """
    current_path = os.path.abspath(start_path)
    while True:
        # 检查当前目录是否包含标识文件/目录
        if os.path.exists(os.path.join(current_path, marker)):
            return current_path
        # 如果已经到达根目录，则停止
        if current_path == os.path.dirname(current_path):
            raise FileNotFoundError(f"无法找到包含 {marker} 的项目根目录")
        # 否则，继续向上一级目录查找
        current_path = os.path.dirname(current_path)


class SharedConfigWindow(QDialog):
    def __init__(self, parent=None):
        super(SharedConfigWindow, self).__init__(parent)
        self.setWindowTitle("共享配置")
        self.resize(800, 600)

        # 设置接口baseUrl
        self.baseUrl = "http://116.205.232.21"

        # 设置主布局
        layout = QVBoxLayout()

        # 搜索栏
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("输入关键字进行搜索...")
        self.search_bar.textChanged.connect(self.filter_table)
        search_layout.addWidget(QLabel("搜索:"))
        search_layout.addWidget(self.search_bar)
        layout.addLayout(search_layout)

        # 表格视图
        self.table_view = QTableView(self)
        self.model = QStandardItemModel(0, 3, self)  # 三列
        self.model.setHorizontalHeaderLabels(['配置名称', '上传者', '上传时间'])
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_view)

        # 控制按钮
        button_layout = QHBoxLayout()
        self.download_button = QPushButton("下载", self)
        self.download_button.clicked.connect(self.on_download_clicked)
        self.upload_button = QPushButton("上传", self)
        self.upload_button.clicked.connect(self.on_upload_clicked)
        self.cancel_button = QPushButton("取消", self)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 初始化数据
        self.load_data_from_api()

    def load_data_from_api(self):
        try:
            # 发送请求
            response = requests.post(self.baseUrl + "/getBattleInfo")
            response.raise_for_status()  # 如果响应状态码不是200，则抛出异常
            # 解析JSON数据
            data = response.json()['data']
            # 清空模型
            self.model.clear()
            # 重新设置列标题
            self.model.setHorizontalHeaderLabels(['配置名称', '上传者', '上传时间'])

            # 将数据填充到模型
            for item in data:
                row = [
                    QStandardItem(item["battle_name"]),
                    QStandardItem(item["creation_name"]),
                    QStandardItem(item["creation_date"])
                ]
                for cell in row:  # 对每一行中的每个单元格进行设置
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # 居中对齐
                self.model.appendRow(row)
                # 存储id以便后续使用
                row[0].setData(item["id"], Qt.ItemDataRole.UserRole)
                row[1].setData(item["battle_name"], Qt.ItemDataRole.UserRole)

        except requests.RequestException as e:
            QMessageBox.critical(self, "错误", f"服务异常: {e}")

    def filter_table(self, text):
        # 使用代理模型过滤
        self.proxy_model.setFilterFixedString(text)

    def on_download_clicked(self):
        indexes = self.table_view.selectedIndexes()
        if not indexes:
            return
        battle_id = self.model.itemFromIndex(self.proxy_model.mapToSource(indexes[0])).data(Qt.ItemDataRole.UserRole)
        battle_name = self.model.itemFromIndex(self.proxy_model.mapToSource(indexes[1])).data(Qt.ItemDataRole.UserRole)

        # 确定下载地址
        download_url = f"{self.baseUrl}/downloadBattleInfo/{battle_id}"
        try:
            # 发送请求下载文件
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            # 确定保存路径
            # 获取项目根目录
            project_root = find_project_root(__file__)
            save_path = os.path.join(project_root, 'config', 'auto_battle')
            os.makedirs(save_path, exist_ok=True)  # 确保目录存在

            # 保存文件
            file_name = f"共享配置-{battle_name}.sample.yml"  # 假设下载的是文本文件
            with open(os.path.join(save_path, file_name), 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            QMessageBox.information(self, "成功", f"文件已下载并保存到 {save_path}")
        except requests.RequestException as e:
            QMessageBox.critical(self, "错误", f"下载失败: {e}")
        except FileNotFoundError as e:
            QMessageBox.critical(self, "错误", str(e))

    def on_upload_clicked(self):
        # 获取配置名称
        battle_name, ok = QInputDialog.getText(self, "共享配置", "请输入配置名称:")
        if not ok or not battle_name:
            return  # 如果用户取消或未输入任何内容，则返回

        # 获取上传者名称
        creation_name, ok = QInputDialog.getText(self, "共享配置", "请输入上传者名称:")
        if not ok or not creation_name:
            return  # 如果用户取消或未输入任何内容，则返回

        # 选择要上传的文件
        file_dialog = QFileDialog.getOpenFileName(self, "选择要上传的配置文件")
        if not file_dialog[0]:
            return  # 如果没有选择文件，则返回

        file_path = file_dialog[0]

        # 准备上传文件
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                # 发送带查询参数的POST请求
                response = requests.post(
                    f"{self.baseUrl}/uploadBattleInfo?battle_name={battle_name}&creation_name={creation_name}",
                    files=files)
                response.raise_for_status()  # 如果响应状态码不是200，则抛出异常
                QMessageBox.information(self, "成功", "文件已成功上传！")
                # 刷新数据
                self.load_data_from_api()
        except requests.RequestException as e:
            QMessageBox.critical(self, "错误", f"上传失败: {e}")
        except IOError as e:
            QMessageBox.critical(self, "错误", f"无法打开文件: {e}")
