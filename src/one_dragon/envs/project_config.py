from one_dragon.base.config.yaml_config import YamlConfig


class ProjectConfig(YamlConfig):

    def __init__(self):
        super().__init__(module_name='project')

        self.project_name = self.get('project_name')
        self.win_title = self.get('win_title')
        self.python_version = self.get('python_version')
        self.pip_version = self.get('pip_version')
        self.github_repository = self.get('github_repository')
        self.gitee_repository = self.get('gitee_repository')
        self.project_git_branch = self.get('project_git_branch')
        self.requirements = self.get('requirements')


project_config = ProjectConfig()
