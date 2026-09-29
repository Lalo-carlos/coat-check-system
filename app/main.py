import io
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import qrcode
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import CashSession, Employee, Movement, Ticket
from app.schemas import (
    BoxSummary,
    CashSessionClose,
    CashSessionCreate,
    EmployeeCreate,
    EmployeeLogin,
    EmployeeLoginResponse,
    EmployeeRead,
    MovementRead,
    TicketCreate,
    TicketLost,
    TicketRead,
    TicketReturn,
    TicketScan,
    TicketStatusUpdate,
)

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

app = FastAPI(
    title="Guardarropía QR avanzado",
    description="Sistema profesional de guardarropía para discotecas con QR, seguridad y caja.",
    version="1.0.0",
)

HTML_PAGE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Guardarropía QR</title>
  <style>
    body { font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }
    .container { max-width: 1100px; margin: 0 auto; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
    .card { background: #111827; border: 1px solid #374151; border-radius: 12px; padding: 18px; }
    input, select, textarea, button { width: 100%; box-sizing: border-box; margin-top: 8px; margin-bottom: 12px; padding: 10px 12px; border-radius: 8px; border: 1px solid #475569; background: #020817; color: #f8fafc; }
    button { background: #2563eb; border: none; cursor: pointer; font-weight: bold; }
    button.secondary { background: #16a34a; }
    button.danger { background: #dc2626; }
    h1, h2 { margin-top: 0; }
    .small { font-size: 12px; color: #cbd5e1; }
    .ticket { background: #0b1220; border: 1px solid #334155; border-radius: 10px; padding: 12px; margin-top: 10px; }
    img { max-width: 180px; margin-top: 8px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Guardarropía QR</h1>

    <div class="grid">
      <div class="card">
        <h2>Login</h2>
        <label>Usuario</label>
        <input id="loginUser" value="cashier1" />
        <label>Contraseña</label>
        <input id="loginPass" type="password" value="1234" />
        <button onclick="loginEmployee()">Entrar</button>
        <div id="loginResult" class="small"></div>
      </div>

      <div class="card">
        <h2>Registrar prenda</h2>
        <label>Percha</label>
        <input id="hanger" placeholder="A-12" />
        <label>Descripción</label>
        <input id="description" placeholder="Chaqueta negra mujer" />
        <label>Precio</label>
        <input id="price" type="number" value="0" />
        <label>Pago</label>
        <select id="paymentMethod">
          <option value="cash">Efectivo</option>
          <option value="bank_qr">QR bancario</option>
          <option value="card">Tarjeta</option>
        </select>
        <label>Notas</label>
        <textarea id="notes" rows="3"></textarea>
        <button class="secondary" onclick="createTicket()">Guardar prenda</button>
        <div id="ticketResult" class="small"></div>
      </div>
    </div>

    <div class="grid" style="margin-top: 20px;">
      <div class="card">
        <h2>Escáner / entrega</h2>
        <label>Token QR</label>
        <input id="scanToken" placeholder="Pega el token QR" />
        <button onclick="scanTicket()">Buscar</button>
        <button class="danger" onclick="returnTicket()">Confirmar entrega</button>
        <div id="scanResult" class="small"></div>
      </div>

      <div class="card">
        <h2>Caja</h2>
        <button onclick="loadSummary()">Ver resumen</button>
        <div id="summaryResult" class="small"></div>
      </div>
    </div>

    <div class="card" style="margin-top: 20px;">
      <h2>Prendas pendientes</h2>
      <button onclick="loadPendingTickets()">Actualizar</button>
      <div id="pendingTickets"></div>
    </div>
  </div>

  <script>
    const state = { token: '', employee: null, selectedTicket: null };

    function setToken(token) { state.token = token; }

    async function api(path, options = {}) {
      const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
      if (state.token) headers['Authorization'] = `Bearer ${state.token}`;
      const response = await fetch(path, { ...options, headers });
      const text = await response.text();
      let data = null;
      try { data = text ? JSON.parse(text) : null; } catch (e) { data = { raw: text }; }
      if (!response.ok) throw new Error(data.detail || 'Error');
      return data;
    }

    async function loginEmployee() {
      try {
        const payload = {
          username: document.getElementById('loginUser').value,
          password: document.getElementById('loginPass').value
        };
        const data = await api('/login', { method: 'POST', body: JSON.stringify(payload) });
        setToken(data.access_token);
        state.employee = data.employee;
        document.getElementById('loginResult').textContent = `Sesión iniciada: ${data.employee.full_name}`;
      } catch (error) {
        document.getElementById('loginResult').textContent = error.message;
      }
    }

    async function createTicket() {
      if (!state.employee) {
        document.getElementById('ticketResult').textContent = 'Debe iniciar sesión';
        return;
      }
      try {
        const payload = {
          hanger_number: document.getElementById('hanger').value || null,
          description: document.getElementById('description').value,
          price: Number(document.getElementById('price').value || 0),
          payment_method: document.getElementById('paymentMethod').value,
          notes: document.getElementById('notes').value || null
        };
        const ticket = await api('/tickets', { method: 'POST', body: JSON.stringify(payload) });
        const qrUrl = `/tickets/${ticket.id}/qr`;
        document.getElementById('ticketResult').innerHTML = `Ticket #${ticket.id}<br>Token: ${ticket.qr_token}<br><img src="${qrUrl}" />`;
        loadPendingTickets();
      } catch (error) {
        document.getElementById('ticketResult').textContent = error.message;
      }
    }

    async function scanTicket() {
      try {
        const token = document.getElementById('scanToken').value;
        const ticket = await api('/tickets/scan', { method: 'POST', body: JSON.stringify({ qr_token: token }) });
        state.selectedTicket = ticket;
        document.getElementById('scanResult').textContent = `Ticket #${ticket.id} - ${ticket.description}`;
      } catch (error) {
        document.getElementById('scanResult').textContent = error.message;
      }
    }

    async function returnTicket() {
      if (!state.selectedTicket) {
        document.getElementById('scanResult').textContent = 'Debe buscar un ticket antes';
        return;
      }
      try {
        const ticket = await api(`/tickets/${state.selectedTicket.id}/return`, { method: 'POST', body: JSON.stringify({ notes: 'Entrega confirmada por interfaz web' }) });
        document.getElementById('scanResult').textContent = `Prenda entregada: #${ticket.id}`;
        loadPendingTickets();
      } catch (error) {
        document.getElementById('scanResult').textContent = error.message;
      }
    }

    async function loadPendingTickets() {
      try {
        const tickets = await api('/tickets/pending');
        const el = document.getElementById('pendingTickets');
        el.innerHTML = '';
        if (!tickets.length) {
          el.innerHTML = '<div class="small">No hay prendas pendientes</div>';
          return;
        }
        tickets.forEach((ticket) => {
          const div = document.createElement('div');
          div.className = 'ticket';
          div.innerHTML = `
            <strong>#${ticket.id}</strong> - ${ticket.description}<br>
            <span class="small">Percha: ${ticket.hanger_number || 'N/A'} | Pago: ${ticket.payment_method}</span><br>
            <img src="/tickets/${ticket.id}/qr" />
            <button onclick="document.getElementById('scanToken').value='${ticket.qr_token || ''}'">Usar QR</button>
          `;
          el.appendChild(div);
        });
      } catch (error) {
        document.getElementById('pendingTickets').textContent = error.message;
      }
    }

    async function loadSummary() {
      try {
        const summary = await api('/box/summary');
        document.getElementById('summaryResult').innerHTML = `
          Tickets retirados: ${summary.total_tickets}<br>
          Ingreso total: $${summary.total_revenue}<br>
          Estados: ${JSON.stringify(summary.status_breakdown)}
        `;
      } catch (error) {
        document.getElementById('summaryResult').textContent = error.message;
      }
    }

    window.onload = () => {
      loadPendingTickets();
      loadSummary();
    };
  </script>
</body>
</html>
"""


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": subject, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_employee(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> Employee:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    employee = db.query(Employee).filter(Employee.username == username).first()
    if employee is None:
        raise credentials_exception
    return employee


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE


@app.post("/login", response_model=EmployeeLoginResponse)
def login(payload: EmployeeLogin, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.username == payload.username).first()
    if not employee or not verify_password(payload.password, employee.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if not employee.active:
        raise HTTPException(status_code=403, detail="Empleado inactivo")
    access_token = create_access_token(employee.username)
    return {"access_token": access_token, "token_type": "bearer", "employee": employee}


@app.post("/employees/login", response_model=EmployeeLoginResponse)
def login_alias(payload: EmployeeLogin, db: Session = Depends(get_db)):
    return login(payload, db)


@app.post("/employees", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    existing = db.query(Employee).filter(Employee.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    employee = Employee(
        username=payload.username,
        password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        active=True,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@app.get("/me", response_model=EmployeeRead)
def me(current_employee: Employee = Depends(get_current_employee)):
    return current_employee


@app.post("/tickets", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db), current_employee: Employee = Depends(get_current_employee)):
    employee_in = db.query(Employee).filter(Employee.id == (payload.employee_in_id or current_employee.id)).first()
    if not employee_in:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    token = secrets.token_urlsafe(24)
    ticket = Ticket(
        qr_token=token,
        hanger_number=payload.hanger_number,
        description=payload.description,
        photo_url=payload.photo_url,
        price=payload.price,
        payment_method=payload.payment_method,
        status="stored",
        notes=payload.notes,
        employee_in_id=employee_in.id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    movement = Movement(
        ticket_id=ticket.id,
        action="created",
        details=f"Prenda registrada por {employee_in.full_name}",
        employee_id=employee_in.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.get("/tickets", response_model=list[TicketRead])
def list_tickets(db: Session = Depends(get_db), current_employee: Employee = Depends(get_current_employee)):
    return db.query(Ticket).order_by(Ticket.date_in.desc()).all()


@app.get("/tickets/pending", response_model=list[TicketRead])
def pending_tickets(db: Session = Depends(get_db), current_employee: Employee = Depends(get_current_employee)):
    return db.query(Ticket).filter(Ticket.status == "stored").order_by(Ticket.date_in.desc()).all()


@app.get("/tickets/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, db: Session = Depends(get_db), current_employee: Employee = Depends(get_current_employee)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket


@app.post("/tickets/scan", response_model=TicketRead)
def scan_ticket(payload: TicketScan, db: Session = Depends(get_db), current_employee: Employee = Depends(get_current_employee)):
    ticket = db.query(Ticket).filter(Ticket.qr_token == payload.qr_token).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="QR no válido o ya usado")
    if ticket.status != "stored":
        raise HTTPException(status_code=400, detail=f"El ticket ya está en estado: {ticket.status}")
    return ticket


@app.post("/tickets/{ticket_id}/return", response_model=TicketRead)
def return_ticket(ticket_id: int, payload: TicketReturn, db: Session = Depends(get_db), current_employee: Employee = Depends(get_current_employee)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if ticket.status != "stored":
        raise HTTPException(status_code=400, detail="La prenda ya fue retirada o anulada")

    ticket.status = "retired"
    ticket.employee_out_id = current_employee.id
    ticket.date_out = datetime.utcnow()
    ticket.qr_token = None
    if payload.notes:
        ticket.notes = payload.notes

    movement = Movement(
        ticket_id=ticket.id,
        action="returned",
        details=f"Prenda entregada por {current_employee.full_name}",
        employee_id=current_employee.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.post("/tickets/{ticket_id}/lost", response_model=TicketRead)
def mark_ticket_lost(ticket_id: int, payload: TicketLost, db: Session = Depends(get_db), current_employee: Employee = Depends(get_current_employee)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if ticket.status == "retired":
        raise HTTPException(status_code=400, detail="No se puede marcar como perdido un ticket ya retirado")
    if current_employee.role not in {"supervisor", "admin"}:
        raise HTTPException(status_code=403, detail="Se requiere aprobación de supervisor")

    ticket.status = "lost"
    ticket.qr_token = None
    ticket.notes = payload.details
    if payload.photo_url:
        ticket.photo_url = payload.photo_url

    movement = Movement(
        ticket_id=ticket.id,
        action="lost",
        details=f"Ticket perdido. Supervisor: {payload.supervisor_name}. Detalles: {payload.details}",
        employee_id=current_employee.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.get("/tickets/{ticket_id}/movements", response_model=list[MovementRead])
def ticket_movements(ticket_id: int, db: Session = Depends(get_db), current_employee: Employee = Depends(get_current_employee)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return db.query(Movement).filter(Movement.ticket_id == ticket_id).order_by(Movement.created_at.desc()).all()


@app.get("/tickets/{ticket_id}/qr")
def generate_qr(ticket_id: int, db: Session = Depends(get_db), current_employee: Employee = Depends(get_current_employee)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    if not ticket.qr_token:
        raise HTTPException(status_code=400, detail="Este ticket ya no tiene QR válido")

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(ticket.qr_token)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")


@app.post("/tickets/{ticket_id}/status", response_model=TicketRead)
def update_status(ticket_id: int, payload: TicketStatusUpdate, db: Session = Depends(get_db), current_employee: Employee = Depends(get_current_employee)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    if payload.status == "retired":
        ticket.status = "retired"
        ticket.employee_out_id = current_employee.id
        ticket.date_out = datetime.utcnow()
        ticket.qr_token = None
    else:
        ticket.status = payload.status

    if payload.notes:
        ticket.notes = payload.notes

    movement = Movement(
        ticket_id=ticket.id,
        action=payload.status,
        details=payload.notes,
        employee_id=current_employee.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.post("/cash-session/open", response_model=dict)
def open_cash_session(payload: CashSessionCreate, db: Session = Depends(get_db), current_employee: Employee = Depends(get_current_employee)):
    session = CashSession(
        employee_id=current_employee.id,
        opening_amount=payload.opening_amount,
        notes=payload.notes,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"id": session.id, "employee_id": current_employee.id, "opening_amount": session.opening_amount, "opened_at": session.opened_at}


@app.post("/cash-session/{session_id}/close", response_model=dict)
def close_cash_session(session_id: int, payload: CashSessionClose, db: Session = Depends(get_db), current_employee: Employee = Depends(get_current_employee)):
    session = db.query(CashSession).filter(CashSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión de caja no encontrada")
    session.closed_at = datetime.utcnow()
    session.closing_amount = payload.closing_amount
    session.notes = payload.notes or session.notes
    db.commit()
    return {"id": session.id, "closing_amount": session.closing_amount, "closed_at": session.closed_at}


@app.get("/box/summary", response_model=BoxSummary)
def box_summary(db: Session = Depends(get_db), current_employee: Employee = Depends(get_current_employee)):
    tickets = db.query(Ticket).all()
    retired_tickets = [t for t in tickets if t.status == "retired"]
    total_revenue = sum(float(t.price) for t in retired_tickets)
    status_breakdown = {
        "stored": sum(1 for t in tickets if t.status == "stored"),
        "retired": sum(1 for t in tickets if t.status == "retired"),
        "lost": sum(1 for t in tickets if t.status == "lost"),
        "cancelled": sum(1 for t in tickets if t.status == "cancelled"),
    }
    return {
        "total_tickets": len(retired_tickets),
        "total_revenue": total_revenue,
        "status_breakdown": status_breakdown,
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "coat-check"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
