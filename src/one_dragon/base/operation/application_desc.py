from one_dragon.base.operation.application_base import Application
from one_dragon.base.operation.application_run_record import AppRunRecord


class ApplicationDesc:

    def __init__(self, app_id: str, app_name: str,
                 app: Application,
                 app_run_record: AppRunRecord):
        self.app_id: str = app_id
        self.app_name: str = app_name
        self.app: Application = app
        self.app_run_record: AppRunRecord = app_run_record
