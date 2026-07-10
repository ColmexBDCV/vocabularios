# Despliegue en biblioteca.colmex.mx

Esta aplicación publica el catálogo público de vocabularios y un administrador para el esquema de metadatos.

## URLs esperadas

- Catálogo público: `https://biblioteca.colmex.mx/vocabularios/`
- Vocabulario SEAES: `https://biblioteca.colmex.mx/vocabularios/seaes/`
- Esquema de metadatos: `https://biblioteca.colmex.mx/esquemas/metadatos/`
- JSON del esquema: `https://biblioteca.colmex.mx/esquemas/metadatos.json`
- JSON-LD del esquema: `https://biblioteca.colmex.mx/esquemas/metadatos.jsonld`
- Administración: `https://biblioteca.colmex.mx/vocabularios/admin`

## Requisito crítico de Python

La aplicación requiere Python 3.9 o superior.

El servidor reporta Python 3.5.2 como versión instalada globalmente. Esa versión no es compatible con esta aplicación ni con las versiones actuales de Flask/Gunicorn. Se recomienda crear un ambiente virtual específico con Python 3.9 o superior.

Ejemplo:

```sh
cd /var/www/vocabularios
python3.9 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Variables de entorno

Configurar al menos:

```sh
export SECRET_KEY="VALOR_LARGO_ALEATORIO"
export METADATA_DB="/var/www/vocabularios/data/metadata.db"
```

Notas:

- `SECRET_KEY` debe ser estable. Si cambia, se invalidan sesiones.
- `METADATA_DB` debe apuntar a una ruta persistente y respaldada.
- La base SQLite puede vivir dentro de la carpeta de la aplicación si esa carpeta se respalda y no se borra durante actualizaciones.

## Inicialización

Solo la primera vez:

```sh
cd /var/www/vocabularios
. .venv/bin/activate
python app.py init-db
python app.py import-schema
python app.py create-admin --username admin --password "CAMBIAR_ESTA_CONTRASENA"
```

Después de iniciar sesión, la contraseña se puede cambiar desde:

```text
https://biblioteca.colmex.mx/vocabularios/admin/password
```

## Ejecución con Gunicorn

Ejemplo de proceso local detrás de Nginx/Apache:

```sh
cd /var/www/vocabularios
. .venv/bin/activate
gunicorn --workers 2 --bind 127.0.0.1:8030 wsgi:application
```

## Proxy reverso

La arquitectura indicada es Nginx como proxy reverso y Apache2 como servidor de aplicaciones. La configuración exacta depende de su esquema institucional, pero la regla debe enviar estas rutas a la aplicación:

```text
/vocabularios/
/vocabularios/admin
/vocabularios/admin/
/vocabularios/login
/vocabularios/logout
/esquemas/
/esquemas/metadatos/
/esquemas/metadatos.json
/esquemas/metadatos.jsonld
/assets/
```

Si se prefiere que absolutamente todo viva debajo de `/vocabularios/`, entonces el esquema puede publicarse bajo:

```text
/vocabularios/esquemas/metadatos/
/vocabularios/esquemas/metadatos.json
/vocabularios/esquemas/metadatos.jsonld
```

Esa decisión debe confirmarse antes de cerrar la configuración final de proxy.

## Actualizaciones

Para actualizar código sin perder datos:

1. Detener el proceso de la aplicación.
2. Reemplazar archivos de código.
3. No borrar `data/metadata.db`.
4. Activar el ambiente virtual.
5. Ejecutar cualquier migración futura si existiera.
6. Reiniciar Gunicorn/proceso WSGI.

## Respaldo

Respaldar:

```text
/var/www/vocabularios/data/metadata.db
```

El archivo SQLite contiene los cambios hechos desde el administrador.

