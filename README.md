# Preventive Maintenance(PM) System 🛠️✅  
**Preventive Maintenance Attendance & Accountability System**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web%20App-black?logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-blue?logo=sqlite&logoColor=white)
![Status](https://img.shields.io/badge/Status-Work%20in%20Progress-yellow)

PM_System is a lightweight **Preventive Maintenance tracking system** designed for real shopfloor execution.  
It works like an **attendance sheet**: planned weekly PM workload is tracked as **DONE / MISSED**, with full traceable history and export-ready records.

This project is a major upgrade from an earlier **trolley-only maintenance tool** built using Streamlit, which was form-heavy and difficult to maintain at scale. PM_System expands coverage to **machines, fixtures, nut runners, and trolleys**, while keeping weekly entry fast and usable.

---

## ✨ Core Philosophy
✅ Attendance-style weekly PM tracking (bulk-first)  
✅ Rotation-based planning (not date-heavy scheduling)  
✅ No task explosion / no CMMS complexity  
✅ Missed PM visibility + audit-ready history  
✅ Simple local deployment (single Windows PC + SQLite)

---

## 🚀 Key Features

### 🔐 Authentication (Static Login)
- Simple role-ready session login  
- Locked for local deployment (single PC)

### 🧾 Asset Master (Single Source of Truth)
- Manage assets with:
  - Asset ID (unique)
  - Asset Name
  - Asset Type (Machine / Fixture / Nut Runner / Trolley)
  - Rotation Slot
  - Status (Active/Scrapped)
- Clean modern UI
- Scales to large asset lists 

### 📅 Weekly PM Attendance Grid (Fast Entry)
- Weekly planned list auto-generated from rotation grouping
- Binary marking:
  - ✅ DONE
  - ❌ MISSED
- Bulk actions:
  - Mark all DONE
  - Reset all
- Explicit Save (no auto-save)
- Print-friendly view for paper-first workflows

### 🧩 PM Findings (Day-to-Day Maintenance Signals)
Track small routine maintenance actions without form overload:
- Dust cleaned
- Tightening done
- Sensor cleaned
- Torque adjusted
- Lubrication done
- etc.

✅ Findings are linked to weekly PM and shown as count per asset (with tooltip summary).

### 🧾 History (Immutable / Audit-Friendly)
- Read-only History pages (append-only log model)
- Separate tabs:
  - Attendance History
  - Findings History
  - Events History
- Filters + Export to CSV

### 🧰 Event Logging (Breakdown / Repair / Modification)
Log real incidents when required:
- Breakdown / Repair / Modification / Other
- Description
- Cost (optional)
- Name / Reference (optional)

---

## 🧠 Why This Exists (Problem Solved)
Typical CMMS tools fail on the shopfloor due to:
- Too much data entry
- Too many micro tasks
- Low adoption by technicians
- History gets messy when missed PM is carried forward

PM_System is designed to be:
- **fast to update**
- **easy to audit**
- **hard to fake**
- **useful for real weekly operations**

---

## 🖥️ Tech Stack
- **Backend:** Python + Flask
- **Frontend:** Jinja (server-rendered HTML)
- **Database:** SQLite
- **Styling:** Custom CSS (modern card + pill UI)
- **Deployment:** Local PC (no server required)

---

## ⚙️ Setup & Run (Local)

### 1) Create virtual environment
```bash
python -m venv venv
