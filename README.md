# 📦 StockSense — Inventory Management System

**StockSense** is a modular Inventory Management System designed to digitize and streamline stock-related operations within a business.

It replaces manual registers, Excel sheets, and scattered inventory tracking with a **centralized, real-time, easy-to-use web application**.

## 🚀 Overview

StockSense provides a unified platform for managing inventory operations such as:

* 📦 Inventory management
* 📥 Incoming stock
* 📤 Outgoing stock
* 🔄 Stock transfers
* 🏭 Warehouse operations
* 📊 Inventory tracking
* 🔐 User authentication
* 👥 Role-based access
* 📈 Dashboard and analytics

The system is designed with separate modules so that additional inventory features can be integrated easily as the application grows.

---

## 🎯 Target Users

### 👨‍💼 Inventory Managers

* Monitor stock levels
* Manage incoming and outgoing inventory
* Track inventory movements
* View stock information

### 👷 Warehouse Staff

* Perform stock transfers
* Handle picking and shelving
* Update stock quantities
* Perform inventory counting

---

## ✨ Key Features

### 🔐 Authentication

* User registration and login
* Secure authentication
* Password reset workflow
* OTP-based password recovery
* Role-based access

### 📊 Inventory Dashboard

* Centralized inventory overview
* Stock status monitoring
* Quick access to inventory operations
* Real-time operational information

### 📦 Stock Management

* Add and manage inventory
* Track incoming stock
* Track outgoing stock
* Monitor stock quantities
* Maintain inventory records

### 🔄 Warehouse Operations

* Stock transfers
* Picking operations
* Shelving
* Inventory counting

### 🧩 Modular Architecture

The application is structured into independent modules, making it easier to:

* Add new features
* Maintain existing functionality
* Scale the application
* Connect additional services and APIs

---

## 🛠️ Technologies Used

### Frontend

* React
* Vite
* JavaScript / JSX
* CSS
* ESLint

### Backend

* Python
* Flask
* REST APIs

### Development Tools

* Visual Studio Code
* Git
* GitHub
* npm
* Python Virtual Environment

---

## 📁 Project Structure

```text
StockSense/
│
├── stocksense-backend/
│   ├── app/
│   ├── .venv/
│   └── ...
│
├── stocksense-react/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── README.md
│
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/geethanvithakollipara/StockSense.git
```

```bash
cd StockSense
```

---

## 🎨 Frontend Setup

Navigate to the React application:

```bash
cd stocksense-react
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend will be available at the local Vite development URL shown in the terminal.

---

## 🐍 Backend Setup

Navigate to the backend:

```bash
cd ../stocksense-backend
```

Create/activate the Python virtual environment if required.

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Set the Flask secret key:

```powershell
$env:SECRET_KEY="stocksense-hackathon-secret"
```

Start the backend server using the project's configured Flask entry point.

---

## 🔗 API Health Check

StockSense includes a backend health endpoint:

```text
/api/health
```

This can be used to verify that the Flask backend is running correctly.

---

## 🔄 Application Flow

```text
User
  │
  ▼
Authentication
  │
  ▼
Dashboard
  │
  ├── Inventory Management
  │
  ├── Incoming Stock
  │
  ├── Outgoing Stock
  │
  ├── Stock Transfer
  │
  ├── Warehouse Operations
  │
  └── Inventory Tracking
           │
           ▼
       Backend APIs
           │
           ▼
        Database
```

---

## 🧠 Project Goals

StockSense focuses on solving common inventory-management problems:

* Manual inventory tracking
* Scattered stock records
* Lack of centralized information
* Difficult stock monitoring
* Inefficient warehouse operations
* Limited visibility into inventory movement

The goal is to provide a **single digital platform for efficient inventory operations**.

---

## 🔮 Future Enhancements

Planned improvements include:

* 📱 Responsive mobile interface
* 📊 Advanced inventory analytics
* 🔔 Low-stock notifications
* 📈 Inventory forecasting
* 📷 Barcode / QR-code scanning
* 🧾 Automated inventory reports
* 👥 Advanced role-based permissions
* ☁️ Cloud deployment
* 🔐 Enhanced security
* 📊 Business intelligence dashboards

---

## 👨‍💻 Development

StockSense is being developed as a modular full-stack application with a React-based frontend and Flask-based backend.

The project follows a Git-based development workflow to maintain and track changes throughout development.

---

## 📌 Project Status

**🚧 Currently in Development**

Core frontend and backend components are being developed and integrated.

---

## 📄 License

This project is currently intended for educational, development, and hackathon purposes.

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.
