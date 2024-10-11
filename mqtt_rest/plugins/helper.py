import os
import textwrap
from functools import wraps
from typing import Optional, List
from fastapi import Request
from pydantic import BaseModel, field_validator
from mqtt_rest.plugins.template_engine import TemplateEngine

THIS_DIR = os.path.dirname(__file__)


helper_templates = TemplateEngine(
    os.path.join(
        THIS_DIR,
        "_helper_commands",
    ),
)


def bash_function():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs) -> str:
            if args or kwargs:
                raise ValueError("The function must not accept any arguments")
            result = func(*args, **kwargs)
            if not isinstance(result, str):
                raise ValueError("The function must return a string")
            return (
                f"\n{func.__name__}() {{" + textwrap.indent(textwrap.dedent(result), "    ") + "}"
            )

        return wrapper

    return decorator


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


def get_single_job(request: Request, data_command: str):
    context = {"request": request, "data_command": data_command}
    return helper_templates.render("single_job.sh", context)


def get_multi_job(request: Request, get_job_options: str, run_job: str):
    context = {"request": request, "get_job_options": get_job_options, "run_job": run_job}
    return helper_templates.render("multi_job.sh", context)
