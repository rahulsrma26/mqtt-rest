from fastapi.responses import PlainTextResponse
from jinja2 import Environment, FileSystemLoader


class TemplateEngine:
    def __init__(self, dir_path: str) -> None:
        self.dir_path = dir_path
        self.env = Environment(
            loader=FileSystemLoader(dir_path),
            variable_start_string="'{{",
            variable_end_string="}}'",
            comment_start_string="{#=%",
            comment_end_string="%=#}",
        )

    def render(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return PlainTextResponse(template.render(context))
