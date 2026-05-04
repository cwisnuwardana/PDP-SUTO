import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import io

st.set_page_config(page_title="SUTO Dew Point PRO+", layout="wide")

# =========================
# LOGIC FUNCTIONS
# =========================
def select_sensor(dew_point):
    if dew_point <= -80:
        return "S220"
    elif dew_point <= -40:
        return "S211"
    else:
        return "S215"

def pressure_check(sensor, pressure_bar):
    if pressure_bar > 16:
        if sensor in ["S211", "S215"]:
            return "High Pressure Option", "⚠ High pressure option required"
        else:
            return "NOT VALID", "❌ S220 not allowed >16 bar"
    return "Standard", "OK"

def chamber_selection(flow_control, dp_available):
    if not flow_control:
        return "A699 3491 (Auto Flow)"
    elif dp_available:
        return "A699 3493 (Bypass)"
    else:
        return "A554 2301 (Manual Valve)"

def flow_check(flow_lpm):
    if flow_lpm < 2:
        return "LOW", "⚠ Flow too low (<2 L/min)"
    elif flow_lpm > 5:
        return "HIGH", "⚠ Flow too high (>5 L/min)"
    return "OK", "OK"

# =========================
# BYPASS SIZING
# =========================
def calculate_bypass(main_flow_m3h, target_lpm=3):
    main_lpm = main_flow_m3h * 16.67

    ratio = target_lpm / main_lpm
    percent = ratio * 100

    return main_lpm, ratio, percent

def needle_valve_estimation(target_lpm=3, max_lpm=5):
    opening = (target_lpm / max_lpm) * 100
    return round(opening, 1)

# =========================
# PDF GENERATOR
# =========================
def generate_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph("DEW POINT ENGINEERING PROPOSAL", styles['Title']))
    content.append(Spacer(1, 12))

    table_data = [[k, str(v)] for k, v in data.items()]
    table = Table(table_data)

    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
    ]))

    content.append(table)
    content.append(Spacer(1, 20))

    doc.build(content)
    buffer.seek(0)
    return buffer

# =========================
# UI
# =========================
st.image("suto_logo.png" width=200)
st.title("SUTO Dew Point Sizing Tool PRO+ (Engineering Mode)")

col1, col2 = st.columns(2)

with col1:
    dew_point = st.selectbox("Target Dew Point (°C Td)", [-100, -80, -60, -40, -20, 0])
    pressure = st.selectbox("Pressure (bar)", [5, 7, 10, 16, 20, 30])

with col2:
    flow_m3h = st.number_input("Main Line Flow (m³/h)", value=10.0)
    flow_control = st.selectbox("Flow Control Available?", ["Yes", "No"])
    dp_available = st.selectbox("Pressure Difference (ΔP)?", ["Yes", "No"])

# =========================
# CALCULATION
# =========================
if st.button("🚀 Calculate Engineering Result"):

    # Sensor
    sensor = select_sensor(dew_point)

    # Pressure
    pressure_option, pressure_status = pressure_check(sensor, pressure)

    # Chamber
    chamber = chamber_selection(flow_control == "Yes", dp_available == "Yes")

    # Bypass calc
    main_lpm, ratio, percent = calculate_bypass(flow_m3h)

    # Target sensor flow
    sensor_flow = 3  # ideal

    # Flow check
    flow_status, flow_msg = flow_check(sensor_flow)

    # Needle valve
    valve_open = needle_valve_estimation(sensor_flow)

    # =========================
    # DISPLAY
    # =========================
    st.subheader("📊 Result Summary")

    st.success(f"Sensor: {sensor}")
    st.info(f"Chamber: {chamber}")

    st.write(f"Pressure Status: {pressure_status}")
    st.write(f"Flow Status: {flow_msg}")

    st.subheader("🔧 Bypass Engineering")

    st.write(f"Main Flow: {flow_m3h} m³/h ({round(main_lpm,2)} L/min)")
    st.write(f"Target Sensor Flow: {sensor_flow} L/min")

    st.write(f"Bypass Ratio: {round(percent,4)} %")
    st.write(f"Needle Valve Opening (est): {valve_open} %")

    if percent < 0.1:
        st.warning("⚠ Very small bypass ratio → use precise needle valve")

    # =========================
    # PDF
    # =========================
    report_data = {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Dew Point": f"{dew_point} °C Td",
        "Pressure": f"{pressure} bar",
        "Main Flow": f"{flow_m3h} m³/h",
        "Sensor": sensor,
        "Chamber": chamber,
        "Bypass Ratio (%)": round(percent, 4),
        "Needle Valve Opening (%)": valve_open,
        "Pressure Status": pressure_status,
        "Flow Status": flow_msg
    }

    pdf = generate_pdf(report_data)

    st.download_button(
        "📄 Download Engineering Proposal",
        pdf,
        file_name="SUTO_Engineering_Proposal.pdf",
        mime="application/pdf"
    )
