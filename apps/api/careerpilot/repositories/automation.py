from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from careerpilot.models.automation import AdapterSetting, AutomationRun, AutomationStep


class AutomationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_run(self, value: AutomationRun) -> AutomationRun:
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value

    def run(self, run_id: UUID) -> AutomationRun:
        value = self.session.get(AutomationRun, run_id)
        if value is None:
            raise LookupError("automation run not found")
        return value

    def runs(self) -> list[AutomationRun]:
        statement = select(AutomationRun).order_by(AutomationRun.created_at.desc())
        return list(self.session.scalars(statement))

    def add_step(self, run_id: UUID, name: str, status: str, **details) -> None:
        self.session.add(AutomationStep(run_id=run_id, name=name, status=status, details=details))
        self.session.commit()

    def settings(self) -> list[AdapterSetting]:
        return list(self.session.scalars(select(AdapterSetting).order_by(AdapterSetting.adapter)))

    def setting(self, adapter: str) -> AdapterSetting:
        value = self.session.scalar(select(AdapterSetting).where(AdapterSetting.adapter == adapter))
        if value is None:
            value = AdapterSetting(adapter=adapter)
            self.session.add(value)
            self.session.commit()
            self.session.refresh(value)
        return value

    def save_setting(self, value: AdapterSetting) -> AdapterSetting:
        self.session.add(value)
        self.session.commit()
        self.session.refresh(value)
        return value
