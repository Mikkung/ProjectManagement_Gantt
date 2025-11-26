import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

# --- 1. SETUP & CONFIG ---
st.set_page_config(layout="wide", page_title="ClickUp Clone V3", page_icon="✅")

# CSS ปรับแต่งให้ดูสะอาดตาเหมือน ClickUp
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; font-weight: 600; color: #5f6b7c; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #7b68ee; border-bottom: 2px solid #7b68ee; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA MANAGEMENT (Flat Structure with Hierarchy) ---
if "tasks_df" not in st.session_state:
    # ใช้โครงสร้างข้อมูลแบบ Flat Table (เหมือน Database จริง)
    # โดยมีคอลัมน์ "Parent Task" เพื่อระบุว่าเป็นลูกของใคร
    data = [
        # Project A: Website
        {"Task": "Website Redesign", "Parent": None, "Start": date.today(), "End": date.today() + timedelta(days=10), "Status": "In Progress", "Assignee": "Team"},
        {"Task": "Design UI", "Parent": "Website Redesign", "Start": date.today(), "End": date.today() + timedelta(days=4), "Status": "Done", "Assignee": "Alice"},
        {"Task": "Develop Backend", "Parent": "Website Redesign", "Start": date.today() + timedelta(days=4), "End": date.today() + timedelta(days=9), "Status": "In Progress", "Assignee": "Bob"},
        {"Task": "Testing", "Parent": "Website Redesign", "Start": date.today() + timedelta(days=9), "End": date.today() + timedelta(days=10), "Status": "Not Started", "Assignee": "Charlie"},
        
        # Project B: Mobile App
        {"Task": "Mobile App Launch", "Parent": None, "Start": date.today() + timedelta(days=2), "End": date.today() + timedelta(days=15), "Status": "Planning", "Assignee": "Team"},
        {"Task": "Setup Flutter", "Parent": "Mobile App Launch", "Start": date.today() + timedelta(days=2), "End": date.today() + timedelta(days=5), "Status": "Done", "Assignee": "Dave"},
        {"Task": "API Integration", "Parent": "Mobile App Launch", "Start": date.today() + timedelta(days=5), "End": date.today() + timedelta(days=12), "Status": "In Progress", "Assignee": "Eve"},
    ]
    st.session_state.tasks_df = pd.DataFrame(data)
    st.session_state.tasks_df["Start"] = pd.to_datetime(st.session_state.tasks_df["Start"])
    st.session_state.tasks_df["End"] = pd.to_datetime(st.session_state.tasks_df["End"])

# State สำหรับเก็บว่า Task ไหน "เปิด" (Expanded) อยู่บ้าง
if "expanded_tasks" not in st.session_state:
    st.session_state.expanded_tasks = set()

# Color Mapping
status_colors = {
    "Not Started": "#d3d3d3", "Planning": "#A9CCE3", 
    "In Progress": "#3498DB", "Done": "#2ECC71", "Main Task": "#2C3E50"
}

# --- 3. LOGIC: CLICK HANDLER (จัดการการคลิกกราฟ) ---
def handle_gantt_click():
    selection = st.session_state.get("gantt_select")
    if selection and selection["selection"]["points"]:
        point = selection["selection"]["points"][0]
        # ดึงข้อมูลที่ซ่อนไว้ใน customdata
        if "customdata" in point:
            task_name = point["customdata"][0]
            is_parent = point["customdata"][1]
            
            if is_parent: # คลิกตัวแม่เท่านั้นถึงจะ Toggle
                if task_name in st.session_state.expanded_tasks:
                    st.session_state.expanded_tasks.remove(task_name)
                else:
                    st.session_state.expanded_tasks.add(task_name)

# --- 4. UI LAYOUT ---
st.title("🚀 Project Manager (Interactive)")

# Tabs แบบ ClickUp
tab_list, tab_board, tab_gantt = st.tabs(["📄 List View", "📋 Board View", "📊 Gantt Chart"])

# === TAB 1: LIST VIEW ===
with tab_list:
    st.caption("จัดการข้อมูลดิบ (Parent = ว่าง คือ Task หลัก / Parent = ชื่อ Task อื่น คือ Subtask)")
    edited_df = st.data_editor(
        st.session_state.tasks_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Status": st.column_config.SelectboxColumn("Status", options=list(status_colors.keys())),
            "Parent": st.column_config.SelectboxColumn("Parent Task", options=[None] + list(st.session_state.tasks_df[st.session_state.tasks_df["Parent"].isnull()]["Task"].unique()))
        },
        key="list_editor"
    )
    # Save Data
    if not edited_df.equals(st.session_state.tasks_df):
        st.session_state.tasks_df = edited_df
        st.rerun()

# === TAB 2: BOARD VIEW ===
with tab_board:
    st.caption("Kanban Board (แสดงเฉพาะ Subtasks เพื่อติดตามงานจริง)")
    cols = st.columns(4)
    statuses = ["Not Started", "Planning", "In Progress", "Done"]
    
    # กรองเอาเฉพาะ Subtask หรือ Task เดี่ยวๆ มาแสดงในบอร์ด
    board_df = st.session_state.tasks_df[st.session_state.tasks_df["Parent"].notnull()]
    
    for i, status in enumerate(statuses):
        with cols[i]:
            st.markdown(f"**{status}**")
            tasks = board_df[board_df["Status"] == status]
            for _, row in tasks.iterrows():
                st.info(f"{row['Task']}\n\n👤 {row['Assignee']}")

# === TAB 3: GANTT CHART (The Star ⭐) ===
with tab_gantt:
    st.caption("คลิกที่ **แถบสีเข้ม (Main Task)** เพื่อดู Subtask ย่อย")
    
    # --- A. เตรียมข้อมูลสำหรับ Plot ---
    plot_rows = []
    y_axis_order = [] # ตัวแปรสำคัญ! ใช้บังคับลำดับบรรทัด
    
    df = st.session_state.tasks_df
    # 1. หา Main Tasks
    main_tasks = df[df["Parent"].isnull()]
    
    for _, main in main_tasks.iterrows():
        main_name = main["Task"]
        is_expanded = main_name in st.session_state.expanded_tasks
        
        # Icon แสดงสถานะ
        prefix = "🔽 " if is_expanded else "▶️ "
        display_name = f"{prefix}{main_name}"
        
        # เพิ่ม Main Task
        plot_rows.append({
            "Task Label": display_name,
            "Start": main["Start"],
            "End": main["End"],
            "Color": "Main Task",
            "RealName": main_name, # ส่งไปใช้ตอนคลิก
            "IsParent": True
        })
        y_axis_order.append(display_name) # บันทึกลำดับไว้
        
        # 2. ถ้า Expand อยู่ ให้ไปหาลูกๆ มาต่อท้าย "ทันที"
        if is_expanded:
            subtasks = df[df["Parent"] == main_name].sort_values("Start") # เรียงลูกตามวันที่เริ่ม
            for _, sub in subtasks.iterrows():
                sub_label = f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↳ {sub['Task']}" # ย่อหน้า
                plot_rows.append({
                    "Task Label": sub_label,
                    "Start": sub["Start"],
                    "End": sub["End"],
                    "Color": sub["Status"], # ลูกใช้สีตาม Status
                    "RealName": sub["Task"],
                    "IsParent": False
                })
                y_axis_order.append(sub_label) # บันทึกลำดับลูกต่อจากแม่ทันที

    plot_df = pd.DataFrame(plot_rows)

    # --- B. สร้างกราฟ ---
    if not plot_df.empty:
        fig = px.timeline(
            plot_df,
            x_start="Start", x_end="End",
            y="Task Label",
            color="Color",
            color_discrete_map=status_colors,
            custom_data=["RealName", "IsParent"], # ซ่อนข้อมูลไว้ส่งกลับ Python
            height=400 + (len(plot_df) * 30)
        )
        
        # *** FIX สำคัญ: บังคับลำดับแกน Y ให้เป็นตามที่เราเรียงมา (แม่ -> ลูก) ***
        fig.update_yaxes(
            autorange="reversed", # เรียงจากบนลงล่าง
            categoryorder="array", # บอก Plotly ว่าขอเรียงเอง
            categoryarray=y_axis_order, # เอา List ลำดับที่เราทำไว้ใส่เข้าไป
            title=""
        )
        
        fig.update_layout(
            xaxis_title="",
            showlegend=False,
            margin=dict(t=10, b=10),
            dragmode=False # ปิดการลากซูม เพื่อให้คลิกง่าย
        )

        # แสดงผล + ดักจับ Event
        st.plotly_chart(
            fig,
            use_container_width=True,
            on_select="rerun",     # คลิกปุ๊บ รีรันปั๊บ
            selection_mode="points",
            key="gantt_select"
        )
        
        # เรียกฟังก์ชันจัดการ logic
        handle_gantt_click()
        
    else:
        st.info("No tasks found. Go to 'List View' to add tasks.")
