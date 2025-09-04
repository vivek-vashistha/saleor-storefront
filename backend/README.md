# Conversational Commerce Backend

The backend component of the Conversational Commerce application, built with FastAPI and Python 3.12.

## Overview

This backend service provides the API endpoints needed to support the conversational commerce frontend. It handles user authentication, product data, conversation management, and integration with AI services for natural language processing.

## Technology Stack

- Python 3.12
- FastAPI
- Dependency Injector for dependency management
- Pydantic for data validation
- pytest for testing

## Getting Started

### Prerequisites

- Python 3.12
- [uv](https://github.com/astral-sh/uv) (for dependency management)
- Docker and Docker Compose (for containerized deployment)

### Docker Desktop on Mac or Windows

If you are using Docker Desktop on Mac or Windows, you need to make the following adjustments:

1. Add these environment variables to your `.env` file:

   ```
   QDRANT_HOST="host.docker.internal"
   MONGODB_HOST="host.docker.internal"
   ```

2. Ensure that host networking is enabled in Docker Desktop settings.
   See the [Docker documentation](https://docs.docker.com/engine/network/drivers/host/#docker-desktop) for more details.

## Docker Compose

You can run the entire application stack using Docker Compose:

1. `cd` into the backend folder

   ```shell
   cd backend
   ```

2. First, set up the products in the repository:

   ```shell
   docker-compose build && docker compose up product_loader
   ```

3. Then, start the backend service:

   ```shell
   docker-compose build --no-cache && docker compose up backend
   ```

4. The services will be available at:
   - Backend API: http://localhost:4003
   - API Documentation: http://localhost:4003/docs

## Local Environment

1. `cd` into the backend folder

   ```shell
   cd backend
   ```

2. Install Python 3.12

   ```shell
   uv python install 3.12
   ```

3. Create a virtual environment and install dependencies using UV:

   ```shell
   uv sync
   ```

4. Run the service:
   ```shell
   uv run uvicorn backend.presentation.api.main:app --reload --port 8000
   ```

## API Documentation

The API documentation is automatically generated and available at:

- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)
