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

### Branches and deployments
Deploys are automatic (`.github/workflows/deploy.yml`), all to the `rva-pieces-website` Cloud Run service:

| Branch | Cloud Run tag | URL | Database |
|---|---|---|---|
| `main` | `prod` (100% traffic) | https://rvapieces.org | `gs://rva-pieces-website_db/db.sqlite3` |
| `dev` | `dev` (0% traffic) | https://dev---rva-pieces-website-7er2of6acq-uk.a.run.app | `gs://rva-pieces-website_db/dev/db.sqlite3` |

- `main` is always what's live. It only accepts PRs, normally from `dev` or `hotfix/*`.
- Work on a feature branch off `dev`, then open a PR into `dev`. Merging deploys it to the dev site.
- **Every dev deploy copies the production database to the dev database first**, so dev has
  real data, and changes made on the dev site never touch production. Anything saved on the dev
  site is wiped on the next dev deploy.
- To test a feature branch on the dev site before merging, take over `dev` with
  `gh workflow run deploy.yml --ref <your-branch>` (or Actions → Deploy to Cloud Run → Run workflow,
  pick your branch). The next push to `dev` puts `dev` back.
- The dev site shares the media bucket with production. It stores its static files under
  `dev-static/` and never overwrites existing media files, but **it does use the real
  Discord webhooks and Lichess/Chessnut credentials**, so be careful with actions that post to them.

One-time setup of the GitHub → Google Cloud connection: `scripts/setup-github-deploy.sh`.

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
