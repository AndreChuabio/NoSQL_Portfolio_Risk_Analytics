# Container Setup Runbook

## Prerequisites
- Install Docker Desktop for macOS and ensure the `docker` CLI is available on your PATH.
- Verify that you can run `docker --version` after installation.

## Starting Services
1. From the repository root, run `docker compose up -d` to start MongoDB and Redis containers defined in `docker-compose.yml`.
2. Check container health:
   - `docker exec nosql_project_mongodb mongo --username root --password example --eval "db.runCommand({ ping: 1 })"`
   - `docker exec nosql_project_redis redis-cli ping`
3. Inspect logs if needed with `docker compose logs mongodb` or `docker compose logs redis`.

## Stopping Services
- Run `docker compose down` to stop containers while preserving volumes.
- Add `--volumes` if you need to remove persistent data.

## Troubleshooting
- Use `docker ps` to confirm containers are running.
- Ensure ports 27017 and 6379 are free before starting the stack.
- For authentication issues with MongoDB, confirm the root username and password match environment variables in `docker-compose.yml`.
