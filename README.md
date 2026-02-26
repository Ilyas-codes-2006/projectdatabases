# 🏸 MatchUp — Web-based Club Ladder

> **Programming Project Databases** · University of Antwerp · Team 5

# Run for now:
python3 -m pip install -r requirements.txt
# To run the project, use:
See the folders backend and frontend and open 2 terminals, one for each. In the backend terminal, run:

## 1. Project Overview

**MatchUp** is a web-based **club ladder** system designed for tennis and padel clubs.
It provides a flexible, ongoing competition format where players (or doubles teams) **challenge opponents**, **schedule matches**, and **move up or down** the rankings based on match outcomes.

Instead of traditional tournament brackets, a ladder keeps all members engaged throughout the season — anyone can climb to the top by consistently winning challenges.

### Key Features

| Feature | Description |
|---|---|
| **Challenge System** | Players challenge opponents within a configurable rank range on their ladder. |
| **Match Scheduling** | Teams set their weekly availability; the system facilitates scheduling within a configurable frequency window. |
| **ELO-based Rating** | After each match the winner gains rating points and the loser drops, keeping rankings dynamic and fair. |
| **Authentication** | Secure user registration and login with **JWT**-based tokens. |
| **Multi-sport Support** | Ladders can be created for different sports (tennis, padel, etc.) with configurable team sizes. |
| **Club Management** | Club admins manage members, create ladders, and oversee match disputes. |

### Core Entities

```
Users ── Members ──> Clubs
                      │
                   Ladders ──> Sports
                      │
                    Teams ──> Team Members (Users)
                      │
                   Matches (home_team vs away_team)
```

- **Users** — Registered players with a global ELO rating.
- **Clubs** — Organisations that host one or more ladders.
- **Ladders** — A ranked competition within a club for a specific sport.
- **Teams** — One or more players competing as a unit on a ladder.
- **Matches** — Scheduled challenges between two teams, tracked through statuses (`pending` → `confirmed` → `completed`).

---

## 2. Current Progress (Milestones)

| Milestone | Status      |
|---|-------------|
| ✅ Scope Description | Completed   |
| ✅ Initial Database Design (PostgreSQL schema) | Completed   |
| ✅ "Hello World" application running on **Google Cloud Platform** | Completed   |
| 🔄 Backend API with ELO rating engine | In Progress |
| 🔄 Frontend scaffold (React + TypeScript + Vite) | In Progress |
| 🔄 Full match scheduling & challenge flow | In Progress |
| 🔄 User authentication (JWT) | In Progress |
| ⬜ Admin dashboard & dispute resolution | Planned     |

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| **Database** | PostgreSQL (mandatory) |
| **Backend** | Python 3 · Flask · Gunicorn · psycopg 3 |
| **Frontend** | React 19 · TypeScript · Vite |
| **Auth** | JWT (HS256) |
| **Reverse Proxy** | Nginx |
| **Hosting** | Google Cloud Platform (GCP) |
| **Project Management** | Jira (Agile / Scrum) |

---

## 4. Local Development — How to Run

### Prerequisites

- **Python 3.12+**
- **Node.js 22+** & **npm**
- **PostgreSQL 15+** running locally (or via Docker)

### 4.1 Clone the repository

```bash
git clone <repository-url>
cd projectdatabases
```

### 4.2 Configure environment variables

Create a `.env` file inside `backend/`:

```dotenv
DB_USER=app
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=matchup

JWT_SECRET=your_jwt_secret
JWT_EXPIRY_HOURS=24
FLASK_DEBUG=true
```

### 4.3 Set up the database

```bash
# Connect to PostgreSQL and create the database & role
psql -U postgres -c "CREATE USER app WITH PASSWORD 'your_password';"
psql -U postgres -c "CREATE DATABASE matchup OWNER app;"
```

> The schema is applied automatically when the Flask app starts (`init_db()`).

### 4.4 Start the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

The API will be available at **http://localhost:5000**.

### 4.5 Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server will be available at **http://localhost:5173**.
API calls to `/api/*` are automatically proxied to the backend.

---

## 5. Online Website

The production site is deployed on **Google Cloud Platform** and accessible at:

> **http://team5.ua-ppdb.com**

The deployment uses **Nginx** as a reverse proxy serving the Vite production build for the frontend and forwarding `/api/` requests to **Gunicorn** (3 workers) over a Unix socket.

---

## 6. Project Structure

```
projectdatabases/
├── backend/                # Flask API
│   ├── app.py              # Application entry-point & routes
│   ├── config.py           # Environment-based configuration
│   ├── db.py               # Database schema & helpers
│   ├── elo.py              # ELO rating calculation
│   ├── wsgi.py             # Gunicorn WSGI entry-point
│   └── requirements.txt
├── frontend/               # React + TypeScript SPA
│   ├── src/
│   ├── vite.config.ts
│   └── package.json
├── nginx/                  # Nginx site configuration
│   └── webapp
├── service/                # systemd service unit
│   └── webapp.service
└── README.md
```

---

## 7. License

This project is developed as part of the **Programming Project Databases** course at the **University of Antwerp** and is intended for educational purposes.
