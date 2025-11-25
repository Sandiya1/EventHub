# EventHub Backend (FastAPI)

EventHub is a backend service for an Event Management & Booking System that supports user authentication, event creation, event registration, real-time seat availability, and role-based access control.

This backend provides REST APIs for the React-based frontend and handles all database operations, authentication, and business logic.

---

## 🚀 Tech Stack

- **Framework:** FastAPI
- **Language:** Python 3.x
- **Database:** MySQL 
- **ORM:** SQLAlchemy
- **Authentication:** JWT (JSON Web Tokens)
- **Server:** Uvicorn
- **Tools:** Pydantic

---

## 📌 Features

- User registration and login with hashed passwords
- JWT authentication and role-based access
- Organizer-specific endpoints (create, update, delete events)
- Participant event registration/unregistration
- Real-time seat availability & database-level concurrency control
- View participants registered for an event
- Background task to send event reminder notifications
- Complete REST API support for frontend integration

---


## ⚙️ Setup Instructions

### 1. Clone the repository
git clone <backend_repo_url>
cd backend



### 2. Create virtual environment
python -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows



### 3. Install dependencies
pip install -r requirements.txt


### 4. Configure environment variables

Create a `.env` file:
DATABASE_URL=mysql+pymysql://username:password@localhost/eventhub
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60




### 5. Start the server
uvicorn app.main:app --reload


---

## 📡 API Endpoints

### Authentication
- `POST /auth/register`
- `POST /auth/login`

### Events
- `GET /events`
- `POST /events/create` (Organizer)
- `PUT /events/update/{event_id}` (Organizer)
- `DELETE /events/delete/{event_id}` (Organizer)
- `GET /events/{event_id}/participants` (Organizer)

### Registration
- `POST /register/{event_id}`
- `DELETE /register/{event_id}`
- `GET /my-registrations`

---

## 🔐 Authentication (JWT)

- On login, backend returns an access token
- Token is included in frontend requests using:

Authorization: Bearer <token>

- Role is validated for protected routes

---

## 🔄 Real-Time Seat Management

Database row-locking ensures no two users book the last seat simultaneously:

event = db.query(Event).filter(Event.id == event_id).with_for_update().first()

---

## 🕒 Background Tasks

Used to sendGrid API to send send real time notifiaction for the participants when the event is 24 hours away or when the organizer deletes , cancels the event

---

## 🗂️ Database Schema

Includes:
- Users table
- Events table
- Registrations table
- Relationships via foreign keys


