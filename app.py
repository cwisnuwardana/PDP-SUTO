import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import io
import os

st.set_page_config(page_title="SUTO Catalog Configurator", layout="wide")

# =========================
# SENSOR
# =========================
def select_sensor(dp):
    if dp <= -80:
        return "S220"
    elif dp <= -40:
        return "S211"
    return "S215"

# =========================
# BASE PART
# =========================
def base_part(sensor, comm, pressure_sensor, wiring):
    code = {"S211":"11","S215":"15","S220":"20"}[sensor]

    if pressure_sensor == "Yes":
        series = "4"
    elif "Modbus" in comm:
        series = "3"
    elif wiring == "3-wire":
        series = "2"
    else:
        series = "1"

    return f"S699 {series}{code}"

# =========================
# OPTION
# =========================
def options(sensor, comm, display, pressure_bar):
    opt = []

    if display == "Yes":
        opt.append("A1388" if "Modbus" in comm else "A1387")

    if pressure_bar > 16 and sensor in ["S211","S215"]:
        opt.append("A1381")

    return opt

# =========================
# ORDER STRING
# =========================
def order_string(base, opt):
    if not opt:
        return base
    return f"{base} + " + " + ".join(opt)

# =========================
# WIRING
# =========================
def wiring(comm, display, pressure):
    if comm == "4-20 mA Only" and display == "No" and pressure == "No":
        return "2-wire"
    return "3-wire"

# =========================
# CHAMBER
# =========================
def chamber(flow_ctrl, dp):
    if flow_ctrl == "No":
        return "A699 3491"
    elif dp == "Yes":
        return "A699 3493"
    return "A554 2301"

# =========================
# DATASHEET PATH
# =========================
def get_datasheet(sensor):
    path = f"datasheets/{sensor}.pdf"
    return path if os.path.exists(path) else None

# =========================
# PDF GENERATOR
# =========================
def generate_pdf(data):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    content = []

    # ===== LOGO =====
    logo_path = "logo_suto.png"

    if os.path.exists(logo_path):
        content.append(Image(logo_path, width=120, height=50))
    else:
        content.append(Paragraph("SUTO", styles['Title']))

    content.append(Spacer(1, 10))

    # ===== TITLE =====
    content.append(
        Paragraph(
            "SUTO CONFIGURATION PROPOSAL",
            styles['Title']
        )
    )

    content.append(Spacer(1, 12))

    # ===== TABLE =====
    table_data = [[k, str(v)] for k, v in data.items()]

    table = Table(table_data)

    table.setStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    ])

    content.append(table)

    # ===== BUILD PDF =====
    doc.build(content)

    buffer.seek(0)

    return buffer

# =========================
# UI
# =========================
st.title("🔥 SUTO Catalog Configurator")

col1, col2 = st.columns(2)

with col1:
    dp = st.selectbox("Dew Point", [-100,-80,-60,-40,-20,0])
    pressure = st.selectbox("Pressure (bar)", [5,7,10,16,20,30])
    ambient = st.number_input("Ambient (°C)", value=30)

with col2:
    flow = st.number_input("Flow (m³/h)", value=10.0)
    comm = st.selectbox("Communication", ["4-20 mA Only","4-20 mA + Modbus"])
    display = st.selectbox("Display", ["No","Yes"])
    pressure_sensor = st.selectbox("Pressure Sensor", ["No","Yes"])

flow_ctrl = st.selectbox("Flow Control", ["Yes","No"])
dp_available = st.selectbox("ΔP Available", ["Yes","No"])

# =========================
# RUN
# =========================
if st.button("🚀 Generate Catalog Output"):

    sensor = select_sensor(dp)
    wire = wiring(comm, display, pressure_sensor)

    base = base_part(sensor, comm, pressure_sensor, wire)
    opt = options(sensor, comm, display, pressure)

    order = order_string(base, opt)
    chamber_sel = chamber(flow_ctrl, dp_available)

    datasheet = get_datasheet(sensor)

    st.subheader("📊 Result")
    st.success(f"Sensor: {sensor}")
    st.info(f"ORDER STRING: {order}")

    st.write(f"Chamber: {chamber_sel}")
    st.write(f"Wiring: {wire}")

    # DATASHEET DOWNLOAD
    if datasheet:
        with open(datasheet, "rb") as f:
            st.download_button(
                f"📥 Download {sensor} Datasheet",
                f,
                file_name=f"{sensor}_datasheet.pdf"
            )
    else:
        st.warning("Datasheet not found")

    # PDF
    report = {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Sensor": sensor,
        "Order String": order,
        "Chamber": chamber_sel,
        "Pressure": f"{pressure} bar",
        "Flow": f"{flow} m³/h",
        "Wiring": wire
    }

    pdf = generate_pdf(report)
elements = []

logo = Image("suto_logo.png")

logo.drawHeight = 60
logo.drawWidth = 180

elements.append(logo)
elements.append(Spacer(1, 20))
