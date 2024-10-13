import textwrap

from fastapi.responses import PlainTextResponse
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel


def get_environment(*args, **kwargs):
    return Environment(
        *args,
        **kwargs,
        variable_start_string="'{{",
        variable_end_string="}}'",
        comment_start_string="{#=%",
        comment_end_string="%=#}",
    )


class BashFunction(BaseModel):
    name: str
    body: str
    context: dict | None = None


def function(func: dict, indent: int = 0, spaces: int = 4, call_afterwards: bool = False) -> str:
    func = BashFunction(**func)
    text = func.body
    if func.context:
        text = get_environment().from_string(func.body).render(func.context)
    template = f"\n{func.name}() {{"
    template += textwrap.indent(textwrap.dedent(text), " " * spaces)
    template += "}"
    if call_afterwards:
        template += f"\n{func.name}"
    return textwrap.indent(template, " " * spaces * indent)


class TemplateEngine:
    def __init__(self, dir_path: str) -> None:
        self.dir_path = dir_path
        self.env = get_environment(loader=FileSystemLoader(dir_path))

    def render(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        template.globals.update(
            {
                "function": function,
            }
        )
        return PlainTextResponse(template.render(context))
