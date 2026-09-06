# 🌾 AgriGuard Pro - Complete Setup Guide

## 📁 Project Structure

```
agriguard_pro/
│
├── 📄 flask_backend.py              # Backend API server (with SQLite)
├── 📄 database.py                   # Database schema and helpers
├── 📄 dashboard.html                # Web interface
├── 📄 arduino_controller.ino        # Arduino code
├── 📄 requirements.txt              # Python dependencies
│
├── 📁 owner_faces/                  # Face samples (auto-created)
│   ├── john_farmer/
│   │   ├── sample_000.jpg
│   │   ├── sample_001.jpg
│   │   └── ...
│   └── mary_smith/
│       └── ...
│
├── 📁 detected_images/              # Detection screenshots (auto-created)
│   ├── person_20251011_143025.jpg
│   ├── bird_20251011_143126.jpg
│   └── ...
│
├── 📁 logs/                         # Legacy logs (auto-created)
│
└── 📊 agriguard.db                  # SQLite database (auto-created)
    ├── settings (table)
    ├── owners (table)
    ├── detections (table)
    ├── logs (table)
    ├── statistics (table)
    └── active_intrusions (table)
```

---

## ⚡ Quick Setup (5 Minutes)

### Step 1: Create Project Folder

```bash
# Create main directory
mkdir agriguard_pro
cd agriguard_pro
```

### Step 2: Create requirements.txt

```bash
# Create file
cat > requirements.txt << 'EOF'
flask>=2.3.0
flask-cors>=4.0.0
opencv-contrib-python>=4.8.0
ultralytics>=8.0.0
pyserial>=3.5
requests>=2.31.0
numpy>=1.24.0
torch>=2.0.0
torchvision>=0.15.0
EOF
```

**Or manually create `requirements.txt` with:**
```
flask>=2.3.0
flask-cors>=4.0.0
opencv-contrib-python>=4.8.0
ultralytics>=8.0.0
pyserial>=3.5
requests>=2.31.0
numpy>=1.24.0
torch>=2.0.0
torchvision>=0.15.0
```

### Step 3: Install Python Packages

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 4: Copy Project Files

Download and place these files in `agriguard_pro/` folder:

1. **`database.py`** - From artifacts (database schema)
2. **`flask_backend.py`** - From artifacts (updated with SQLite)
3. **`dashboard.html`** - From artifacts (web interface)
4. **`arduino_controller.ino`** - From artifacts (Arduino code)

### Step 5: Initialize Database

```bash
# Initialize SQLite database
python database.py
```

**Expected output:**
```
Initializing database...
✓ Database initialized successfully
Database ready!
```

### Step 6: Upload Arduino Code

1. Open **Arduino IDE**
2. File → Open → `arduino_controller.ino`
3. Tools → Board → Select your Arduino (Uno/Mega)
4. Tools → Port → Select COM port
5. Upload button (→)
6. Wait for "Done uploading"

### Step 7: Start Backend Server

```bash
python flask_backend.py
```

**Expected output:**
```
============================================================
🌾 AgriGuard Pro - Backend API Server with SQLite
============================================================

✓ Database connected
✓ Server starting on http://localhost:5000
✓ API endpoints ready
✓ CORS enabled for frontend
✓ Face recognition initialized
Loaded 0 registered owners

 * Running on http://0.0.0.0:5000
Press Ctrl+C to stop
```

### Step 8: Start Frontend (New Terminal)

```bash
# Open new terminal, activate venv again
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Start HTTP server
python -m http.server 8000
```

**Expected output:**
```
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
```

### Step 9: Open Dashboard

Open browser and go to:
```
http://localhost:8000/dashboard.html
```

---

## 🎮 First-Time Usage

### 1. Configure Telegram (Optional)

**Dashboard → Settings Tab:**

1. **Get Bot Token:**
   - Open Telegram → Search `@BotFather`
   - Send: `/newbot`
   - Follow instructions
   - Copy bot token

2. **Get Chat ID:**
   - Search `@userinfobot`
   - Start chat
   - Copy your chat ID

3. **Enter in Dashboard:**
   - Paste Bot Token
   - Paste Chat ID
   - Click "Save Settings"
   - Click "Test Telegram"

### 2. Register Owner Face

**Dashboard → Owners Tab:**

1. Enter your name (e.g., "John Farmer")
2. Click **"Start Camera"** → Allow camera access
3. Click **"Start Face Capture"**
4. Look at camera, slowly move head around
5. Wait for 50 samples (progress bar)
6. Auto-trains when complete
7. Test by clicking **"Test Face Recognition"**

### 3. Start Surveillance

**Dashboard → Top Right:**

1. Click **"Start System"** button
2. Wait 3-5 seconds for initialization
3. Status changes to **"ACTIVE"** (green)
4. Go to **"Live Feed"** tab to see camera
5. Walk in front of camera to test

---

## 📊 Database Features

### What's Stored in Database:

✅ **Settings** - All configuration (persists across restarts)
✅ **Owners** - Face recognition data  
✅ **Detections** - Complete history with images
✅ **Logs** - System events (last 1000)
✅ **Statistics** - Detection counts
✅ **Active Intrusions** - Current tracking state

### Advantages:

- 🔄 **No data loss** on page refresh
- 📊 **Persistent statistics** across sessions
- 🗄️ **Complete audit trail** forever
- 🔍 **Queryable history** (SQL)
- 💾 **Single file backup** (agriguard.db)

### Database Commands:

```bash
# View database
sqlite3 agriguard.db

# Inside SQLite:
.tables                    # List all tables
SELECT * FROM owners;      # View owners
SELECT * FROM detections LIMIT 10;  # Recent detections
SELECT * FROM settings;    # Current settings
.exit                      # Exit SQLite
```

---

## 🔧 Configuration

### Hardware Settings (Settings Tab):

- **Arduino Port**: COM3 (Windows) or /dev/ttyUSB0 (Linux)
- **Camera Index**: 0 (default), 1 (external USB camera)

### Detection Settings (Settings Tab):

- **Confidence Threshold**: 0.3-0.9 (default: 0.5)
- **Arduino Action Cooldown**: 1-10s (default: 3s)
- **Intrusion Timeout**: 5-30s (default: 10s)
- **Face Threshold**: 50-100 (default: 70)

### Telegram Settings (Settings Tab):

- **Bot Token**: From @BotFather
- **Chat ID**: From @userinfobot
- **Telegram Alerts**: Toggle ON/OFF
- **Face Recognition**: Toggle ON/OFF

---

## 🧪 Testing

### Test 1: Hardware

**Dashboard → Quick Actions:**
- Click "Test Motor" → Should rotate
- Click "Test Buzzer" → Should sound
- Click "Test Lights" → Should turn on
- Click "Test Telegram" → Check phone

### Test 2: Face Recognition

**Dashboard → Owners Tab:**
- Click "Test Face Recognition"
- Look at camera
- Should show "OWNER RECOGNIZED" (green)

### Test 3: Detection

1. Start system
2. Walk in front of camera
3. If owner: NO alert (just logged)
4. Ask friend: Alert + lights

---

## 📱 Access from Other Devices

### Same Network:

1. Find your computer's IP:
```bash
# Windows:
ipconfig
# Look for IPv4 Address: 192.168.1.XXX

# Linux/Mac:
ifconfig | grep inet
# or
hostname -I
```

2. On phone/tablet, open:
```
http://192.168.1.XXX:8000/dashboard.html
```

### Remote Access (ngrok):

```bash
# Install ngrok from ngrok.com
# Then run:
ngrok http 5000

# You get URL like: https://abc123.ngrok.io
# Update API_URL in dashboard.html
# Access from anywhere
```

---

## 🔄 Daily Operations

### Morning Startup:

```bash
# Terminal 1:
cd agriguard_pro
venv\Scripts\activate  # or source venv/bin/activate
python flask_backend.py

# Terminal 2:
cd agriguard_pro
venv\Scripts\activate
python -m http.server 8000
```

### Check Status:

- Open `http://localhost:8000/dashboard.html`
- View statistics on Dashboard tab
- Check logs in Logs tab
- Review detections in Detections tab

### Evening Shutdown:

- Click "Stop System"
- Press Ctrl+C in both terminals
- Data is safe in database!

---

## 💾 Backup & Restore

### Backup Everything:

```bash
# Backup database
cp agriguard.db agriguard_backup_$(date +%Y%m%d).db

# Backup face data
tar -czf owner_faces_backup.tar.gz owner_faces/

# Backup detected images
tar -czf detected_images_backup.tar.gz detected_images/
```

### Restore from Backup:

```bash
# Restore database
cp agriguard_backup_20251011.db agriguard.db

# Restore face data
tar -xzf owner_faces_backup.tar.gz

# Restore images
tar -xzf detected_images_backup.tar.gz
```

### Export Data:

**From Dashboard:**
- Detections Tab → "Export CSV" button

**From Command Line:**
```bash
sqlite3 agriguard.db

.mode csv
.output detections_export.csv
SELECT * FROM detections;
.output stdout
.exit
```

---

## 🐛 Troubleshooting

### Database Issues:

**Error: "database is locked"**
```bash
# Stop all Python processes
# Delete lock file if exists
rm agriguard.db-journal

# Restart backend
```

**Error: "no such table"**
```bash
# Reinitialize database
python database.py
```

**Corrupt database:**
```bash
# Backup first
cp agriguard.db agriguard_corrupt.db

# Try recovery
sqlite3 agriguard.db ".recover" > recovered.sql
sqlite3 agriguard_new.db < recovered.sql
mv agriguard_new.db agriguard.db

# Or start fresh
rm agriguard.db
python database.py
```

### Backend Won't Start:

```bash
# Check if port in use
# Windows:
netstat -ano | findstr :5000
# Kill process if found

# Linux/Mac:
lsof -i :5000
kill -9 <PID>
```

### Data Not Persisting:

```bash
# Check database file exists
ls -lh agriguard.db

# Check write permissions
# Linux/Mac:
chmod 664 agriguard.db

# Windows:
# Right-click → Properties → Security → Edit
```

---

## 🔐 Security

### Production Deployment:

1. **Change Default Ports:**
```python
# In flask_backend.py, line ~900:
app.run(host='0.0.0.0', port=8080)  # Change from 5000
```

2. **Add Authentication:**
```bash
pip install flask-httpauth

# Add to flask_backend.py:
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@auth.verify_password
def verify(username, password):
    return username == 'admin' and password == 'secure_password'

@app.route('/api/status')
@auth.login_required
def get_status():
    # your code
```

3. **Use HTTPS:**
```bash
# Generate certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Run with SSL
app.run(ssl_context=('cert.pem', 'key.pem'))
```

4. **Firewall Rules:**
```bash
# Linux:
sudo ufw allow 5000/tcp
sudo ufw allow from 192.168.1.0/24 to any port 5000

# Windows:
netsh advfirewall firewall add rule name="AgriGuard" dir=in action=allow protocol=TCP localport=5000
```

---

## 📈 Performance Optimization

### For Raspberry Pi:

```python
# Use smaller YOLO model
model = YOLO('yolov8n.pt')  # Nano - fastest

# Reduce frame rate
time.sleep(0.05)  # ~20 FPS instead of 30
```

### For Better Detection:

```python
# Use larger model (needs better hardware)
model = YOLO('yolov8m.pt')  # Medium - more accurate

# Adjust confidence
surveillance_state['settings']['confidenceThreshold'] = 0.6
```

### Database Maintenance:

```bash
# Vacuum database (compact)
sqlite3 agriguard.db "VACUUM;"

# Analyze for optimization
sqlite3 agriguard.db "ANALYZE;"

# Clean old logs (keeps last 1000)
python -c "from database import DB; DB.clear_logs()"
```

---

## 🔄 Auto-Start on Boot

### Windows (Task Scheduler):

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: "When computer starts"
4. Action: Start batch file
5. Create `start_agriguard.bat`:
```batch
@echo off
cd C:\path\to\agriguard_pro
call venv\Scripts\activate
start python flask_backend.py
start python -m http.server 8000
```

### Linux (systemd):

```bash
# Create service file
sudo nano /etc/systemd/system/agriguard.service

# Add:
[Unit]
Description=AgriGuard Pro Surveillance
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/agriguard_pro
Environment="PATH=/home/youruser/agriguard_pro/venv/bin"
ExecStart=/home/youruser/agriguard_pro/venv/bin/python flask_backend.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable
sudo systemctl enable agriguard
sudo systemctl start agriguard
```

### Raspberry Pi (cron):

```bash
crontab -e

# Add:
@reboot sleep 30 && cd /home/pi/agriguard_pro && /home/pi/agriguard_pro/venv/bin/python flask_backend.py &
```

---

## 📊 Database Schema Reference

### Tables:

**settings** - System configuration
- key (TEXT): Setting name
- value (TEXT): Setting value
- updated_at (TIMESTAMP)

**owners** - Registered owners
- id (TEXT): Owner identifier
- name (TEXT): Owner name
- samples (INTEGER): Number of face samples
- face_data (BLOB): Serialized recognizer
- created_at (TIMESTAMP)

**detections** - Detection history
- id (INTEGER): Auto-increment ID
- type (TEXT): Intruder type
- confidence (REAL): Detection confidence
- action (TEXT): Action taken
- image_path (TEXT): Photo filename
- owner_name (TEXT): If owner detected
- is_owner (BOOLEAN): Owner flag
- created_at (TIMESTAMP)

**logs** - System logs
- id (INTEGER): Auto-increment ID
- level (TEXT): info/warning/error/success
- message (TEXT): Log message
- created_at (TIMESTAMP)

**statistics** - Detection counts
- stat_key (TEXT): Statistic name
- stat_value (INTEGER): Count
- updated_at (TIMESTAMP)

**active_intrusions** - Current tracking
- intrusion_type (TEXT): Type of intruder
- last_seen (REAL): Unix timestamp
- telegram_sent (BOOLEAN): Alert sent flag
- last_action (REAL): Last Arduino action time

---

## ✅ Post-Setup Checklist

After setup, verify:

- [ ] Database initialized (`agriguard.db` exists)
- [ ] Backend starts without errors
- [ ] Frontend accessible in browser
- [ ] Arduino uploaded and connected
- [ ] At least one owner registered
- [ ] Face recognition tested
- [ ] Telegram configured and tested
- [ ] Hardware actions tested (motor, buzzer, lights)
- [ ] Detection system tested
- [ ] Data persists after refresh
- [ ] Statistics updating correctly

---

## 🎉 You're Ready!

Your AgriGuard Pro system is now:
- ✅ Fully functional with persistent storage
- ✅ Protected against data loss
- ✅ Ready for 24/7 operation
- ✅ Backing up to SQLite database
- ✅ Tracking everything permanently

**Start protecting your farm! 🚜🌾**

---

**Quick Commands Reference:**

```bash
# Start System
python flask_backend.py                    # Terminal 1
python -m http.server 8000                 # Terminal 2

# Access Dashboard
http://localhost:8000/dashboard.html

# Initialize/Reset Database
python database.py

# View Database
sqlite3 agriguard.db

# Backup
cp agriguard.db backup.db

# Check Logs
tail -f face_debug.log  # If enabled
```

---

**Need Help?** Check the detailed troubleshooting guides provided earlier!

**System Version:** 4.0 - SQLite Database Integration
**Database:** agriguard.db (SQLite3)
**Last Updated:** October 2025