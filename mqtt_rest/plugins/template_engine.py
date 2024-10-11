import os
from typing import List, Optional
import textwrap
from fastapi import Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, field_validator
from jinja2 import Environment, FileSystemLoader

THIS_DIR = os.path.dirname(__file__)


def get_environment(*args, **kwargs):
    return Environment(
        *args,
        **kwargs,
        variable_start_string="'{{",
        variable_end_string="}}'",
        comment_start_string="{#=%",
        comment_end_string="%=#}",
    )


class TemplateEngine:
    def __init__(self, dir_path: str) -> None:
        self.dir_path = dir_path
        self.env = get_environment(loader=FileSystemLoader(dir_path))

    def render(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return PlainTextResponse(template.render(context))


helper_templates = TemplateEngine(
    os.path.join(
        THIS_DIR,
        "_helper_commands",
    ),
)


class Command(BaseModel):
    command: str
    package: str | None

    @field_validator("package", mode="before")
    def set_package(cls, v, values):
        return v or values.get("command")


def get_installer(
    request: Request,
    dependencies: Optional[List[Command]] = None,
    description: Optional[str] = None,
):
    context = {"request": request}
    if dependencies:
        context["dependencies"] = dependencies
    if description:
        context["description"] = textwrap.dedent(description)
    return helper_templates.render("install.sh", context)


def get_single_job(request: Request, data_command: str, get_cron_frequency: str):
    context = {
        "request": request,
        "data_command": data_command,
        "get_cron_frequency": get_cron_frequency,
    }
    return helper_templates.render("single_job.sh", context)


def get_multi_job(request: Request, get_job_options: str, run_job: str, get_cron_frequency: str):
    context = {
        "request": request,
        "get_job_options": get_job_options,
        "run_job": run_job,
        "get_cron_frequency": get_cron_frequency,
    }
    return helper_templates.render("multi_job.sh", context)
