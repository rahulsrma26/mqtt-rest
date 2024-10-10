import os
from typing import Optional
from fastapi import Request
from fastapi.templating import Jinja2Templates


THIS_DIR = os.path.dirname(__file__)


def get_template(dir_path: str) -> Jinja2Templates:
    return Jinja2Templates(
        directory=dir_path,
        comment_start_string="{#=%",
        comment_end_string="%=#}",
    )


helper_templates = get_template(
    os.path.join(
        THIS_DIR,
        "_helper_commands",
    ),
)


def get_installer(request: Request, dependencies: Optional[str] = None):
    context = {"request": request}
    if dependencies:
        context["dependencies"] = dependencies
    return helper_templates.TemplateResponse("install.sh", context)


def get_single_job(request: Request, data_command: str):
    context = {"request": request, "data_command": data_command}
    return helper_templates.TemplateResponse("single_job.sh", context)
