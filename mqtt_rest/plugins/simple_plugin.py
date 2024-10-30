import abc
import os
import textwrap
from typing import Callable, Dict, List

from pydantic import BaseModel, ConfigDict, field_validator

from mqtt_rest.plugins.simple_template_engine import BashFunction, TemplateEngine

THIS_DIR = os.path.dirname(__file__)

helper_templates = TemplateEngine(
    os.path.join(
        THIS_DIR,
        "simple_plugin_templates",
    ),
)


def render(template_name: str, context: dict, **kwargs) -> str:
    context.update(kwargs)
    return helper_templates.render(template_name, context)


class Command(BaseModel):
    command: str
    install_func: BashFunction | None = None


class Installer(BaseModel):
    dependencies: List[Command] | None = None
    description: str | None = None

    def render(self, url: str):
        return render("install.sh", self.model_dump(), url=url)

    @field_validator("description", mode="before")
    def update_description(cls, value):
        if value:
            return textwrap.dedent(value)
        return value


class BaseJob(BaseModel, abc.ABC):
    job_func: BashFunction
    freq2cron_func: BashFunction
    need_root: bool = False

    @abc.abstractmethod
    def render(self, url: str):
        pass


class SingleJob(BaseJob):
    def render(self, url: str):
        return render("single_job.sh", self.model_dump(), url=url)


class MultiJob(BaseJob):
    job_options_func: BashFunction

    def render(self, url: str):
        return render("multi_job.sh", self.model_dump(), url=url)


def get_cron_frequency(freq: str):
    options = []
    if "m" in freq:
        options.append('m) echo "*/$number * * * *";;')
    if "h" in freq:
        options.append('h) echo "0 */$number * * *";;')
    if "d" in freq:
        options.append('d) echo "0 0 */$number * *";;')
    return BashFunction(
        body="""
        local frequency=$1
        local unit=${frequency: -1}
        local number=${frequency:0:${#frequency}-1}

        case $unit in
            {% for option in options -%}
            '_{{ option }}_'
            {% endfor -%}
            *) echo "Invalid frequency unit. Please use one of '_{{valids}}_'."
            exit 1 ;;
        esac
        """,
        name="get_cron_frequency",
        context={"options": options, "valids": ",".join(freq)},
    )


JOB_FREQUENCY_MINUTE_HOUR_DAY = get_cron_frequency("mhd")
JOB_FREQUENCY_HOUR_DAY = get_cron_frequency("hd")
JOB_FREQUENCY_DAY = get_cron_frequency("d")


class SensorValue(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: bool | int | float | str
    unit: str | None = None


class SimplePlugin(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    install: Installer
    manager: SingleJob | MultiJob
    parser: Callable[[str], Dict[str, SensorValue]]
