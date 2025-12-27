# Sakshya AI - Minimal Viable Product (MVP)

**Sakshya AI** ("Evidence AI") is a legal decision-support tool designed to assist Indian judges and advocates in automating the process of witness confrontation under **Section 145 of the Bharatiya Sakshya Adhiniyam**.

It identifies **semantic contradictions** and **material omissions** between a witness's prior statement (e.g., FIR) and their later testimony (e.g., Court Deposition), focusing on the critical distinction between "Active Participation" and "Passive Presence".

## 🚀 Features

*   **AI-Powered Consistency Check**: Detects contradictions, omissions, and exaggerations between FIRs, Section 161 statements, and Court Depositions.
*   **Legal Logic Safeguards**: Implements strict suppression rules (Actor Consistency, Action Compatibility) to minimize false positives.
*   **Multilingual Support 🇮🇳**: Auto-detects and analyzes statements in **Hindi, Malayalam, Tamil, Telugu, Kannada, and Bengali** (via English pivot translation).
*   **Document Upload & OCR 📄**: Supports **PDFs (Typed)** and **Images (Handwritten)** using Tesseract OCR.
*   **Smart Output**: Prioritizes findings (Critical vs Minor) and groups related omissions.
*   **Judge-Friendly UI**: Clear table layout, legal footnotes, and severity badges.

## 🛠️ Tech Stack

*   **Backend**: Python, FastAPI
*   **Frontend**: React, Vite, TailwindCSS
*   **AI Engine**: Google Gemini API (`gemini-2.0-flash`)
*   **OCR**: Tesseract, pdfplumber

## 📦 Installation & Setup

### Prerequisites
*   Node.js & npm
*   Python 3.10+
*   Google Gemini API Key
*   **Tesseract OCR** (Required for processing Image/Handwritten documents)

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
2.  **Upload Documents** (PDF/Image) OR Paste the **Prior Statement** (e.g., FIR text) in the left box.
3.  **Upload Documents** OR Paste the **Later Statement** (e.g., Deposition text) in the right box.
4.  Click **"Analyze Statements"**.
5.  Review the **Confrontation Table** for identified contradictions and their legal severity.

## ⚠️ Legal Disclaimer

This tool is for **preliminary analysis only**. It does NOT constitute legal advice. The AI identifies semantic inconsistencies but does not assess the truthfulness of any statement. Advocates must verify all citations with original case records.
