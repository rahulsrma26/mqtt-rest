# MQTT-REST

MQTT-REST is a project that bridges MQTT and RESTful APIs, allowing seamless communication between IoT devices using MQTT and web services using REST.

It's useful if you want to monitor arbritary stuff from a machine in Home-assistant without writing custom integration.

## Development

```sh
git clone https://github.com/rahulsrma26/mqtt-rest
cd mqtt-rest
poetry shell
poetry install
poetry run python -m mqtt_rest.run
```

If you dont want poetry to managing virtual environment then dont need to run `poetry run` or `poetry shell`. In that case one can directly run `python -m mqtt_rest.run`.

Visit `/docs` endpoint to access API docs via SwaggerUI.

### Testing

```sh
poetry run pytest
```

### Linting

```sh
poetry run ruff check
```
