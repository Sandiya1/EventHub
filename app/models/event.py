from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base

class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("seats_available >= 0", name="ck_event_seats_nonneg"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(2000))
    venue = Column(String(200), nullable=False)
    speaker = Column(String(120), nullable=False)
    event_date = Column(DateTime, nullable=False) 
    total_seats = Column(Integer, nullable=False)
    seats_available = Column(Integer, nullable=False)

    organizer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))


    organizer = relationship("User", back_populates="events")
    registrations = relationship(
    "Registration",
    back_populates="event",
    cascade="all, delete-orphan"
)
