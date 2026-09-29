import io
import secrets
from datetime import datetime

import qrcode
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Employee, Movement, Ticket
from app.schemas import (
    BoxSummary,
    EmployeeCreate,
    EmployeeLogin,
    EmployeeRead,
    MovementRead,
    TicketCreate,
    TicketLost,
    TicketRead,
    TicketReturn,
    TicketScan,
    TicketStatusUpdate,
)

app = FastAPI(
    title="Guardarropía QR",
    description="Sistema MVP de guardarropía para discoteca",
    version="0.1.0",
)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Guardarropía QR</title>
  <style>
    body { font-family: Arial, sans-serif; background: #111827; color: #f3f4f6; margin: 0; padding: 24px; }
    .container { max-width: 1100px; margin: 0 auto; }
    h1, h2 { margin-top: 0; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
    .card { background: #1f2937; padding: 18px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,.25); }
    label { display: block; margin-bottom: 6px; color: #cbd5e1; }
    input, select, button, textarea { width: 100%; box-sizing: border-box; margin-bottom: 12px; padding: 10px 12px; border-radius: 8px; border: 1px solid #374151; background: #0f172a; color: white; }
    button { background: #2563eb; cursor: pointer; border: none; font-weight: bold; }
    button.secondary { background: #16a34a; }
    button.danger { background: #dc2626; }
    .log, .tickets, .summary { margin-top: 18px; }
    .ticket { background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 12px; margin-top: 10px; }
    .small { font-size: 12px; color: #cbd5e1; }
    img { max-width: 180px; display: block; margin: 8px 0; }
    .hidden { display: none; }
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
        <label>Percha / casillero</label>
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
        <h2>Escáner / devolución</h2>
        <label>Token QR</label>
        <input id="scanToken" placeholder="Pegue el token QR" />
        <button onclick="scanTicket()">Buscar ticket</button>
        <button class="danger" onclick="returnTicket()">Confirmar entrega</button>
        <div id="scanResult" class="small"></div>
      </div>

      <div class="card">
        <h2>Caja</h2>
        <button onclick="loadSummary()">Ver resumen</button>
        <div id="summaryResult" class="small"></div>
      </div>
    </div>

    <div class="card tickets">
      <h2>Prendas pendientes</h2>
      <button onclick="loadPendingTickets()">Actualizar lista</button>
      <div id="pendingTickets"></div>
    </div>

    <div class="card log">
      <h2>Logs</h2>
      <div id="logs"></div>
    </div>
  </div>

  <script>
    const state = { employee: null, selectedTicket: null };

    function addLog(msg) {
      const el = document.getElementById('logs');
      const p = document.createElement('div');
      p.className = 'small';
      p.textContent = new Date().toLocaleTimeString() + ' - ' + msg;
      el.prepend(p);
    }

    async function api(path, options = {}) {
      const response = await fetch(path, {
        headers: { 'Content-Type': 'application/json' },
        ...options
      });
      const text = await response.text();
      let data = null;
      try { data = text ? JSON.parse(text) : null; } catch (e) { data = { raw: text }; }
      if (!response.ok) {
        throw new Error(data.detail || data.error || 'Error');
      }
      return data;
    }

    async function loginEmployee() {
      try {
        const payload = {
          username: document.getElementById('loginUser').value,
          password: document.getElementById('loginPass').value
        };
        const employee = await api('/employees/login', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        state.employee = employee;
        document.getElementById('loginResult').textContent = 'Sesión iniciada: ' + employee.full_name;
        addLog('Login: ' + employee.full_name);
      } catch (error) {
        document.getElementById('loginResult').textContent = error.message;
        addLog('Login error: ' + error.message);
      }
    }

    async function createTicket() {
      if (!state.employee) {
        document.getElementById('ticketResult').textContent = 'Debe iniciar sesión primero';
        return;
      }
      try {
        const payload = {
          hanger_number: document.getElementById('hanger').value || null,
          description: document.getElementById('description').value,
          price: Number(document.getElementById('price').value || 0),
          payment_method: document.getElementById('paymentMethod').value,
          notes: document.getElementById('notes').value || null,
          employee_in_id: state.employee.id
        };
        const ticket = await api('/tickets', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        document.getElementById('ticketResult').innerHTML = `Ticket creado: #${ticket.id}<br>Token: ${ticket.qr_token}`;
        const qrUrl = '/tickets/' + ticket.id + '/qr';
        const img = `<img src="${qrUrl}" alt="QR">`;
        document.getElementById('ticketResult').innerHTML += '<br>' + img;
        addLog('Ticket creado: #' + ticket.id);
        loadPendingTickets();
      } catch (error) {
        document.getElementById('ticketResult').textContent = error.message;
        addLog('Error ticket: ' + error.message);
      }
    }

    async function scanTicket() {
      try {
        const token = document.getElementById('scanToken').value;
        const ticket = await api('/tickets/scan', {
          method: 'POST',
          body: JSON.stringify({ qr_token: token })
        });
        state.selectedTicket = ticket;
        document.getElementById('scanResult').textContent = `Ticket #${ticket.id} - ${ticket.description}`;
        addLog('Ticket encontrado: #' + ticket.id);
      } catch (error) {
        document.getElementById('scanResult').textContent = error.message;
        addLog('Scan error: ' + error.message);
      }
    }

    async function returnTicket() {
      if (!state.employee) {
        document.getElementById('scanResult').textContent = 'Debe iniciar sesión primero';
        return;
      }
      if (!state.selectedTicket) {
        document.getElementById('scanResult').textContent = 'Debe buscar un ticket primero';
        return;
      }
      try {
        const ticket = await api('/tickets/' + state.selectedTicket.id + '/return', {
          method: 'POST',
          body: JSON.stringify({ employee_out_id: state.employee.id, notes: 'Entrega confirmada por frontend' })
        });
        document.getElementById('scanResult').textContent = `Ticket entregado: #${ticket.id}`;
        addLog('Entrega confirmada: #' + ticket.id);
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
        tickets.forEach(ticket => {
          const div = document.createElement('div');
          div.className = 'ticket';
          div.innerHTML = `
            <strong>#${ticket.id}</strong> - ${ticket.description}<br>
            <span class="small">Percha: ${ticket.hanger_number || 'N/A'} | Pago: ${ticket.payment_method} | Precio: ${ticket.price}</span><br>
            <span class="small">Token: ${ticket.qr_token}</span><br>
            <img src="/tickets/${ticket.id}/qr" alt="QR ${ticket.id}" />
            <button onclick="document.getElementById('scanToken').value='${ticket.qr_token}'; state.selectedTicket=${JSON.stringify(ticket)};">Usar QR</button>
          `;
          el.appendChild(div);
        });
      } catch (error) {
        addLog('Error pending: ' + error.message);
      }
    }

    async function loadSummary() {
      try {
        const summary = await api('/box/summary');
        document.getElementById('summaryResult').innerHTML = `
          Total retiradas: ${summary.total_tickets}<br>
          Ingreso total: $${summary.total_revenue}<br>
          Estado: ${JSON.stringify(summary.status_breakdown)}
        `;
      } catch (error) {
        document.getElementById('summaryResult').textContent = error.message;
      }
    }

    window.onload = () => {
      loadPendingTickets();
      loadSummary();
      addLog('Frontend cargado');
    };
  </script>
</body>
</html>
"""


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE


@app.post("/employees", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    existing = db.query(Employee).filter(Employee.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    employee = Employee(
        username=payload.username,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
        active=True,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@app.post("/employees/login", response_model=EmployeeRead)
def login_employee(payload: EmployeeLogin, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.username == payload.username).first()
    if not employee or employee.password != payload.password:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if not employee.active:
        raise HTTPException(status_code=403, detail="Empleado inactivo")
    return employee


@app.post("/tickets", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == payload.employee_in_id).first()
    if not employee:
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
        employee_in_id=payload.employee_in_id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    movement = Movement(
        ticket_id=ticket.id,
        action="created",
        details=f"Prenda registrada por {employee.full_name}",
        employee_id=employee.id,
    )
    db.add(movement)
    db.commit()
    return ticket


@app.get("/tickets/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket


@app.post("/tickets/scan", response_model=TicketRead)
def scan_ticket(payload: TicketScan, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.qr_token == payload.qr_token).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="QR no válido o ya usado")
    if ticket.status != "stored":
        raise HTTPException(status_code=400, detail=f"El ticket ya está en estado: {ticket.status}")
    return ticket


@app.post("/tickets/{ticket_id}/return", response_model=TicketRead)
def return_ticket(ticket_id: int, payload: TicketReturn, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if ticket.status != "stored":
        raise HTTPException(status_code=400, detail="La prenda ya fue retirada o anulada")

    employee = db.query(Employee).filter(Employee.id == payload.employee_out_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    ticket.status = "retired"
    ticket.employee_out_id = payload.employee_out_id
    ticket.date_out = datetime.utcnow()
    ticket.qr_token = None
    if payload.notes:
        ticket.notes = payload.notes

    movement = Movement(
        ticket_id=ticket.id,
        action="returned",
        details=f"Prenda entregada por {employee.full_name}",
        employee_id=employee.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.post("/tickets/{ticket_id}/lost", response_model=TicketRead)
def mark_ticket_lost(ticket_id: int, payload: TicketLost, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if ticket.status == "retired":
        raise HTTPException(status_code=400, detail="No se puede marcar como perdido un ticket ya retirado")

    employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    ticket.status = "lost"
    ticket.qr_token = None
    ticket.notes = payload.details
    if payload.photo_url:
        ticket.photo_url = payload.photo_url

    movement = Movement(
        ticket_id=ticket.id,
        action="lost",
        details=f"Ticket perdido. Supervisor: {payload.supervisor_name}. Detalles: {payload.details}",
        employee_id=employee.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.get("/tickets", response_model=list[TicketRead])
def list_tickets(db: Session = Depends(get_db)):
    return db.query(Ticket).order_by(Ticket.date_in.desc()).all()


@app.get("/tickets/pending", response_model=list[TicketRead])
def pending_tickets(db: Session = Depends(get_db)):
    return db.query(Ticket).filter(Ticket.status == "stored").order_by(Ticket.date_in.desc()).all()


@app.get("/tickets/{ticket_id}/movements", response_model=list[MovementRead])
def ticket_movements(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return db.query(Movement).filter(Movement.ticket_id == ticket_id).order_by(Movement.created_at.desc()).all()


@app.get("/tickets/{ticket_id}/qr")
def generate_qr(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(ticket.qr_token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")


@app.post("/tickets/{ticket_id}/status", response_model=TicketRead)
def update_ticket_status(ticket_id: int, payload: TicketStatusUpdate, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    if payload.status == "retired":
        ticket.status = "retired"
        ticket.employee_out_id = payload.employee_id
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
        employee_id=payload.employee_id,
    )
    db.add(movement)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.get("/box/summary")
def box_summary(db: Session = Depends(get_db)):
    tickets = db.query(Ticket).all()
    retained = [t for t in tickets if t.status == "retired"]
    total_tickets = len(retained)
    total_revenue = sum(float(t.price) for t in retained)
    status_breakdown = {
        "stored": sum(1 for t in tickets if t.status == "stored"),
        "retired": sum(1 for t in tickets if t.status == "retired"),
        "lost": sum(1 for t in tickets if t.status == "lost"),
        "cancelled": sum(1 for t in tickets if t.status == "cancelled"),
    }
    return {
        "total_tickets": total_tickets,
        "total_revenue": total_revenue,
        "status_breakdown": status_breakdown,
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "coat-check"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
