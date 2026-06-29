# Catálogo público de vocabularios locales

Portable static catalog for publishing repository-local RDF vocabularies outside Hyrax.

## Published routes

Deploy the contents of this directory at your web root to expose:

- `/vocabularios`
- `/vocabularios/seaes`
- `/vocabularios/seaes.ttl`
- `/vocabularios/seaes.jsonld`

The SEAES namespace is intentionally stable and should not be replaced:

```text
https://biblioteca.colmex.mx/vocabularios/seaes#
```

## Placeholders to replace

- `PLACEHOLDER_SERVER_NAME`: production hostname in web server examples.
- `PLACEHOLDER_WEB_ROOT`: absolute filesystem path where this package is deployed.
- `PLACEHOLDER_HYRAX_APP_PATH`: absolute filesystem path to the Hyrax application.

## Validation

From this directory:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-test.txt
python tests/validate_vocab.py
```

The test checks that Turtle and JSON-LD parse as RDF, define the same SEAES properties and controlled values, and keep the expected labels and definitions.

## Deployment

Copy this directory to any static host, Apache/Nginx document root, object storage static website, or CDN origin. The files are plain HTML, CSS, Turtle, and JSON-LD.

For extensionless HTML routes, configure the web server to resolve:

- `/vocabularios` to `/vocabularios/index.html`
- `/vocabularios/seaes` to `/vocabularios/seaes/index.html`

Example web server snippets are in `config/`.

## Production checklist

- Serve over HTTPS.
- Replace `PLACEHOLDER_SERVER_NAME` and `PLACEHOLDER_WEB_ROOT` in server config examples.
- Keep directory listing disabled.
- Serve `.ttl` as `text/turtle`.
- Serve `.jsonld` as `application/ld+json`.
- Use the security headers shown in `config/`.
- Deploy only the public static files needed by the site; do not expose temporary virtual environments or server logs.
- Keep the namespace stable once published.

## Future vocabularies

See `docs/add-future-vocabularies.md`.

## Hyrax integration

This package is intentionally outside Hyrax. Use the URI namespace and controlled value list in Hyrax metadata configuration. See `docs/hyrax-integration-placeholders.md`.
