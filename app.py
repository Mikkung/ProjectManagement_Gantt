import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="My Project Manager", layout="wide")

st.title("🚀 My Custom Project Management Tool")

# 1. สร้าง Data ตั้งต้น (หากยังไม่มีข้อมูลใน Session State)
if "data" not in st.session_state:
    # สร้าง DataFrame ตัวอย่าง
    default_data = {
        "Project": ["Website Redesign", "Website Redesign", "Mobile App"],
        "Task": ["Design UI", "Develop Backend", "Setup API"],
        "Subtask": ["Homepage", "Database Schema", "Auth System"],
        "Start Date": [date.today(), date.today() + timedelta(days=2), date.today()],
        "Due Date": [date.today() + timedelta(days=5), date.today() + timedelta(days=10), date.today() + timedelta(days=7)],
        "Priority": ["High", "Medium", "High"],
        "Status": ["In Progress", "Not Started", "In Progress"],
        "Assigned To": ["Dev A", "Dev B", "Dev A"]
    }
    st.session_state.data = pd.DataFrame(default_data)

# 2. ส่วนการกรอกข้อมูล (Editable Grid เหมือน Excel/ClickUp)
st.subheader("📝 Task List (Editable)")
st.caption("คุณสามารถแก้ไขข้อมูล เพิ่มแถว หรือลบแถวได้โดยตรงจากตารางด้านล่าง")

# ตั้งค่า Configuration ของแต่ละคอลัมน์เพื่อให้กรอกง่ายขึ้น
column_config = {
    "Start Date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"),
    "Due Date": st.column_config.DateColumn("Due Date", format="YYYY-MM-DD"),
    "Priority": st.column_config.SelectboxColumn("Priority", options=["High", "Medium", "Low"], required=True),
    "Status": st.column_config.SelectboxColumn("Status", options=["Not Started", "In Progress", "Done", "Blocked"], required=True),
    "Project": st.column_config.TextColumn("Project", required=True),
}

# แสดงตารางแบบแก้ไขได้ (Data Editor)
edited_df = st.data_editor(
    st.session_state.data,
    num_rows="dynamic", # อนุญาตให้เพิ่มแถวได้
    column_config=column_config,
    use_container_width=True,
    key="editor"
)

# อัปเดตข้อมูลกลับไปยัง Session State เมื่อมีการแก้ไข
st.session_state.data = edited_df

# แปลงวันที่ให้เป็น datetime object เพื่อให้ Plotly ใช้งานได้
plot_df = edited_df.copy()
plot_df["Start Date"] = pd.to_datetime(plot_df["Start Date"])
plot_df["Due Date"] = pd.to_datetime(plot_df["Due Date"])

# กรองข้อมูลเอาเฉพาะ Task ที่มีวันที่ครบถ้วนมาแสดง
valid_tasks = plot_df.dropna(subset=["Start Date", "Due Date"])

st.divider()

# 3. การแสดงผล (Visualization Views)
tab1, tab2 = st.tabs(["📊 Gantt Chart", "📅 Calendar View"])

with tab1:
    st.subheader("Project Timeline")
    if not valid_tasks.empty:
        # สร้าง Gantt Chart ด้วย Plotly Timeline
        fig = px.timeline(
            valid_tasks, 
            x_start="Start Date", 
            x_end="Due Date", 
            y="Task", 
            color="Status", # แยกสีตามสถานะ
            hover_data=["Project", "Subtask", "Assigned To", "Priority"],
            title="Gantt Chart Overview",
            color_discrete_map={"Not Started": "gray", "In Progress": "blue", "Done": "green", "Blocked": "red"}
        )
        # ปรับแกน Y ให้เรียงลำดับจากบนลงล่าง (ปกติ Plotly จะเรียงล่างขึ้นบน)
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(xaxis_title="Date", yaxis_title="Tasks")
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("กรุณากรอกวันที่ Start และ Due Date ให้ครบถ้วนเพื่อแสดง Gantt Chart")

with tab2:
    st.subheader("Upcoming Deadlines")
    # แสดงมุมมองแบบปฏิทินรายการ (Agenda View)
    if not valid_tasks.empty:
        # เรียงตามวันครบกำหนด
        calendar_view = valid_tasks.sort_values(by="Due Date")
        
        for index, row in calendar_view.iterrows():
            with st.expander(f"{row['Due Date'].date()} : {row['Task']} ({row['Project']})"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Status", row['Status'])
                col2.metric("Priority", row['Priority'])
                col3.write(f"**Assigned to:** {row['Assigned To']}\n\n**Subtask:** {row['Subtask']}")
    else:
        st.write("ไม่มีข้อมูล Task")