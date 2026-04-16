from sqlalchemy import Column, String, Date, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Appointment(Base):
    __tablename__ = "appointments"

    id         = Column(Integer, primary_key=True, index=True)
    org_id     = Column(String, nullable=False)
    employee_id= Column(String, nullable=False)
    customer   = Column(String, nullable=False)
    date       = Column(Date, nullable=False)
    time       = Column(String, nullable=False)   # e.g. "14:00"
    service    = Column(String, nullable=True)
    status     = Column(String, default="booked") # booked, cancelled, completed


class Employee(Base):
    __tablename__ = "employees"

    id     = Column(Integer, primary_key=True, index=True)
    org_id = Column(String, nullable=False)
    name   = Column(String, nullable=False)
    role   = Column(String, nullable=False)
    email  = Column(String, nullable=False)
    status = Column(String, default="active")     # active, inactive


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id          = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, nullable=False)
    start_date  = Column(Date, nullable=False)
    end_date    = Column(Date, nullable=False)
    reason      = Column(Text, nullable=True)
    status      = Column(String, default="pending") # pending, approved, rejected
    created_at  = Column(DateTime, nullable=False)