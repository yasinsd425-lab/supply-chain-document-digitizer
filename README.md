# 🏭 SupplyChain Pro: Intelligent Invoice Digitization Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](YOUR_STREAMLIT_APP_URL)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![AI Engine](https://img.shields.io/badge/AI-Llama3.3%20via%20Groq-purple)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**SupplyChain Pro** is an enterprise-grade document processing application designed to automate the extraction of structured data from messy, unstructured supply chain invoices. 

Built with a **Hybrid AI Engine**, it seamlessly handles both digital PDFs (via direct parsing) and scanned images (via OCR), utilizing **Llama 3.3 (70B)** to map data into standardized financial formats.

---

## 🚀 Live Demo
**Try the deployed application here:** 👉 **[Launch SupplyChain Pro](https://supply-chain-document-digitizer-8jftgqtgdclovhplkinqwj.streamlit.app/)** *(Login Credentials: username=`admin`, password=`admin`)*

---

## 🌟 Key Features

### 🧠 Hybrid Extraction Engine
- **Smart Routing:** Automatically detects if a PDF is digital or scanned.
- **Speed:** Processes digital files in **<1 second** using direct text parsing.
- **Robustness:** Falls back to **EasyOCR** for scanned/noisy documents.

### 🛡️ Financial Integrity & Validation
- **Math Sanity Check:** Automatically validates line items (`Qty` × `Unit Price` = `Total`).
- **Audit Flags:** Highlights discrepancies with a ⚠️ warning tag for accountant review.
- **Currency Detection:** Identifies and normalizes currency symbols.

### 📊 Interactive Analytics Dashboard
- **Spend Analysis:** Visual breakdown of spending by Vendor and Date using Plotly charts.
- **Executive Metrics:** Real-time calculation of Total Spend, Top Suppliers, and Average Invoice Value.

### 📂 Enterprise Export
- **Multi-Sheet Excel:** Generates a professional `.xlsx` report with separate sheets for "Executive Summary" and "Line Item Details".
- **Editable Grids:** Allows users to manually correct AI-extracted data before export.

---

## 🛠️ Tech Stack

* **Frontend:** Streamlit (Custom CSS, Session State Management)
* **AI/LLM:** Groq API (Llama-3.3-70b-versatile)
* **OCR & Processing:** `EasyOCR`, `pdf2image`, `PyPDF`, `OpenCV`
* **Data Manipulation:** Pandas, NumPy
* **Visualization:** Plotly Express
* **Infrastructure:** Streamlit Cloud (Linux/Debian)

---

## ⚙️ Architecture Pipeline

```mermaid
graph LR
    A[User Uploads PDF] --> B{Is Digital?}
    B -- Yes --> C[Fast Text Parser]
    B -- No --> D[OCR / Computer Vision]
    C & D --> E[Raw Text]
    E --> F[Groq Llama 3.3 Engine]
    F --> G[JSON Structure Extraction]
    G --> H[Math Validation Layer]
    H --> I[Dashboard & Excel Export]
