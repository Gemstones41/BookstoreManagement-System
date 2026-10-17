# Bookstore Management System

CS492 group project: a Java 17 / Spring Boot 4.1.1 REST API with Spring Data JPA, MySQL, BCrypt registration, and JWT login. Maven Wrapper 3.10.0 is included. The current repository is an API backend; a complete browser storefront is not included.

## Run with Docker

Install and start Docker Desktop (or another Docker Engine with Compose v2+). Python 3 is used only to generate local credentials and run the optional verification script. Java, Maven, and MySQL do not need to be installed on the host.

From the repository root:

```sh
python3 scripts/setup-env.py
docker compose config --quiet
docker compose up --build --wait --wait-timeout 240
```

The setup script creates a private `.env` with independently generated database/root passwords and a 256-bit Base64 JWT key. It refuses to overwrite existing settings. Compose refuses to start with missing or empty secrets. Keep `.env` stable across restarts and out of Git; `.env.example` documents the fields without providing credentials. Changing MySQL passwords in `.env` does not change accounts in an existing database volume; coordinate credential changes through MySQL instead of deleting team data.

- API: http://127.0.0.1:8000/books (requires a token).
- Health: http://127.0.0.1:8000/actuator/health (includes the database check; details hidden).
- The root URL is not a completed application home page.

`APP_PORT` can be changed in `.env` if port 8000 is occupied. Ports bind to the local machine. MySQL is accessible to services as `db:3306` and is not published to the host. The JDBC connection disables TLS for this local development network; configure verified TLS for deployments elsewhere.

## Optional database viewer

```sh
docker compose --profile tools up -d --wait
```

Open http://127.0.0.1:8080 and select MySQL, server `db`, username `bookstore`, database `bookstore`, and the `DB_PASSWORD` value in your private `.env`. `ADMINER_PORT` controls this port. Adminer has no default app login and does not create customer/admin accounts.

## Verify real application behavior

The Docker build runs Maven `verify`, including a disposable H2 application-context test and JWT key validation tests. These build tests do not substitute for the following MySQL runtime checks:

```sh
python3 scripts/smoke-test.py --state .env.smoke-state.json
docker compose down
docker compose up -d --wait --wait-timeout 240
python3 scripts/smoke-test.py --state .env.smoke-state.json --verify-persistence
```

The first script registers a temporary customer through the real API, logs in using BCrypt verification, checks rejected access, creates/updates/searches a book, and saves private temporary credentials. The second confirms the original JWT, customer, and book survive container recreation using the existing MySQL volume, then deletes the test records and state file. Both state and `.env` files are ignored by Git and excluded from Docker's build context. If using a different port, pass `--url http://127.0.0.1:PORT` to both script invocations.

No mock password hashes or seeded accounts are installed. Hibernate's existing `ddl-auto=update` manages the application's actual entities for development. The previous PostgreSQL sample schema is not used. Review backups and proper migrations before using real/shared data.

## Stop, inspect, and rebuild

```sh
docker compose ps
docker compose logs --tail 100 app db
docker compose down
docker compose up --build --wait --wait-timeout 240
```

`down` preserves the named `mysql_data` volume. Avoid `down --volumes` on shared data: it deletes the database. The application runs as an unprivileged user with a read-only root filesystem and temporary writable storage. The image contains the executable JAR, not the source, Maven cache, or local credentials.

## Native Java development

With Java 17+ and an existing MySQL database/user, supply `DB_PASSWORD` and `JWT_SECRET` through your local environment. Optionally set `SPRING_DATASOURCE_URL` and `SPRING_DATASOURCE_USERNAME` (defaults are local MySQL and `bookstore`). Spring Boot does not automatically import the Compose `.env` file for native runs. Then run `sh ./mvnw spring-boot:run`. The native server listens on port 8080.

To run tests outside Docker: `sh ./mvnw verify`. Tests use an in-memory H2 database and generate their own signing key; they do not require local MySQL credentials.

## API and current limitations

Public JSON endpoints: `POST /customers/register`, `POST /customers/login`. Login returns a real JWT used in `Authorization: Bearer TOKEN`. `GET /books`, book CRUD/search, and customer routes require authentication; `/admin` requires an admin role.

Containerization does not complete application security. Current customer-management routes do not enforce account ownership, `/customers/create` accepts role data from an authenticated caller, and book writes require authentication without a staff/admin restriction. Account lockout and disabled-account enforcement are not implemented. Incorrect credentials need consistent HTTP 401 handling. Keep this development stack local until those rules are implemented and tested. Passwords are now write-only in JSON responses, but broader customer data authorization remains outstanding.

The existing registration HTML form is not wired as a complete frontend and does not match the JSON registration endpoint. Use the API verification script for the current backend.
