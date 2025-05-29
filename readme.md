# 🛡️ Image Moderation API

A FastAPI-based REST API for automated image moderation. This system detects and blocks unwanted or harmful images—such as nudity, violence, hate symbols, or extremist content—before they reach end users.

## 📌 Features

- 🚀 REST API built with FastAPI
- 🧠 Mock moderation engine with category-wise confidence scoring
- 🔐 Secure authentication using bearer tokens
- 🧾 Usage tracking per token
- 🛠️ Admin panel for managing tokens
- 📦 Dockerized backend and frontend
- 🌐 Minimal UI for token input and image upload

## 📂 Project Structure
├── backend/
    ├── main.py # FastAPI application and routing
    ├── image_moderator.py # Moderation logic (mock implementation)
    ├── database.py # MongoDB interaction layer
    ├── models.py # Pydantic models
    ├── config.py # Configuration via environment variables
    ├── requirements.txt # Dependencies
    ├── Dockerfile # Docker container for backend
    ├── docker-compose.yml # Multi-container orchestration
├── frontend/ # Minimal frontend UI
│ └── index.html
├── .env.example # Example environment configuration
└── README.md # This file

# 🧪 API Endpoints

### 🔐 Authentication (Admin-only)

- `POST /auth/tokens` — Create new bearer token  
- `GET /auth/tokens` — List all issued tokens  
- `DELETE /auth/tokens/{token}` — Revoke token  

### 📸 Moderation

- `POST /moderate` — Upload image for moderation  

### 📊 Usage

- `GET /usage/{token}` — View usage stats for a token  

### 🩺 Health

- `GET /health` — Check health of database/API

---

## 🧰 Setup Instructions

### 1. Clone Repository

```bash
git https://github.com/ArbanArfan/Image-Moderation-FastAPI.git
cd Image-Moderation-FastAPI

```ConfigureEnvironment
Config.py
cp .env.example .env

Build and Run with Docker
docker-compose up --build

Once up:

Backend: http://localhost:7000

Frontend: http://localhost:8080

Admin Token: m5AwYRHli3UGtdD6uT42YJiZ4koLk3c3jNcwt-3W3a8