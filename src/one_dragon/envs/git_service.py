import os
from typing import Optional, Callable, List

from one_dragon.envs.env_config import env_config, GH_PROXY_URL, DEFAULT_ENV_PATH, DEFAULT_GIT_DIR_PATH
from one_dragon.envs.project_config import project_config
from one_dragon.utils import http_utils, cmd_utils, file_utils, os_utils
from one_dragon.utils.log_utils import log

GITHUB_ENV_DOWNLOAD_PREFIX = 'https://github.com/DoctorReid/OneDragon-Env/releases/download'
DOT_GIT_DIR_PATH = os.path.join(os_utils.get_work_dir(), '.git')


class GitLog:

    def __init__(self, format_str: str):
        arr = format_str.split(' #@# ')
        self.commit_id: str = arr[0]
        self.author: str = arr[1]
        self.commit_time: str = arr[2]
        self.commit_message: str = arr[3]


class GitService:

    def __init__(self):
        self.project = project_config
        self.env = env_config

    def download_env_file(self, file_name: str, save_file_path: str,
                          progress_callback: Optional[Callable[[float, str], None]] = None) -> bool:
        """
        下载环境文件
        :param file_name: 要下载的文件名
        :param save_file_path: 保存路径，包含文件名
        :param progress_callback: 下载进度的回调，进度发生改变时，通过该方法通知调用方。
        :return: 是否下载成功
        """
        download_url = f'{GITHUB_ENV_DOWNLOAD_PREFIX}/{self.project.project_name}/{file_name}'
        proxy = self.env.proxy_address
        if proxy == GH_PROXY_URL:
            download_url = GH_PROXY_URL + download_url
            proxy = None
        return http_utils.download_file(download_url, save_file_path,
                                        proxy=proxy, progress_callback=progress_callback)

    def get_os_git_path(self) -> Optional[str]:
        """
        获取系统环境变量中的git路径
        :return:
        """
        log.info('获取系统环境变量的git')
        message = cmd_utils.run_command(['where', 'git'])
        if message is not None and message.endswith('.exe'):
            return message
        else:
            return None

    def get_git_version(self) -> Optional[str]:
        """
        获取当前使用的git版本
        :return:
        """
        log.info('检测当前git版本')
        cmd_result = cmd_utils.run_command([self.env.git_path, '--version'])  # 示例 git version 2.35.2.windows.1
        if cmd_result is not None:
            prefix = 'git version '
            return cmd_result[cmd_result.find(prefix) + len(prefix): ]
        else:
            return None

    def install_default_git(self, progress_callback: Optional[Callable[[float, str], None]]) -> bool:
        """
        安装默认的git
        :param progress_callback: 进度回调。进度发生改变时，通过该方法通知调用方。
        :return: 是否安装成功
        """
        log.info('开始安装 git')
        if self.get_git_version() is not None:
            log.info('已经安装了git')
            return True
        for _ in range(2):
            zip_file_name = 'PortableGit.zip'
            zip_file_path = os.path.join(DEFAULT_ENV_PATH, zip_file_name)
            if not os.path.exists(zip_file_path):
                success = self.download_env_file(zip_file_name, zip_file_path,
                                                 progress_callback=progress_callback)
                if not success:
                    return False

            msg = f'开始解压 {zip_file_name}'
            log.info(msg)
            if progress_callback:
                progress_callback(0, msg)

            success = file_utils.unzip_file(zip_file_path, DEFAULT_GIT_DIR_PATH)

            msg = '解压成功' if success else '解压失败 准备重试'
            if progress_callback:
                progress_callback(1 if success else 0, msg)

            if not success:  # 解压失败的话 可能是之前下的zip包坏了 尝试删除重来
                os.remove(zip_file_path)
                continue
            else:
                return True

        # 重试之后还是失败了
        return False

    def fetch_latest_code(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> bool:
        """
        更新最新的代码
        :return: 是否成功
        """
        log.info(f'.git目录 {DOT_GIT_DIR_PATH}')
        if not os.path.exists(DOT_GIT_DIR_PATH):  # 第一次直接克隆
            return self.clone_repository(progress_callback)
        else:  # 已经克隆了
            return self.checkout_latest_project_branch(progress_callback)

    def clone_repository(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> bool:
        """
        克隆仓库
        :return: 是否成功
        """
        log.info('开始克隆仓库')
        if progress_callback is not None:
            progress_callback(-1, '')
        result = cmd_utils.run_command([self.env.git_path, 'clone', '-b', self.project.project_git_branch,
                                        self.get_git_repository(),
                                        '.'])
        return result is not None

    def checkout_latest_project_branch(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> bool:
        """
        切换到最新的目标分支
        :return:
        """
        log.info('获取远程代码')
        fetch_result = cmd_utils.run_command([self.env.git_path, 'fetch', 'origin', self.project.project_git_branch])
        if fetch_result is None:
            log.error('获取远程代码失败')
            return False
        elif progress_callback is not None:
            progress_callback(1/5, '获取远程代码成功')

        clean_result = self.is_current_branch_clean()
        if clean_result is None or not clean_result:
            # 有修改的话 自行commit完再做更新
            log.error('当前代码有修改 请自行处理后再更新')
            return True
        elif progress_callback is not None:
            progress_callback(2/5, '当前代码无修改')

        current_result = self.get_current_branch()
        if current_result is None:
            log.error('获取当前分支失败')
            return False
        elif progress_callback is not None:
            progress_callback(3/5, '获取当前分支成功')

        if current_result != self.project.project_git_branch:
            checkout_result = cmd_utils.run_command([self.env.git_path, 'checkout', f'{self.project.project_git_branch}'])
            if checkout_result is None or not checkout_result:
                log.error('切换到目标分支失败')
                return False
        if progress_callback is not None:
            progress_callback(4/5, '切换到目标分支成功')

        rebase_result = cmd_utils.run_command([self.env.git_path, 'rebase', '-i', f'origin/{self.project.project_git_branch}'])
        if rebase_result is None or not rebase_result:
            log.error('更新本地代码失败')
            cmd_utils.run_command([self.env.git_path, 'rebase', '--abort'])  # 回滚回去
            return False
        elif progress_callback is not None:
            progress_callback(5/5, '更新本地代码成功')

        return True

    def get_current_branch(self) -> Optional[str]:
        """
        获取当前分支名称
        :return:
        """
        log.info('检测当前代码分支')
        return cmd_utils.run_command([self.env.git_path, 'branch', '--show-current'])

    def is_current_branch_clean(self) -> Optional[bool]:
        """
        当前分支是否没有任何修改内容
        :return:
        """
        log.info('检测当前代码是否有修改')
        status_str = cmd_utils.run_command([self.env.git_path, 'status'])
        if status_str is None:
            return None
        else:
            return status_str.find('nothing to commit, working tree clean') != -1

    def get_requirement_time(self) -> Optional[str]:
        """
        获取 requirements.txt 的最后更新时间
        :return:
        """
        log.info('获取依赖文件的最后修改时间')
        return cmd_utils.run_command([self.env.git_path, 'log', '-1', '--pretty=format:"%ai%', '--', self.project.requirements])

    def fetch_total_commit(self) -> int:
        """
        获取commit的总数。获取失败时返回0
        :return:
        """
        log.info('获取commit总数')
        result = cmd_utils.run_command([self.env.git_path, 'rev-list', '--count', 'HEAD'])
        return 0 if result is None else int(result)

    def fetch_page_commit(self, page_num: int, page_size: int) -> List[GitLog]:
        """
        获取分页的commit
        :param page_num: 页码 从0开始
        :param page_size: 每页数量
        :return:
        """
        log.info(f'获取commit 第{page_num + 1}页')
        result = cmd_utils.run_command([
            self.env.git_path, 'log', f'-{page_size}',
            '--pretty=format:"%h #@# %an #@# %ai #@# %s"',
            '--date=short',
            f'--skip={page_num * page_size}'
        ])

        log_list: List[GitLog] = []
        if result is None:
            return log_list
        str_list = result.split('\n')
        for format_str in str_list:
            log_list.append(GitLog(format_str))

        return log_list

    def get_git_repository(self) -> str:
        """
        获取使用的仓库地址
        :return:
        """
        suffix = self.project.github_repository if self.env.repository_from == 'github' else self.project.gitee_repository
        prefix = 'https://' if self.env.git_method == 'https' else 'git@'
        return prefix + suffix


git_service = GitService()
