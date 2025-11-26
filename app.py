import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="My Project Manager V2", layout="wide")
st.title("🚀 Interactive Project Manager")

# ---------------------------------------------------------
# 1. DATA INITIALIZATION
# ---------------------------------------------------------
if "data" not in st.session_state:
    default_data = {
        "Project": ["Website Redesign", "Website Redesign", "Mobile App", "Mobile App"],
        "Task": ["Frontend", "Frontend", "Backend", "Backend"],
        "Subtask": ["Homepage Design", "About Page", "API Setup", "Database Config"],
        "Start Date": [date.today(), date.today() + timedelta(days=2), date.today(), date.today() + timedelta(days=3)],
        "Due Date": [date.today() + timedelta(days=5), date.today() + timedelta(days=6), date.today() + timedelta(days=7), date.today() + timedelta(days=8)],
        "Priority": ["High", "Medium", "High", "Critical"],
        "Status": ["In Progress", "Not Started", "In Progress", "Blocked"],
        "Assigned To": ["Dev A", "Dev A", "Dev B", "Dev B"]
    }
    st.session_state.data = pd.DataFrame(default_data)

# แปลงข้อมูลวันที่ให้ถูกต้องเสมอ
st.session_state.data["Start Date"] = pd.to_datetime(st.session_state.data["Start Date"])
st.session_state.data["Due Date"] = pd.to_datetime(st.session_state.data["Due Date"])

# ---------------------------------------------------------
# 2. SIDEBAR CONTROLS (ตัวควบคุมการแสดงผล)
# ---------------------------------------------------------
st.sidebar.header("⚙️ Display Settings")

# 2.1 Filter by Project
unique_projects = st.session_state.data["Project"].unique()
selected_projects = st.sidebar.multiselect(
    "Filter by Project", 
    options=unique_projects, 
    default=unique_projects
)

# 2.2 Filter by Status
unique_status = st.session_state.data["Status"].unique()
selected_status = st.sidebar.multiselect(
    "Filter by Status",
    options=unique_status,
    default=unique_status
)

# 2.3 Toggle View Mode (เปิด/ปิด Subtask)
st.sidebar.divider()
show_subtasks = st.sidebar.toggle("Show Subtasks (Expand Details)", value=True)

# ---------------------------------------------------------
# 3. DATA PROCESSING
# ---------------------------------------------------------

# กรองข้อมูลตามที่เลือกใน Sidebar
filtered_df = st.session_state.data.copy()
filtered_df = filtered_df[filtered_df["Project"].isin(selected_projects)]
filtered_df = filtered_df[filtered_df["Status"].isin(selected_status)]

# Logic การแสดงผล (Expand vs Collapse)
if show_subtasks:
    # --- กรณีแสดง Subtasks (ละเอียด) ---
    plot_data = filtered_df.copy()
    # สร้าง label ใหม่ให้แกน Y แสดงชื่อ Task คู่กับ Subtask
    plot_data["Y_Label"] = plot_data["Task"] + " : " + plot_data["Subtask"]
    y_axis_col = "Y_Label"
    color_col = "Status"
    title_text = "Detailed View (Subtasks)"
else:
    # --- กรณีปิด Subtasks (รวมกลุ่ม) ---
    # Group ข้อมูลตาม Task หลัก และหา Start ต่ำสุด และ Due สูงสุด
    plot_data = filtered_df.groupby(["Project", "Task"], as_index=False).agg({
        "Start Date": "min",
        "Due Date": "max",
        "Status": "first", # เอาสถานะของงานแรกมาโชว์ (หรือจะปรับ logic อื่นก็ได้)
        "Assigned To": lambda x: ", ".join(set(x)) # รวมชื่อคนรับผิดชอบ
    })
    y_axis_col = "Task"
    color_col = "Project" # เปลี่ยนสีตาม Project แทน เพราะ Status อาจจะปนกัน
    title_text = "High-Level View (Main Tasks Only)"

# ---------------------------------------------------------
# 4. MAIN INTERFACE
# ---------------------------------------------------------

# ส่วน Data Editor (ยังคงให้แก้ไขได้เฉพาะข้อมูลดิบ)
with st.expander("📝 Edit Source Data", expanded=False):
    column_config = {
        "Start Date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"),
        "Due Date": st.column_config.DateColumn("Due Date", format="YYYY-MM-DD"),
        "Priority": st.column_config.SelectboxColumn("Priority", options=["Critical", "High", "Medium", "Low"]),
        "Status": st.column_config.SelectboxColumn("Status", options=["Not Started", "In Progress", "Done", "Blocked"]),
    }
    
    edited_df = st.data_editor(
        st.session_state.data,
        num_rows="dynamic",
        column_config=column_config,
        use_container_width=True,
        key="editor"
    )
    # Save กลับเข้า Session
    if not edited_df.equals(st.session_state.data):
        st.session_state.data = edited_df
        st.rerun() # รีเฟรชหน้าทันทีที่แก้ข้อมูล

st.divider()

# ส่วนแสดงผล Gantt Chart
st.subheader(f"📊 {title_text}")

if not plot_data.empty:
    # ตรวจสอบว่ามีข้อมูลวันที่ครบไหม
    plot_data = plot_data.dropna(subset=["Start Date", "Due Date"])
    
    fig = px.timeline(
        plot_data, 
        x_start="Start Date", 
        x_end="Due Date", 
        y=y_axis_col,
        color=color_col,
        hover_data=plot_data.columns, # โชว์ข้อมูลทั้งหมดเมื่อเอาเมาส์ชี้
        height=400 + (len(plot_data) * 20) # ปรับความสูงกราฟตามจำนวนงาน
    )
    
    fig.update_yaxes(autorange="reversed", title="") # เรียงจากบนลงล่าง
    fig.update_layout(
        xaxis_title="Timeline",
        showlegend=True,
        # เพิ่มเส้นตารางให้อ่านง่ายขึ้น
        xaxis=dict(showgrid=True, gridcolor='LightGrey', tickformat="%d %b"),
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No tasks found matching your filters.")
