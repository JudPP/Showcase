This project was created from the official Django sample available in their [documentation](https://github.com/docker/awesome-compose/tree/master/official-documentation-samples/django/). 
# Installation
This project uses a [Dockerfile](https://docs.docker.com/engine/reference/builder/) to handle containerisation of the app and to set-up Python correctly.

To run the app use the command: 
- ``docker compose --env-file default.env up`` in the project folder.

The port is specified in the docker-compose.yml for the app as an environment variable, which the ``.env`` file handles.

To change the port use the command:
- ``"PORT=8000" docker compose up`` in the project folder (Linux Bash). 
- ``set "PORT=8000" && docker compose up`` in the project folder (Windows CMD).

## Updating
If the python dependencies have been changed use the command:
- ``docker compose --env-file default.env up --build`` in the project folder.

# Admin
## Automatic
The admin is generated automatically through the following environment variables:

``ENV DJANGO_SUPERUSER_PASSWORD=admin``
``ENV DJANGO_SUPERUSER_USERNAME=admin``
``ENV DJANGO_SUPERUSER_EMAIL=admin@admin.com``

## Manual
To create an admin user bash into the running container: <br>
- ``docker exec -t -i container_name /bin/bash``.

Then to interactively create the user run the command: <br>
- ``python manage.py createsuperuser``

## GOOGLE API
- To run the system you must first run calendarAPI.py and login to google to generate a token.