## RVA Pieces Static Website

### Required Tools
```aiignore
Docker
Docker Compose
Python 3.12
Django
Pipenv
A modern IDE (Intellij, VSCode, etc.)
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
2. Then run `docker compose up`
3. Go to http://localhost:8000/
