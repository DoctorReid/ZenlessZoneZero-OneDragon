import time

import os
import shutil
from typing import Optional, Callable, List, Tuple

from one_dragon.envs.env_config import DEFAULT_ENV_PATH, DEFAULT_GIT_DIR_PATH, ProxyTypeEnum, EnvConfig, \
    RepositoryTypeEnum, GitMethodEnum
from one_dragon.envs.project_config import ProjectConfig
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

    def __init__(self, project_config: ProjectConfig, env_config: EnvConfig):
        self.project_config: ProjectConfig = project_config
        self.env_config: EnvConfig = env_config

        self.is_proxy_set: bool = False  # 是否已经设置代理了

    def download_env_file(self, file_name: str, save_file_path: str,
                          progress_callback: Optional[Callable[[float, str], None]] = None) -> bool:
        """
        下载环境文件
        :param file_name: 要下载的文件名
        :param save_file_path: 保存路径，包含文件名
        :param progress_callback: 下载进度的回调，进度发生改变时，通过该方法通知调用方。
        :return: 是否下载成功
        """
        download_url = f'{GITHUB_ENV_DOWNLOAD_PREFIX}/{self.project_config.project_name}/{file_name}'
        proxy = None
        if self.env_config.is_gh_proxy:
            download_url = f'{self.env_config.gh_proxy_url}/{download_url}'
        elif self.env_config.is_personal_proxy:
            proxy = self.env_config.personal_proxy

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
        cmd_result = cmd_utils.run_command([self.env_config.git_path, '--version'])  # 示例 git version 2.35.2.windows.1
        if cmd_result is not None:
            prefix = 'git version '
            return cmd_result[cmd_result.find(prefix) + len(prefix): ]
        else:
            return None

    def install_default_git(self, progress_callback: Optional[Callable[[float, str], None]]) -> Tuple[bool, str]:
        """
        安装默认的git
        :param progress_callback: 进度回调。进度发生改变时，通过该方法通知调用方。
        :return: 是否安装成功
        """
        log.info('开始安装 git')
        if self.get_git_version() is not None:
            msg = '已经安装了git'
            log.info(msg)
            return True, msg
        for _ in range(2):
            zip_file_name = 'PortableGit.zip'
            zip_file_path = os.path.join(DEFAULT_ENV_PATH, zip_file_name)
            if not os.path.exists(zip_file_path):
                success = self.download_env_file(zip_file_name, zip_file_path,
                                                 progress_callback=progress_callback)
                if not success:
                    return False, '下载PortableGit.zip失败 请尝试到「脚本环境」更改网络代理'

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
                return True, '安装Git成功'

        # 重试之后还是失败了
        return False, '安装Git失败'

    def fetch_latest_code(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[bool, str]:
        """
        更新最新的代码
        :return: 是否成功
        """
        log.info(f'.git目录 {DOT_GIT_DIR_PATH}')
        self.set_safe_dir()
        if not os.path.exists(DOT_GIT_DIR_PATH):  # 第一次直接克隆
            return self.clone_repository(progress_callback)
        else:  # 已经克隆了
            return self.checkout_latest_project_branch(progress_callback)

    def clone_repository(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[bool, str]:
        """
        克隆仓库
        :return: 是否成功
        """

        msg = '清空临时文件夹'
        log.info(msg)
        if progress_callback is not None:
            progress_callback(-1, msg)

        # 先关闭打开的git 防止占据了.temp_clone文件夹
        cmd_utils.run_command(['taskkill', '/F', '/IM', 'git.exe'])
        cmd_utils.run_command(['taskkill', '/F', '/IM', 'ssh.exe'])

        curr_path = os_utils.get_work_dir()
        for sub_dir_name in os.listdir(curr_path):
            if not sub_dir_name.startswith('.temp_clone_'):
                continue
            sub_dir_path = os.path.join(curr_path, sub_dir_name)
            if not os.path.isdir(sub_dir_path):
                continue
            if os.path.exists(sub_dir_path):
                try:
                    shutil.rmtree(sub_dir_path)
                except:
                    pass

        # 使用随机文件夹名称 避免重复
        current_time = time.strftime('%H%M%S')
        temp_folder = f'.temp_clone_{current_time}'
        temp_dir_path = os.path.join(curr_path, temp_folder)

        msg = '开始克隆仓库 初次克隆时间较长 请耐心等待'
        log.info(msg)
        if progress_callback is not None:
            progress_callback(-1, msg)
        repo_url = self.get_git_repository(for_clone=True)
        result = cmd_utils.run_command([self.env_config.git_path, 'clone',
                                        '--depth', '1',
                                        '-b', self.project_config.project_git_branch,
                                        repo_url, temp_folder])
        if result is None:
            return False, '克隆仓库失败'

        msg = '开始复制文件'
        log.info(msg)
        if progress_callback is not None:
            progress_callback(-1, msg)
        result = cmd_utils.run_command(['xcopy', temp_dir_path, os_utils.get_work_dir(),
                                        '/E', '/H', '/C', '/I', '/Y'
                                        ])
        success = result is not None
        msg = '克隆仓库成功' if success else '克隆仓库失败'
        return success, msg

    def fetch_remote_branch(self) -> Tuple[bool, str]:
        """
        获取远程分支代码
        """
        log.info('获取远程代码')
        fetch_result = cmd_utils.run_command([self.env_config.git_path, 'fetch', 'origin', self.project_config.project_git_branch])
        if fetch_result is None:
            msg = '获取远程代码失败'
            log.error(msg)
            return False, msg
        else:
            msg = '获取远程代码成功'
            log.info(msg)
            return True, msg

    def checkout_latest_project_branch(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[bool, str]:
        """
        切换到最新的目标分支
        :return:
        """
        log.info('核对当前仓库')
        current_repo = cmd_utils.run_command([self.env_config.git_path, 'config', '--get', 'remote.origin.url'])
        if current_repo is None or not current_repo:
            log.info('未找到远程仓库')
            self.update_git_remote()
            log.info('添加远程仓库地址')
        elif current_repo != self.get_git_repository():
            log.info('远程仓库地址不一致')
            self.update_git_remote()
            log.info('更新远程仓库地址')

        log.info('获取远程代码')
        fetch_result, msg = self.fetch_remote_branch()
        if not fetch_result:
            return False, msg
        elif progress_callback is not None:
            progress_callback(1/5, msg)

        clean_result = self.is_current_branch_clean()
        if clean_result is None or not clean_result:
            if self.env_config.force_update:
                reset_result = cmd_utils.run_command(
                    [self.env_config.git_path, 'reset', '--hard', f'origin/{self.project_config.project_git_branch}'])
                if reset_result is None or not reset_result:
                    msg = '强制更新失败'
                    log.error(msg)
                    return False, msg
            else:
                msg = '未开启强制更新 当前代码有修改 请自行处理后再更新'
                log.error(msg)
                return False, msg
        elif progress_callback is not None:
            progress_callback(2/5, '当前代码无修改')

        current_result = self.get_current_branch()
        if current_result is None:
            msg = '获取当前分支失败'
            log.error(msg)
            return False, msg
        elif progress_callback is not None:
            progress_callback(3/5, '获取当前分支成功')

        if current_result != self.project_config.project_git_branch:
            checkout_result = cmd_utils.run_command([self.env_config.git_path, 'checkout', f'origin/{self.project_config.project_git_branch}'])
            if checkout_result is None or not checkout_result:
                msg = '切换到目标分支失败'
                log.error(msg)
                return False, msg
        if progress_callback is not None:
            progress_callback(4/5, '切换到目标分支成功')

        rebase_result = cmd_utils.run_command([self.env_config.git_path, 'pull', '--rebase'])
        if rebase_result is None or not rebase_result:
            msg = '更新本地代码失败'
            log.error(msg)
            cmd_utils.run_command([self.env_config.git_path, 'rebase', '--strategy-option theirs'])  # 回滚回去
            return False, msg
        elif progress_callback is not None:
            progress_callback(5/5, '更新本地代码成功')

        return True, ''

    def get_current_branch(self) -> Optional[str]:
        """
        获取当前分支名称
        :return:
        """
        log.info('检测当前代码分支')
        return cmd_utils.run_command([self.env_config.git_path, 'branch', '--show-current'])

    def is_current_branch_clean(self) -> Optional[bool]:
        """
        当前分支是否没有任何修改内容
        :return:
        """
        log.info('检测当前代码是否有修改')
        status_str = cmd_utils.run_command([self.env_config.git_path, 'status'])
        if status_str is None:
            return None
        else:
            return status_str.find('nothing to commit, working tree clean') != -1

    def is_current_branch_latest(self) -> Tuple[bool, str]:
        """
        当前分支是否已经最新 与远程分支一致
        """
        fetch, msg = self.fetch_remote_branch()
        if not fetch:
            return fetch, msg
        log.info('检测当前代码是否最新')
        diff_result = cmd_utils.run_command([self.env_config.git_path, 'diff', '--name-only', 'HEAD', f'origin/{self.project_config.project_git_branch}'])
        if len(diff_result.strip()) == 0:
            return True, ''
        else:
            return False, '与远程分支不一致'

    def get_requirement_time(self) -> Optional[str]:
        """
        获取 requirements.txt 的最后更新时间
        :return:
        """
        log.info('获取依赖文件的最后修改时间')
        return cmd_utils.run_command([self.env_config.git_path, 'log', '-1', '--pretty=format:"%ai', '--', self.project_config.requirements])

    def fetch_total_commit(self) -> int:
        """
        获取commit的总数。获取失败时返回0
        :return:
        """
        log.info('获取commit总数')
        result = cmd_utils.run_command([self.env_config.git_path, 'rev-list', '--count', 'HEAD'])
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
            self.env_config.git_path, 'log', f'-{page_size}',
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

    def get_git_repository(self, for_clone: bool = False) -> str:
        """
        获取使用的仓库地址
        :return:
        """
        if self.env_config.repository_type == RepositoryTypeEnum.GITHUB.value.value:
            if self.env_config.git_method == GitMethodEnum.HTTPS.value.value:
                if self.env_config.is_gh_proxy and for_clone:
                    return f'{self.env_config.gh_proxy_url}/{self.project_config.github_https_repository}'
                else:
                    return self.project_config.github_https_repository
            else:
                return self.project_config.github_ssh_repository
        elif self.env_config.repository_type == RepositoryTypeEnum.GITEE.value.value:
            if self.env_config.git_method == GitMethodEnum.HTTPS.value.value:
                return self.project_config.gitee_https_repository
            else:
                return self.project_config.gitee_ssh_repository
        else:
            return ''

    def init_git_proxy(self) -> None:
        """
        初始化 git 使用的代理
        :return:
        """
        if self.is_proxy_set:
            return
        if not os.path.exists(DOT_GIT_DIR_PATH):  # 未有.git文件夹
            return

        if not self.env_config.is_personal_proxy:  # 没有代理
            cmd_utils.run_command([self.env_config.git_path, 'config', '--local', '--unset', 'http.proxy'])
        else:
            proxy_address = self.env_config.personal_proxy
            cmd_utils.run_command([self.env_config.git_path, 'config', '--local', 'http.proxy', proxy_address])
        self.is_proxy_set = True

    def update_git_remote(self) -> None:
        """
        更新remote
        """
        if not os.path.exists(DOT_GIT_DIR_PATH):  # 未有.git文件夹
            return

        remote = self.get_git_repository()
        cmd_utils.run_command([self.env_config.git_path, 'remote', 'set-url', 'origin', remote])

    def set_safe_dir(self) -> None:
        """
        部分场景会没有权限clone代码 需要先授权
        :return:
        """
        cmd_utils.run_command([self.env_config.git_path, 'config', '--global', '--add', 'safe.directory',
                               os.path.normpath(os_utils.get_work_dir()).replace(os.path.sep, '/')])

    def reset_to_commit(self, commit_id: str) -> bool:
        """
        回滚到特定commit
        """
        reset_result = cmd_utils.run_command([self.env_config.git_path, 'reset', '--hard', commit_id])
        return reset_result is not None

    def get_current_version(self) -> Optional[str]:
        """
        获取当前代码版本
        @return:
        """
        log_list = self.fetch_page_commit(0, 1)
        return None if len(log_list) == 0 else log_list[0].commit_id
