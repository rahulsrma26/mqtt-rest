import textwrap
from functools import wraps
from mqtt_rest.plugins.template_engine import get_environment


def bash_function():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs) -> str:
            result = func(*args, **kwargs)
            if not isinstance(result, str):
                raise ValueError("The function must return a string")
            return (
                f"\n{func.__name__}() {{" + textwrap.indent(textwrap.dedent(result), " " * 4) + "}"
            )

        return wrapper

    return decorator


@bash_function()
def get_cron_frequency(freq: str):
    options = []
    if "m" in freq:
        options.append('m) echo "*/$number * * * *";;')
    if "h" in freq:
        options.append('h) echo "0 */$number * * *";;')
    if "d" in freq:
        options.append('d) echo "0 0 */$number * *";;')
    template = get_environment().from_string("""
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
    """)
    return template.render(options=options, valids=",".join(freq))


JOB_FREQUENCY_MINUTE_HOUR_DAY = get_cron_frequency("mhd")
JOB_FREQUENCY_HOUR_DAY = get_cron_frequency("hd")
JOB_FREQUENCY_DAY = get_cron_frequency("d")
