import streamlit as st
import pandas as pd
import datetime
import qrcode
import io
import random
import string
import plotly.express as px
import base64
import numpy as np

# ----------------------------
# Session State Initialization
# ----------------------------
if 'students_df' not in st.session_state:
    st.session_state.students_df = pd.DataFrame(columns=['Student ID', 'Name', 'Email'])

if 'attendance_df' not in st.session_state:
    st.session_state.attendance_df = pd.DataFrame(columns=['Student ID', 'Name', 'Date', 'Status', 'Method'])

if 'active_sessions' not in st.session_state:
    st.session_state.active_sessions = {}

# ----------------------------
# Page Configuration
# ----------------------------
st.set_page_config(page_title="Smart Attendance System", layout="wide")

# ----------------------------
# Helper Functions
# ----------------------------
def generate_session_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

def get_image_download_link(img, filename):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f'<a href="data:image/png;base64,{img_str}" download="{filename}">Download QR Code</a>'

# ----------------------------
# Sidebar Navigation
# ----------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", 
    ["Upload Students", "Mark Attendance", "QR Attendance", "View Records", "Attendance Stats"])

# ----------------------------
# Page: Upload Students
# ----------------------------
if page == "Upload Students":
    st.header("📤 Upload Student List")
    
    # Option 1: Upload CSV
    st.subheader("Option 1: Upload CSV File")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            required_cols = {'Name', 'Student ID', 'Email'}
            if not required_cols.issubset(df.columns):
                st.error(f"CSV must contain these columns: {required_cols}")
            else:
                st.session_state.students_df = df[['Student ID', 'Name', 'Email']]
                st.success("Student list uploaded successfully!")
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    # Option 2: Manual Entry
    st.subheader("Option 2: Manual Entry")
    with st.form("manual_entry_form"):
        cols = st.columns(3)
        student_id = cols[0].text_input("Student ID")
        name = cols[1].text_input("Name")
        email = cols[2].text_input("Email")
        
        if st.form_submit_button("Add Student"):
            if student_id and name:
                new_student = pd.DataFrame([[student_id, name, email]], 
                                           columns=['Student ID', 'Name', 'Email'])
                st.session_state.students_df = pd.concat(
                    [st.session_state.students_df, new_student], 
                    ignore_index=True
                )
                st.success("Student added!")
    
    if not st.session_state.students_df.empty:
        st.subheader("Current Student List")
        st.dataframe(st.session_state.students_df)

# ----------------------------
# Page: Manual Attendance
# ----------------------------
elif page == "Mark Attendance":
    st.header("✅ Manual Attendance")
    
    if st.session_state.students_df.empty:
        st.warning("No students found. Please upload student list first.")
    else:
        session_date = st.date_input("Session Date", datetime.date.today())
        st.subheader("Mark Attendance")
        attendance_records = []
        
        for _, student in st.session_state.students_df.iterrows():
            status = st.checkbox(
                f"{student['Name']} (ID: {student['Student ID']})",
                value=True,
                key=f"att_{student['Student ID']}_{session_date}"
            )
            attendance_records.append({
                'Student ID': student['Student ID'],
                'Name': student['Name'],
                'Date': session_date,
                'Status': 'Present' if status else 'Absent',
                'Method': 'Manual'
            })
        
        if st.button("Save Attendance"):
            new_records = pd.DataFrame(attendance_records)
            st.session_state.attendance_df = pd.concat(
                [st.session_state.attendance_df, new_records],
                ignore_index=True
            )
            st.success(f"Attendance saved for {session_date}!")

# ----------------------------
# Page: QR Attendance
# ----------------------------
elif page == "QR Attendance":
    st.header("📱 QR Code Attendance")
    
    if st.session_state.students_df.empty:
        st.warning("No students found. Please upload student list first.")
    else:
        st.subheader("Current Active Sessions")
        
        if st.button("Create New Session"):
            session_id = generate_session_id()
            st.session_state.active_sessions[session_id] = {
                'created_at': datetime.datetime.now(),
                'expires_at': datetime.datetime.now() + datetime.timedelta(hours=1),
                'checked_in': []
            }
            st.success(f"Created new session: {session_id}")
        
        for session_id, session_data in st.session_state.active_sessions.items():
            with st.expander(f"Session: {session_id}"):
                cols = st.columns([3, 1, 1])
                with cols[0]:
                    qr_url = f"http://your-attendance-server.com/checkin?session={session_id}"
                    qr_img = create_qr_code(qr_url)
                    st.image(np.array(qr_img), caption=f"Scan to check in - Session {session_id}", width=200)
                    st.markdown(get_image_download_link(qr_img, f"attendance_qr_{session_id}.png"), unsafe_allow_html=True)
                
                with cols[1]:
                    st.write(f"Created: {session_data['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"Expires: {session_data['expires_at'].strftime('%Y-%m-%d %H:%M')}")
                
                with cols[2]:
                    if st.button(f"Close Session", key=f"close_{session_id}"):
                        present_ids = session_data['checked_in']
                        all_ids = st.session_state.students_df['Student ID'].tolist()
                        absent_ids = [id for id in all_ids if id not in present_ids]
                        
                        new_records = [
                            {
                                'Student ID': student_id,
                                'Name': st.session_state.students_df.loc[
                                    st.session_state.students_df['Student ID'] == student_id, 'Name'
                                ].values[0],
                                'Date': session_data['created_at'].date(),
                                'Status': 'Absent',
                                'Method': 'QR'
                            }
                            for student_id in absent_ids
                        ]
                        
                        if new_records:
                            st.session_state.attendance_df = pd.concat(
                                [st.session_state.attendance_df, pd.DataFrame(new_records)],
                                ignore_index=True
                            )
                        
                        del st.session_state.active_sessions[session_id]
                        st.success(f"Session {session_id} closed. Absentees recorded.")
                
                st.subheader("Simulate Student Check-In")
                student_id = st.selectbox(
                    "Select student to check in",
                    st.session_state.students_df['Student ID'].tolist(),
                    key=f"sim_checkin_{session_id}"
                )
                
                if st.button("Simulate Check-In", key=f"checkin_{session_id}"):
                    if student_id not in session_data['checked_in']:
                        session_data['checked_in'].append(student_id)
                        student = st.session_state.students_df.loc[
                            st.session_state.students_df['Student ID'] == student_id
                        ].iloc[0]
                        new_record = {
                            'Student ID': student_id,
                            'Name': student['Name'],
                            'Date': session_data['created_at'].date(),
                            'Status': 'Present',
                            'Method': 'QR'
                        }
                        st.session_state.attendance_df = pd.concat(
                            [st.session_state.attendance_df, pd.DataFrame([new_record])],
                            ignore_index=True
                        )
                        st.success(f"{student['Name']} checked in successfully!")
                    else:
                        st.warning("This student has already checked in")
                
                st.write("Checked-in students:")
                if session_data['checked_in']:
                    present_df = st.session_state.students_df[
                        st.session_state.students_df['Student ID'].isin(session_data['checked_in'])
                    ]
                    st.dataframe(present_df[['Student ID', 'Name']])
                else:
                    st.write("No students checked in yet")

# ----------------------------
# Page: View Records
# ----------------------------
elif page == "View Records":
    st.header("📄 Attendance Records")
    
    if not st.session_state.attendance_df.empty:
        st.dataframe(st.session_state.attendance_df)
        
        st.subheader("Export Data")
        export_format = st.selectbox("Format", ["CSV", "Excel"])
        
        if export_format == "CSV":
            csv = st.session_state.attendance_df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                f"attendance_{datetime.date.today()}.csv",
                "text/csv"
            )
        else:
            excel_buffer = io.BytesIO()
            st.session_state.attendance_df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_buffer.seek(0)
            st.download_button(
                "Download Excel",
                excel_buffer,
                f"attendance_{datetime.date.today()}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("No attendance records found.")

# ----------------------------
# Page: Attendance Stats
# ----------------------------
elif page == "Attendance Stats":
    st.header("📊 Attendance Statistics")
    
    if not st.session_state.attendance_df.empty:
        stats_df = st.session_state.attendance_df.groupby(['Student ID', 'Name'])['Status'] \
            .value_counts().unstack(fill_value=0)
        
        stats_df['Present'] = stats_df.get('Present', 0)
        stats_df['Absent'] = stats_df.get('Absent', 0)
        stats_df['Total Sessions'] = stats_df['Present'] + stats_df['Absent']
        stats_df['Attendance %'] = (stats_df['Present'] / stats_df['Total Sessions'] * 100).round(1)
        
        st.subheader("Student Attendance Summary")
        st.dataframe(stats_df)
        
        st.subheader("Visualizations")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Attendance Distribution**")
            fig1 = px.pie(
                stats_df.reset_index(),
                values='Present',
                names='Name',
                hover_data=['Student ID']
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.write("**Attendance Percentage**")
            fig2 = px.bar(
                stats_df.reset_index().sort_values('Attendance %'),
                x='Attendance %',
                y='Name',
                orientation='h'
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader("Attendance Method Breakdown")
        method_df = st.session_state.attendance_df.groupby('Method')['Status'].count().reset_index()
        fig3 = px.pie(method_df, values='Status', names='Method')
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("No attendance records found.")

# ----------------------------
# Sample Data for Development
# ----------------------------
if st.session_state.students_df.empty:
    st.session_state.students_df = pd.DataFrame({
        'Student ID': ['S001', 'S002', 'S003'],
        'Name': ['John Doe', 'Jane Smith', 'Robert Brown'],
        'Email': ['john@edu.com', 'jane@edu.com', 'robert@edu.com']
    })
