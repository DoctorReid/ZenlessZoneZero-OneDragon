from one_dragon.envs.env_config import EnvConfig
from one_dragon.envs.git_service import GitService
from one_dragon.envs.project_config import ProjectConfig
from one_dragon.envs.python_service import PythonService


class OneDragonEnvContext:

    def __init__(self):
        """
        存项目和环境信息的
        安装器可以使用这个减少引入依赖
        """
        self.project_config: ProjectConfig = ProjectConfig()
        self.env_config: EnvConfig = EnvConfig()
        self.git_service: GitService = GitService(self.project_config, self.env_config)
        self.python_service: PythonService = PythonService(self.project_config, self.env_config, self.git_service)

    def init_by_config(self) -> None:
        pass