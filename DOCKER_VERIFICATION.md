# Docker verification — October 17, 2026

Upstream: `93nessa/BookstoreManagement-System`, base commit `84760158355bf6c55644e60696ec2f9631e4f2c8`.

## Implemented

- Multi-stage Java 17 build using the repository's Maven wrapper and Spring Boot 4.1.1. Maven `verify` runs during image creation.
- MySQL 8.4, matching the existing JDBC driver and JPA entities. The earlier proposed PostgreSQL schema and fake user seeds are not used.
- Persistent database volume, authenticated database health check, application/database health endpoint, and startup readiness dependencies.
- Optional Adminer 5 viewer; application/viewer published only on loopback. MySQL has no published host port.
- Generated per-machine database credentials and JWT signing key, required Compose variables, ignored private settings, and an allowlist for Docker's build context.
- Non-root runtime user, read-only application filesystem, temporary writable storage, and dropped Linux capabilities.
- Existing password hashing/login retained. Customer JSON password fields are write-only so responses no longer expose hashes. No demo accounts or mock authentication were added.
- README instructions and repeatable API/persistence checks.

## Executed checks

Test platform: macOS Apple Silicon running a Linux arm64 Docker Engine via a newly created Colima test VM. Docker client 29.9.1, Engine 29.5.2, Compose 5.6.0. Ports 18080/18081 and Compose project `cs492-verification` isolated the checks from default ports and other projects.

| Check | Result |
| --- | --- |
| Compose configuration | Passed. Missing DB password, MySQL root password, or JWT key each prevented startup. |
| Environment generator | Passed. Fresh random credentials, file mode 0600, and existing credentials preserved on a second invocation. |
| Image build | Passed from the actual repository source. |
| Maven tests | 3 passed, 0 failed/errors/skipped: application context on disposable H2; JWT round-trip/restart/foreign-key rejection; weak signing-key rejection. |
| Live MySQL/application readiness | Both healthy. Schema created from the existing entities. |
| Real registration and login | Passed against MySQL with a random temporary customer/password. No password hash in registration JSON. |
| Negative authentication checks | Incorrect password issued no token; anonymous and invalid-JWT requests were denied; customer token was denied access to `/admin`. This does not prove complete application authorization. |
| Book workflow | Create, update title and stock, search by ISBN: passed. |
| Persistence | After `down` and recreation without deleting the volume, the original customer, book, and JWT remained usable. |
| Test record cleanup | Temporary book and customer removed through the real API after the persistence check; private state file removed. |
| Runtime restrictions | UID 10001 and read-only root filesystem verified; local `.env`, Maven cache, and source workspace absent from runtime image. |
| Adminer | Optional profile started; HTTP 200 and viewer content verified over loopback. Database GUI login was not manually exercised. |

Final tested image ID: `sha256:dd6fa0220e7f6deab222bf9ea9ce34fec8f54986c8699376ef72c046847e3138`.

Resolved MySQL image: `mysql@sha256:24989179f58856db763f418010c1169fecc944e3ec1ea7e921572d83eb070f70`.

Resolved Adminer image: `adminer@sha256:e3a6b4942dd088a29cc8bbce22553429247c5c2b30b07d856ae49012b5c84a5b`.

## Limits and follow-up work

This is a verified local development environment for the API backend. A complete storefront, successful admin login, account lockout, and full production security were not demonstrated. Intel/Windows builds were not run.

Existing application authorization needs further work: customer routes lack ownership checks, authenticated `/customers/create` accepts role data, book writes are not staff-only, and disabled accounts are not enforced. Incorrect credentials need consistent HTTP 401 handling. These are application issues, not fixed by Docker. The existing HTML registration form is not connected as a working frontend.

Hibernate `ddl-auto=update` is retained for development; production/shared data needs backups and reviewed migrations. Local JDBC TLS is disabled inside this development network. Previously committed credentials and the old shared signing key should be retired wherever they were used.

The test VM was created for this verification. Docker, Compose, Buildx, Colima, and Lima were installed through Homebrew to run the checks. No automatic login/background service was configured. Local test containers are stopped after verification; the test volume is preserved.

## Official references

- [Spring Boot requirements](https://docs.spring.io/spring-boot/system-requirements.html)
- [Docker Java guide](https://docs.docker.com/guides/java/)
- [Compose required variables](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/)
- [Compose startup readiness](https://docs.docker.com/compose/how-tos/startup-order/)
- [Official MySQL image](https://hub.docker.com/_/mysql)
