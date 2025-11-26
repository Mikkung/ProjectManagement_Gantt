import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

st.set_page_config(layout="wide", page_title="Clickable Gantt")

st.title("🖱️ Clickable Gantt Chart")
st.info("💡 ลองคลิกที่แท่ง **Main Task (สีเขียว)** เพื่อดู Subtask ย่อย")

# ---------------------------------------------------------
# 1. PREPARE DATA
# ---------------------------------------------------------
if "tasks_db" not in st.session_state:
    # เก็บข้อมูลแบบ Dictionary โดยมี Key เป็น Main Task
    st.session_state.tasks_db = [
        {
            "Main Task": "Website Redesign", 
            "Start": date.today(), 
            "End": date.today() + timedelta(days=10),
            "Subtasks": [
                {"Task": "Design UI", "Start": date.today(), "End": date.today() + timedelta(days=3)},
                {"Task": "Develop Backend", "Start": date.today() + timedelta(days=3), "End": date.today() + timedelta(days=8)},
                {"Task": "Testing", "Start": date.today() + timedelta(days=8), "End": date.today() + timedelta(days=10)},
            ]
        },
        {
            "Main Task": "Mobile App", 
            "Start": date.today() + timedelta(days=2), 
            "End": date.today() + timedelta(days=15),
            "Subtasks": [
                {"Task": "Setup Flutter", "Start": date.today() + timedelta(days=2), "End": date.today() + timedelta(days=5)},
                {"Task": "API Integration", "Start": date.today() + timedelta(days=5), "End": date.today() + timedelta(days=12)},
            ]
        }
    ]

# State สำหรับเก็บว่า Task ไหนเปิดอยู่ (Expanded)
if "expanded_tasks" not in st.session_state:
    st.session_state.expanded_tasks = set() # ใช้ Set เก็บชื่อ Task ที่เปิดอยู่

# ---------------------------------------------------------
# 2. LOGIC: CLICK HANDLER
# ---------------------------------------------------------
# ฟังก์ชันจัดการเมื่อมีการคลิก
def handle_selection():
    # ดึงข้อมูลจากการคลิกครั้งล่าสุด
    selection = st.session_state.get("gantt_selection")
    
    if selection and selection["selection"]["points"]:
        # ดึงข้อมูลจุดที่ถูกคลิก
        clicked_point = selection["selection"]["points"][0]
        custom_data = clicked_point.get("customdata", [])
        
        if custom_data:
            task_name = custom_data[0] # ชื่อ Main Task
            is_main = custom_data[1]   # เป็น Main Task หรือไม่ (True/False)
            
            # ถ้าคลิกที่ Main Task ให้สลับสถานะ (Expand <-> Collapse)
            if is_main:
                if task_name in st.session_state.expanded_tasks:
                    st.session_state.expanded_tasks.remove(task_name)
                else:
                    st.session_state.expanded_tasks.add(task_name)
                
                # Trick: สั่ง Rerun เพื่ออัปเดตกราฟทันที
                # (Streamlit จะ Rerun อัตโนมัติเมื่อ Widget เปลี่ยนค่า แต่การทำแบบนี้ชัวร์กว่าสำหรับ Logic ที่ซับซ้อน)

# ---------------------------------------------------------
# 3. BUILD PLOT DATA
# ---------------------------------------------------------
plot_rows = []

for item in st.session_state.tasks_db:
    main_name = item["Main Task"]
    is_expanded = main_name in st.session_state.expanded_tasks
    
    # สัญลักษณ์หน้าชื่อ (เพื่อให้รู้ว่ากดได้)
    icon = "🔽" if is_expanded else "▶️"
    display_name = f"{icon} {main_name}"
    
    # 1. Add Main Task Row
    plot_rows.append({
        "Task": display_name,
        "Start": item["Start"],
        "End": item["End"],
        "Color": "Main Task",
        "Type": "Main",
        "RealName": main_name, # เก็บชื่อจริงไว้ใช้ตอนคลิก
        "IsMain": True         # Flag บอกว่าเป็นตัวแม่
    })
    
    # 2. Add Subtasks (ถ้า Expand อยู่)
    if is_expanded:
        for sub in item["Subtasks"]:
            plot_rows.append({
                "Task": f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↳ {sub['Task']}", # ย่อหน้า
                "Start": sub["Start"],
                "End": sub["End"],
                "Color": "Subtask",
                "Type": "Sub",
                "RealName": main_name, # ยังคงเก็บชื่อแม่ไว้ (เผื่ออยากลิงก์กลับ)
                "IsMain": False
            })

df_plot = pd.DataFrame(plot_rows)

# ---------------------------------------------------------
# 4. DRAW GANTT
# ---------------------------------------------------------
if not df_plot.empty:
    fig = px.timeline(
        df_plot, 
        x_start="Start", 
        x_end="End", 
        y="Task", 
        color="Color",
        color_discrete_map={"Main Task": "#2E86C1", "Subtask": "#AED6F1"},
        # ส่งข้อมูล custom_data เข้าไปในกราฟ เพื่อให้ตอนคลิกเราดึงค่ากลับมาได้
        custom_data=["RealName", "IsMain"] 
    )
    
    fig.update_yaxes(autorange="reversed", title="")
    fig.update_layout(
        xaxis_title="",
        showlegend=False,
        height=400 + (len(df_plot) * 30),
        # ปิด Mode การ Zoom เพื่อให้คลิกง่ายขึ้น
        dragmode=False 
    )

    # -----------------------------------------------------
    # *หัวใจสำคัญ* : st.plotly_chart พร้อม on_select
    # -----------------------------------------------------
    event = st.plotly_chart(
        fig, 
        use_container_width=True,
        on_select="rerun",           # เมื่อคลิกเลือก ให้ Rerun App
        selection_mode="points",     # โหมดเลือกจุด
        key="gantt_selection"        # Key สำหรับดึงค่า selection
    )
    
    # เรียกฟังก์ชันจัดการคลิก (จะทำงานหลังจาก Rerun)
    handle_selection()
    
else:
    st.write("No data found")
