from __future__ import annotations

import argparse
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from urllib.parse import quote, urlparse

from flask import Flask, Response, flash, g, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


APP_ROOT = Path(__file__).resolve().parent
DEFAULT_DB = APP_ROOT / "data" / "metadata.db"
DEFAULT_SCHEMA = APP_ROOT / "scripts" / "metadatos.seed.json"
PUBLIC_ROOT = APP_ROOT / "public"
SCHEMA_BASE = "https://biblioteca.colmex.mx/esquemas/metadatos"
MAINTAINER = "CID_BIBLIOTECA_COLMEX"
ISSUED = "2026-07-03"


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["DATABASE"] = Path(os.environ.get("METADATA_DB", DEFAULT_DB))
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex(32))

    @app.before_request
    def open_database():
        g.db = connect_db(app.config["DATABASE"])

    @app.teardown_request
    def close_database(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.get("/")
    def root():
        return redirect("/vocabularios/")

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.get("/vocabularios/static/<path:filename>")
    def prefixed_static(filename: str):
        return send_from_directory(APP_ROOT / "static", filename)

    @app.get("/assets/<path:filename>")
    @app.get("/vocabularios/assets/<path:filename>")
    def public_assets(filename: str):
        return send_from_directory(PUBLIC_ROOT / "assets", filename)

    @app.get("/vocabularios/")
    def vocabulary_catalog():
        return send_from_directory(PUBLIC_ROOT / "vocabularios", "index.html")

    @app.get("/vocabularios/seaes/")
    def seaes_vocabulary():
        return send_from_directory(PUBLIC_ROOT / "vocabularios" / "seaes", "index.html")

    @app.get("/vocabularios/seaes.ttl")
    def seaes_turtle():
        return send_from_directory(PUBLIC_ROOT / "vocabularios", "seaes.ttl", mimetype="text/turtle")

    @app.get("/vocabularios/seaes.jsonld")
    def seaes_jsonld():
        return send_from_directory(PUBLIC_ROOT / "vocabularios", "seaes.jsonld", mimetype="application/ld+json")

    @app.get("/esquemas/")
    @app.get("/vocabularios/esquemas/")
    def schema_catalog():
        return send_from_directory(PUBLIC_ROOT / "esquemas", "index.html")

    @app.get("/vocabularios/login")
    @app.get("/login")
    def login_form():
        return render_template("login.html")

    @app.post("/vocabularios/login")
    @app.post("/login")
    def login():
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = g.db.execute("select * from users where username = ?", (username,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Usuario o contraseña incorrectos.")
            return redirect(url_for("login_form"))
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["csrf_token"] = secrets.token_urlsafe(32)
        return redirect(admin_path(""))

    @app.post("/vocabularios/logout")
    @app.post("/logout")
    @login_required
    def logout():
        session.clear()
        return redirect(auth_path("/login"))

    @app.get("/vocabularios/admin/password")
    @app.get("/admin/password")
    @login_required
    def password_form():
        return render_template("change_password.html")

    @app.post("/vocabularios/admin/password")
    @app.post("/admin/password")
    @login_required
    @csrf_required
    def change_password():
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        user = g.db.execute("select * from users where id = ?", (session["user_id"],)).fetchone()
        if not user or not check_password_hash(user["password_hash"], current_password):
            flash("La contraseña actual no es correcta.")
            return redirect(admin_path("/password"))
        if len(new_password) < 12:
            flash("La nueva contraseña debe tener al menos 12 caracteres.")
            return redirect(admin_path("/password"))
        if new_password != confirm_password:
            flash("La confirmación no coincide con la nueva contraseña.")
            return redirect(admin_path("/password"))
        g.db.execute(
            "update users set password_hash = ? where id = ?",
            (generate_password_hash(new_password, method="pbkdf2:sha256"), session["user_id"]),
        )
        g.db.commit()
        flash("Contraseña actualizada.")
        return redirect(admin_path("/fields"))

    @app.get("/vocabularios/admin")
    @app.get("/admin")
    @login_required
    def admin_index():
        return render_template("admin_home.html")

    @app.get("/vocabularios/admin/fields")
    @app.get("/admin/fields")
    @login_required
    def admin_fields():
        fields = fetch_fields(g.db)
        return render_template("admin_fields.html", fields=fields)

    @app.get("/vocabularios/admin/fields/new")
    @app.get("/admin/fields/new")
    @login_required
    def new_field():
        return render_template("field_form.html", field=empty_field(), action=admin_path("/fields"))

    @app.post("/vocabularios/admin/fields")
    @app.post("/admin/fields")
    @login_required
    @csrf_required
    def create_field():
        field = form_to_field(request.form)
        errors = validate_field(field)
        if errors:
            for error in errors:
                flash(error)
            return render_template("field_form.html", field=field, action=admin_path("/fields")), 400
        save_field(g.db, field)
        flash("Campo creado.")
        return redirect(admin_path("/fields"))

    @app.get("/vocabularios/admin/fields/<path:field_id>/edit")
    @app.get("/admin/fields/<path:field_id>/edit")
    @login_required
    def edit_field(field_id: str):
        field = get_field(g.db, field_id)
        if not field:
            flash("Campo no encontrado.")
            return redirect(admin_path("/fields"))
        return render_template("field_form.html", field=field, action=admin_field_path(field_id))

    @app.post("/vocabularios/admin/fields/<path:field_id>")
    @app.post("/admin/fields/<path:field_id>")
    @login_required
    @csrf_required
    def update_field(field_id: str):
        field = form_to_field(request.form)
        field["id"] = field_id
        errors = validate_field(field)
        if errors:
            for error in errors:
                flash(error)
            return render_template("field_form.html", field=field, action=admin_field_path(field_id)), 400
        save_field(g.db, field)
        flash("Campo actualizado.")
        return redirect(admin_path("/fields"))

    @app.post("/vocabularios/admin/fields/<path:field_id>/delete")
    @app.post("/admin/fields/<path:field_id>/delete")
    @login_required
    @csrf_required
    def delete_field(field_id: str):
        g.db.execute("delete from fields where id = ?", (field_id,))
        g.db.commit()
        flash("Campo eliminado.")
        return redirect(admin_path("/fields"))

    @app.get("/vocabularios/esquemas/metadatos/")
    @app.get("/esquemas/metadatos/")
    def public_schema():
        fields = fetch_fields(g.db)
        return render_template("public_schema.html", fields=fields, schema_base=SCHEMA_BASE, issued=ISSUED, maintainer=MAINTAINER)

    @app.get("/vocabularios/esquemas/metadatos.json")
    @app.get("/esquemas/metadatos.json")
    def public_schema_json():
        data = schema_json(fetch_fields(g.db))
        return Response(json.dumps(data, ensure_ascii=False, indent=2) + "\n", mimetype="application/json")

    @app.get("/vocabularios/esquemas/metadatos.jsonld")
    @app.get("/esquemas/metadatos.jsonld")
    def public_schema_jsonld():
        data = schema_jsonld(fetch_fields(g.db))
        return Response(json.dumps(data, ensure_ascii=False, indent=2) + "\n", mimetype="application/ld+json")

    @app.context_processor
    def inject_paths():
        return {
            "admin_path": admin_path,
            "admin_field_path": admin_field_path,
            "auth_path": auth_path,
        }

    return app


def connect_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    return db


def init_db(path: Path) -> None:
    db = connect_db(path)
    db.executescript(
        """
        create table if not exists users (
          id integer primary key autoincrement,
          username text not null unique,
          password_hash text not null,
          created_at text not null
        );

        create table if not exists fields (
          id text primary key,
          code text not null,
          labels_json text not null default '[]',
          templates_json text not null default '[]',
          predicates_json text not null default '[]',
          uris_json text not null default '[]',
          marc_json text not null default '[]',
          notes_json text not null default '[]',
          proposal_notes_json text not null default '[]',
          source_sheets_json text not null default '[]',
          usage_json text not null default '{}',
          mapping_hints_json text not null default '{}',
          multiple integer,
          required integer,
          in_use integer,
          ai_use_description text not null default '',
          confidence_notes text not null default '',
          updated_at text not null
        );
        create index if not exists idx_fields_code on fields(code);
        """
    )
    db.commit()
    db.close()


def import_schema(path: Path, schema_path: Path) -> None:
    init_db(path)
    data = json.loads(schema_path.read_text(encoding="utf-8"))
    db = connect_db(path)
    for field in data["fields"]:
        save_field(db, field)
    db.close()


def create_admin(path: Path, username: str, password: str) -> None:
    init_db(path)
    db = connect_db(path)
    db.execute(
        """
        insert into users (username, password_hash, created_at)
        values (?, ?, ?)
        on conflict(username) do update set password_hash = excluded.password_hash
        """,
        (username, generate_password_hash(password, method="pbkdf2:sha256"), now()),
    )
    db.commit()
    db.close()


def production_prefixed_request() -> bool:
    return request.path.startswith("/vocabularios/")


def auth_path(path: str) -> str:
    prefix = "/vocabularios" if production_prefixed_request() else ""
    return f"{prefix}{path}"


def admin_path(path: str = "") -> str:
    prefix = "/vocabularios" if production_prefixed_request() else ""
    return f"{prefix}/admin{path}"


def admin_field_path(field_id: str, suffix: str = "") -> str:
    return f"{admin_path('/fields')}/{quote(field_id, safe='')}{suffix}"


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(auth_path("/login"))
        return view(*args, **kwargs)

    return wrapper


def csrf_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if request.form.get("csrf_token") != session.get("csrf_token"):
            flash("La sesión expiró. Inténtelo de nuevo.")
            return redirect(auth_path("/login"))
        return view(*args, **kwargs)

    return wrapper


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def loads(value: str, fallback):
    try:
        return json.loads(value)
    except Exception:
        return fallback


def row_to_field(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "code": row["code"],
        "labels": loads(row["labels_json"], []),
        "templates": loads(row["templates_json"], []),
        "predicates": loads(row["predicates_json"], []),
        "uris": loads(row["uris_json"], []),
        "marc": loads(row["marc_json"], []),
        "notes": loads(row["notes_json"], []),
        "proposalNotes": loads(row["proposal_notes_json"], []),
        "sourceSheets": loads(row["source_sheets_json"], []),
        "usage": loads(row["usage_json"], {}),
        "mappingHints": loads(row["mapping_hints_json"], {}),
        "multiple": int_to_bool(row["multiple"]),
        "required": int_to_bool(row["required"]),
        "inUse": int_to_bool(row["in_use"]),
        "aiUseDescription": row["ai_use_description"],
        "confidenceNotes": row["confidence_notes"],
        "updatedAt": row["updated_at"],
    }


def fetch_fields(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute("select * from fields order by lower(code)").fetchall()
    return [row_to_field(row) for row in rows]


def get_field(db: sqlite3.Connection, field_id: str) -> dict | None:
    row = db.execute("select * from fields where id = ?", (field_id,)).fetchone()
    return row_to_field(row) if row else None


def save_field(db: sqlite3.Connection, field: dict) -> None:
    db.execute(
        """
        insert into fields (
          id, code, labels_json, templates_json, predicates_json, uris_json, marc_json,
          notes_json, proposal_notes_json, source_sheets_json, usage_json, mapping_hints_json,
          multiple, required, in_use, ai_use_description, confidence_notes, updated_at
        )
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(id) do update set
          code = excluded.code,
          labels_json = excluded.labels_json,
          templates_json = excluded.templates_json,
          predicates_json = excluded.predicates_json,
          uris_json = excluded.uris_json,
          marc_json = excluded.marc_json,
          notes_json = excluded.notes_json,
          proposal_notes_json = excluded.proposal_notes_json,
          source_sheets_json = excluded.source_sheets_json,
          usage_json = excluded.usage_json,
          mapping_hints_json = excluded.mapping_hints_json,
          multiple = excluded.multiple,
          required = excluded.required,
          in_use = excluded.in_use,
          ai_use_description = excluded.ai_use_description,
          confidence_notes = excluded.confidence_notes,
          updated_at = excluded.updated_at
        """,
        (
            field["id"],
            field["code"],
            json.dumps(field.get("labels", []), ensure_ascii=False),
            json.dumps(field.get("templates", []), ensure_ascii=False),
            json.dumps(field.get("predicates", []), ensure_ascii=False),
            json.dumps(field.get("uris", []), ensure_ascii=False),
            json.dumps(field.get("marc", []), ensure_ascii=False),
            json.dumps(field.get("notes", []), ensure_ascii=False),
            json.dumps(field.get("proposalNotes", []), ensure_ascii=False),
            json.dumps(field.get("sourceSheets", []), ensure_ascii=False),
            json.dumps(field.get("usage", {}), ensure_ascii=False),
            json.dumps(field.get("mappingHints", {}), ensure_ascii=False),
            bool_to_int(field.get("multiple")),
            bool_to_int(field.get("required")),
            bool_to_int(field.get("inUse")),
            field.get("aiUseDescription", ""),
            field.get("confidenceNotes", ""),
            now(),
        ),
    )
    db.commit()


def int_to_bool(value):
    if value is None:
        return None
    return bool(value)


def bool_to_int(value):
    if value is None or value == "":
        return None
    return 1 if value is True or value == "true" else 0


def lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def one(value: str) -> list[str]:
    value = value.strip()
    return [value] if value else []


def form_bool(name: str):
    value = request.form.get(name, "")
    if value == "":
        return None
    return value == "true"


def form_to_field(form) -> dict:
    code = form.get("code", "").strip()
    field_id = form.get("id", "").strip()
    return {
        "id": field_id,
        "code": code,
        "labels": one(form.get("labels", "")),
        "templates": one(form.get("templates", "")),
        "predicates": one(form.get("predicates", "")),
        "uris": one(form.get("uris", "")),
        "marc": one(form.get("marc", "")),
        "notes": lines(form.get("notes", "")),
        "proposalNotes": lines(form.get("proposalNotes", "")),
        "sourceSheets": lines(form.get("sourceSheets", "")),
        "usage": {
            key: True
            for key in ["facet", "userVisible", "thesis", "books", "videos", "colmexJournalArticles"]
            if form.get(f"usage_{key}") == "true"
        },
        "mappingHints": {"matchTerms": lines(form.get("matchTerms", ""))},
        "multiple": form_bool("multiple"),
        "required": form_bool("required"),
        "inUse": form_bool("inUse"),
        "aiUseDescription": form.get("aiUseDescription", "").strip(),
        "confidenceNotes": form.get("confidenceNotes", "").strip(),
    }


def valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_field(field: dict) -> list[str]:
    errors = []
    required_scalars = {
        "id": "URI del campo",
        "code": "Campo Hyrax (código)",
        "aiUseDescription": "Descripción para mapeo con IA",
    }
    required_lists = {
        "labels": "Descriptores",
        "templates": "Plantilla",
        "predicates": "Predicados",
        "uris": "URI de predicado",
        "marc": "MARC",
    }
    for key, label in required_scalars.items():
        if not str(field.get(key, "")).strip():
            errors.append(f"{label} es obligatorio.")
    for key, label in required_lists.items():
        if not field.get(key):
            errors.append(f"{label} es obligatorio.")
    for key, label in {"multiple": "Multiple?", "required": "Obligatorio para el sistema", "inUse": "En uso"}.items():
        if field.get(key) is None:
            errors.append(f"{label} es obligatorio.")
    if not field.get("mappingHints", {}).get("matchTerms"):
        errors.append("Términos de coincidencia para IA es obligatorio.")
    if field.get("id") and not valid_url(field["id"]):
        errors.append("URI del campo debe ser una URL válida que empiece con http:// o https://.")
    for uri in field.get("uris", []):
        if not valid_url(uri):
            errors.append("URI de predicado debe ser una URL válida que empiece con http:// o https://.")
    return errors


def empty_field() -> dict:
    return {
        "id": "",
        "code": "",
        "labels": [],
        "templates": [],
        "predicates": [],
        "uris": [],
        "marc": [],
        "notes": [],
        "proposalNotes": [],
        "sourceSheets": [],
        "usage": {},
        "mappingHints": {"matchTerms": []},
        "multiple": None,
        "required": None,
        "inUse": None,
        "aiUseDescription": "",
        "confidenceNotes": "",
    }


def slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_") or "campo"


def schema_json(fields: list[dict]) -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}.json",
        "title": "Esquema de metadatos de la Biblioteca Daniel Cosío Villegas",
        "description": "Esquema publicado para apoyar el mapeo de campos externos a términos de metadatos.",
        "issued": ISSUED,
        "maintainer": MAINTAINER,
        "namespace": f"{SCHEMA_BASE}#",
        "fields": fields,
    }


def schema_jsonld(fields: list[dict]) -> dict:
    graph = [
        {
            "@id": SCHEMA_BASE,
            "@type": ["skos:ConceptScheme", "schema:DefinedTermSet"],
            "dcterms:title": {"@value": "Esquema de metadatos de la Biblioteca Daniel Cosío Villegas", "@language": "es"},
            "dcterms:issued": ISSUED,
            "dcterms:publisher": MAINTAINER,
        }
    ]
    for field in fields:
        label = field["labels"][0] if field["labels"] else field["code"]
        graph.append(
            {
                "@id": field["id"],
                "@type": ["skos:Concept", "schema:DefinedTerm"],
                "skos:prefLabel": {"@value": label, "@language": "es"},
                "skos:notation": field["code"],
                "skos:inScheme": {"@id": SCHEMA_BASE},
                "schema:identifier": field["code"],
                "schema:name": label,
                "schema:alternateName": field.get("labels", [])[1:],
                "schema:description": field.get("aiUseDescription", ""),
                "schema:additionalType": field.get("predicates", []),
                "schema:sameAs": field.get("uris", []),
                "schema:isPartOf": field.get("templates", []),
                "schema:keywords": field.get("mappingHints", {}).get("matchTerms", []),
            }
        )
    return {
        "@context": {
            "dcterms": "http://purl.org/dc/terms/",
            "schema": "https://schema.org/",
            "skos": "http://www.w3.org/2004/02/skos/core#",
        },
        "@graph": graph,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init-db", "import-schema", "create-admin", "run"])
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8030)
    args = parser.parse_args()

    db_path = Path(args.db)
    if args.command == "init-db":
        init_db(db_path)
        print(f"Initialized {db_path}")
    elif args.command == "import-schema":
        import_schema(db_path, Path(args.schema))
        print(f"Imported {args.schema} into {db_path}")
    elif args.command == "create-admin":
        password = args.password or os.environ.get("ADMIN_PASSWORD")
        if not password:
            raise SystemExit("Provide --password or ADMIN_PASSWORD.")
        create_admin(db_path, args.username, password)
        print(f"Created/updated admin user {args.username}")
    elif args.command == "run":
        app = create_app()
        app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
