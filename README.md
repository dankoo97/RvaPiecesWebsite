## RVA Pieces Static Website

### Required Tools
```aiignore
Docker
Docker Compose
Npm
Python 3.13
Django
Pipenv
A modern IDE (Intellij, VSCode, etc.) w/ any relevant plugins
A modern browser
```

Check out the live website at rvapieces.org

### How to run
1. In the root directory create a .env file
    ```aiignore
    # Example .env file
    DJANGO_SETTINGS_MODULE="RvaPiecesWebsite.settings"
    DJANGO_SECRET_KEY="{your secret key}"
    DEBUG=True
    DJANGO_LOGLEVEL=info
    DJANGO_ALLOWED_HOSTS="localhost, 127.0.0.1"
    LICHESS_API_KEY={your lichess api key}
    CHESSNUT_API_KEY={your chessnut api key}
    CHESSNUT_CLUB_ID=945  // Rvapieces club id
    CACHE_MIDDLEWARE_SECONDS=0  // disables caching
    ```
2. Generate a secret key for django (https://djecrety.ir/)
3. Create a lock file with `pipenv install`
4. Install npm packages with `npm install`
5. Start up the python environment with `pipenv shell`
6. Create the database migrations with `python manage.py makemigrations`
7. Apply the database migrations with `python manage.py migrate`
8. Run the server with `python manage.py runserver`
9. Visit http://localhost:8000 (It should open automatically)

To apply css: \
Open a terminal and run \
```python manage.py sass static/scss static/styles --watch```

To apply js: \
Install npm, open a terminal and run \
```npm run watch:js```

To push changes to the live website:
1. Make sure the docker engine is running
2. Run `docker build -t {the name of the image} .`
3. Run `docker push {the name of the image}`
4. Go to the Google Cloud console and open the `rva-pieces-website` service
5. Click "Edit & deploy new revision"
6. Select the latest image url (it ***does not*** automatically select the latest revision)
7. Update any environment variables
8. Make sure that it is not automatically switching traffic to the new revision
9. Deploy
10. Set a revision tag for your change and test your changes there
11. If everything is working, switch traffic to the new revision

To use the live website's images locally:
1. Add `READ_FROM_CLOUD=True` to your `.env` file
2. Any media file that isn't in your local `media/` folder will be loaded from the `rva-pieces-website_media` bucket
3. Uploads still save to your local `media/` folder. The bucket is never written to
4. Optionally set `CLOUD_READ_BUCKET_NAME` to read from a different bucket

To download the latest database:
1. Go to the Google Cloud console and open Cloud Storage
2. Open the `rva-pieces-website_media` bucket
3. Find and download `db.sqlite3`
4. Replace your local database with the downloaded one
