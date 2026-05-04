import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import io

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="SUTO Dew Point PRO Tool", layout="wide")

# =========================
# SIZING LOGIC
# =========================
def select_sensor(dew_point):
    if dew_point <= -80:
        return "S220"
    elif dew_point <= -40:
        return "S211"
    else:
        return "S215"

def pressure_check(sensor, pressure):
    if pressure > 1.6:
        if sensor in ["S211", "S215"]:
            return "High Pressure Option", "⚠ High pressure option required"
        else:
            return "NOT VALID", "❌ S220 not allowed >1.6 MPa"
    return "Standard", "OK"

def chamber_selection(flow_control, dp_available):
    if not flow_control:
        return "A699 3491 (Auto Flow)"
    elif dp_available:
        return "A699 3493 (Bypass)"
    else:
        return "A554 2301 (Manual Valve)"

def flow_check(flow):
    if flow < 2:
        return "LOW", "⚠ Flow too low (<2 L/min)"
    elif flow > 5:
        return "HIGH", "⚠ Flow too high (>5 L/min)"
    return "OK", "OK"

# =========================
# PDF GENERATOR (PRO)
# =========================
def generate_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []

    # Title
    content.append(Paragraph("DEW POINT SENSOR PROPOSAL", styles['Title']))
    content.append(Spacer(1, 12))

    # Info Table
    table_data = [[k, str(v)] for k, v in data.items()]
    table = Table(table_data)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
    ]))

    content.append(table)
    content.append(Spacer(1, 20))

    # Recommendation
    content.append(Paragraph("Recommendation Summary:", styles['Heading2']))
    content.append(Spacer(1, 10))

    content.append(Paragraph(f"Sensor: <b>{data['Sensor']}</b>", styles['Normal']))
    content.append(Paragraph(f"Chamber: <b>{data['Chamber']}</b>", styles['Normal']))
    content.append(Paragraph(f"Pressure Option: <b>{data['Pressure Option']}</b>", styles['Normal']))
    content.append(Spacer(1, 10))

    if "❌" in data["Warning"] or "⚠" in data["Warning"]:
        content.append(Paragraph(f"<b>Warning:</b> {data['Warning']}", styles['Normal']))

    doc.build(content)
    buffer.seek(0)
    return buffer

# =========================
# UI HEADER
# =========================
st.title("🔥 SUTO Dew Point Sizing Tool - PRO")

mode = st.radio("Mode", ["Manual Input", "Simulasi Data (Flowmeter / S331)"])

# =========================
# INPUT SECTION
# =========================
col1, col2 = st.columns(2)

with col1:
    dew_point = st.selectbox(
        "Target Dew Point",
        [-100, -80, -60, -40, -20, 0, 10]
    )

    pressure = st.selectbox(
        "System Pressure (MPa)",
        [0.5, 0.7, 1.0, 1.6, 2.0, 3.0]
    )

with col2:
    if mode == "Manual Input":
        flow = st.selectbox("Flow (L/min)", [1, 2, 3, 4, 5, 6])
    else:
        # Simulasi data real
        flow = 3.2
        st.info(f"Live Flow (Simulated): {flow} L/min")

    flow_control = st.selectbox("Flow Control Available?", ["Yes", "No"])
    dp_available = st.selectbox("Pressure Difference (ΔP)?", ["Yes", "No"])

# =========================
# CALCULATION
# =========================
if st.button("🚀 Generate Recommendation"):

    sensor = select_sensor(dew_point)
    pressure_option, pressure_status = pressure_check(sensor, pressure)
    chamber = chamber_selection(flow_control == "Yes", dp_available == "Yes")
    flow_status, flow_msg = flow_check(flow)

    # STATUS DISPLAY
    st.subheader("Result Summary")

    st.success(f"Sensor: {sensor}")
    st.info(f"Chamber: {chamber}")

    if pressure_option == "NOT VALID":
        st.error(pressure_status)
    else:
        st.warning(pressure_status)

    if flow_status != "OK":
        st.warning(flow_msg)
    else:
        st.success("Flow OK")

    # =========================
    # REPORT DATA
    # =========================
    report_data = {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Dew Point": f"{dew_point} °C Td",
        "Pressure": f"{pressure} MPa",
        "Flow": f"{flow} L/min",
        "Sensor": sensor,
        "Chamber": chamber,
        "Pressure Option": pressure_option,
        "Warning": f"{pressure_status} | {flow_msg}"
    }

    pdf = generate_pdf(report_data)

    st.download_button(
        "📄 Download Proposal PDF",
        pdf,
        file_name="SUTO_Proposal.pdf",
        mime="application/pdf"
    )
