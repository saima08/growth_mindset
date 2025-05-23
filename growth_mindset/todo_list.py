import streamlit as st
import json
import os
from datetime import datetime, date

TODO_FILE = "todo.json"
DEFAULT_CATEGORY = "General"
PRIORITY_COLORS = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}

def load_tasks():
    if not os.path.exists(TODO_FILE):
        return []
    with open(TODO_FILE, "r") as file:
        try:
            tasks = json.load(file)
            # Convert string dates to date objects
            for task in tasks:
                if task.get('due_date'):
                    task['due_date'] = datetime.strptime(task['due_date'], "%Y-%m-%d").date()
            return tasks
        except (json.JSONDecodeError, KeyError):
            return []

def save_tasks(tasks):
    # Convert date objects to strings for JSON serialization
    formatted_tasks = []
    for task in tasks:
        task_copy = task.copy()
        if task_copy.get('due_date'):
            task_copy['due_date'] = task_copy['due_date'].isoformat()
        formatted_tasks.append(task_copy)
    
    with open(TODO_FILE, "w") as file:
        json.dump(formatted_tasks, file, indent=4)

def initialize_session_state():
    if 'editing_index' not in st.session_state:
        st.session_state.editing_index = None

def get_task_status_icon(task):
    if task['done']:
        return "✅"
    if task.get('due_date') and task['due_date'] < date.today():
        return "⏰"
    return "📌"

# Initialize session state
initialize_session_state()

# Configure page
st.set_page_config(page_title="Todo List Manager", layout="centered", page_icon="✅")
st.title("🎯 Todo List Manager")

# Sidebar for filters and actions
with st.sidebar:
    st.header("⚙️ Settings & Filters")
    show_completed = st.checkbox("Show Completed Tasks", value=True)
    sort_option = st.selectbox("Sort Tasks By", ["Priority", "Due Date", "Category"])
    
    if st.button("🚮 Clear Completed Tasks"):
        tasks = load_tasks()
        tasks = [task for task in tasks if not task['done']]
        save_tasks(tasks)
        st.rerun()

# Add Task Section
with st.expander("➕ Add New Task", expanded=True):
    with st.form("task_form"):
        new_task = st.text_input("Task Description*", help="Required field")
        col1, col2 = st.columns(2)
        with col1:
            priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
            due_date = st.date_input("Due Date", min_value=date.today())
        with col2:
            category = st.text_input("Category", value=DEFAULT_CATEGORY)
        
        if st.form_submit_button("Add Task"):
            if new_task:
                tasks = load_tasks()
                tasks.append({
                    "task": new_task,
                    "done": False,
                    "priority": priority,
                    "due_date": due_date,
                    "category": category if category else DEFAULT_CATEGORY,
                    "created_at": datetime.now().isoformat()
                })
                save_tasks(tasks)
                st.success("Task added successfully!")
                st.rerun()
            else:
                st.warning("Please enter a task description!")

# Task List Section
tasks = load_tasks()
pending_tasks = [task for task in tasks if not task['done']]
completed_tasks = [task for task in tasks if task['done']]

# Statistics
st.subheader("📊 Statistics")
stat_col1, stat_col2, stat_col3 = st.columns(3)
with stat_col1:
    st.metric("Total Tasks", len(tasks))
with stat_col2:
    st.metric("Pending", len(pending_tasks))
with stat_col3:
    st.metric("Completed", len(completed_tasks))

# Display Tasks
def display_task(task, index):
    status_icon = get_task_status_icon(task)
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        
        with col1:
            st.write(f"""
            {status_icon} **{task['task']}**  
            � {task['category']} | {PRIORITY_COLORS[task['priority']]} {task['priority']} 
            {f"📅 {task['due_date'].strftime('%a, %d %b')}" if task.get('due_date') else ""}
            """)
        
        with col2:
            if not task['done'] and st.button(f"✅ Done", key=f"done_{index}"):
                tasks[index]['done'] = True
                save_tasks(tasks)
                st.rerun()
        
        with col3:
            if st.button(f"✏️ Edit", key=f"edit_{index}"):
                st.session_state.editing_index = index
                st.rerun()
        
        with col4:
            if st.button(f"🗑️ Delete", key=f"delete_{index}"):
                tasks.pop(index)
                save_tasks(tasks)
                st.rerun()
        
        with col5:
            if task['done'] and st.button(f"↩️ Undo", key=f"undo_{index}"):
                tasks[index]['done'] = False
                save_tasks(tasks)
                st.rerun()

# Edit Task Modal
if st.session_state.editing_index is not None:
    task_to_edit = tasks[st.session_state.editing_index]
    with st.form("edit_form"):
        st.subheader("Edit Task")
        edited_task = st.text_input("Task Description", value=task_to_edit['task'])
        edited_priority = st.selectbox(
            "Priority",
            ["High", "Medium", "Low"],
            index=["High", "Medium", "Low"].index(task_to_edit['priority'])
        )
        edited_due_date = st.date_input(
            "Due Date",
            value=task_to_edit.get('due_date', date.today())
        )
        edited_category = st.text_input(
            "Category",
            value=task_to_edit.get('category', DEFAULT_CATEGORY)
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save Changes"):
                tasks[st.session_state.editing_index].update({
                    "task": edited_task,
                    "priority": edited_priority,
                    "due_date": edited_due_date,
                    "category": edited_category
                })
                save_tasks(tasks)
                st.session_state.editing_index = None
                st.rerun()
        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state.editing_index = None
                st.rerun()

# Display Pending Tasks
st.subheader("📥 Active Tasks")
if pending_tasks:
    # Sorting
    if sort_option == "Priority":
        pending_tasks.sort(key=lambda x: ["High", "Medium", "Low"].index(x['priority']))
    elif sort_option == "Due Date":
        pending_tasks.sort(key=lambda x: x.get('due_date', date.max))
    elif sort_option == "Category":
        pending_tasks.sort(key=lambda x: x['category'])

    for index, task in enumerate(pending_tasks):
        display_task(task, tasks.index(task))
else:
    st.info("No pending tasks! Add a new task above.")

# Display Completed Tasks
if show_completed and completed_tasks:
    st.subheader("📤 Completed Tasks")
    for index, task in enumerate(completed_tasks):
        display_task(task, tasks.index(task))

# Footer
st.markdown("---")
st.caption("🎯 Stay organized and productive! | Built with Streamlit")