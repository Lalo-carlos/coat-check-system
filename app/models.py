from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="cashier")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tickets_in = relationship("Ticket", foreign_keys="Ticket.employee_in_id", back_populates="employee_in")
    tickets_out = relationship("Ticket", foreign_keys="Ticket.employee_out_id", back_populates="employee_out")
    movements = relationship("Movement", back_populates="employee")
    cash_sessions = relationship("CashSession", back_populates="employee")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    qr_token = Column(String, unique=True, index=True, nullable=True)
    hanger_number = Column(String, index=True, nullable=True)
    description = Column(String, nullable=False)
    photo_url = Column(String, nullable=True)
    price = Column(Float, default=0.0)
    payment_method = Column(String, default="cash")
    status = Column(String, default="stored")
    notes = Column(Text, nullable=True)
    date_in = Column(DateTime, default=datetime.utcnow)
    date_out = Column(DateTime, nullable=True)

    employee_in_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    employee_out_id = Column(Integer, ForeignKey("employees.id"), nullable=True)

    employee_in = relationship("Employee", foreign_keys=[employee_in_id], back_populates="tickets_in")
    employee_out = relationship("Employee", foreign_keys=[employee_out_id], back_populates="tickets_out")
    movements = relationship("Movement", back_populates="ticket")


class Movement(Base):
    __tablename__ = "movements"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    action = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="movements")
    employee = relationship("Employee", back_populates="movements")


class CashSession(Base):
    __tablename__ = "cash_sessions"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    opening_amount = Column(Float, default=0.0)
    closing_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)

    employee = relationship("Employee", back_populates="cash_sessions")
