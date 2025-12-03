import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import io

# --- PAGE CONFIG ---
st.set_page_config(page_title="Mareero System", page_icon="🏢", layout="wide")

# --- 1. CSS: HIDE WATERMARKS & STYLE BUTTONS ---
st.markdown("""
<style>
    /* Hide Streamlit Logos */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stStatusWidget"] {visibility: hidden;}
    
    /* Adjust top padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
    }
    
    /* Make the Delete Icon Button Red and Round-ish */
    div[data-testid="stButton"] button {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    SHEET_URL = st.secrets["gcp_sheet_url"] 
except Exception as e:
    st.error(f"⚠️ Connection Error: {e}")
    st.stop()

# --- 3. REPORT FUNCTIONS ---
def generate_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Warbixin')
    output.seek(0)
    return output

def generate_pdf(df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFillColor(colors.HexColor("#8B0000"))
    c.rect(0, height-100, width, 100, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width/2, height-60, "MAREERO OPERATION REPORT")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height-80, f"Date: {datetime.now().strftime('%d %B %Y')}")
    
    # Simple Content for PDF
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    y = height - 150
    c.drawString(40, y, f"Total Records: {len(df)}")
    c.save()
    buffer.seek(0)
    return buffer

# --- 4. APP UI ---
st.title("🏢 Mareero Auto Spare Parts")

tab_staff, tab_manager = st.tabs(["📝 Staff Area", "🔐 Manager Area"])

# --- STAFF TAB ---
with tab_staff:
    st.info("Fadlan halkan ku diiwaangeli warbixintaada maalinlaha ah.")
    with st.form("log_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            branch = st.selectbox("📍 Branch", ["Kaydka M.Hassan", "Branch 1", "Branch 3", "Branch 4", "Branch 5"])
            employee = st.text_input("👤 Magacaaga")
        with c2:
            cat_map = {"Alaabta Maqan": "Maqan", "Dalab Sare": "Dalab Sare", "Dalab Cusub": "Dalab Cusub"}
            cat_key = st.selectbox("📂 Nooca", list(cat_map.keys()))
            item = st.text_input("📦 Magaca Alaabta")
        note = st.text_input("📝 Note / Qty")
        if st.form_submit_button("🚀 Submit", use_container_width=True):
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
                    st.success("Sent!")
                except Exception as e: st.error(f"Error: {e}")
            else: st.error("Fill Name & Item")

# --- MANAGER TAB ---
with tab_manager:
    # --- LOGIN ROW (Compact) ---
    # [5, 1] ratio keeps the button small and next to input
    # vertical_alignment="bottom" ensures they line up perfectly
    c_pass, c_btn = st.columns([5, 1], vertical_alignment="bottom")
    
    with c_pass:
        password = st.text_input("Password", type="password", placeholder="Enter Password...", label_visibility="collapsed")
    with c_btn:
        # Small Enter Icon
        login_click = st.button("➡️", help="Enter")

    # --- DASHBOARD ---
    if password == "mareero2025" or login_click:
        if password == "mareero2025":
            try:
                df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl=0) or pd.DataFrame()
                df = df.dropna(how="all")
            except: df = pd.DataFrame()

            if not df.empty:
                # Metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("Total", len(df))
                m2.metric("Missing", len(df[df['Category']=='Maqan']) if 'Category' in df.columns else 0)
                m3.metric("New Req", len(df[df['Category']=='Dalab Cusub']) if 'Category' in df.columns else 0)
                
                st.divider()
                
                # Reports
                c_pdf, c_xls = st.columns(2)
                with c_pdf:
                    if st.button("📄 PDF", use_container_width=True):
                        st.download_button("⬇️ PDF", generate_pdf(df), "report.pdf", "application/pdf")
                with c_xls:
                    if st.button("📊 Excel", use_container_width=True):
                        st.download_button("⬇️ Excel", generate_excel(df), "data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

                st.divider()
                st.write("### 🛠️ Edit / Delete")
                
                # Table with Checkbox
                df_edit = df.copy()
                df_edit.insert(0, "Select", False)
                
                edited = st.data_editor(
                    df_edit,
                    num_rows="fixed",
                    hide_index=True,
                    use_container_width=True,
                    column_config={"Select": st.column_config.CheckboxColumn("❌", width="small")}
                )

                st.write("")
                # --- ACTION BUTTONS ---
                # Save (Wide) --- Spacer --- Delete (Small Icon)
                c_save, c_mid, c_del = st.columns([3, 3, 1])
                
                with c_save:
                    if st.button("💾 Save Changes", use_container_width=True):
                        try:
                            final = edited.drop(columns=["Select"])
                            conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=final)
                            st.cache_data.clear()
                            st.success("Saved!")
                            st.rerun()
                        except Exception as e: st.error(e)
                
                with c_del:
                    # THE SMALL DELETE ICON
                    if st.button("🗑️", type="primary", help="Delete Selected Rows"):
                        try:
                            final = edited[edited["Select"]==False].drop(columns=["Select"])
                            conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=final)
                            st.cache_data.clear()
                            st.success("Deleted!")
                            st.rerun()
                        except Exception as e: st.error(e)
            else: st.warning("No Data")
        else: st.error("Wrong Password")
