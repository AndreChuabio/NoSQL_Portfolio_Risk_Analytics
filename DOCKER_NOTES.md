# Docker Setup - Currently Not in Use

This directory contains Docker configuration files that are **currently set aside** per project requirements.

## Files
- `docker-compose.yml`: MongoDB and Redis container orchestration
- `docs/runbooks/container_setup.md`: Docker deployment guide

## Future Use
These files will be utilized when:
1. Deploying to production environments
2. Setting up containerized development environments
3. Running integration tests in CI/CD pipelines

## Current Setup
The project currently uses:
- **MongoDB**: Local installation or MongoDB Atlas cloud cluster
- **Redis**: Local installation via brew/apt or standalone Docker container

## Re-enabling Docker
To use Docker in the future:
1. Ensure Docker Desktop is installed
2. Run `docker compose up -d` from project root
3. Follow instructions in `docs/runbooks/container_setup.md`

---
**Note**: Docker files are tracked in git but not actively used in current development workflow.
