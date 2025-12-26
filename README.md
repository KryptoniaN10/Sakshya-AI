# Sakshya AI - Minimal Viable Product (MVP)

**Sakshya AI** ("Evidence AI") is a legal decision-support tool designed to assist Indian judges and advocates in automating the process of witness confrontation under **Section 145 of the Bharatiya Sakshya Adhiniyam**.

It identifies **semantic contradictions** and **material omissions** between a witness's prior statement (e.g., FIR) and their later testimony (e.g., Court Deposition), focusing on the critical distinction between "Active Participation" and "Passive Presence".

## 🚀 Features

*   **Automated Confrontation**: Compares two witness statements to find discrepancies.
*   **Strict Legal Logic**:
    *   **Contradiction**: Active Assault vs. Passive Presence (Critical).
    *   **Omission**: Silence on minor details (treated cautiously for FIRs).
*   **3-Level Severity System**:
    *   🔴 **Critical**: Identity mismatch, Presence denial, Core role change.
    *   🟠 **Material**: Weapon inconsistency, Timeline shifts.
    *   🟡 **Minor**: Small details, natural memory gaps.
*   **Judge-Friendly UI**: Clear table layout, legal footnotes, and severity badges.

## 🛠️ Tech Stack

*   **Backend**: Python, FastAPI
*   **Frontend**: React, Vite, TailwindCSS
*   **AI Engine**: Google Gemini API (`gemini-2.5-flash`)

## 📦 Installation & Setup

### Prerequisites
*   Node.js & npm
*   Python 3.10+
*   Google Gemini API Key

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

**Configuration**:
Create a `.env` file in the `backend/` directory:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

**Run Server**:
```bash
uvicorn main:app --reload --port 8009
```
*Backend runs on: http://127.0.0.1:8009*

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
*Frontend runs on: http://localhost:5174* (or similar port shown in terminal)

## 📝 Usage

1.  Open the Frontend in your browser.
2.  Paste the **Prior Statement** (e.g., FIR text) in the left box.
3.  Paste the **Later Statement** (e.g., Deposition text) in the right box.
4.  Click **"Analyze Statements"**.
5.  Review the **Confrontation Table** for identified contradictions and their legal severity.

## ⚠️ Legal Disclaimer

This tool is for **preliminary analysis only**. It does NOT constitute legal advice. The AI identifies semantic inconsistencies but does not assess the truthfulness of any statement. Advocates must verify all citations with original case records.
