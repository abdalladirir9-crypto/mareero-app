import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import io

# --- PAGE CONFIG ---
st.set_page_config(page_title="Mareero Intelligence", page_icon="🏢", layout="wide")

# --- 1. SETUP DATABASE ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("⚠️ Database Error. Check internet or secrets.")
    st.stop()

# --- 2. REPORT GENERATOR ENGINE ---
def generate_pdf(df):
    """
    Creates a professional PDF report in memory.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # --- A. GENERATE CHARTS ---
    # Chart 1: Issues by Category
    fig1, ax1 = plt.subplots(figsize=(5, 4))
    if not df.empty:
        df['Category'].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax1, colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
    ax1.set_title("Report Distribution")
    ax1.set_ylabel('')
    
    img_data1 = io.BytesIO()
    plt.savefig(img_data1, format='png')
    img_data1.seek(0)
    
    # Chart 2: Activity by Branch
    fig2, ax2 = plt.subplots(figsize=(5, 4))
    if not df.empty:
        df['Branch'].value_counts().plot(kind='bar', color='#D32F2F', ax=ax2)
    ax2.set_title("Activity by Branch")
    
    img_data2 = io.BytesIO()
    plt.savefig(img_data2, format='png', bbox_inches='tight')
    img_data2.seek(0)

    # --- B. DRAW PDF ---
    # Header
    c.setFillColorRGB(0.8, 0.1, 0.1) # Red
    c.rect(0, height-100, width, 100, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1) # White
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height-60, "MAREERO INTELLIGENCE REPORT")
    c.setFont("Helvetica", 12)
    date_str = datetime.now().strftime('%d %B %Y')
    c.drawCentredString(width/2, height-80, f"Generated: {date_str}")

    # Executive Summary
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height-150, "EXECUTIVE SUMMARY:")
    
    c.setFont("Helvetica", 12)
    total_logs = len(df)
    missing_cnt = len(df[df['Category'].str.contains('Missing', na=False)]) if not df.empty else 0
    new_cnt = len(df[df['Category'].str.contains('New', na=False)]) if not df.empty else 0
    
    c.drawString(50, height-180, f"• Total Activity Logs: {total_logs}")
    c.drawString(50, height-200, f"• Critical Missing Items: {missing_cnt}")
    c.drawString(50, height-220, f"• New Business Opportunities: {new_cnt}")

    # Draw Charts
    try:
        c.drawImage(ImageReader(img_data1), 50, height-500, width=250, height=200)
        c.drawImage(ImageReader(img_data2), 300, height-500, width=250, height=200)
    except:
        c.drawString(50, height-400, "Not enough data for charts.")

    # Critical List
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height-550, "⚠️ TOP 10 CRITICAL ALERTS:")
    
    c.setFont("Helvetica", 10)
    y = height - 580
    
    if not df.empty:
        critical_df = df[df['Category'].isin(['Missing', 'High Demand'])].head(10)
        for index, row in critical_df.iterrows():
            text = f"• [{row['Category']}] {row['Item']} ({row['Branch']})"
            c.drawString(50, y, text)
            y -= 20
    
    c.save()
    buffer.seek(0)
    return buffer

# --- 3. THE APP UI ---
st.title("🏢 Mareero Operations")

# TABS
tab_staff, tab_manager = st.tabs(["📝 Staff Entry", "🔐 Manager HQ"])

# --- STAFF TAB ---
with tab_staff:
    st.info("Staff Area: Please report items below.")
    with st.form("log_form"):
        c1, c2 = st.columns(2)
        with c1:
            branch = st.selectbox("📍 Branch", ["Branch 1", "Branch 2", "Branch 3", "Branch 4", "Branch 5"])
            employee = st.text_input("👤 Your Name")
        with c2:
            category = st.selectbox("📂 Report Type", ["Missing", "High Demand", "New Request", "Damaged"])
            item = st.text_input("📦 Item Name")
        
        note = st.text_input("📝 Note / Qty")
        
        if st.form_submit_button("🚀 Submit to HQ"):
            if employee and item:
                # Load Data
                data = conn.read(worksheet="Sheet1", ttl=0)
                data = data.dropna(how="all")
                
                new_row = pd.DataFrame([{
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Branch": branch,
                    "Employee": employee,
                    "Category": category,
                    "Item": item,
                    "Note": note
                }])
                
                updated = pd.concat([data, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated)
                st.success("✅ Saved!")
            else:
                st.error("Name and Item required.")

# --- MANAGER TAB ---
with tab_manager:
    password = st.text_input("Enter Admin Password", type="password")
    
    if password == "mareero2025":
        st.success("🔓 Access Granted")
        
        # Load Data
        df = conn.read(worksheet="Sheet1", ttl=0)
        df = df.dropna(how="all")
        
        # 1. LIVE METRICS
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Logs", len(df))
        m2.metric("Missing Stock", len(df[df['Category'] == 'Missing']))
        m3.metric("New Requests", len(df[df['Category'] == 'New Request']))
        
        st.divider()
        
        # 2. PDF DOWNLOAD BUTTON
        col_btn, col_info = st.columns([1, 2])
        with col_btn:
            st.subheader("📄 Daily Report")
            if st.button("Generate PDF Report"):
                with st.spinner("Analyzing Data & Drawing Charts..."):
                    pdf_bytes = generate_pdf(df)
                    st.download_button(
                        label="📥 Download Now",
                        data=pdf_bytes,
                        file_name=f"Mareero_Report_{datetime.now().date()}.pdf",
                        mime="application/pdf"
                    )
        
        # 3. LIVE TABLE
        st.subheader("📋 Live Database")
        st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
        
    elif password:
        st.error("Wrong Password")