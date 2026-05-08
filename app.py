import streamlit as st
import os
import io

from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="PDP SUTO",
    page_icon="suto_logo.png",
    layout="wide"
)


# =========================================================
# TITLE
# =========================================================
st.image("suto_logo.png", width=220)
st.title("💧 PDP SUTO Selection Model")
st.caption("S211 / S215 / S220 Dew Point Engineering Tool")


# =========================================================
# SENSOR SELECTION
# =========================================================
def select_sensor(dp):

    if dp <= -80:
        return "S220"

    elif dp <= -40:
        return "S211"

    else:
        return "S215"


# =========================================================
# WIRING
# =========================================================
def wiring_logic(comm, display, pressure_sensor):

    if (
        comm == "4-20 mA Only"
        and display == "No"
        and pressure_sensor == "No"
    ):
        return "2-wire"

    return "3-wire"


# =========================================================
# BASE PART NUMBER
# =========================================================
def base_part(sensor, comm, pressure_sensor, wiring):

    sensor_code = {
        "S211": "11",
        "S215": "15",
        "S220": "20"
    }[sensor]

    # 2-wire Analog
    if wiring == "2-wire":
        series = "1"

    # 3-wire Analog
    elif comm == "4-20 mA Only":
        series = "2"

    # Modbus
    elif pressure_sensor == "No":
        series = "3"

    # Pressure Sensor
    else:
        series = "4"

    return f"S699 {series}{sensor_code}"


# =========================================================
# OPTIONS
# =========================================================
def option_codes(sensor, comm, display, pressure_option):

    options = []

    # =====================================
    # PRESSURE
    # =====================================
    if "35" in pressure_option:

        if sensor == "S220":
            options.append("❌ S220 NOT ALLOWED >16 bar")

        else:
            options.append("A1381")

    else:
        options.append("A1380")

    # =====================================
    # DISPLAY
    # =====================================
    if display == "Yes":

        if "Modbus" in comm:
            options.append("A1388")

        else:
            options.append("A1387")

    else:
        options.append("A1389")

    return options


# =========================================================
# ORDER STRING
# =========================================================
def order_string(base, options):

    clean_options = []

    for o in options:

        if "❌" not in o:
            clean_options.append(o)

    if clean_options:
        return base + "." + ".".join(clean_options)

    return base


# =========================================================
# CHAMBER SELECTION
# =========================================================
def chamber_selection(pressure_option, flow_control):

    # High Pressure Chamber
    if "35" in pressure_option:
        return "A699 3590"

    # Quick Coupling Chamber
    if flow_control == "No":
        return "A699 3491"

    # Bypass Chamber
    return "A699 3493"


# =========================================================
# CABLE OPTION
# =========================================================
def cable_option(cable):

    if cable == "5 m":
        return "A553 0104"

    return "A553 0105"


# =========================================================
# DATASHEET
# =========================================================
def get_datasheet(sensor):

    path = "datasheets/SUTO_DP_211_215_220.pdf"

    if os.path.exists(path):
        return path

    return None


# =========================================================
# AMBIENT CHECK
# =========================================================
def ambient_check(temp):

    if temp > 50:

        return (
            "⚠ Ambient too high (>50°C). "
            "Recommended max ambient: 50°C. "
            "Use cooling chamber / remote installation."
        )

    elif temp < 0:

        return (
            "⚠ Ambient too low (<0°C). "
            "Recommended min ambient: 0°C. "
            "Use heated enclosure if required."
        )

    return "OK"


# =========================================================
# BYPASS CALCULATION
# =========================================================
def bypass_calc(flow_m3h):

    main_lpm = flow_m3h * 16.67

    target_flow = 3

    bypass_ratio = (
        target_flow / main_lpm
    ) * 100

    valve_opening = (
        target_flow / 5
    ) * 100

    return (
        main_lpm,
        bypass_ratio,
        valve_opening
    )


# =========================================================
# PDF GENERATOR
# =========================================================
def generate_pdf(data):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    content = []

    # =====================================
    # LOGO
    # =====================================
    logo_path = "suto_logo.png"

    if os.path.exists(logo_path):

        logo = Image(
            logo_path,
            width=330,
            height=60
        )

        content.append(logo)

    else:

        content.append(
            Paragraph(
                "SUTO",
                styles['Title']
            )
        )

    content.append(Spacer(1, 10))

    # =====================================
    # TITLE
    # =====================================
    content.append(
        Paragraph(
            "SUTO PDP PROPOSAL",
            styles['Title']
        )
    )

    content.append(Spacer(1, 15))

    # =====================================
    # TABLE
    # =====================================
    table_data = []

    for k, v in data.items():

        table_data.append(
            [k, str(v)]
        )

    table = Table(table_data)

    table.setStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ])

    content.append(table)

    # =====================================
    # BUILD PDF
    # =====================================
    doc.build(content)

    buffer.seek(0)

    return buffer


# =========================================================
# UI
# =========================================================
st.subheader("⚙️ Application Input")

col1, col2 = st.columns(2)

with col1:

    dew_point = st.selectbox(
        "Dew Point (°C Td)",
        [-100, -80, -60, -40, -20, 0]
    )

    pressure_option = st.selectbox(
        "Operating Pressure",
        [
            "0...16 bar (A1380)",
            "0...35 bar (A1381)"
        ]
    )

    ambient = st.number_input(
        "Ambient Temperature (°C)",
        value=30
    )

    flow = st.number_input(
        "Main Flow (m³/h)",
        value=10.0
    )

with col2:

    comm = st.selectbox(
        "Communication",
        [
            "4-20 mA Only",
            "4-20 mA + Modbus"
        ]
    )

    display = st.selectbox(
        "Display",
        [
            "No",
            "Yes"
        ]
    )

    pressure_sensor = st.selectbox(
        "Integrated Pressure Sensor",
        [
            "No",
            "Yes"
        ]
    )

    flow_control = st.selectbox(
        "Flow Control Available",
        [
            "Yes",
            "No"
        ]
    )

    cable = st.selectbox(
        "Cable Length",
        [
            "5 m",
            "10 m"
        ]
    )


# =========================================================
# GENERATE
# =========================================================
if st.button("🚀 Generate Catalog Output"):

    # =====================================
    # SENSOR
    # =====================================
    sensor = select_sensor(
        dew_point
    )

    # =====================================
    # WIRING
    # =====================================
    wiring = wiring_logic(
        comm,
        display,
        pressure_sensor
    )

    # =====================================
    # BASE PART
    # =====================================
    base = base_part(
        sensor,
        comm,
        pressure_sensor,
        wiring
    )

    # =====================================
    # OPTIONS
    # =====================================
    options = option_codes(
        sensor,
        comm,
        display,
        pressure_option
    )

    # =====================================
    # ORDER STRING
    # =====================================
    final_order = order_string(
        base,
        options
    )

    # =====================================
    # CHAMBER
    # =====================================
    chamber = chamber_selection(
        pressure_option,
        flow_control
    )

    # =====================================
    # CABLE
    # =====================================
    cable_code = cable_option(
        cable
    )

    # =====================================
    # AMBIENT
    # =====================================
    ambient_status = ambient_check(
        ambient
    )

    # =====================================
    # BYPASS
    # =====================================
    (
        main_lpm,
        bypass_ratio,
        valve_opening
    ) = bypass_calc(flow)

    # =====================================
    # DISPLAY RESULT
    # =====================================
    st.subheader("📊 Configuration Result")

    st.success(f"Sensor : {sensor}")

    st.info(
        f"Order String : {final_order}"
    )

    st.write(f"Wiring : {wiring}")

    st.write(
        f"Pressure Option : {pressure_option}"
    )

    st.write(
        f"Chamber : {chamber}"
    )

    st.write(
        f"Cable : {cable_code}"
    )

    st.write(
        f"Ambient Status : {ambient_status}"
    )

    # =====================================
    # WARNINGS
    # =====================================
    for o in options:

        if "❌" in o:
            st.error(o)

    # =====================================
    # ENGINEERING
    # =====================================
    st.subheader("🔧 Engineering")

    st.write(
        f"Main Flow : {flow} m³/h"
    )

    st.write(
        f"Main Flow : {round(main_lpm,2)} L/min"
    )

    st.write(
        f"Bypass Ratio : {round(bypass_ratio,4)} %"
    )

    st.write(
        f"Needle Valve Opening : {round(valve_opening,1)} %"
    )

    # =====================================
    # DATASHEET
    # =====================================
    datasheet = get_datasheet(sensor)

    if datasheet:

        with open(datasheet, "rb") as f:

            st.download_button(
                f"📥 Download {sensor} Datasheet",
                f,
                file_name=f"{sensor}_datasheet.pdf"
            )

    else:

        st.warning(
            "Datasheet not found"
        )

    # =====================================
    # PDF DATA
    # =====================================
    report = {

        "Date":
            datetime.now().strftime("%Y-%m-%d"),

        "Sensor":
            sensor,

        "Order String":
            final_order,

        "Pressure":
            pressure_option,

        "Communication":
            comm,

        "Display":
            display,

        "Pressure Sensor":
            pressure_sensor,

        "Wiring":
            wiring,

        "Chamber":
            chamber,

        "Cable":
            cable_code,

        "Ambient":
            ambient_status,

        "Main Flow":
            f"{flow} m3/h",

        "Bypass Ratio":
            f"{round(bypass_ratio,4)} %",

        "Needle Valve":
            f"{round(valve_opening,1)} %"
    }

    # =====================================
    # GENERATE PDF
    # =====================================
    pdf = generate_pdf(report)

    st.download_button(
        "📄 Download Proposal PDF",
        pdf,
        file_name="SUTO_Proposal.pdf",
        mime="application/pdf"
    )
