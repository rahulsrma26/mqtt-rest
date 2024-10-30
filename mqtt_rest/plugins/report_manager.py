from datetime import datetime, timezone

from sqlmodel import Field, SQLModel, select

from mqtt_rest.db import SessionDep
from mqtt_rest.plugins.simple_plugin import helper_templates


class Report(SQLModel, table=True):
    plugin: str = Field(primary_key=True)
    device: str = Field(primary_key=True)
    incoming_ip: str
    result: str
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={
            "onupdate": lambda: datetime.now(timezone.utc),
        },
    )


def update_report(session: SessionDep, report: Report) -> str:
    statement = select(Report).where(Report.plugin == report.plugin, Report.device == report.device)
    old_report = session.exec(statement).first()
    if not old_report:
        old_report = report
    else:
        for key, value in report.model_dump(exclude_unset=True).items():
            setattr(old_report, key, value)
    session.add(old_report)
    session.commit()
    session.refresh(old_report)
    return helper_templates.render("report.txt", report.model_dump())


def get_report(session: SessionDep, plugin: str, device: str) -> str | None:
    statement = select(Report).where(Report.plugin == plugin, Report.device == device)
    report = session.exec(statement).first()
    if not report:
        return None
    return helper_templates.render("report.txt", report[0].model_dump())


def delete_report(session: SessionDep, plugin: str, device: str) -> bool:
    statement = select(Report).where(Report.plugin == plugin, Report.device == device)
    report = session.exec(statement).first()
    if report:
        session.delete(report)
        session.commit()
        return True
    return False


def get_report_url(url: str, plugin: str, device_id: str) -> str:
    base, _ = url.split(f"/{plugin}/", 1)
    return f"{base}/reports/{plugin}/{device_id}"
