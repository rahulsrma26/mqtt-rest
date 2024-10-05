import os
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
