import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import io

# --- PAGE CONFIG ---
st.set_page_config(page_title="Mareero System", page_icon="🏢", layout="wide")

# --- CSS: HIDE WATERMARKS & STYLE BUTTONS ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stStatusWidget"] {visibility: hidden;}
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
    }
    
    /* Make Delete Button Red */
    div[data-testid="stButton"] button {
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. SETUP DATABASE ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    SHEET_URL = st.secrets["gcp_sheet_url"] 
except Exception as e:
    st.error(f"⚠️ Error: {e}")
    st.stop()

# --- 2. REPORT ENGINES ---

def generate_excel(df):
    output = io.BytesIO()
    # Use OpenPyXL to fix column widths
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Warbixin')
        
        # FIX: Auto-adjust column width so dates don't show as #####
        worksheet = writer.sheets['Warbixin']
        for i, col in enumerate(df.columns):
            # Find the length of the longest item in the column
            max_len = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            ) + 2 
            col_letter = chr(65 + i)
            worksheet.column_dimensions[col_letter].width = max_len
            
    output.seek(0)
    return output

def generate_pdf(df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Colors
    primary_color = colors.HexColor("#8B0000")
    text_color = colors.HexColor("#2C3E50")
    
    # Header
    c.setFillColor(primary_color)
    c.rect(0, height-100, width, 100, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width/2, height-60, "MAREERO OPERATION REPORT")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height-80, f"Taariikhda: {datetime.now().strftime('%d %B %Y')}")

    # Summary
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height-140, "1. KOOBITAAN (SUMMARY):")
    
    # Somali Text
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.darkgrey)
    c.drawString(40, height-160, "Warbixinta guud ee maanta (Shaqooyinka, Maqan, Dalab Cusub).")
    
    # Metrics Calculation
    total = len(df)
    missing = len(df[df['Category'] == 'Maqan']) if not df.empty and 'Category' in df.columns else 0
    new_req = len(df[df['Category'] == 'Dalab Cusub']) if not df.empty and 'Category' in df.columns else 0
    
    # Summary Box
    c.setStrokeColor(colors.lightgrey)
    c.rect(40, height-250, 515, 60, fill=0)
    c.setFillColor(text_color)
    c.setFont("Helvetica", 12)
    c.drawString(60, height-210, f"Wadarta: {total}")
    c.drawString(240, height-210, f"Maqan: {missing}")
    c.drawString(420, height-210, f"Dalab Cusub: {new_req}")

    # Charts
    y_chart = height-300
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y_chart, "2. SHAXDA XOGTA (CHARTS):")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.darkgrey)
    c.drawString(40, y_chart-20, "Kala bixinta xogta ee Qeybaha (Categories) iyo Laamaha (Branches).")

    if not df.empty and 'Category' in df.columns and 'Branch' in df.columns:
        try:
            # Pie Chart
            fig1, ax1 = plt.subplots(figsize=(4, 3))
            df['Category'].value_counts().plot.pie(autopct='%1.0f%%', ax=ax1, colors=['#ff9999','#66b3ff','#99ff99'])
            ax1.set_ylabel('')
            ax1.set_title("Qeybaha", fontsize=10)
            img1 = io.BytesIO()
            plt.savefig(img1, format='png', bbox_inches='tight')
            plt.close(fig1)
            img1.seek(0)
            c.drawImage(ImageReader(img1), 40, y_chart-260, width=240, height=180)
            
            # Bar Chart
            fig2, ax2 = plt.subplots(figsize=(4, 3))
            df['Branch'].value_counts().plot(kind='bar', color='#8B0000', ax=ax2)
            ax2.set_title("Laamaha", fontsize=10)
            plt.xticks(rotation=45, ha='right')
            img2 = io.BytesIO()
            plt.savefig(img2, format='png', bbox_inches='tight')
            plt.close(fig2)
            img2.seek(0)
            c.drawImage(ImageReader(img2), 300, y_chart-260, width=240, height=180)
        except: pass

    # List
    y_list = y_chart - 290
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y_list, "3. ALAABTA (ITEMS LIST):")
    
    c.setFillColor(colors.lightgrey)
    c.rect(40, y_list-50, 515, 20, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y_list-45, "CATEGORY")
    c.drawString(150, y_list-45, "ITEM")
    c.drawString(300, y_list-45, "BRANCH")
    c.drawString(420, y_list-45, "NOTE")
    
    y_row = y_list - 70
    c.setFont("Helvetica", 10)
    
    if not df.empty:
        for _, row in df.head(15).iterrows():
            c.drawString(50, y_row, str(row.get('Category', ''))[:15])
            c.drawString(150, y_row, str(row.get('Item', ''))[:25])
            c.drawString(300, y_row, str(row.get('Branch', ''))[:20])
            c.drawString(420, y_row, str(row.get('Note', ''))[:20])
            c.line(40, y_row-5, 555, y_row-5)
            y_row -= 20
            if y_row < 50: c.showPage(); y_row = height-50

    c.save()
    buffer.seek(0)
    return buffer

# --- 3. APP UI ---
st.title("🏢 Mareero System")

tab_staff, tab_manager = st.tabs(["📝 Qeybta Shaqaalaha", "🔐 Maamulka"])

# --- STAFF TAB ---
with tab_staff:
    st.info("Fadlan halkan ku diiwaangeli warbixintaada maalinlaha ah.")
    with st.form("log_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            branch = st.selectbox("📍 Branch", ["Kaydka M.Hassan", "Branch 1", "Branch 3", "Branch 4", "Branch 5"])
            employee = st.text_input("👤 Magacaaga")
        with c2:
            cat_map = {"Alaab Maqan": "Maqan", "Dalab Sare": "Dalab Sare", "Dalab Cusub": "Dalab Cusub"}
            cat_key = st.selectbox("📂 Nooca", list(cat_map.keys()))
            item = st.text_input("📦 Magaca Alaabta")
        note = st.text_input("📝 Faahfaahin")
        
        if st.form_submit_button("🚀 Gudbi", use_container_width=True):
            if employee and item:
                try:
                    data = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
                    if data is None: data = pd.DataFrame()
                    data = data.dropna(how="all")
                    
                    new_row = pd.DataFrame([{
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Branch": branch, "Employee": employee,
                        "Category": cat_map[cat_key], "Item": item, "Note": note
                    }])
                    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=pd.concat([data, new_row], ignore_index=True))
                    st.cache_data.clear()
                    st.success("✅ Sent!")
                except Exception as e: st.error(f"Error: {e}")
            else: st.error("Fadlan buuxi Magaca iyo Alaabta")

# --- MANAGER TAB ---
with tab_manager:
    # Login Row
    c_pass, c_btn = st.columns([5, 1], vertical_alignment="bottom")
    with c_pass:
        password = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter Password...")
    with c_btn:
        login_click = st.button("➡️", help="Enter")

    if password == "mareero2025" or login_click:
        if password == "mareero2025":
            st.success("🔓 Soo dhawoow Maamule")
            try:
                df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0)
                if df is None: df = pd.DataFrame()
                df = df.dropna(how="all")
            except: df = pd.DataFrame()

            if not df.empty:
                # Safe Metric Calculation (Prevents Crash)
                count_missing = len(df[df['Category'] == 'Maqan']) if 'Category' in df.columns else 0
                count_new = len(df[df['Category'] == 'Dalab Cusub']) if 'Category' in df.columns else 0
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Wadarta", len(df))
                m2.metric("Maqan", count_missing)
                m3.metric("Dalab Cusub", count_new)
                
                st.divider()
                
                # Reports
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Download PDF", use_container_width=True):
                        st.download_button("📥 Save PDF", generate_pdf(df), "report.pdf", "application/pdf")
                with c2:
                    if st.button("Download Excel", use_container_width=True):
                        st.download_button("📥 Save Excel", generate_excel(df), "data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                st.divider()
                st.subheader("🛠️ Wax ka bedel / Tirtir")
                
                # Table
                df_edit = df.copy()
                df_edit.insert(0, "Select", False)
                edited = st.data_editor(
                    df_edit,
                    num_rows="fixed",
                    hide_index=True,
                    use_container_width=True,
                    column_config={"Select": st.column_config.CheckboxColumn("❌", width="small")}
                )
                
                # Action Buttons
                c_save, _, c_del = st.columns([3, 4, 1])
                with c_save:
                    if st.button("💾 Kaydi (Save)", use_container_width=True):
                        try:
                            final = edited.drop(columns=["Select"])
                            conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=final)
                            st.cache_data.clear()
                            st.success("Saved!")
                            st.rerun()
                        except Exception as e: st.error(e)
                with c_del:
                    if st.button("🗑️", type="primary", help="Delete"):
                        try:
                            final = edited[edited["Select"]==False].drop(columns=["Select"])
                            conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=final)
                            st.cache_data.clear()
                            st.success("Deleted!")
                            st.rerun()
                        except Exception as e: st.error(e)
            else: st.warning("No Data")
        else: st.error("Wrong Password")
