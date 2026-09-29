import os
import secrets
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

from fpdf import FPDF
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import CashSession, Employee, Movement, Ticket
from app.schemas import BoxSummary, CashSessionClose, CashSessionCreate, EmployeeRead, MovementRead, TicketRead
from app.security import create_access_token, hash_password, verify_password

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Guardarropía QR - Producción v2.1",
    description="Sistema profesional de guardarropía con reportes, caja y impresión.",
    version="2.1.0",
)

Base.metadata.create_all(bind=engine)


def get_current_employee(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> Employee:
    error = HTTPException(status_code=401, detail="Credenciales inválidas")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise error
    except JWTError:
        raise error
    employee = db.query(Employee).filter(Employee.username == username, Employee.active.is_(True)).first()
    if not employee:
        raise error
    return employee


def require_admin(employee: Employee = Depends(get_current_employee)) -> Employee:
    if employee.role != "admin":
        raise HTTPException(status_code=403, detail="Se requiere rol admin")
    return employee


def require_supervisor(employee: Employee = Depends(get_current_employee)) -> Employee:
    if employee.role not in {"supervisor", "admin"}:
        raise HTTPException(status_code=403, detail="Se requiere supervisor o admin")
    return employee


# ========== AUTENTICACIÓN ==========
@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.username == username).first()
    if not employee or not verify_password(password, employee.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if not employee.active:
        raise HTTPException(status_code=403, detail="Empleado inactivo")
    return {"access_token": create_access_token(employee.username), "token_type": "bearer", "employee": employee}


@app.post("/employees", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(username: str, password: str, full_name: str, role: str = "cashier", db: Session = Depends(get_db)):
    if db.query(Employee).filter(Employee.username == username).first():
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    employee = Employee(
        username=username,
        password=hash_password(password),
        full_name=full_name,
        role=role,
        active=True,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@app.get("/me", response_model=EmployeeRead)
def me(employee: Employee = Depends(get_current_employee)):
    return employee


# ========== FOTOS ==========
@app.post("/photos")
def upload_photo(file: UploadFile = File(...), employee: Employee = Depends(get_current_employee)):
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Formato no permitido")
    suffix = Path(file.filename or "photo.jpg").suffix.lower() or ".jpg"
    filename = f"{secrets.token_urlsafe(16)}{suffix}"
    destination = UPLOAD_DIR / filename
    destination.write_bytes(file.file.read())
    return {"filename": filename, "url": f"/photos/{filename}"}


@app.get("/photos/{filename}")
def get_photo(filename: str):
    path = UPLOAD_DIR / Path(filename).name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    return FileResponse(path)


# ========== ADMINISTRACIÓN ==========
@app.get("/admin/employees", response_model=list[EmployeeRead])
def list_employees(db: Session = Depends(get_db), _: Employee = Depends(require_admin)):
    return db.query(Employee).order_by(Employee.created_at.desc()).all()


@app.patch("/admin/employees/{employee_id}/toggle")
def toggle_employee(employee_id: int, active: bool, db: Session = Depends(get_db), _: Employee = Depends(require_admin)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    employee.active = active
    db.commit()
    return {"id": employee.id, "active": employee.active}


# ========== CAJA ==========
@app.post("/cash-session/open")
def open_session(opening_amount: float = 0.0, notes: str = "", db: Session = Depends(get_db), employee: Employee = Depends(get_current_employee)):
    session = CashSession(
        employee_id=employee.id,
        opening_amount=opening_amount,
        notes=notes,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"id": session.id, "opened_at": session.opened_at, "opening_amount": session.opening_amount}


@app.post("/cash-session/{session_id}/close")
def close_session(session_id: int, closing_amount: float, notes: str = "", db: Session = Depends(get_db), employee: Employee = Depends(get_current_employee)):
    session = db.query(CashSession).filter(CashSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    session.closed_at = datetime.utcnow()
    session.closing_amount = closing_amount
    session.notes = notes or session.notes
    db.commit()
    return {"id": session.id, "closing_amount": session.closing_amount, "closed_at": session.closed_at}


# ========== REPORTES ==========
@app.get("/reports/daily")
def daily_report(db: Session = Depends(get_db), employee: Employee = Depends(get_current_employee)):
    today = datetime.utcnow().date()
    tickets = db.query(Ticket).filter(Ticket.date_in >= datetime(today.year, today.month, today.day)).all()
    created = len(tickets)
    retired = len([t for t in tickets if t.status == "retired"])
    lost = len([t for t in tickets if t.status == "lost"])
    revenue = sum(float(t.price) for t in tickets if t.status == "retired")
    by_payment = {}
    for t in tickets:
        if t.status == "retired":
            by_payment[t.payment_method] = by_payment.get(t.payment_method, 0) + float(t.price)
    return {
        "date": today.isoformat(),
        "created_tickets": created,
        "retired_tickets": retired,
        "lost_tickets": lost,
        "revenue": revenue,
        "revenue_by_payment": by_payment,
        "pending": sum(1 for t in tickets if t.status == "stored"),
    }


@app.get("/reports/shift")
def shift_report(start: str, end: str, db: Session = Depends(get_db), employee: Employee = Depends(require_supervisor)):
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    tickets = db.query(Ticket).filter(Ticket.date_in.between(start_dt, end_dt)).all()
    return {
        "period": f"{start} to {end}",
        "created": len(tickets),
        "retired": len([t for t in tickets if t.status == "retired"]),
        "revenue": sum(float(t.price) for t in tickets if t.status == "retired"),
        "by_payment": {m: sum(float(t.price) for t in tickets if t.status == "retired" and t.payment_method == m) for m in {"cash", "card", "bank_qr", "other"}},
    }


def generate_pdf_report(data: dict) -> BytesIO:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Reporte de Guardarropía", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Fecha: {data.get('date', 'N/A')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Resumen", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Prendas registradas: {data.get('created_tickets', 0)}", ln=True)
    pdf.cell(0, 8, f"Prendas entregadas: {data.get('retired_tickets', 0)}", ln=True)
    pdf.cell(0, 8, f"Prendas perdidas: {data.get('lost_tickets', 0)}", ln=True)
    pdf.cell(0, 8, f"Prendas pendientes: {data.get('pending', 0)}", ln=True)
    pdf.cell(0, 8, f"Ingreso total: ${data.get('revenue', 0):.2f}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Desglose por método de pago", ln=True)
    pdf.set_font("Arial", "", 11)
    for method, amount in data.get("revenue_by_payment", {}).items():
        pdf.cell(0, 8, f"{method}: ${amount:.2f}", ln=True)
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer


@app.get("/reports/daily/pdf")
def daily_report_pdf(db: Session = Depends(get_db), employee: Employee = Depends(get_current_employee)):
    data = daily_report(db, employee)
    pdf_buffer = generate_pdf_report(data)
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=reporte_diario.pdf"})


@app.get("/reports/shift/pdf")
def shift_report_pdf(start: str, end: str, db: Session = Depends(get_db), employee: Employee = Depends(require_supervisor)):
    data = shift_report(start, end, db, employee)
    pdf_buffer = generate_pdf_report(data)
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=reporte_turno.pdf"})


# ========== AUDITORÍA ==========
@app.get("/tickets/{ticket_id}/audit", response_model=list[MovementRead])
def ticket_audit(ticket_id: int, db: Session = Depends(get_db), employee: Employee = Depends(get_current_employee)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return db.query(Movement).filter(Movement.ticket_id == ticket_id).order_by(Movement.created_at.desc()).all()


# ========== SINCRONIZACIÓN OFFLINE ==========
@app.post("/sync/upload")
def sync_upload(payload: dict, db: Session = Depends(get_db), employee: Employee = Depends(get_current_employee)):
    """
    Endpoint para sincronizar datos guardados offline.
    El cliente envía: {"tickets": [...], "movements": [...]}
    """
    synced = {"tickets": 0, "movements": 0}
    # Aquí iría lógica de sincronización real
    # Por ahora retornamos confirmación
    return {"synced": synced, "status": "success"}


@app.get("/sync/status")
def sync_status(employee: Employee = Depends(get_current_employee)):
    return {"status": "online", "timestamp": datetime.utcnow().isoformat()}


# ========== HEALTH ==========
@app.get("/health")
def health():
    return {"status": "ok", "version": "2.1", "timestamp": datetime.utcnow().isoformat()}
