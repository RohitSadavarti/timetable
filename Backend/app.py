import streamlit as st
import pandas as pd
import sqlite3
import random
from datetime import datetime, timedelta
import numpy as np
from io import StringIO
import re

# Page configuration
st.set_page_config(
    page_title="Automatic Timetable Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #4CAF50, #2196F3);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .timetable-cell {
        padding: 8px;
        border: 1px solid #ddd;
        text-align: center;
        background-color: #f8f9fa;
    }
    .teacher-cell {
        background-color: #e3f2fd !important;
        font-weight: bold;
    }
    .subject-cell {
        background-color: #f3e5f5 !important;
    }
    .break-cell {
        background-color: #fff3e0 !important;
        color: #ff6f00;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("""
<div class="main-header">
    <h1>🎓 Automatic Timetable Generator</h1>
    <p>Upload your database and generate optimal class schedules</p>
</div>
""", unsafe_allow_html=True)

class TimetableGenerator:
    def __init__(self):
        self.teachers = {}
        self.subjects = {}
        self.classes = {}
        self.teacher_subject_map = {}
        self.time_slots = []
        self.working_days = []
        self.timetable = {}
        
    def parse_sql_file(self, sql_content):
        """Parse SQL file and extract data"""
        try:
            # Create in-memory database
            conn = sqlite3.connect(':memory:')
            cursor = conn.cursor()
            
            # Execute SQL commands
            sql_commands = sql_content.split(';')
            for command in sql_commands:
                command = command.strip()
                if command and not command.lower().startswith('select'):
                    try:
                        cursor.execute(command)
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            st.warning(f"SQL Warning: {e}")
            
            conn.commit()
            
            # Extract data from tables
            self.extract_data_from_db(conn)
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"Error parsing SQL file: {e}")
            return False
    
    def extract_data_from_db(self, conn):
        """Extract data from database tables"""
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            
            if 'teacher' in table_name.lower():
                self.extract_teachers(cursor, table_name)
            elif 'subject' in table_name.lower():
                self.extract_subjects(cursor, table_name)
            elif 'class' in table_name.lower():
                self.extract_classes(cursor, table_name)
    
    def extract_teachers(self, cursor, table_name):
        """Extract teacher data"""
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            for row in rows:
                teacher_data = dict(zip(columns, row))
                teacher_id = teacher_data.get('Teacher_ID') or teacher_data.get('teacher_id')
                if teacher_id:
                    self.teachers[teacher_id] = {
                        'name': teacher_data.get('Teacher_Name') or teacher_data.get('name', f'Teacher {teacher_id}'),
                        'max_lectures_per_week': teacher_data.get('Max_Lectures_Per_Week') or teacher_data.get('max_lectures', 20),
                        'preferred_slots': teacher_data.get('Preferred_Slots') or teacher_data.get('preferred_slots', 'Any')
                    }
        except Exception as e:
            st.warning(f"Could not extract teachers from {table_name}: {e}")
    
    def extract_subjects(self, cursor, table_name):
        """Extract subject data"""
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            for row in rows:
                subject_data = dict(zip(columns, row))
                subject_id = subject_data.get('Subject_ID') or subject_data.get('subject_id')
                if subject_id:
                    self.subjects[subject_id] = {
                        'name': subject_data.get('Subject_Name') or subject_data.get('name', f'Subject {subject_id}'),
                        'is_common': subject_data.get('Is_Common') or subject_data.get('is_common', False),
                        'weekly_lectures': subject_data.get('Weekly_Lectures') or subject_data.get('lectures', 3)
                    }
        except Exception as e:
            st.warning(f"Could not extract subjects from {table_name}: {e}")
    
    def extract_classes(self, cursor, table_name):
        """Extract class data"""
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            for row in rows:
                class_data = dict(zip(columns, row))
                class_id = class_data.get('Class_ID') or class_data.get('class_id')
                if class_id:
                    self.classes[class_id] = {
                        'name': class_data.get('Class_Name') or class_data.get('name', class_id),
                        'subjects': []
                    }
        except Exception as e:
            st.warning(f"Could not extract classes from {table_name}: {e}")
    
    def setup_default_data(self):
        """Setup default data for demonstration"""
        # Default teachers
        self.teachers = {
            'T1': {'name': 'Prof. A', 'max_lectures_per_week': 20, 'preferred_slots': 'Any'},
            'T2': {'name': 'Prof. B', 'max_lectures_per_week': 18, 'preferred_slots': 'Any'},
            'T3': {'name': 'Prof. C', 'max_lectures_per_week': 18, 'preferred_slots': 'Any'},
            'T4': {'name': 'Prof. D', 'max_lectures_per_week': 18, 'preferred_slots': 'Any'},
            'T5': {'name': 'Prof. E', 'max_lectures_per_week': 20, 'preferred_slots': 'Any'},
            'T6': {'name': 'Prof. F', 'max_lectures_per_week': 20, 'preferred_slots': 'Any'},
        }
        
        # Default subjects
        self.subjects = {
            'S1': {'name': 'Accounting', 'is_common': True, 'weekly_lectures': 4},
            'S2': {'name': 'DBMS', 'is_common': False, 'weekly_lectures': 4},
            'S3': {'name': 'OS', 'is_common': False, 'weekly_lectures': 4},
            'S4': {'name': 'Programming', 'is_common': True, 'weekly_lectures': 4},
            'S5': {'name': 'Web Tech', 'is_common': False, 'weekly_lectures': 4},
            'S6': {'name': 'Software Eng', 'is_common': False, 'weekly_lectures': 4},
        }
        
        # Default classes
        self.classes = {
            'FYCS': {'name': 'First Year CS', 'subjects': ['S1', 'S4']},
            'SYCS': {'name': 'Second Year CS', 'subjects': ['S2', 'S6']},
            'TYCS': {'name': 'Third Year CS', 'subjects': ['S3', 'S5']},
        }
        
        # Default teacher-subject mapping
        self.teacher_subject_map = {
            ('T1', 'FYCS', 'S1'): True,
            ('T1', 'FYCS', 'S4'): True,
            ('T2', 'SYCS', 'S2'): True,
            ('T2', 'SYCS', 'S6'): True,
            ('T3', 'TYCS', 'S3'): True,
            ('T3', 'TYCS', 'S5'): True,
        }
    
    def generate_time_slots(self, start_time="09:00", end_time="17:00", lecture_duration=60, break_times=None):
        """Generate time slots for the day"""
        if break_times is None:
            break_times = [("11:00", "11:15", "Short Break"), ("13:00", "14:00", "Lunch Break")]
        
        self.time_slots = []
        current_time = datetime.strptime(start_time, "%H:%M")
        end_dt = datetime.strptime(end_time, "%H:%M")
        
        slot_num = 1
        while current_time < end_dt:
            slot_end = current_time + timedelta(minutes=lecture_duration)
            
            # Check for breaks
            is_break = False
            for break_start, break_end, break_name in break_times:
                break_start_dt = datetime.strptime(break_start, "%H:%M")
                break_end_dt = datetime.strptime(break_end, "%H:%M")
                
                if current_time <= break_start_dt < slot_end:
                    # Add break slot
                    self.time_slots.append({
                        'slot': f'Break-{len(self.time_slots)+1}',
                        'start_time': break_start,
                        'end_time': break_end,
                        'type': 'break',
                        'name': break_name
                    })
                    current_time = break_end_dt
                    is_break = True
                    break
            
            if not is_break and current_time < end_dt:
                self.time_slots.append({
                    'slot': f'P{slot_num}',
                    'start_time': current_time.strftime("%H:%M"),
                    'end_time': slot_end.strftime("%H:%M"),
                    'type': 'lecture'
                })
                current_time = slot_end
                slot_num += 1
    
    def generate_timetable(self, working_days=None):
        """Generate the complete timetable"""
        if working_days is None:
            working_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        self.working_days = working_days
        
        # Initialize timetable structure
        for class_id in self.classes:
            self.timetable[class_id] = {}
            for day in working_days:
                self.timetable[class_id][day] = {}
                for slot in self.time_slots:
                    if slot['type'] == 'lecture':
                        self.timetable[class_id][day][slot['slot']] = {
                            'subject': None,
                            'teacher': None,
                            'time': f"{slot['start_time']}-{slot['end_time']}"
                        }
                    else:
                        self.timetable[class_id][day][slot['slot']] = {
                            'subject': slot['name'],
                            'teacher': 'Break',
                            'time': f"{slot['start_time']}-{slot['end_time']}"
                        }
        
        # Schedule lectures using constraint satisfaction
        self.schedule_lectures()
    
    def schedule_lectures(self):
        """Schedule lectures using a simple greedy algorithm with constraints"""
        # Create subject-teacher assignments
        assignments = []
        for (teacher_id, class_id, subject_id), can_teach in self.teacher_subject_map.items():
            if can_teach and subject_id in self.subjects:
                lectures_needed = self.subjects[subject_id]['weekly_lectures']
                for _ in range(lectures_needed):
                    assignments.append({
                        'teacher': teacher_id,
                        'class': class_id,
                        'subject': subject_id,
                        'subject_name': self.subjects[subject_id]['name']
                    })
        
        # Track teacher and class schedules
        teacher_schedule = {tid: {day: [] for day in self.working_days} for tid in self.teachers}
        class_schedule = {cid: {day: [] for day in self.working_days} for cid in self.classes}
        
        # Shuffle assignments for randomization
        random.shuffle(assignments)
        
        # Schedule each assignment
        scheduled = []
        for assignment in assignments:
            teacher_id = assignment['teacher']
            class_id = assignment['class']
            subject_id = assignment['subject']
            
            # Find available slot
            slot_found = False
            for day in self.working_days:
                if slot_found:
                    break
                for slot_data in self.time_slots:
                    if slot_data['type'] != 'lecture':
                        continue
                    
                    slot = slot_data['slot']
                    
                    # Check if slot is available for both teacher and class
                    if (slot not in teacher_schedule[teacher_id][day] and 
                        slot not in class_schedule[class_id][day] and
                        self.timetable[class_id][day][slot]['subject'] is None):
                        
                        # Assign the slot
                        self.timetable[class_id][day][slot] = {
                            'subject': assignment['subject_name'],
                            'teacher': self.teachers[teacher_id]['name'],
                            'time': f"{slot_data['start_time']}-{slot_data['end_time']}"
                        }
                        
                        # Update schedules
                        teacher_schedule[teacher_id][day].append(slot)
                        class_schedule[class_id][day].append(slot)
                        scheduled.append(assignment)
                        slot_found = True
                        break
        
        # Report unscheduled assignments
        unscheduled = len(assignments) - len(scheduled)
        if unscheduled > 0:
            st.warning(f"⚠️ {unscheduled} lectures could not be scheduled due to constraints")

# Initialize session state
if 'generator' not in st.session_state:
    st.session_state.generator = TimetableGenerator()

# Sidebar for configuration
with st.sidebar:
    st.header("🔧 Configuration")
    
    # File upload
    st.subheader("1. Upload Database")
    uploaded_file = st.file_uploader(
        "Choose SQL file",
        type=['sql'],
        help="Upload your database SQL file"
    )
    
    if uploaded_file is not None:
        sql_content = str(uploaded_file.read(), "utf-8")
        if st.button("📤 Process SQL File"):
            with st.spinner("Processing SQL file..."):
                success = st.session_state.generator.parse_sql_file(sql_content)
                if success:
                    st.success("✅ SQL file processed successfully!")
                else:
                    st.error("❌ Failed to process SQL file")
    
    # Use default data button
    if st.button("📋 Use Default Data"):
        st.session_state.generator.setup_default_data()
        st.success("✅ Default data loaded!")
    
    st.subheader("2. Time Settings")
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time())
    with col2:
        end_time = st.time_input("End Time", value=datetime.strptime("17:00", "%H:%M").time())
    
    lecture_duration = st.slider("Lecture Duration (minutes)", 45, 90, 60, 5)
    
    st.subheader("3. Working Days")
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    working_days = []
    cols = st.columns(3)
    for i, day in enumerate(days):
        with cols[i % 3]:
            if st.checkbox(day, value=(day != 'Saturday')):
                working_days.append(day)
    
    # Generate timetable button
    if st.button("🎯 Generate Timetable", type="primary"):
        if not st.session_state.generator.teachers:
            st.error("❌ No teacher data found! Please upload SQL file or use default data.")
        else:
            with st.spinner("Generating timetable..."):
                st.session_state.generator.generate_time_slots(
                    start_time.strftime("%H:%M"),
                    end_time.strftime("%H:%M"),
                    lecture_duration
                )
                st.session_state.generator.generate_timetable(working_days)
                st.success("✅ Timetable generated successfully!")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📅 Generated Timetable")
    
    if st.session_state.generator.timetable:
        # Class selection tabs
        if st.session_state.generator.classes:
            class_tabs = st.tabs(list(st.session_state.generator.classes.keys()))
            
            for i, (class_id, class_data) in enumerate(st.session_state.generator.classes.items()):
                with class_tabs[i]:
                    st.subheader(f"📚 {class_data['name']} ({class_id})")
                    
                    if class_id in st.session_state.generator.timetable:
                        # Create timetable dataframe
                        timetable_data = []
                        
                        # Header row with time slots
                        slots = [slot for slot in st.session_state.generator.time_slots]
                        headers = ['Day'] + [f"{slot['slot']}\n{slot['start_time']}-{slot['end_time']}" for slot in slots]
                        
                        for day in st.session_state.generator.working_days:
                            row = [day]
                            for slot in slots:
                                slot_key = slot['slot']
                                if slot_key in st.session_state.generator.timetable[class_id][day]:
                                    cell_data = st.session_state.generator.timetable[class_id][day][slot_key]
                                    if cell_data['subject']:
                                        if 'Break' in str(cell_data['teacher']):
                                            cell_content = f"🍽️ {cell_data['subject']}"
                                        else:
                                            cell_content = f"📖 {cell_data['subject']}\n👨‍🏫 {cell_data['teacher']}"
                                    else:
                                        cell_content = "❌ Free"
                                else:
                                    cell_content = "❌ Free"
                                row.append(cell_content)
                            timetable_data.append(row)
                        
                        # Display as dataframe
                        df = pd.DataFrame(timetable_data, columns=headers)
                        st.dataframe(df, use_container_width=True, height=300)
    else:
        st.info("👆 Configure settings and click 'Generate Timetable' to create your schedule")

with col2:
    st.header("📊 Summary")
    
    # Display loaded data summary
    if st.session_state.generator.teachers:
        st.subheader("👨‍🏫 Teachers")
        teacher_df = pd.DataFrame.from_dict(st.session_state.generator.teachers, orient='index')
        teacher_df.index.name = 'ID'
        st.dataframe(teacher_df, use_container_width=True)
        
        st.subheader("📚 Subjects")
        if st.session_state.generator.subjects:
            subject_df = pd.DataFrame.from_dict(st.session_state.generator.subjects, orient='index')
            subject_df.index.name = 'ID'
            st.dataframe(subject_df, use_container_width=True)
        
        st.subheader("🏫 Classes")
        if st.session_state.generator.classes:
            class_df = pd.DataFrame.from_dict(st.session_state.generator.classes, orient='index')
            class_df.index.name = 'ID'
            st.dataframe(class_df, use_container_width=True)
    else:
        st.info("No data loaded yet. Please upload SQL file or use default data.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🎓 Automatic Timetable Generator | Built with Streamlit</p>
    <p><em>Upload your database, configure settings, and generate optimal class schedules!</em></p>
</div>
""", unsafe_allow_html=True)
