import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Employee, Movement, Ticket
from app.schemas import EmployeeRead, TicketRead
from app.security import create_access_token, hash_password, verify_password

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Guardarropía QR - Fase 2", version="2.0.0")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


def current_employee(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> Employee:
    error = HTTPException(status_code=401, detail="Credenciales inválidas")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise error
    except JWTError as exc:
        raise error from exc
    employee = db.query(Employee).filter(Employee.username == username, Employee.active.is_(True)).first()
    if not employee:
        raise error
    return employee


def require_admin(employee: Employee = Depends(current_employee)) -> Employee:
    if employee.role != "admin":
        raise HTTPException(status_code=403, detail="Se requiere rol admin")
    return employee


@app.get("/", response_class=HTMLResponse)
def home():
    return FileResponse("static/scan.html")


@app.post("/phase2/login")
def login(payload: dict, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.username == payload.get("username")).first()
    if not employee or not verify_password(payload.get("password", ""), employee.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return {"access_token": create_access_token(employee.username), "token_type": "bearer", "employee": employee}


@app.post("/phase2/photos", response_model=dict)
def upload_photo(file: UploadFile = File(...), employee: Employee = Depends(current_employee)):
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Formato no permitido; usa JPG, PNG o WEBP")
    suffix = Path(file.filename or "photo.jpg").suffix.lower() or ".jpg"
    filename = f"{secrets.token_urlsafe(16)}{suffix}"
    destination = UPLOAD_DIR / filename
    destination.write_bytes(file.file.read())
    return {"filename": filename, "url": f"/phase2/photos/{filename}"}


@app.get("/phase2/photos/{filename}")
def get_photo(filename: str):
    path = UPLOAD_DIR / Path(filename).name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    return FileResponse(path)


@app.get("/phase2/admin/employees", response_model=list[EmployeeRead])
def employees(db: Session = Depends(get_db), _: Employee = Depends(require_admin)):
    return db.query(Employee).order_by(Employee.created_at.desc()).all()


@app.patch("/phase2/admin/employees/{employee_id}/active")
def change_employee_status(employee_id: int, active: bool, db: Session = Depends(get_db), _: Employee = Depends(require_admin)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    employee.active = active
    db.commit()
    return {"id": employee.id, "active": employee.active}


@app.get("/phase2/reports/daily")
def daily_report(db: Session = Depends(get_db), employee: Employee = Depends(current_employee)):
    today = datetime.utcnow().date()
    tickets = db.query(Ticket).all()
    created = [t for t in tickets if t.date_in and t.date_in.date() == today]
    retired = [t for t in created if t.status == "retired"]
    by_payment = {}
    for ticket in retired:
        by_payment[ticket.payment_method] = by_payment.get(ticket.payment_method, 0) + float(ticket.price)
    return {
        "date": today.isoformat(),
        "created_tickets": len(created),
        "retired_tickets": len(retired),
        "revenue": sum(float(t.price) for t in retired),
        "revenue_by_payment": by_payment,
        "pending": sum(1 for t in tickets if t.status == "stored"),
        "requested_by": employee.username,
    }


@app.get("/phase2/tickets/{ticket_id}/audit")
def audit(ticket_id: int, db: Session = Depends(get_db), _: Employee = Depends(current_employee)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return db.query(Movement).filter(Movement.ticket_id == ticket_id).order_by(Movement.created_at.desc()).all()


@app.get("/health")
def health():
    return {"status": "ok", "phase": 2}
