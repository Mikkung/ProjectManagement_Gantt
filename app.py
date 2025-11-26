import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

# --- 1. CONFIGURATION & STYLE ---
st.set_page_config(layout="wide", page_title="ClickUp Clone", page_icon="✅")

# CSS เพื่อปรับแต่งให้ดูเหมือน ClickUp (Clean Look)
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px; color: #87909e; font-weight: 600; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #f0f1f3; color: #7b68ee; border-bottom: 2px solid #7b68ee; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #292d34; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA MANAGEMENT ---
if "tasks" not in st.session_state:
    # สร้างข้อมูลเริ่มต้นให้ครบถ้วน
    default_data = [
        {"ID": "TASK-1", "Project": "Website Revamp", "Title": "Design Mockups", "Assignee": "Alice", "Status": "In Progress", "Priority": "High", "Start": date.today(), "Due": date.today() + timedelta(days=5)},
        {"ID": "TASK-2", "Project": "Website Revamp", "Title": "Frontend Code", "Assignee": "Bob", "Status": "To Do", "Priority": "High", "Start": date.today() + timedelta(days=5), "Due": date.today() + timedelta(days=12)},
        {"ID": "TASK-3", "Project": "Mobile App", "Title": "API Integration", "Assignee": "Charlie", "Status": "Review", "Priority": "Critical", "Start": date.today(), "Due": date.today() + timedelta(days=3)},
        {"ID": "TASK-4", "Project": "Mobile App", "Title": "App Store Submission", "Assignee": "Dave", "Status": "Blocked", "Priority": "Medium", "Start": date.today() + timedelta(days=10), "Due": date.today() + timedelta(days=15)},
        {"ID": "TASK-5", "Project": "Marketing", "Title": "Facebook Ads", "Assignee": "Alice", "Status": "Done", "Priority": "Low", "Start": date.today() - timedelta(days=5), "Due": date.today()},
    ]
    st.session_state.tasks = pd.DataFrame(default_data)
    
    # แปลงวันที่ให้เป็น datetime
    st.session_state.tasks["Start"] = pd.to_datetime(st.session_state.tasks["Start"])
    st.session_state.tasks["Due"] = pd.to_datetime(st.session_state.tasks["Due"])

# สีประจำสถานะ (ClickUp Style)
status_colors = {
    "To Do": "#d3d3d3",       # Gray
    "In Progress": "#3399ff", # Blue
    "Review": "#8e44ad",      # Purple
    "Blocked": "#e74c3c",     # Red
    "Done": "#2ecc71"         # Green
}

# --- 3. SIDEBAR (NAVIGATION & QUICK ADD) ---
with st.sidebar:
    st.title("✅ My Workspace")
    
    st.divider()
    
    # Filter ข้อมูล
    st.subheader("🔍 Filters")
    selected_project = st.multiselect("Project", st.session_state.tasks["Project"].unique(), default=st.session_state.tasks["Project"].unique())
    selected_assignee = st.multiselect("Assignee", st.session_state.tasks["Assignee"].unique(), default=st.session_state.tasks["Assignee"].unique())
    
    st.divider()
    
    # Quick Add Form
    st.subheader("⚡ Quick Add Task")
    with st.form("quick_add"):
        new_project = st.selectbox("Project", ["Website Revamp", "Mobile App", "Marketing", "General"])
        new_title = st.text_input("Task Name")
        new_assignee = st.selectbox("Assignee", ["Alice", "Bob", "Charlie", "Dave"])
        submitted = st.form_submit_button("Add Task")
        
        if submitted and new_title:
            new_task = {
                "ID": f"TASK-{len(st.session_state.tasks)+1}",
                "Project": new_project,
                "Title": new_title,
                "Assignee": new_assignee,
                "Status": "To Do",
                "Priority": "Medium",
                "Start": pd.to_datetime(date.today()),
                "Due": pd.to_datetime(date.today() + timedelta(days=1))
            }
            st.session_state.tasks = pd.concat([st.session_state.tasks, pd.DataFrame([new_task])], ignore_index=True)
            st.success("Task added!")
            st.rerun()

# --- 4. MAIN CONTENT ---

# กรองข้อมูล
df_view = st.session_state.tasks.copy()
df_view = df_view[df_view["Project"].isin(selected_project)]
df_view = df_view[df_view["Assignee"].isin(selected_assignee)]

# Header & Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Tasks", len(df_view))
col2.metric("In Progress", len(df_view[df_view["Status"]=="In Progress"]))
col3.metric("Critical Tasks", len(df_view[df_view["Priority"]=="Critical"]))
col4.metric("Completed", len(df_view[df_view["Status"]=="Done"]))

st.write("") # Spacer

# TABS: หัวใจสำคัญของ ClickUp (List | Board | Gantt)
tab_list, tab_board, tab_gantt = st.tabs(["📄 List View", "📋 Board View", "📊 Gantt View"])

# --- TAB 1: LIST VIEW (Editable Table) ---
with tab_list:
    st.caption("จัดการงานทั้งหมดในรูปแบบตาราง (แก้ไขได้)")
    
    column_config = {
        "ID": st.column_config.TextColumn("ID", disabled=True, width="small"),
        "Project": st.column_config.SelectboxColumn("Project", width="medium", options=["Website Revamp", "Mobile App", "Marketing", "General"]),
        "Status": st.column_config.SelectboxColumn("Status", width="small", options=list(status_colors.keys()), required=True),
        "Priority": st.column_config.SelectboxColumn("Priority", width="small", options=["Low", "Medium", "High", "Critical"]),
        "Start": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"),
        "Due": st.column_config.DateColumn("Due Date", format="YYYY-MM-DD"),
        "Title": st.column_config.TextColumn("Task Name", width="large"),
    }
    
    edited_df = st.data_editor(
        df_view,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="main_editor"
    )
    
    # Save Logic
    if not edited_df.equals(df_view):
        # Update เฉพาะ rows ที่แสดงอยู่กลับเข้าไปใน session state ใหญ่
        # (ใน Code จริงอาจต้องใช้ Index map แต่นี่เป็น Demo ง่ายๆ)
        st.session_state.tasks = edited_df # Override ง่ายๆ สำหรับ Demo
        st.rerun()

# --- TAB 2: BOARD VIEW (Kanban) ---
with tab_board:
    st.caption("ลากวางไม่ได้ (ข้อจำกัด Streamlit) แต่ดูสถานะงานแบบ Kanban ได้ชัดเจน")
    
    cols = st.columns(len(status_colors))
    
    for i, (status, color) in enumerate(status_colors.items()):
        with cols[i]:
            # Header สีๆ แบบ ClickUp
            st.markdown(f"<div style='background-color:{color}; padding: 5px; border-radius: 5px; color: white; text-align: center; font-weight: bold;'>{status}</div>", unsafe_allow_html=True)
            st.write("")
            
            # ดึงงานใน Status นั้นๆ
            tasks_in_status = df_view[df_view["Status"] == status]
            
            for _, row in tasks_in_status.iterrows():
                with st.container():
                    # Card Style
                    st.info(f"**{row['Title']}**\n\n👤 {row['Assignee']} | 📅 {row['Due'].strftime('%d/%m')}")

# --- TAB 3: GANTT VIEW (Interactive) ---
with tab_gantt:
    st.caption("ไทม์ไลน์โปรเจกต์ (สีตามสถานะงาน)")
    
    if not df_view.empty:
        # ใช้สีตามสถานะที่ตั้งไว้
        fig = px.timeline(
            df_view, 
            x_start="Start", 
            x_end="Due", 
            y="Title", 
            color="Status",
            color_discrete_map=status_colors, # Map สีให้ตรงกับสถานะ
            hover_data=["Assignee", "Project", "Priority"],
            text="Assignee" # โชว์ชื่อคนบนแท่งกราฟเลย
        )
        
        fig.update_yaxes(autorange="reversed", title="")
        fig.update_layout(
            xaxis_title="",
            height=400 + (len(df_view) * 20),
            showlegend=True,
            legend_title_text='Status',
            xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)'),
            plot_bgcolor='rgba(0,0,0,0)' # พื้นหลังใส
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tasks available for Gantt chart.")
