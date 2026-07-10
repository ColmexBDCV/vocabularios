# Metadata Schema Admin

Small SQLite-backed app for editing and publishing the metadata schema.

## Local setup

```sh
cd /Users/asmartinez/Documents/Codex/2026-06-29/files-mentioned-by-the-user-implement/outputs/metadata-schema-admin
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py init-db
python app.py import-schema
python app.py create-admin --username admin --password "CHANGE_THIS_PASSWORD"
python app.py run --port 8030
```

Open:

```text
http://localhost:8030/login
```

Public schema routes:

```text
http://localhost:8030/esquemas/metadatos/
http://localhost:8030/esquemas/metadatos.json
http://localhost:8030/esquemas/metadatos.jsonld
```

## Production notes

- Change the admin password before deployment.
- Set a stable `SECRET_KEY` environment variable.
- Put the app behind HTTPS.
- Back up `data/metadata.db`.
- Use Python 3.9 or newer.
- Use `gunicorn wsgi:application` behind a web server or institutional hosting platform.
- See `DEPLOYMENT.md` for the Biblioteca server handoff notes.

Do not publish a database that still uses a temporary local password.
