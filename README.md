# TexKnit Stock Management Application

A premium, enterprise-grade desktop solution for managing textile and chemical inventory. Built with **Python** and **PySide6**, this application specializes in safety-first stock tracking, procurement, and professional billing.

---

## ✨ Key Features

### 🏢 **Advanced Inventory Management**
- **Chemical Safety**: Track Hazard Classes (Flammable, Toxic, etc.), Expiry Dates, and Storage Temperature ranges.
- **ABC Analysis**: Automated material classification (A, B, C) based on unit cost and stock value.
- **Real-Time Thresholds**: Instant "Low Stock" and "Expiry Impending" alerts on the Safety Intelligence Dashboard.

### 🧾 **Professional Invoicing**
- **Automated Workflows**: Generate professional invoices directly from Material Request Slips (MRS).
- **Auto-Population**: Selective customer lookup with auto-populating GSTIN and address details.
- **Stock Integration**: Invoicing a product automatically reduces the live inventory quantity.

### 📦 **Procurement & Supply Chain**
- **Purchase Indents**: Standardized PI system for store managers with Admin approval workflows.
- **Supplier Catalogs**: Manage products per vendor with rating-based performance tracking.
- **AI Procurement Assistant**: Smart recommendations for restocking based on consumption patterns.

### 🛡️ **Security & Auditing**
- **Role-Based Access**: Specialized interfaces for Admins, Supervisors, and Store Managers.
- **Audit Intelligence**: Comprehensive logs of every stock mutation, adjustment, and user login.
- **Data Safety**: Built-in automated database backup system.

---

## 🛠 Tech Stack

- **Core**: Python 3.x
- **UI Framework**: PySide6 (Qt)
- **Database**: Peewee ORM (SQLite / PostgreSQL)
- **Security**: Bcrypt password hashing
- **Visuals**: Matplotlib / QtCharts for analytics

---

## 🚀 Quick Start

### 1. Installation
Ensure you have Python installed, then install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configuration
The application supports both SQLite (standalone) and PostgreSQL (network). Edit `config.json`:
```json
{
  "db_type": "sqlite",
  "db_name": "stock_management.db"
}
```

### 3. Run Application
```bash
python main.py
```

- **Default Admin Login**: `admin` / `admin123`

---

## 📂 Documentation
- [Detailed Database Schema](DB_SCHEMA.md)
- [Project Architecture & Components](C:\Users\Nella\.gemini\antigravity\brain\30294b8b-4e37-4eb0-9dd7-21b4fd807c8a\project_analysis.md)

---

## 🎨 UI Aesthetics
- **Premium Design**: Dark-accented sidebar with a warm beige theme (`#F9F7F5`).
- **Modern Layouts**: Card-based interface with smooth hover transitions and high-legibility typography.
