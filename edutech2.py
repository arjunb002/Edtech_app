import streamlit as st
import re
from datetime import datetime
import sqlite3
from streamlit_ace import st_ace

# Initialize database
def init_db():
    conn = sqlite3.connect('student_projects.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, name TEXT, email TEXT, institution TEXT, 
                  role TEXT, join_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects
                 (id INTEGER PRIMARY KEY, title TEXT, description TEXT, 
                  created_by INTEGER, created_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS project_members
                 (project_id INTEGER, user_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY, project_id INTEGER, sender_id INTEGER,
                  message TEXT, sent_date TEXT)''')
    conn.commit()
    conn.close()

def is_edu_email(email):
    # Check if email ends with .edu or similar educational domains
    edu_domains = ['.edu', '.ac.', '.edu.']
    return any(domain in email.lower() for domain in edu_domains)

def main():
    st.title("Student Project Collaboration Platform (Prototype)")
    st.sidebar.image("https://img.icons8.com/color/96/000000/student-center.png", width=100)
    
    # Initialize database
    init_db()
    
    # Session state for login
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    # Always fetch user info if logged in
    if st.session_state.user_id is not None:
        conn = sqlite3.connect('student_projects.db')
        c = conn.cursor()
        user = c.execute("SELECT name, role FROM users WHERE id=?", (st.session_state.user_id,)).fetchone()
        conn.close()
        if user:
            st.session_state.user_info = {'name': user[0], 'role': user[1]}
        else:
            st.session_state.user_info = None
    else:
        st.session_state.user_info = None

    # Show profile in the top right if logged in
    if st.session_state.user_info:
        col1, col2 = st.columns([6, 1])
        with col2:
            name = st.session_state.user_info['name']
            role = st.session_state.user_info['role']
            badge_color = "#4CAF50" if role.lower() == "student" else "#2196F3"
            st.markdown(
                f"<div style='text-align:right;'>"
                f"<b>{name}</b> <span style='background-color:{badge_color};color:white;padding:2px 8px;border-radius:8px;font-size:0.9em;'>{role}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

    # Sidebar for navigation
    if st.session_state.user_id is None:
        menu = "Login/Register"
    else:
        menu_options = ["Create Project", "Browse Projects", "My Projects", "Messages", "Community", "Logout"]
        menu = st.sidebar.selectbox("Menu", menu_options)
    
    if menu == "Login/Register":
        col1, col2 = st.columns(2)
        
        with col1:
            st.header("Login")
            with st.form("login_form"):
                login_email = st.text_input("Email")
                if st.form_submit_button("Login"):
                    conn = sqlite3.connect('student_projects.db')
                    c = conn.cursor()
                    user = c.execute("SELECT id FROM users WHERE email=?", (login_email,)).fetchone()
                    conn.close()
                    if user:
                        st.session_state.user_id = user[0]
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("User not found")
        
        with col2:
            st.header("Register")
            with st.form("registration_form"):
                name = st.text_input("Full Name")
                email = st.text_input("Educational Email")
                institution = st.text_input("Institution Name")
                role = st.selectbox("Role", ["Student", "Teacher"])
                
                if st.form_submit_button("Register"):
                    if not is_edu_email(email):
                        st.error("Please use an educational email address")
                    else:
                        conn = sqlite3.connect('student_projects.db')
                        c = conn.cursor()
                        c.execute("INSERT INTO users (name, email, institution, role, join_date) VALUES (?, ?, ?, ?, ?)",
                                (name, email, institution, role, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        conn.close()
                        st.success("Registration successful! Please login.")

    elif menu == "Create Project":
        st.header("Create New Project")
        
        with st.form("project_form"):
            title = st.text_input("Project Title")
            description = st.text_area("Project Description")
            skills_needed = st.multiselect("Skills Needed", 
                ["Programming", "Design", "Writing", "Research", "Data Analysis"])
            max_members = st.number_input("Maximum Team Members", min_value=2, value=5)
            
            if st.form_submit_button("Create Project"):
                conn = sqlite3.connect('student_projects.db')
                c = conn.cursor()
                c.execute("INSERT INTO projects (title, description, created_by, created_date) VALUES (?, ?, ?, ?)",
                         (title, description, st.session_state.user_id, datetime.now().strftime("%Y-%m-%d")))
                project_id = c.lastrowid
                # Add creator as first member
                c.execute("INSERT INTO project_members (project_id, user_id) VALUES (?, ?)",
                         (project_id, st.session_state.user_id))
                conn.commit()
                conn.close()
                st.success("Project created successfully!")

    elif menu == "Browse Projects":
        st.header("Available Projects")
        
        # Search and filter
        search = st.text_input("Search projects")
        
        conn = sqlite3.connect('student_projects.db')
        c = conn.cursor()
        if search:
            projects = c.execute("SELECT * FROM projects WHERE title LIKE ? OR description LIKE ?",
                               (f"%{search}%", f"%{search}%")).fetchall()
        else:
            projects = c.execute("SELECT * FROM projects").fetchall()
        
        for project in projects:
            with st.expander(f"Project: {project[1]}"):
                st.write(f"Description: {project[2]}")
                creator = c.execute("SELECT name FROM users WHERE id=?", (project[3],)).fetchone()
                st.write(f"Created by: {creator[0]}")
                
                # Check if user is already a member
                is_member = c.execute("""
                    SELECT 1 FROM project_members 
                    WHERE project_id=? AND user_id=?
                """, (project[0], st.session_state.user_id)).fetchone()
                
                if not is_member:
                    if st.button(f"Join Project {project[0]}"):
                        c.execute("INSERT INTO project_members (project_id, user_id) VALUES (?, ?)",
                                 (project[0], st.session_state.user_id))
                        conn.commit()
                        st.success("Joined project successfully!")
                else:
                    st.info("You are already a member of this project")
                
                # Online Code Editor (Prototype)
                st.subheader("Online Code Editor (Prototype)")
                st.caption("Note: Code is not saved. For demo purposes only.")
                code = st_ace(
                    placeholder="Write your code here...",
                    language="python",
                    theme="monokai",
                    key=f"ace_browse_{project[0]}"
                )
                if code:
                    st.code(code, language="python")
        
        conn.close()

    elif menu == "My Projects":
        st.header("My Projects")
        
        conn = sqlite3.connect('student_projects.db')
        c = conn.cursor()
        my_projects = c.execute("""
            SELECT p.*, COUNT(pm.user_id) as member_count 
            FROM projects p
            JOIN project_members pm ON p.id = pm.project_id
            WHERE p.id IN (
                SELECT project_id FROM project_members WHERE user_id=?
            )
            GROUP BY p.id
        """, (st.session_state.user_id,)).fetchall()
        
        for project in my_projects:
            with st.expander(f"Project: {project[1]}"):
                st.write(f"Description: {project[2]}")
                st.write(f"Start Date: {project[4]}")
                
                # Show team members
                members = c.execute("""
                    SELECT u.name, u.role FROM users u
                    JOIN project_members pm ON u.id = pm.user_id
                    WHERE pm.project_id=?
                """, (project[0],)).fetchall()
                
                st.write("Team:")
                for member in members:
                    st.write(f"- {member[0]} ({member[1]})")
                
                # Online Code Editor (Prototype)
                st.subheader("Online Code Editor (Prototype)")
                st.caption("Note: Code is not saved. For demo purposes only.")
                code = st_ace(
                    placeholder="Write your code here...",
                    language="python",
                    theme="monokai",
                    key=f"ace_my_{project[0]}"
                )
                if code:
                    st.code(code, language="python")
        
        conn.close()

    elif menu == "Messages":
        st.header("Project Messages")
        
        conn = sqlite3.connect('student_projects.db')
        c = conn.cursor()
        
        # Get user's projects
        projects = c.execute("""
            SELECT p.id, p.title FROM projects p
            JOIN project_members pm ON p.id = pm.project_id
            WHERE pm.user_id=?
        """, (st.session_state.user_id,)).fetchall()
        
        if projects:
            selected_project = st.selectbox("Select Project", 
                [p[1] for p in projects], key='selected_project')
            project_id = projects[[p[1] for p in projects].index(selected_project)][0]
            
            # Show messages
            messages = c.execute("""
                SELECT m.message, u.name, m.sent_date 
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.project_id=?
                ORDER BY m.sent_date DESC
            """, (project_id,)).fetchall()
            
            st.write("Messages:")
            for i, msg in enumerate(messages):
                st.text_area(
                    "",
                    f"{msg[1]} ({msg[2]}): {msg[0]}",
                    height=50,
                    disabled=True,
                    key=f"msg_{i}_{msg[2]}"
                )
            
            # Before the form, check if we need to clear the text area
            if "clear_new_message" in st.session_state and st.session_state["clear_new_message"]:
                st.session_state["new_message"] = ""
                st.session_state["clear_new_message"] = False

            with st.form("message_form"):
                message = st.text_area("New Message", key="new_message")
                if st.form_submit_button("Send"):
                    if message.strip():
                        c.execute(
                            "INSERT INTO messages (project_id, sender_id, message, sent_date) VALUES (?, ?, ?, ?)",
                            (project_id, st.session_state.user_id, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        )
                        conn.commit()
                        st.success("Message sent!")
                        st.session_state["clear_new_message"] = True  # Set flag to clear on next run
                        st.rerun()
                    else:
                        st.warning("Cannot send an empty message.")
        else:
            st.info("Join some projects to start messaging!")
        
        conn.close()

    elif menu == "Community":
        st.header("Community: Students & Teachers")
        conn = sqlite3.connect('student_projects.db')
        c = conn.cursor()
        users = c.execute("SELECT name, institution, role FROM users").fetchall()
        conn.close()
        students = [u for u in users if u[2].lower() == "student"]
        teachers = [u for u in users if u[2].lower() == "teacher"]

        st.subheader("Students")
        for s in students:
            st.markdown(f"**{s[0]}** ({s[1]}) <span style='background-color:#4CAF50;color:white;padding:2px 8px;border-radius:8px;font-size:0.8em;'>Student</span>", unsafe_allow_html=True)

        st.subheader("Teachers")
        for t in teachers:
            st.markdown(f"**{t[0]}** ({t[1]}) <span style='background-color:#2196F3;color:white;padding:2px 8px;border-radius:8px;font-size:0.8em;'>Teacher</span>", unsafe_allow_html=True)

    elif menu == "Logout":
        st.session_state.user_id = None
        st.success("Logged out successfully!")
        st.rerun()

if __name__ == "__main__":
    main()

