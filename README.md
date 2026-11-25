# Parish Cards

Simple Flask web application to track parish memberhips, applications for membership, member dues and other payments. More work to follow.

## Docker

nginx terminates TLS with a snakeoil certificate and proxies to gunicorn. There is no database container. The SQLite file is `StJohnDC.db` on a mounted host directory, at `/data/StJohnDC.db` inside the app container. The directory is mounted, rather than the file alone, so SQLite can keep its journal next to the database.

XeLaTeX and the Liberation fonts are installed in the app image. Report templates select Liberation Sans by name.

```sh
cp .env.example .env
# set SECRET_KEY in .env
docker compose up --build -d
```

`.env.example` points `CARDS_DATABASE_DIR` at `..`, which is the folder that already holds `StJohnDC.db` for the Makefile. Set `CARDS_DATABASE_DIR=./data` to mount only the `data/` directory in this repo.

`SSL_PORT` in `.env` is the HTTPS port (443 by default). Open https://localhost/ when it is 443, and https://localhost:$SSL_PORT/ otherwise. Port 80 redirects to that HTTPS port.

`SSL_CERTIFICATE` and `SSL_CERTIFICATE_KEY` are the certificate and private key paths inside the nginx container. They default to the built-in snakeoil pair, which is self-signed for localhost, so the browser will warn until you accept it. `SSL_CERT_DIR` is a host directory mounted at `/etc/nginx/ssl`. Put your own files in that directory, point the two paths at `/etc/nginx/ssl/<file>`, and run `docker compose up -d`.

```sh
docker compose logs -f
docker compose down
```

### Copy the database

`StJohnDC.db` is the file `/data/StJohnDC.db` in the `app` container. Stop `app` before copying so SQLite is not writing the file. The container has to exist, so run `docker compose up -d` once before the first copy.

Copy a database file into the volume:

```sh
docker compose stop app
docker compose cp ~/Backups/StJohnDC.db app:/data/StJohnDC.db
docker compose start app
```

Copy the database file out of the volume:

```sh
docker compose stop app
docker compose cp app:/data/StJohnDC.db ~/Backups/StJohnDC.db
docker compose start app
```

That file is also on the host at `$CARDS_DATABASE_DIR/StJohnDC.db`. With `CARDS_DATABASE_DIR=..`, the host path is `../StJohnDC.db`.
