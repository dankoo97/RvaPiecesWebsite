## RVA Pieces Static Website

### Required Tools
```aiignore
Docker
Docker Compose
Python 3.12+
Django
Pipenv
A modern IDE (Intellij, VSCode, etc.) w/ any relevant plugins
A modern browser
```

### How to run
1. In the root directory create a .env file
    ```aiignore
    # Example .env file
    DJANGO_SETTINGS_MODULE="RvaPiecesWebsite.settings"
    DJANGO_SECRET_KEY="{your secret key}"
    DEBUG=True
    DJANGO_LOGLEVEL=info
    DJANGO_ALLOWED_HOSTS="localhost, 127.0.0.1"
    DATABASE_ENGINE=postgresql_psycopg2
    DATABASE_NAME=rvapiecessite
    DATABASE_USERNAME=dbuser
    DATABASE_PASSWORD=dbpassword
    DATABASE_HOST=db
    DATABASE_PORT=5432
    ```
2. Generate a secret key for django (https://djecrety.ir/)
3. Create a lock file with `pipenv install`
4. Start up the python environment with `pipenv shell`
5. Create the database migrations with `python manage.py makemigrations`
6. Build the image with `docker compose build`
7. Start up the container with `docker compose up`
8. Navigate to http://localhost:8000/ and verify that the site is running
9. Create a superuser with `docker compose exec -it web python manage.py createsuperuser`
10. Navigate to http://localhost:8000/admin/ and login with the credentials you just created to start populating the database
