## 🚚 Truck Trip Planner & ELD  (Django + React + Docker Compose)
This project includes a Django backend (served by Gunicorn) and a React frontend (built with Vite and served via Nginx).
Both are containerized and orchestrated with Docker Compose.

## ⚙️ Prerequisites

Make sure you have installed:

* Docker
* Docker Compose
* (Optional) make — preinstalled on macOS/Linux, or installable via WSL on Windows

## 🚀 Run the Project
1. Add `.env` for both frontend and backend, you can follow the `.env.example` in each folder for what to include
2. Build containers
```make build```
3. Start services
```make up```

## This starts:

🐍 Django backend → http://localhost:8000

⚛️ React frontend → http://localhost:80
