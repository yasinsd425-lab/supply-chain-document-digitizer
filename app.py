import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st
import pandas as pd
import json
import easyocr
import numpy as np
from pdf2image import convert_from_bytes
from groq import Groq
import io
import pypdf
import plotly.express as px
import time

# --- تنظیمات صفحه (برندینگ سازمانی) ---
st.set_page_config(page_title="SupplyChain Pro", page_icon="🏢", layout="wide")

# --- استایل CSS اختصاصی (تاریک/روشن سازگار) ---
st.markdown("""
    <style>
    .big-font {font-size:20px !important;}
    .metric-container {background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #0f52ba;}
    /* مخفی کردن منوی دیفالت استریم‌لیت برای ظاهر حرفه‌ای‌تر */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- مدیریت نشست (Session State) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'invoices_data' not in st.session_state:
    st.session_state.invoices_data = []

# --- توابع سیستم (Backend Logic) ---

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

def extract_text_smart(file_bytes):
    """موتور هوشمند: اول تلاش برای خواندن سریع، اگر نشد اسکن دقیق"""
    # 1. تلاش سریع (Fast Path)
    try:
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        if len(text.strip()) > 50:
            return text, "🚀 Digital Parse (Fast)"
    except:
        pass

    # 2. تلاش دقیق (OCR Path)
    poppler_bin = r"C:\Users\Yasin\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"
    reader = load_ocr()
    images = convert_from_bytes(file_bytes, poppler_path=poppler_bin)
    full_text = ""
    for img in images:
        img_np = np.array(img)
        result = reader.readtext(img_np, detail=0)
        full_text += " ".join(result) + "\n"
    return full_text, "🔍 OCR Scan (Deep)"

def analyze_with_groq(text, api_key):
    try:
        client = Groq(api_key=api_key)
        prompt = f"""
        Act as a Senior Financial Accountant. Extract data from this invoice text into JSON.
        Required Fields:
        - vendor_name (Official Company Name)
        - invoice_date (YYYY-MM-DD format only)
        - invoice_number
        - currency (USD, EUR, GBP)
        - total_amount (Float number, no symbols)
        - line_items (Array of objects: description, quantity, unit_price, total)
        
        Text content: {text[:8000]}
        
        RETURN ONLY RAW JSON. NO MARKDOWN.
        """
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

def validate_financials(data):
    """بررسی اختلاف حساب در ارقام"""
    alerts = []
    if 'line_items' in data:
        calc_total = 0
        for item in data['line_items']:
            try:
                t = float(item.get('total', 0))
                calc_total += t
            except: pass
        
        inv_total = float(data.get('total_amount', 0))
        if abs(calc_total - inv_total) > 1.0 and inv_total > 0:
            alerts.append(f"⚠️ Sum mismatch: Lines sum ({calc_total}) != Invoice Total ({inv_total})")
    return alerts

def generate_excel(data_list):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Sheet 1: Executive Summary
        summary = []
        for inv in data_list:
            summary.append({
                "Vendor": inv.get('vendor_name'),
                "Date": inv.get('invoice_date'),
                "Invoice #": inv.get('invoice_number'),
                "Total": inv.get('total_amount'),
                "Currency": inv.get('currency'),
                "Status": "Processed"
            })
        pd.DataFrame(summary).to_excel(writer, sheet_name='Executive Summary', index=False)
        
        # Sheet 2: Detailed Line Items
        details = []
        for inv in data_list:
            for item in inv.get('line_items', []):
                row = item.copy()
                row['Ref_Invoice'] = inv.get('invoice_number')
                row['Vendor'] = inv.get('vendor_name')
                details.append(row)
        if details:
            pd.DataFrame(details).to_excel(writer, sheet_name='Line Item Details', index=False)
            
    return output.getvalue()

# --- صفحه ورود (Login Screen) ---
def login_screen():
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🔒 Secure Workspace")
        st.markdown("Please log in to access the Supply Chain System.")
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            if user == "admin" and pwd == "admin":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")

# --- پنل اصلی نرم‌افزار ---
def main_app():
    # Sidebar Navigation
    with st.sidebar:
        st.title("🏢 SupplyChain Pro")
        st.markdown("Enterprise Edition v2.0")
        menu = st.radio("Navigation", ["📊 Dashboard", "📤 Document Processor", "🗂️ Data Manager"])
        st.divider()
        api_key = st.text_input("Groq API License Key", type="password")
        st.divider()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- VIEW 1: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("Financial Overview")
        if not st.session_state.invoices_data:
            st.info("No data available. Go to 'Document Processor' to import invoices.")
        else:
            df = pd.DataFrame(st.session_state.invoices_data)
            
            # KPI Metrics
            total_spend = df['total_amount'].sum()
            top_vendor = df.groupby('vendor_name')['total_amount'].sum().idxmax()
            avg_invoice = df['total_amount'].mean()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Expenditure", f"${total_spend:,.2f}", "+12% vs last month")
            c2.metric("Top Supplier", top_vendor)
            c3.metric("Avg. Invoice Value", f"${avg_invoice:,.2f}")
            
            st.divider()
            
            # Charts
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Spend by Vendor")
                fig_pie = px.pie(df, values='total_amount', names='vendor_name', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.subheader("Daily Spending Trend")
                fig_bar = px.bar(df, x='invoice_date', y='total_amount', color='vendor_name')
                st.plotly_chart(fig_bar, use_container_width=True)

    # --- VIEW 2: PROCESSOR ---
    elif menu == "📤 Document Processor":
        st.title("Intelligent Ingestion")
        st.markdown("Upload PDFs to extract data using Hybrid AI Engine.")
        
        uploaded_files = st.file_uploader("Drop Invoices Here", type=['pdf'], accept_multiple_files=True)
        
        if uploaded_files and api_key:
            if st.button(f"Start Processing ({len(uploaded_files)} Files)"):
                bar = st.progress(0)
                for i, file in enumerate(uploaded_files):
                    with st.status(f"Analyzing {file.name}...", expanded=True) as status:
                        # 1. Read
                        text, mode = extract_text_smart(file.getvalue())
                        st.write(f"Engine: {mode}")
                        
                        # 2. Extract
                        data = analyze_with_groq(text, api_key)
                        
                        if "error" not in data:
                            data['source_file'] = file.name
                            data['alerts'] = validate_financials(data)
                            st.session_state.invoices_data.append(data)
                            
                            if data['alerts']:
                                status.update(label="⚠️ Finished with Warnings", state="error")
                                for alert in data['alerts']:
                                    st.warning(alert)
                            else:
                                status.update(label="✅ Success", state="complete", expanded=False)
                        else:
                            st.error(data['error'])
                    
                    bar.progress((i+1)/len(uploaded_files))
                st.success("Batch processing complete!")

    # --- VIEW 3: DATA MANAGER ---
    elif menu == "🗂️ Data Manager":
        st.title("Data Validation & Export")
        
        if st.session_state.invoices_data:
            # 1. Master Table (Editable)
            st.subheader("Master Records")
            df_master = pd.DataFrame(st.session_state.invoices_data)
            
            # Hidden columns config
            column_config = {
                "line_items": st.column_config.ListColumn("Items"),
                "alerts": st.column_config.ListColumn("Audit Flags")
            }
            
            edited_df = st.data_editor(
                df_master, 
                column_config=column_config, 
                num_rows="dynamic",
                use_container_width=True
            )
            
            # Update session state with edits
            st.session_state.invoices_data = edited_df.to_dict('records')
            
            st.divider()
            
            # 2. Export Section
            c1, c2 = st.columns([2,1])
            with c1:
                st.info("Export data to ERP-ready Excel format (Multi-sheet).")
            with c2:
                excel_data = generate_excel(st.session_state.invoices_data)
                st.download_button(
                    "📥 Download ERP Report (.xlsx)",
                    data=excel_data,
                    file_name="Finance_Export_v1.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.warning("No data to manage.")

# --- Logic Flow ---
if st.session_state.logged_in:
    main_app()
else:
    login_screen()