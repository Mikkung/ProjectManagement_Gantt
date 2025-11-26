import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

st.set_page_config(layout="wide", page_title="Expandable Gantt")

# ---------------------------------------------------------
# 1. SETUP DATA (สร้างข้อมูลตัวอย่าง)
# ---------------------------------------------------------
if "data" not in st.session_state:
    data = [
        # Project 1: Website
        {"Task": "Website Redesign", "Subtask": "Design UI", "Start": date.today(), "End": date.today() + timedelta(days=5), "Status": "In Progress"},
        {"Task": "Website Redesign", "Subtask": "Develop Backend", "Start": date.today() + timedelta(days=3), "End": date.today() + timedelta(days=10), "Status": "Not Started"},
        {"Task": "Website Redesign", "Subtask": "Testing", "Start": date.today() + timedelta(days=9), "End": date.today() + timedelta(days=12), "Status": "Not Started"},
        
        # Project 2: Mobile App
        {"Task": "Mobile App", "Subtask": "Setup Flutter", "Start": date.today(), "End": date.today() + timedelta(days=3), "Status": "Done"},
        {"Task": "Mobile App", "Subtask": "API Integration", "Start": date.today() + timedelta(days=2), "End": date.today() + timedelta(days=7), "Status": "In Progress"},
    ]
    st.session_state.data = pd.DataFrame(data)
    # แปลงเป็น datetime
    st.session_state.data["Start"] = pd.to_datetime(st.session_state.data["Start"])
    st.session_state.data["End"] = pd.to_datetime(st.session_state.data["End"])

# ---------------------------------------------------------
# 2. STATE MANAGEMENT (จัดการสถานะการเปิด/ปิด)
# ---------------------------------------------------------
# สร้าง DataFrame สำหรับควบคุมการ Expand (มี 1 แถวต่อ 1 Task หลัก)
unique_tasks = st.session_state.data["Task"].unique()

if "task_states" not in st.session_state:
    # สร้าง dict เก็บสถานะว่า Task ไหนเปิดอยู่บ้าง (True/False)
    st.session_state.task_states = {task: False for task in unique_tasks}

# ---------------------------------------------------------
# 3. LAYOUT แบ่ง 2 คอลัมน์
# ---------------------------------------------------------
st.title("📂 Interactive Expand/Collapse Gantt Chart")
col_control, col_gantt = st.columns([1, 3]) # แบ่งสัดส่วน ซ้าย 1 : ขวา 3

# --- LEFT COLUMN: CONTROL PANEL ---
with col_control:
    st.subheader("📌 Task List")
    st.caption("Tick 'Show Sub' to expand in chart")
    
    # สร้าง DataFrame ชั่วคราวมาแสดงเป็นตารางควบคุม
    control_df = pd.DataFrame({
        "Task Name": unique_tasks,
        "Show Sub": [st.session_state.task_states[t] for t in unique_tasks] # ดึงค่า True/False เดิมมาใส่
    })

    # แสดง Data Editor ให้ติ๊กถูกได้
    edited_control = st.data_editor(
        control_df,
        column_config={
            "Show Sub": st.column_config.CheckboxColumn("Expand", help="Show subtasks in Gantt", default=False)
        },
        disabled=["Task Name"], # ห้ามแก้ชื่อ
        hide_index=True,
        key="control_panel"
    )

    # Update State เมื่อมีการติ๊ก
    for index, row in edited_control.iterrows():
        task_name = row["Task Name"]
        is_expanded = row["Show Sub"]
        st.session_state.task_states[task_name] = is_expanded

# --- RIGHT COLUMN: GANTT CHART LOGIC ---
with col_gantt:
    st.subheader("📊 Timeline")

    # เตรียมข้อมูลที่จะพล็อต (Plot Data)
    plot_rows = []
    
    # วนลูปสร้างข้อมูลตามสถานะ Expand/Collapse
    for task in unique_tasks:
        task_data = st.session_state.data[st.session_state.data["Task"] == task]
        
        # 1. สร้างแถว "Main Task" (แถบสีเขียวแม่) เสมอ
        start_min = task_data["Start"].min()
        end_max = task_data["End"].max()
        
        plot_rows.append({
            "Y_Label": f"<b>{task}</b>", # ตัวหนา
            "Start": start_min,
            "End": end_max,
            "ColorGroup": "Main Task", # สีเขียว
            "Details": f"Total Subtasks: {len(task_data)}"
        })
        
        # 2. ถ้าถูกติ๊ก Expand -> ให้เพิ่มแถว "Subtasks" (แถบสีน้ำเงินลูก)
        if st.session_state.task_states[task]:
            for _, row in task_data.iterrows():
                plot_rows.append({
                    "Y_Label": f"&nbsp;&nbsp;&nbsp;&nbsp;↳ {row['Subtask']}", # ย่อหน้าเทียม
                    "Start": row["Start"],
                    "End": row["End"],
                    "ColorGroup": "Subtask", # สีน้ำเงิน
                    "Details": f"Status: {row['Status']}"
                })

    # สร้าง DataFrame สำหรับ Plotly
    final_plot_df = pd.DataFrame(plot_rows)

    # วาดกราฟ
    if not final_plot_df.empty:
        # กำหนดสีให้เหมือนรูป (แม่=เขียวอ่อน, ลูก=น้ำเงินเข้ม)
        color_map = {"Main Task": "#90EE90", "Subtask": "#4682B4"} 
        
        fig = px.timeline(
            final_plot_df,
            x_start="Start",
            x_end="End",
            y="Y_Label",
            color="ColorGroup",
            color_discrete_map=color_map,
            hover_data=["Details"],
            height=400 + (len(final_plot_df) * 30) # ความสูง Dynamic
        )
        
        fig.update_yaxes(autorange="reversed", title="") # เรียงบนลงล่าง
        fig.update_layout(
            xaxis_title="",
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'), # เส้น Grid จางๆ
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data to display")
