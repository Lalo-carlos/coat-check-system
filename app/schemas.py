from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EmployeeCreate(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=4)
    full_name: str = Field(..., min_length=2)
    role: str = "cashier"


class EmployeeLogin(BaseModel):
    username: str
    password: str


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: str
    active: bool


class TicketCreate(BaseModel):
    hanger_number: Optional[str] = None
    description: str = Field(..., min_length=3)
    photo_url: Optional[str] = None
    price: float = 0.0
    payment_method: str = "cash"
    notes: Optional[str] = None
    employee_in_id: int


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    qr_token: str
    hanger_number: Optional[str]
    description: str
    photo_url: Optional[str]
    price: float
    payment_method: str
    status: str
    notes: Optional[str]
    date_in: datetime
    date_out: Optional[datetime]
    employee_in_id: int
    employee_out_id: Optional[int]


class TicketScan(BaseModel):
    qr_token: str


class TicketReturn(BaseModel):
    employee_out_id: int
    notes: Optional[str] = None


class TicketLost(BaseModel):
    employee_id: int
    details: str
    supervisor_name: str
    photo_url: Optional[str] = None


class MovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    action: str
    details: Optional[str]
    employee_id: int
    created_at: datetime


class BoxSummary(BaseModel):
    total_tickets: int
    total_revenue: float
    status_breakdown: dict


class TicketStatusUpdate(BaseModel):
    status: str
    employee_id: int
    notes: Optional[str] = None
