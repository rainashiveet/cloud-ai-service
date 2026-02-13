# Cloud-Native AI Inference Service

A production-style AI inference service with containerized deployment, featuring FAISS vector search and RAG (Retrieval-Augmented Generation) capabilities.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [Running Locally (Without Docker)](#running-locally-without-docker)
6. [Running with Docker](#running-with-docker)
7. [Running with Docker Compose](#running-with-docker-compose)
8. [API Documentation](#api-documentation)
9. [Project Structure](#project-structure)
10. [How It Works](#how-it-works)
11. [CI/CD Pipeline](#cicd-pipeline)
12. [Troubleshooting](#troubleshooting)

---

## Project Overview

This project demonstrates how to build a production-style AI inference service with the following features:

- **FastAPI Backend**: Modern, fast Python web framework with automatic API documentation
- **FAISS Vector Search**: Efficient similarity search for document retrieval
- **RAG Pipeline**: Retrieval-Augmented Generation for intelligent responses
- **Docker Containerization**: Consistent deployment across environments
- **CI/CD Pipeline**: Automated testing and building with GitHub Actions

### What Can This Service Do?

1. **Semantic Search**: Find documents similar to your query using AI embeddings
2. **Question Answering**: Get AI-generated answers based on retrieved context
3. **Health Monitoring**: Built-in health check endpoint for monitoring
4. **Swagger UI**: Interactive API documentation at `/docs`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT REQUEST                          │
│                    (POST /query with question)                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI LAYER (main.py)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  GET /health │  │ POST /query  │  │ Swagger UI at /docs  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  - Request validation (Pydantic)                               │
│  - Response formatting                                          │
│  - Error handling                                               │
│  - Logging                                                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                 INFERENCE LAYER (inference.py)                  │
│                                                                 │
│  ┌─────────────────────┐        ┌─────────────────────┐        │
│  │   Embedding Model   │        │    FAISS Index      │        │
│  │ (sentence-transformers)       │   (Vector Store)    │        │
│  │                     │        │                     │        │
│  │ - Text to vectors   │───────▶│ - Similarity search │        │
│  │ - 384 dimensions    │        │ - Fast retrieval    │        │
│  └─────────────────────┘        └─────────────────────┘        │
│                    │                        │                   │
│                    └────────────┬───────────┘                   │
│                                 ▼                               │
│                    ┌─────────────────────┐                      │
│                    │   RAG Pipeline      │                      │
│                    │                     │                      │
│                    │ 1. Encode query     │                      │
│                    │ 2. Search index     │                      │
│                    │ 3. Generate answer  │                      │
│                    │ 4. Measure latency  │                      │
│                    └─────────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API RESPONSE                             │
│  {                                                              │
│    "answer": "Based on retrieved information...",               │
│    "retrieved_documents": ["doc1", "doc2"],                     │
│    "similarity_scores": [0.85, 0.72],                           │
│    "latency_ms": 45.23                                          │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**: API layer (main.py) is separate from AI logic (inference.py)
2. **Modularity**: Each component can be tested and modified independently
3. **Production-Ready**: Logging, error handling, latency measurement
4. **Containerizable**: Runs identically in any environment with Docker

---

## Prerequisites

### Software You Need to Install

| Software | Version | Why You Need It | How to Verify |
|----------|---------|-----------------|---------------|
| **Python** | 3.10+ | Runs your backend code | `python --version` |
| **pip** | 23.x+ | Install Python packages | `pip --version` |
| **Docker Desktop** | Latest | Run containers | `docker --version` |
| **Docker Compose** | v2.x+ | Run multi-container apps | `docker-compose --version` |
| **Git** | 2.x+ | Version control | `git --version` |

### Installing Docker Desktop (Important!)

Docker Desktop includes both Docker and Docker Compose.

**Windows:**
1. Download from: https://www.docker.com/products/docker-desktop
2. Run the installer
3. Restart your computer
4. Open Docker Desktop and complete setup
5. Wait until Docker Desktop shows "Docker Desktop is running"

**Mac:**
1. Download from: https://www.docker.com/products/docker-desktop
2. Drag to Applications folder
3. Open Docker from Applications
4. Complete the setup wizard

**Linux (Ubuntu):**
```bash
# Update package index
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER

# Log out and back in for changes to take effect

# Install Docker Compose
sudo apt-get install docker-compose-plugin
```

### Verifying Installation

Open a terminal/command prompt and run:

```bash
# Check Python
python --version
# Expected: Python 3.10.x or higher

# Check pip
pip --version
# Expected: pip 23.x.x

# Check Docker (make sure Docker Desktop is running!)
docker --version
# Expected: Docker version 24.x.x

# Check Docker Compose
docker-compose --version
# Expected: Docker Compose version v2.x.x

# Test Docker is working
docker run hello-world
# Should download and run a test container successfully
```

---

## Quick Start

The fastest way to get the service running:

```bash
# 1. Navigate to the project directory
cd cloud-ai-service

# 2. Start all services with Docker Compose
docker-compose up

# 3. Wait for "Application startup complete" message
# (First run takes ~2-3 minutes to download model)

# 4. Open in browser
# API: http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

---

## Running Locally (Without Docker)

If you want to run without Docker (for development):

### Step 1: Create Virtual Environment (Recommended)

A virtual environment keeps project dependencies separate from your system Python.

```bash
# Navigate to project directory
cd cloud-ai-service

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# You should see (venv) in your terminal prompt
```

### Step 2: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# This will install:
# - fastapi: Web framework
# - uvicorn: Server
# - faiss-cpu: Vector search
# - sentence-transformers: Embeddings
# - And others...
```

### Step 3: Run the Server

```bash
# Navigate to app directory
cd app

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# You should see:
# INFO:     Application startup complete.
```

### Step 4: Test the API

Open your browser or use curl:

```bash
# Health check
curl http://localhost:8001/health

# Query endpoint
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is machine learning?"}'

```

---

## ⚠️ Important Port Note

The application listens on port **8000 inside the container**, and is exposed on
port **8001 on your machine**.

## Running with Docker

### Understanding Docker Basics

**What is an Image?**
An image is a blueprint. Think of it like a recipe - it contains all instructions to create something.

**What is a Container?**
A container is a running instance of an image. Like the actual dish cooked from the recipe.

**What is a Port?**
A port is like a door number. Port 8001 means "door 8001" on your computer.

### Building and Running

```bash
# Navigate to project directory
cd cloud-ai-service

# Build the Docker image (creates the blueprint)
docker build -t ai-service .

# What this does:
# - Reads the Dockerfile
# - Downloads Python base image
# - Copies your code
# - Installs dependencies
# - Creates a new image called "ai-service"

# Run a container from the image
docker run -p 8000:8000 ai-service

# What -p 8000:8000 means:
# - First 8000: port on YOUR computer
# - Second 8000: port inside the container
# - Maps them together so you can access the service

# The service is now running at http://localhost:8001
```

### Running in Background

```bash
# Add -d flag to run in background (detached mode)
docker run -d -p 8001:8000 ai-service

# View running containers
docker ps

# View logs
docker logs <container_id>

# Stop container
docker stop <container_id>
```

---

## Running with Docker Compose

Docker Compose lets you run multiple services together with a single command.

### What's in docker-compose.yml?

```yaml
services:
  ai-service:    # Your FastAPI application
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
  
  redis:         # Cache layer (optional)
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Commands

```bash
# Start all services (in foreground)
docker-compose up

# Start all services (in background)
docker-compose up -d

# View logs
docker-compose logs

# Follow logs (like tail -f)
docker-compose logs -f

# View logs for specific service
docker-compose logs ai-service

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Rebuild after code changes
docker-compose up --build
```

### Why Use Docker Compose?

1. **One Command**: Start everything with `docker-compose up`
2. **Networking**: Services can communicate by name (ai-service → redis)
3. **Volumes**: Data persists even if containers are removed
4. **Health Checks**: Docker Compose waits for services to be healthy

---

## API Documentation

### Interactive Documentation (Swagger UI)

Open http://localhost:8001/docs in your browser. You'll see:

- All available endpoints
- Request/response schemas
- Try it out button for testing

### Endpoints

#### GET /health

Check if the service is healthy.

**Request:**
```bash
curl http://localhost:8001/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1706000000.123,
  "version": "1.0.0",
  "model_loaded": true,
  "documents_indexed": 15
}
```

#### POST /query

Submit a query for AI-powered response.

**Request:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "k": 3}'
```

**Response:**
```json
{
  "answer": "Based on the retrieved information (high confidence):\nMachine Learning is a subset of artificial intelligence...",
  "query": "What is machine learning?",
  "retrieved_documents": [
    "Machine Learning is a subset of artificial intelligence...",
    "Deep Learning is a specialized branch..."
  ],
  "similarity_scores": [0.85, 0.72, 0.65],
  "latency_ms": 45.23,
  "status": "success"
}
```

---

## Project Structure

```
cloud-ai-service/
│
├── app/
│   ├── __init__.py          # Makes app a Python package
│   ├── main.py              # FastAPI application (API layer)
│   └── inference.py         # AI/ML logic (inference layer)
│
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI pipeline
│
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Multi-container orchestration
└── README.md                # This file
```

### File Purposes

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI routes, request handling, API documentation |
| `app/inference.py` | Embedding model, FAISS index, RAG pipeline |
| `requirements.txt` | List of Python packages to install |
| `Dockerfile` | Instructions to build Docker image |
| `docker-compose.yml` | Define services and their relationships |
| `.github/workflows/ci.yml` | Automated testing on GitHub |

---

## How It Works

### The Inference Pipeline

When you send a query to `/query`:

1. **Receive Query** (main.py)
   - FastAPI receives the POST request
   - Validates the query using Pydantic models

2. **Generate Embedding** (inference.py)
   - Convert your text query into a vector (384 numbers)
   - Uses sentence-transformers model

3. **Search Index** (inference.py)
   - FAISS finds the most similar documents
   - Returns top-k matches with similarity scores

4. **Generate Answer** (inference.py)
   - Construct an answer from retrieved documents
   - Include confidence level based on similarity

5. **Return Response** (main.py)
   - Format response as JSON
   - Include latency measurement

### The Knowledge Base

The service includes a default knowledge base with information about:
- Machine Learning
- Deep Learning
- Natural Language Processing
- Vector Databases
- FAISS
- Docker
- FastAPI
- And more...

You can extend this by modifying `DEFAULT_KNOWLEDGE_BASE` in `inference.py`.

---

## CI/CD Pipeline

### What is CI/CD?

- **CI (Continuous Integration)**: Automatically test your code when you push to GitHub
- **CD (Continuous Deployment)**: Automatically deploy your code

### What Our Pipeline Does

Located at `.github/workflows/ci.yml`, it runs when you:
- Push to `main` branch
- Create a pull request

### Pipeline Steps

1. **Code Quality Check**
   - Install dependencies
   - Run Black (code formatter)
   - Run Flake8 (linter)
   - Run pytest (tests)

2. **Build Docker Image**
   - Build the image
   - Test that it starts correctly
   - Verify health endpoint works

3. **Security Scan**
   - Check dependencies for known vulnerabilities

### How to Use

1. Push your code to GitHub
2. Go to your repository → Actions tab
3. See the pipeline running
4. Green checkmark = all passed!

---

## Troubleshooting

### Common Issues

#### "docker: command not found"
- **Solution**: Docker Desktop is not installed or not running
- Download and install Docker Desktop
- Make sure Docker Desktop is actually running (check system tray)

#### "Port 8000 already in use"
- **Solution**: Something else is using port 8000
- Find and stop the other process, or use a different port:
  ```bash
  docker run -p 8001:8000 ai-service
  ```

#### "Model download is slow"
- **Explanation**: First run downloads the embedding model (~100MB)
- Subsequent runs use cached model
- Wait 2-3 minutes on first run

#### "ModuleNotFoundError: No module named 'app'"
- **Solution**: You're running from wrong directory
- Make sure you're in the `cloud-ai-service` directory
- Or run with: `uvicorn app.main:app`

#### Docker build fails
- **Solution**: Check your Dockerfile syntax
- Make sure requirements.txt exists
- Check for network issues (proxy, firewall)

### Viewing Logs

```bash
# Docker Compose logs
docker-compose logs ai-service

# Follow logs in real-time
docker-compose logs -f ai-service

# Docker container logs
docker logs <container_id>
```

### Debugging Tips

1. **Check container status**
   ```bash
   docker ps -a
   ```

2. **Access container shell**
   ```bash
   docker exec -it <container_id> /bin/bash
   ```

3. **Check health endpoint**
   ```bash
   curl http://localhost:8001/health
   ```

---

## Next Steps

1. **Add Your Own Knowledge Base**: Modify `DEFAULT_KNOWLEDGE_BASE` in `inference.py`
2. **Add Authentication**: Implement API key authentication
3. **Connect a Real LLM**: Integrate OpenAI or other LLM API for better answers
4. **Add Redis Caching**: Cache query results for faster responses
5. **Deploy to Cloud**: Deploy to AWS, GCP, or Azure

---

## License

This project is for educational purposes.

---

## Contact

For questions, open an issue on GitHub.
