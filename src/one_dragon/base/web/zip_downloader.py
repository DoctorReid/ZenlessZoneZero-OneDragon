import os
from typing import Callable, Optional

from one_dragon.utils import file_utils, http_utils
from one_dragon.utils.log_utils import log
from one_dragon.base.web.common_downloader import CommonDownloader


class ZipDownloader(CommonDownloader):

    def __init__(
            self,
            save_file_path: str,
            save_file_name: str,
            github_release_download_url: Optional[str] = None,
            gitee_release_download_url: Optional[str] = None,
            mirror_chan_download_url: Optional[str] = None,
            check_existed_list: Optional[list[str]] = None,
            ) -> None:
        """
        一个Zip的通用下载器 可提供3个下载源 并检查文件是否存在 如果存在则不进行下载 下载后进行文件解压

        Args:
            save_file_path (str): 文件保存的路径
            save_file_name (str): 文件保存的名称
            github_release_download_url (Optional[str], optional): Github Release下载地址. Defaults to None.
            gitee_release_download_url (Optional[str], optional): Gitee Release下载地址. Defaults to None.
            mirror_chan_download_url (Optional[str], optional): Mirror酱下载地址. Defaults to None.
            check_existed_list (Optional[list[str]], optional): 需要检查文件是否存在的列表 完整路径的列表. Defaults to None.
        """
        CommonDownloader.__init__(
            self,
            save_file_path=save_file_path,
            save_file_name=save_file_name,
            github_release_download_url=github_release_download_url,
            gitee_release_download_url=gitee_release_download_url,
            mirror_chan_download_url=mirror_chan_download_url,
            check_existed_list=check_existed_list
        )

    def download(
            self,
            download_by_github: bool = True,
            download_by_gitee: bool = False,
            download_by_mirror_chan: bool = False,
            proxy_url: Optional[str] = None,
            ghproxy_url: Optional[str] = None,
            skip_if_existed: bool = True,
            progress_callback: Optional[Callable[[float, str], None]] = None
            ) -> bool:
        result = CommonDownloader.download(
            self,
            download_by_github=download_by_github,
            download_by_gitee=download_by_gitee,
            download_by_mirror_chan=download_by_mirror_chan,
            proxy_url=proxy_url,
            ghproxy_url=ghproxy_url,
            skip_if_existed=skip_if_existed,
            progress_callback=progress_callback
        )

        if not result:
            return result
        
        self.unzip()

        return True
        
    def unzip(self) -> None:
        """
        对目标压缩包进行解压
        """
        # 文件已存在则不解压
        exists = CommonDownloader.is_file_existed(self)
        if exists:
            return
        
        zip_file_path = os.path.join(self.save_file_path, self.save_file_name)
        if not os.path.exists(zip_file_path):
            return
        
        file_utils.unzip_file(zip_file_path=zip_file_path, unzip_dir_path=self.save_file_path)
        log.info(f"解压完成 {zip_file_path}")

    def is_file_existed(self) -> bool:
        """
        检查文件是否存在
        额外判断压缩包是否已经存在了
        """
        exists = CommonDownloader.is_file_existed(self)
        if exists:
            return True
        
        zip_file_path = os.path.join(self.save_file_path, self.save_file_name)
        if os.path.exists(zip_file_path):
            return True
        
        return False
