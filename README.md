# Customer Care Call Center System

A web-based Customer Care Call Center application built using Python and Flask. The system helps customer-care teams manage incoming customer complaints, track call status, and transfer unresolved issues from Junior Executives to Senior Executives.

## Features

- **Login System:** Separate login access for Junior and Senior Executives.
- **Junior Dashboard:** View and manage customer calls.
- **Receive Calls:** Move waiting calls into progress.
- **Resolve Calls:** Mark customer issues as resolved.
- **Transfer to Senior:** Escalate calls that require senior-level support.
- **Senior Dashboard:** View escalated calls and resolve customer issues.
- **Add New Calls:** Record customer details and complaints.
- **Call History & Search:** Find calls using customer information or Call ID.
- **Role-Based Access:** Restrict dashboard actions according to user role.
- **SQLite Database:** Store customer calls and user account information.

## Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- Werkzeug
- Git and GitHub

## Project Structure

```text
Customer-Care-Call-Center/
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

The SQLite database is created locally by the application and is excluded from the public Git repository.

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/Aks870/Customer-Care-Call-Center.git
cd Customer-Care-Call-Center
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the application

```bash
python app.py
```

### 4. Open the application

Visit the following address in your browser:

```text
http://127.0.0.1:5000
```

## Security Note

Before deploying publicly, configure a secure secret key using an environment variable, protect user credentials, and configure persistent database storage for the hosting environment. Do not publish real passwords, secret keys, or private customer information.

## Project Purpose

This project demonstrates a customer-care workflow with authentication, call management, role-based access, complaint escalation, and database integration. It is a learning project that can be extended for more advanced customer-support workflows.

## Author

**Ankit Singh**

GitHub: [@Aks870](https://github.com/Aks870)
