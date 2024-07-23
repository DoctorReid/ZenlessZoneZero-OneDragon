import os
import shutil
from typing import Optional, Callable, List, Tuple

from one_dragon.envs.env_config import GH_PROXY_URL, DEFAULT_ENV_PATH, DEFAULT_GIT_DIR_PATH, ProxyTypeEnum, EnvConfig, \
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
        proxy = self.env_config.proxy_address
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
                    return False, '下载PortableGit.zip失败'

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
        if not os.path.exists(DOT_GIT_DIR_PATH):  # 第一次直接克隆
            return self.clone_repository(progress_callback)
        else:  # 已经克隆了
            return self.checkout_latest_project_branch(progress_callback)

    def clone_repository(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[bool, str]:
        """
        克隆仓库
        :return: 是否成功
        """
        temp_folder = '.temp_clone'

        msg = '清空临时文件夹'
        log.info(msg)
        if progress_callback is not None:
            progress_callback(-1, msg)

        temp_dir_path = os.path.join(os_utils.get_work_dir(), temp_folder)
        if os.path.exists(temp_dir_path):
            shutil.rmtree(temp_dir_path)

        msg = '开始克隆仓库'
        log.info(msg)
        if progress_callback is not None:
            progress_callback(-1, msg)
        result = cmd_utils.run_command([self.env_config.git_path, 'clone', '-b', self.project_config.project_git_branch,
                                        self.get_git_repository(), temp_folder])
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
            log.error(msg)
            return True, msg

    def checkout_latest_project_branch(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Tuple[bool, str]:
        """
        切换到最新的目标分支
        :return:
        """
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
                    [self.env_config.git_path, 'reset', '--hard', 'HEAD'])
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
            checkout_result = cmd_utils.run_command([self.env_config.git_path, 'checkout', f'{self.project_config.project_git_branch}'])
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
            cmd_utils.run_command([self.env_config.git_path, 'rebase', '--abort'])  # 回滚回去
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

    def is_current_brand_latest(self) -> Tuple[bool, str]:
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

    def get_git_repository(self) -> str:
        """
        获取使用的仓库地址
        :return:
        """
        if self.env_config.repository_type == RepositoryTypeEnum.GITHUB.value.value:
            if self.env_config.git_method == GitMethodEnum.HTTPS.value.value:
                return self.project_config.github_https_repository
            else:
                return self.project_config.github_ssh_repository
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

        if self.env_config.proxy_type != ProxyTypeEnum.PERSONAL.value.value:  # 没有代理
            cmd_utils.run_command([self.env_config.git_path, 'config', '--local', '--unset', 'http.proxy'])
            cmd_utils.run_command([self.env_config.git_path, 'config', '--local', '--unset', 'https.proxy'])
        else:
            proxy_address = self.env_config.proxy_address
            cmd_utils.run_command([self.env_config.git_path, 'config', '--local', 'http.proxy', proxy_address])
            cmd_utils.run_command([self.env_config.git_path, 'config', '--local', 'https.proxy', proxy_address])
        self.is_proxy_set = True

    def update_git_remote(self) -> None:
        """
        更新remote
        """
        if not os.path.exists(DOT_GIT_DIR_PATH):  # 未有.git文件夹
            return
        cmd_utils.run_command([self.env_config.git_path, 'remote', 'set-url', 'origin', self.get_git_repository()])
