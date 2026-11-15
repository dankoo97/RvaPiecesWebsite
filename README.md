## RVA Pieces Static Website

### Required Tools
```aiignore
uv (https://docs.astral.sh/uv/getting-started/installation/)
Npm
Docker and Docker Compose (optional, only for running in containers)
A modern IDE (Intellij, VSCode, etc.) w/ any relevant plugins
A modern browser
```

uv installs Python 3.13 and all the Python packages (Django included) for you, so you don't
need to install them yourself.

Check out the live website at rvapieces.org

### How to run
1. In the root directory create a .env file
    ```aiignore
    # Example .env file
    DJANGO_SETTINGS_MODULE=RvaPiecesWebsite.settings
    DJANGO_SECRET_KEY={your secret key}
    DEBUG=True
    DJANGO_LOGLEVEL=info
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
    LICHESS_API_TOKEN={your lichess api token}
    CHESSNUT_API_KEY={your chessnut api key}
    # Rvapieces club id
    CHESSNUT_CLUB_ID=945
    # Disables page caching
    CACHE_MIDDLEWARE_SECONDS=0
    ```
2. Generate a secret key for django (https://djecrety.ir/)
3. Install the Python packages with `uv sync --group dev`. This creates `.venv` from `uv.lock`,
   including the dev tools (ruff, djlint, pre-commit)
4. Install the git hooks with `uv run pre-commit install`
5. Install npm packages with `npm install`
6. Apply the database migrations with `uv run --env-file .env python manage.py migrate`
7. Run the server with `uv run --env-file .env python manage.py runserver`
8. Visit http://localhost:8000

Nothing in the code reads `.env` by itself, so pass `--env-file .env` to `uv run` (or set
`UV_ENV_FILE=.env` in your shell once and leave the flag off). `uv run` uses the project's
`.venv` without having to activate it. You can also activate it yourself
(`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` elsewhere) if you'd rather
run `python manage.py ...` directly.

To add or upgrade a package, use `uv add <package>` (or `uv add --group dev <package>`) and
commit the updated `pyproject.toml` and `uv.lock`. Don't edit `uv.lock` by hand.

To run the tests: \
```uv run --env-file .env python manage.py test```

To apply css: \
Open a terminal and run \
```uv run --env-file .env python manage.py sass static/scss static/styles --watch```

To apply js: \
Open a terminal and run \
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
  `dev-static/` and never overwrites existing media files.
- The dev site reads from the live Lichess/Chessnut/Discord services but can't create anything
  on them (`EXTERNAL_WRITES_ENABLED=False`): submitting a game or sharing to Discord shows a
  warning instead. Guard any new outside-service write with
  `helpers.external_writes.require_external_writes(...)`.
- `static/images/404blunder.gif` is too large for git. It's served from
  `gs://rva-pieces-website_media/images/404blunder.gif`.

One-time setup of the GitHub → Google Cloud connection: `scripts/setup-github-deploy.sh`.

### Environment variables in Cloud Run
The code reads all configuration from environment variables (`os.environ`, mostly in
`RvaPiecesWebsite/settings.py`). For the deployed sites they're defined in `deploy/env/`:

- `common.yaml`: settings shared by prod and dev
- `prod.yaml` / `dev.yaml`: per-environment values, which override `common.yaml`

Each file has an `env:` section (plain values) and a `secrets:` section that maps an env var to a
Secret Manager secret, e.g. `LICHESS_API_TOKEN: "LICHESS_API_TOKEN:latest"`. Every deploy applies
the merged settings **in full**: anything not in the files is removed, and changes made in the
Cloud Run console are undone on the next deploy.

- **Change or add a plain value:** edit the YAML and open a PR. It takes effect on the next
  deploy of that environment.
- **Change a secret's value:** add a new version in Secret Manager. References ending in `:latest`
  pick it up on the next deploy, with no repo change needed. A pinned one (e.g. `:4`) needs its
  version bumped in the YAML.
- **Add a secret:** create it in Secret Manager, grant `django-gcs-access@rva-pieces-website.iam.gserviceaccount.com`
  the *Secret Manager Secret Accessor* role on it, then add it under `secrets:`.
- **Give dev its own value** (e.g. a test token): override the key in `dev.yaml`.

Locally, the same variables come from your `.env` file.

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
