# api_integration.py - FastAPI backend to connect both systems

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import asyncio
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = FastAPI(title="Maintenance Integration API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501"],  # React and Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def init_db():
    conn = sqlite3.connect('maintenance_system.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS work_orders (
        id TEXT PRIMARY KEY,
        equipment_id TEXT,
        technician_id TEXT,
        priority TEXT,
        status TEXT,
        created_at TIMESTAMP,
        scheduled_date TIMESTAMP,
        estimated_duration INTEGER,
        failure_probability REAL,
        health_score REAL,
        maintenance_type TEXT,
        location TEXT,
        description TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id TEXT PRIMARY KEY,
        work_order_id TEXT,
        recipient TEXT,
        channel TEXT,
        content TEXT,
        status TEXT,
        sent_at TIMESTAMP,
        read_at TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS equipment_status (
        equipment_id TEXT PRIMARY KEY,
        failure_probability REAL,
        health_score REAL,
        risk_level TEXT,
        last_updated TIMESTAMP,
        temperature REAL,
        vibration REAL,
        pressure REAL,
        maintenance_due_date TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Pydantic models
class WorkOrderCreate(BaseModel):
    equipment_id: str
    technician_id: str
    priority: str
    maintenance_type: str
    scheduled_date: str
    estimated_duration: int
    location: str
    description: str

class NotificationRequest(BaseModel):
    work_order_id: str
    technician_id: str
    channels: List[str]
    priority: str
    equipment_info: Dict

class EquipmentUpdate(BaseModel):
    equipment_id: str
    failure_probability: float
    health_score: float
    risk_level: str
    temperature: Optional[float] = None
    vibration: Optional[float] = None
    pressure: Optional[float] = None

class DashboardAlert(BaseModel):
    equipment_id: str
    alert_type: str
    severity: str
    message: str
    threshold_exceeded: str

# Technician database
TECHNICIANS = {
    'Tech-A-Smith': {
        'name': 'John Smith',
        'email': 'john.smith@company.com',
        'phone': '+1-555-0101',
        'mobile': '+1-555-0102',
        'specializations': ['Motor', 'Generator', 'Electrical'],
        'push_token': 'push_token_john_smith'
    },
    'Tech-B-Johnson': {
        'name': 'Sarah Johnson',
        'email': 'sarah.johnson@company.com',
        'phone': '+1-555-0201',
        'mobile': '+1-555-0202',
        'specializations': ['Pump', 'Compressor', 'Hydraulics'],
        'push_token': 'push_token_sarah_johnson'
    }
}

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Maintenance Integration API", "status": "running"}

@app.post("/api/work-orders")
async def create_work_order(work_order: WorkOrderCreate, background_tasks: BackgroundTasks):
    """Create work order from dashboard predictions"""
    
    work_order_id = f"WO-{datetime.now().strftime('%Y%m%d')}-{hash(work_order.equipment_id) % 10000:04d}"
    
    # Store work order in database
    conn = sqlite3.connect('maintenance_system.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO work_orders 
    (id, equipment_id, technician_id, priority, status, created_at, scheduled_date, 
     estimated_duration, maintenance_type, location, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        work_order_id,
        work_order.equipment_id,
        work_order.technician_id,
        work_order.priority,
        'Created',
        datetime.now(),
        datetime.fromisoformat(work_order.scheduled_date.replace('Z', '+00:00')),
        work_order.estimated_duration,
        work_order.maintenance_type,
        work_order.location,
        work_order.description
    ))
    
    conn.commit()
    conn.close()
    
    # Trigger notifications in background
    background_tasks.add_task(
        send_notifications, 
        work_order_id, 
        work_order.technician_id,
        work_order.priority,
        work_order.equipment_id
    )
    
    return {
        "work_order_id": work_order_id,
        "status": "created",
        "message": "Work order created and notifications scheduled"
    }

@app.post("/api/notifications/send")
async def send_notification_request(notification: NotificationRequest):
    """Send notifications through multiple channels"""
    
    technician = TECHNICIANS.get(notification.technician_id)
    if not technician:
        raise HTTPException(status_code=404, detail="Technician not found")
    
    results = []
    
    for channel in notification.channels:
        if channel == 'email':
            result = await send_email_notification(
                technician['email'],
                notification.work_order_id,
                notification.equipment_info,
                notification.priority
            )
            results.append({"channel": "email", "status": result})
        
        elif channel == 'sms':
            result = await send_sms_notification(
                technician['mobile'],
                notification.work_order_id,
                notification.equipment_info
            )
            results.append({"channel": "sms", "status": result})
        
        elif channel == 'push':
            result = await send_push_notification(
                technician['push_token'],
                notification.work_order_id,
                notification.equipment_info
            )
            results.append({"channel": "push", "status": result})
    
    return {"results": results}

@app.get("/api/work-orders")
async def get_work_orders(status: Optional[str] = None, technician_id: Optional[str] = None):
    """Get work orders with optional filtering"""
    
    conn = sqlite3.connect('maintenance_system.db')
    
    query = "SELECT * FROM work_orders WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    if technician_id:
        query += " AND technician_id = ?"
        params.append(technician_id)
    
    query += " ORDER BY created_at DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df.to_dict('records')

@app.put("/api/work-orders/{work_order_id}/status")
async def update_work_order_status(work_order_id: str, status: str):
    """Update work order status"""
    
    conn = sqlite3.connect('maintenance_system.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE work_orders SET status = ? WHERE id = ?",
        (status, work_order_id)
    )
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Work order not found")
    
    conn.commit()
    conn.close()
    
    return {"work_order_id": work_order_id, "status": status}

@app.post("/api/equipment/update")
async def update_equipment_status(equipment: EquipmentUpdate):
    """Update equipment status from dashboard predictions"""
    
    conn = sqlite3.connect('maintenance_system.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO equipment_status 
    (equipment_id, failure_probability, health_score, risk_level, last_updated, 
     temperature, vibration, pressure)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        equipment.equipment_id,
        equipment.failure_probability,
        equipment.health_score,
        equipment.risk_level,
        datetime.now(),
        equipment.temperature,
        equipment.vibration,
        equipment.pressure
    ))
    
    conn.commit()
    conn.close()
    
    # Check if alert threshold is exceeded
    if equipment.failure_probability > 0.7:  # Critical threshold
        return {
            "status": "updated",
            "alert": True,
            "message": f"Critical alert: {equipment.equipment_id} exceeds failure threshold"
        }
    
    return {"status": "updated", "alert": False}

@app.get("/api/dashboard/alerts")
async def get_dashboard_alerts():
    """Get current dashboard alerts"""
    
    conn = sqlite3.connect('maintenance_system.db')
    
    # Get equipment with high failure probability
    df = pd.read_sql_query('''
    SELECT * FROM equipment_status 
    WHERE failure_probability > 0.4 
    ORDER BY failure_probability DESC
    ''', conn)
    
    conn.close()
    
    alerts = []
    for _, row in df.iterrows():
        if row['failure_probability'] > 0.7:
            severity = 'critical'
            message = f"CRITICAL: {row['equipment_id']} requires immediate attention"
        elif row['failure_probability'] > 0.5:
            severity = 'high'
            message = f"HIGH: {row['equipment_id']} needs maintenance soon"
        else:
            severity = 'medium'
            message = f"MEDIUM: {row['equipment_id']} for preventive maintenance"
        
        alerts.append({
            'equipment_id': row['equipment_id'],
            'severity': severity,
            'message': message,
            'failure_probability': row['failure_probability'],
            'health_score': row['health_score'],
            'last_updated': row['last_updated']
        })
    
    return alerts

@app.get("/api/technicians")
async def get_technicians():
    """Get available technicians"""
    return TECHNICIANS

@app.get("/api/notifications/history")
async def get_notification_history():
    """Get notification history"""
    
    conn = sqlite3.connect('maintenance_system.db')
    df = pd.read_sql_query('''
    SELECT n.*, w.equipment_id, w.priority 
    FROM notifications n
    LEFT JOIN work_orders w ON n.work_order_id = w.id
    ORDER BY n.sent_at DESC
    LIMIT 100
    ''', conn)
    conn.close()
    
    return df.to_dict('records')

# WebSocket for real-time updates
@app.websocket("/ws/alerts")
async def websocket_alerts(websocket):
    """WebSocket endpoint for real-time alerts"""
    await websocket.accept()
    
    try:
        while True:
            # Check for new alerts every 30 seconds
            await asyncio.sleep(30)
            
            alerts = await get_dashboard_alerts()
            await websocket.send_json({
                "type": "alerts_update",
                "data": alerts,
                "timestamp": datetime.now().isoformat()
            })
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()

# Background task functions
async def send_notifications(work_order_id: str, technician_id: str, priority: str, equipment_id: str):
    """Background task to send notifications"""
    
    technician = TECHNICIANS.get(technician_id)
    if not technician:
        return
    
    equipment_info = {
        "equipment_id": equipment_id,
        "priority": priority
    }
    
    # Send email
    await send_email_notification(
        technician['email'],
        work_order_id,
        equipment_info,
        priority
    )
    
    # Send SMS for high priority
    if priority in ['Critical', 'High']:
        await send_sms_notification(
            technician['mobile'],
            work_order_id,
            equipment_info
        )
    
    # Send push notification
    await send_push_notification(
        technician['push_token'],
        work_order_id,
        equipment_info
    )

async def send_email_notification(email: str, work_order_id: str, equipment_info: Dict, priority: str):
    """Send email notification"""
    try:
        # Configure your SMTP settings
        smtp_server = "smtp.company.com"
        smtp_port = 587
        smtp_user = "maintenance@company.com"
        smtp_password = "your_password"
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = email
        msg['Subject'] = f"🔧 New Maintenance Assignment - Work Order {work_order_id}"
        
        body = f"""
        New maintenance task assigned:
        
        Work Order ID: {work_order_id}
        Equipment: {equipment_info.get('equipment_id', 'Unknown')}
        Priority: {priority}
        
        Please log into the system for full details.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Uncomment to actually send emails
        # server = smtplib.SMTP(smtp_server, smtp_port)
        # server.starttls()
        # server.login(smtp_user, smtp_password)
        # server.send_message(msg)
        # server.quit()
        
        # Log notification
        log_notification(work_order_id, email, 'email', body, 'sent')
        
        return "sent"
    except Exception as e:
        print(f"Email error: {e}")
        return "failed"

async def send_sms_notification(phone: str, work_order_id: str, equipment_info: Dict):
    """Send SMS notification"""
    try:
        # Using Twilio example - configure with your credentials
        # from twilio.rest import Client
        
        message = f"🔧 MAINTENANCE ALERT\nWO: {work_order_id}\nEquipment: {equipment_info.get('equipment_id', 'Unknown')}\nCheck system for details."
        
        # Uncomment to actually send SMS
        # client = Client('your_account_sid', 'your_auth_token')
        # client.messages.create(
        #     body=message,
        #     from_='+1234567890',
        #     to=phone
        # )
        
        # Log notification
        log_notification(work_order_id, phone, 'sms', message, 'sent')
        
        return "sent"
    except Exception as e:
        print(f"SMS error: {e}")
        return "failed"

async def send_push_notification(push_token: str, work_order_id: str, equipment_info: Dict):
    """Send push notification"""
    try:
        # Using Firebase FCM example
        fcm_url = "https://fcm.googleapis.com/fcm/send"
        
        payload = {
            "to": push_token,
            "notification": {
                "title": f"New Work Order: {work_order_id}",
                "body": f"Maintenance needed for {equipment_info.get('equipment_id', 'equipment')}",
                "click_action": "FLUTTER_NOTIFICATION_CLICK"
            },
            "data": {
                "work_order_id": work_order_id,
                "equipment_id": equipment_info.get('equipment_id', ''),
                "type": "maintenance_assignment"
            }
        }
        
        headers = {
            "Authorization": "key=YOUR_SERVER_KEY",
            "Content-Type": "application/json"
        }
        
        # Uncomment to actually send push notifications
        # response = requests.post(fcm_url, json=payload, headers=headers)
        
        # Log notification
        log_notification(work_order_id, push_token, 'push', str(payload), 'sent')
        
        return "sent"
    except Exception as e:
        print(f"Push notification error: {e}")
        return "failed"

def log_notification(work_order_id: str, recipient: str, channel: str, content: str, status: str):
    """Log notification to database"""
    conn = sqlite3.connect('maintenance_system.db')
    cursor = conn.cursor()
    
    notification_id = f"NOTIF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(recipient) % 1000:03d}"
    
    cursor.execute('''
    INSERT INTO notifications 
    (id, work_order_id, recipient, channel, content, status, sent_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        notification_id,
        work_order_id,
        recipient,
        channel,
        content,
        status,
        datetime.now()
    ))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)