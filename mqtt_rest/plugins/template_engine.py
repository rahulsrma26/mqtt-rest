import hashlib
import textwrap
from typing import Any

from fastapi.responses import PlainTextResponse
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, model_validator


def get_environment(*args, **kwargs):
    return Environment(
        *args,
        **kwargs,
        variable_start_string="'_{{",
        variable_end_string="}}_'",
        comment_start_string="{#=%",
        comment_end_string="%=#}",
    )


class BashFunction(BaseModel):
    body: str
    name: str | None = None
    context: dict | None = None

    @model_validator(mode="before")
    @classmethod
    def update_name(cls, data: Any) -> Any:
        if not data.get("name"):
            data["name"] = "f" + hashlib.md5(data["body"].encode()).hexdigest()
        return data


def function(func: dict, indent: int = 0, spaces: int = 4) -> str:
    func = BashFunction(**func)
    text = func.body
    if func.context:
        text = get_environment().from_string(func.body).render(func.context)
    template = f"\n{func.name}() {{"
    template += textwrap.indent(textwrap.dedent(text), " " * spaces)
    template += "}"
    return textwrap.indent(template, " " * spaces * indent)


def echo(text: str, indent: int = 0, spaces: int = 4) -> str:
    lines = textwrap.dedent(text).splitlines()
    lines = [textwrap.indent(f'echo "{line}"', " " * spaces * indent) for line in lines]
    return "\n" + "\n".join(lines)


class TemplateEngine:
    def __init__(self, dir_path: str) -> None:
        self.dir_path = dir_path
        self.env = get_environment(loader=FileSystemLoader(dir_path))

    def render(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        template.globals.update(
            {
                "function": function,
                "echo": echo,
            }
        )
        return PlainTextResponse(template.render(context))
