# app/routers/events.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from app.db.session import get_db
from app.models.event import Event
from app.models.registration import Registration
from app.auth.deps import require_organizer, require_participant
from app.routers.auth import EventCreate, EventUpdate
from app.email_utils import send_email

router = APIRouter(prefix="/events", tags=["events"])

def now_utc() -> datetime:
    return datetime.utcnow()

def event_status(event: Event) -> str:
    """Return 'completed', 'soon' (<=24h), or 'upcoming'"""
    now = now_utc()
    if event.event_date <= now:
        return "completed"
    hours_left = (event.event_date - now).total_seconds() / 3600.0
    if hours_left <= 24:
        return "soon"
    return "upcoming"


# -----------------------
# LIST / GET
# -----------------------
@router.get("/list")
def list_events(db: Session = Depends(get_db)):
    events: List[Event] = db.query(Event).all()
    result = []
    for ev in events:
        result.append({
            "id": ev.id,
            "title": ev.title,
            "description": getattr(ev, "description", None),
            "venue": ev.venue,
            "speaker": ev.speaker,
            "event_date": ev.event_date,
            "total_seats": ev.total_seats,
            "seats_available": ev.seats_available,
            "organizer_id": ev.organizer_id,
            "status": event_status(ev)
        })
    return result

@router.get("/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "id": event.id,
        "title": event.title,
        "description": getattr(event, "description", None),
        "venue": event.venue,
        "speaker": event.speaker,
        "event_date": event.event_date,
        "total_seats": event.total_seats,
        "seats_available": event.seats_available,
        "organizer_id": event.organizer_id,
        "status": event_status(event)
    }


# -----------------------
# CREATE (organizer)
# -----------------------
@router.post("/create", status_code=201)
def create_event(payload: EventCreate, db: Session = Depends(get_db), user = Depends(require_organizer)):
    # Enforce future date
    if payload.event_date <= now_utc():
        raise HTTPException(status_code=400, detail="event_date must be in the future")

    event = Event(
        title=payload.title,
        description=getattr(payload, "description", None),
        venue=payload.venue,
        speaker=payload.speaker,
        event_date=payload.event_date,
        total_seats=payload.total_seats,
        seats_available=payload.total_seats,
        organizer_id=user.id
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"msg": "Event created successfully", "event_id": event.id}


# -----------------------
# UPDATE (organizer) — BLOCK updates to completed events
# -----------------------
@router.put("/update/{event_id}")
def update_event(
    event_id: int,
    payload: EventUpdate,
    db: Session = Depends(get_db),
    user = Depends(require_organizer)
):
    event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or unauthorized")

    # Block updating completed events (Option A)
    if event.event_date <= now_utc():
        raise HTTPException(status_code=403, detail="Cannot update an event that is already completed")

    # Keep old values for email notifications
    old_date = event.event_date
    old_venue = event.venue

    # Apply updates (only fields provided)
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)

    db.commit()
    db.refresh(event)

    # Notify participants only if the event is still upcoming (should be, because we blocked completed)
    registrations = db.query(Registration).filter(Registration.event_id == event_id).all()
    for reg in registrations:
        p = reg.user
        subject = f"Event Updated: {event.title}"
        body = f"""
            <p>Hello {p.name},</p>
            <p>We would like to inform you that the event you registered for has been updated.</p>
            <p>The event <strong>{event.title}</strong> has been updated.</p>
            <p><strong>Old Date:</strong> {old_date} | <strong>Old Speaker:</strong> {old_venue} | <strong> Old Venue:</strong> {old_venue}<br>
            <strong>New Date:</strong> {event.event_date} | <strong>New Speaker:</strong> {event.speaker} | <strong>New Venue:</strong> {event.venue}</p>
            <p><strong>New Venue:</strong> {event.venue}</p>
            <p>By EventHub Team</p>
        """
        # Send immediately for updates
        send_email(p.email, subject, body)

    return {"msg": "Event updated successfully!"}


# -----------------------
# DELETE (organizer)
# -----------------------
@router.delete("/delete/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_organizer),
):
    event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or unauthorized")

    registrations = db.query(Registration).filter(Registration.event_id == event_id).all()

    # Only send cancellation emails if the event is upcoming
    now = now_utc()
    should_notify = event.event_date > now

    if should_notify:
        for reg in registrations:
            participant = reg.user
            subject = f"Event Cancelled: {event.title}"
            body = f"""
                <p>Hello {participant.name},</p>
                <p>We regret to inform you that the event you registered for has been cancelled.</p>
                <p>The event <strong>{event.title}</strong> scheduled on 
                <strong>{event.event_date}</strong> has been cancelled by the organizer.</p>
                <p>We apologize for the inconvenience </p>
                <p>By EventHub Team</p>
            """
            # Send immediately for cancellations
            send_email(participant.email, subject, body)
    else:
        # Event already completed — do not notify participants
        print("Event already completed — no cancellation emails sent.")

    db.delete(event)
    db.commit()

    return {
        "msg": f"Event '{event.title}' deleted",
        "notified": should_notify
    }


# -----------------------
# MY REGISTRATIONS (participant)
# -----------------------
@router.get("/my/registrations")
def get_my_registrations(
    db: Session = Depends(get_db),
    user = Depends(require_participant)
):
    registrations = db.query(Registration).filter(Registration.user_id == user.id).all()
    events = [
        {
            "event_id": r.event.id,
            "title": r.event.title,
            "venue": r.event.venue,
            "date": r.event.event_date,
            "speaker": r.event.speaker,
            "seats_booked": r.seats_booked,
            "registered_at": r.registered_at,
            "status": event_status(r.event)
        }
        for r in registrations
    ]
    return {"user": user.name, "registered_events": events}


# -----------------------
# REGISTER (participant)
# -----------------------
@router.post("/register/{event_id}")
def register_for_event(
    event_id: int,
    seats: int = 1,
    db: Session = Depends(get_db),
    user = Depends(require_participant)
):
    # Lock the event row (prevents race conditions)
    event = db.query(Event)\
        .filter(Event.id == event_id)\
        .with_for_update()\
        .first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    now = now_utc()

    # No late registrations
    if now >= event.event_date:
        raise HTTPException(status_code=400, detail="This event is already completed. Registration is closed.")

    # Check seats AFTER locking
    if event.seats_available < seats:
        raise HTTPException(status_code=400, detail="Not enough seats available")

    # Duplicate check
    existing = db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.user_id == user.id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already registered for this event")

    # Create registration safely
    registration = Registration(
        user_id=user.id,
        event_id=event_id,
        seats_booked=seats
    )

    db.add(registration)
    event.seats_available -= seats  # safe update
    db.commit()                      # lock is released here
    db.refresh(event)

    # reminder logic...
    reminder_time = event.event_date - timedelta(hours=24)
    subject = f"Reminder: {event.title} is happening soon!"
    body = f"""
        <h3>Hello {user.name},</h3>
        <p>We would like to remind you that the event you registered for is happening soon.</p>
        <p>You have registered for <strong>{event.title}</strong>.</p>
        <p>Date & Time: {event.event_date}</p>
        <p>Venue: {event.venue}</p>
        <p>Speaker: {event.speaker}</p>
        <p>Don't forget it's less than 24 hours away!</p>
        <p>By EventHub Team</p>
    """

    if now >= reminder_time:
        send_email(user.email, subject, body)
    else:
        send_email(user.email, subject, body, int(reminder_time.timestamp()))

    return {
        "msg": f"Registered successfully for {event.title}",
        "event_id": event.id,
        "status": event_status(event)
    }

# -----------------------
# VIEW REGISTRATIONS (organizer)
# -----------------------
@router.get("/registrations/{event_id}")
def view_event_registrations(
    event_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_organizer),
):
    event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == user.id).first()
    if not event:
        raise HTTPException(status_code=403, detail="Not your event")

    registrations = db.query(Registration).filter(Registration.event_id == event_id).all()
    return [
        {
            "participant": reg.user.name,
            "email": reg.user.email,
            "seats_booked": reg.seats_booked,
            "registered_at": reg.registered_at
        }
        for reg in registrations
    ]


# -----------------------
# CANCEL REGISTRATION (participant)
# -----------------------
@router.delete("/cancel/{event_id}")
def cancel_registration(
    event_id: int,
    db: Session = Depends(get_db),
    user = Depends(require_participant)
):
    # check registration exists
    registration = db.query(Registration).filter(
        Registration.event_id == event_id,
        Registration.user_id == user.id
    ).first()

    if not registration:
        raise HTTPException(
            status_code=404,
            detail="You are not registered for this event"
        )

    # fetch the event
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Prevent cancellation for completed events
    if event.event_date <= now_utc():
        raise HTTPException(status_code=400, detail="Cannot cancel registration for completed events")

    # increase the available seats
    event.seats_available += registration.seats_booked

    # delete the registration
    db.delete(registration)
    db.commit()

    return {
        "msg": f"Your registration for '{event.title}' has been cancelled",
        "seats_available": event.seats_available
    }
