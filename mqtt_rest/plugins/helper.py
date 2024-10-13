import abc
import os
import textwrap
from typing import List

from pydantic import BaseModel, field_validator

from mqtt_rest.plugins.template_engine import BashFunction, TemplateEngine

THIS_DIR = os.path.dirname(__file__)

helper_templates = TemplateEngine(
    os.path.join(
        THIS_DIR,
        "_helper_commands",
    ),
)


class Command(BaseModel):
    command: str
    package: str | None = None
    post_install: BashFunction | None = None


class Installer(BaseModel):
    url: str
    dependencies: List[Command] | None = None
    description: str | None = None

    def render(self):
        return helper_templates.render("install.sh", self.model_dump())

    @field_validator("description", mode="before")
    def update_description(cls, value):
        if value:
            return textwrap.dedent(value)
        return value


class BaseJob(BaseModel, abc.ABC):
    url: str
    run_job: BashFunction
    get_cron_frequency: BashFunction
    need_root: bool = False

    @abc.abstractmethod
    def render(self):
        pass


class SingleJob(BaseJob):
    def render(self):
        return helper_templates.render("single_job.sh", self.model_dump())


class MultiJob(BaseJob):
    get_job_options: BashFunction

    def render(self):
        return helper_templates.render("multi_job.sh", self.model_dump())


def get_cron_frequency(freq: str):
    options = []
    if "m" in freq:
        options.append('m) echo "*/$number * * * *";;')
    if "h" in freq:
        options.append('h) echo "0 */$number * * *";;')
    if "d" in freq:
        options.append('d) echo "0 0 */$number * *";;')
    return BashFunction(
        name="get_cron_frequency",
        body="""
        local frequency=$1
        local unit=${frequency: -1}
        local number=${frequency:0:${#frequency}-1}

        case $unit in
            {% for option in options -%}
            '{{ option }}'
            {% endfor -%}
            *) echo "Invalid frequency unit. Please use one of '{{valids}}'."
            exit 1 ;;
        esac
        """,
        context={"options": options, "valids": ",".join(freq)},
    )


JOB_FREQUENCY_MINUTE_HOUR_DAY = get_cron_frequency("mhd")
JOB_FREQUENCY_HOUR_DAY = get_cron_frequency("hd")
JOB_FREQUENCY_DAY = get_cron_frequency("d")
