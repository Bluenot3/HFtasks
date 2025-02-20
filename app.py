import gradio as gr
import threading
import time
from datetime import datetime
from report_generator import (
    generate_csv_report,
    generate_xlsx_report,
    generate_pdf_report,
    generate_diagram_report,
)
import cohere

# Initialize the Cohere client using your provided API key.
COHERE_API_KEY = "COHORE_API_KEY"
co = cohere.Client(COHERE_API_KEY)

# Define labeled examples for classification as dictionaries.
cohere_examples = [
    {"text": "generate a report on unemployment", "label": "report"},
    {"text": "create a report on market trends", "label": "report"},
    {"text": "generate diagram of sales data", "label": "diagram"},
    {"text": "create a diagram of quarterly revenue", "label": "diagram"}
]

def cohere_parse_command(command):
    """Uses Cohere's classify endpoint to determine the intent of the command."""
    try:
        response = co.classify(
            model="large",
            inputs=[command],
            examples=cohere_examples
        )
        prediction = response.classifications[0].prediction
        return prediction
    except Exception as e:
        print("Cohere classification error, falling back to keyword search:", e)
        lower = command.lower()
        if "diagram" in lower:
            return "diagram"
        elif "report" in lower:
            return "report"
        else:
            return "unknown"

# Global containers for pending tasks and generated files.
task_bucket = []      # Queue of tasks waiting to be processed.
generated_files = []  # Global list of filenames generated.
bucket_lock = threading.Lock()

def process_single_task(task):
    """Process one task with a countdown timer and update its details."""
    print(f"[{datetime.now()}] Processing task: {task['command']}")
    # Simulate processing delay.
    for remaining in range(5, 0, -1):
        task["timer"] = remaining
        time.sleep(1)
    intent = cohere_parse_command(task["command"])
    cmd = task["command"].lower()
    # Pass the entire command as "subject" for dynamic content.
    if intent == "report":
        if "csv" in cmd:
            filename = generate_csv_report(subject=task["command"])
            task["result"] = f"CSV report generated for '{task['command']}'"
        elif "xlsx" in cmd:
            filename = generate_xlsx_report(subject=task["command"])
            task["result"] = f"XLSX report generated for '{task['command']}'"
        else:
            filename = generate_pdf_report(subject=task["command"])
            task["result"] = f"PDF report generated for '{task['command']}'"
    elif intent == "diagram":
        filename = generate_diagram_report()
        task["result"] = f"Diagram generated for '{task['command']}'"
    else:
        filename = None
        task["result"] = f"Unrecognized command: {task['command']}"
    if filename:
        task["file"] = filename
        generated_files.append(filename)
    task["completed_at"] = datetime.now().strftime("%H:%M:%S")
    task["status"] = "Complete"
    task["details"] = f"Task '{task['command']}' processed with result: {task['result']}"
    print(f"[{datetime.now()}] Task completed: {task}")

def background_task_processor():
    """Continuously monitors the task bucket and spawns a new thread per task."""
    while True:
        time.sleep(1)
        task = None
        with bucket_lock:
            if task_bucket:
                task = task_bucket.pop(0)
        if task:
            task["status"] = "In Progress"
            threading.Thread(target=process_single_task, args=(task,), daemon=True).start()

def submit_task(command, current_tasks):
    """Adds a new task when the user clicks Submit (command remains visible)."""
    if command.strip() == "":
        return current_tasks, generated_files, command
    new_task = {
        "command": command,
        "submitted_at": datetime.now().strftime("%H:%M:%S"),
        "timer": "",
        "result": "",
        "file": "",
        "completed_at": "",
        "status": "Pending",
        "details": ""
    }
    with bucket_lock:
        task_bucket.append(new_task)
        current_tasks.append(new_task)
    return current_tasks, generated_files, command

def build_tasks_html(tasks):
    """Builds an HTML table showing task details."""
    html = """
    <style>
      table {width: 100%; border-collapse: collapse; margin: 10px 0; font-family: Arial, sans-serif;}
      th, td {border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 14px;}
      th {background-color: #f2f2f2;}
      .Complete {background-color: #d4edda;}
      .In\\ Progress {background-color: #fff3cd;}
      .Pending {background-color: #f8d7da;}
    </style>
    <table>
      <tr>
        <th>Submitted At</th>
        <th>Command</th>
        <th>Status</th>
        <th>Timer</th>
        <th>Result</th>
        <th>Completed At</th>
        <th>Details</th>
        <th>Done</th>
      </tr>
    """
    for task in tasks:
        status = task.get("status", "Pending")
        timer = task.get("timer", "")
        result = task.get("result", "")
        completed_at = task.get("completed_at", "")
        details = task.get("details", "")
        checkbox = "<input type='checkbox' disabled " + ("checked" if status == "Complete" else "") + ">"
        html += (
            f"<tr class='{status}'>"
            f"<td>{task.get('submitted_at','')}</td>"
            f"<td>{task.get('command','')}</td>"
            f"<td>{status}</td>"
            f"<td>{timer}</td>"
            f"<td>{result}</td>"
            f"<td>{completed_at}</td>"
            f"<td>{details}</td>"
            f"<td>{checkbox}</td>"
            f"</tr>"
        )
    html += "</table>"
    return html

def refresh_ui(tasks, files):
    """Refreshes the UI by rebuilding the task list and updating the files state."""
    # Update files state from the global generated_files list.
    files = generated_files[:]
    tasks_html = build_tasks_html(tasks)
    return tasks, files, tasks_html, files

def update_dropdown(files):
    """Updates the dropdown choices for preview from the list of generated files."""
    return files

def preview_file(file_path):
    """Returns HTML for previewing the file based on its type."""
    if not file_path:
        return "No file selected."
    if file_path.endswith(".png"):
        return f'<img src="{file_path}" style="max-width:100%;">'
    elif file_path.endswith(".pdf"):
        return f'<embed src="{file_path}" type="application/pdf" width="100%" height="600px">'
    elif file_path.endswith(".csv") or file_path.endswith(".xlsx"):
        return f'<a href="{file_path}" target="_blank">Download and view file: {file_path}</a>'
    else:
        return f'<a href="{file_path}" target="_blank">Download file: {file_path}</a>'

def main():
    threading.Thread(target=background_task_processor, daemon=True).start()
    
    with gr.Blocks(css="""
        body {background-color: #121212; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #fdfdfd; margin: 0; padding: 0;}
        .gradio-container {max-width: 900px; margin: auto; padding: 20px; background-color: #1e1e1e; border-radius: 8px; box-shadow: 0px 0px 15px rgba(0,0,0,0.5);}
        .title {text-align: center; color: #fdfdfd; margin-bottom: 20px;}
        .section-title {color: #fdfdfd; margin-top: 30px; border-bottom: 2px solid #fdfdfd; padding-bottom: 5px;}
    """) as demo:
        gr.Markdown("<h1 class='title'>Advanced Multi-Task Application</h1>")
        gr.Markdown(
            "Enter a task command below or click one of the sample commands. For example: <i>generate a report on unemployment in the United States in 2024</i>.<br>"
            "Tasks run concurrently and once complete, files will appear in the <b>Completed Downloads</b> section.<br>"
            "You can also preview a completed file in the <b>File Preview</b> section."
        )
        
        with gr.Row():
            with gr.Column(scale=8):
                command_input = gr.Textbox(label="Task Command", placeholder="Type your command here...", lines=2)
            with gr.Column(scale=2):
                submit_btn = gr.Button("Submit", variant="primary")
        
        gr.Markdown("<h3 class='section-title'>Sample Commands</h3>")
        with gr.Row():
            sample1 = gr.Button("Report on US Unemployment 2024")
            sample2 = gr.Button("Diagram of Sales Data")
            sample3 = gr.Button("CSV Report of User Activity")
        
        gr.Markdown("<h3 class='section-title'>Task List</h3>")
        tasks_html_output = gr.HTML(label="Tasks Overview")
        
        gr.Markdown("<h3 class='section-title'>Completed Downloads</h3>")
        file_output = gr.Files(label="Download Files", file_count="multiple")
        
        gr.Markdown("<h3 class='section-title'>File Preview</h3>")
        with gr.Row():
            file_dropdown = gr.Dropdown(choices=[], label="Select File for Preview")
            preview_btn = gr.Button("Preview File")
        preview_output = gr.HTML(label="File Preview")
        
        with gr.Row():
            refresh_btn = gr.Button("Manual Refresh")
            auto_refresh_toggle = gr.Checkbox(value=True, label="Auto Refresh Task List")
        
        tasks_state = gr.State([])
        files_state = gr.State([])
        
        # Submit: add task then immediately refresh UI.
        submit_btn.click(
            submit_task,
            inputs=[command_input, tasks_state],
            outputs=[tasks_state, files_state, command_input]
        ).then(
            refresh_ui,
            inputs=[tasks_state, files_state],
            outputs=[tasks_state, files_state, tasks_html_output, file_output]
        )
        sample1.click(lambda: "generate a report on unemployment in the United States in 2024", None, command_input)
        sample2.click(lambda: "generate diagram of sales data", None, command_input)
        sample3.click(lambda: "generate csv report of user activity", None, command_input)
        refresh_btn.click(
            refresh_ui,
            inputs=[tasks_state, files_state],
            outputs=[tasks_state, files_state, tasks_html_output, file_output]
        )
        # Hidden auto-refresh button.
        auto_refresh_btn = gr.Button("Auto Refresh", visible=False, elem_id="auto_refresh_btn")
        auto_refresh_btn.click(
            refresh_ui,
            inputs=[tasks_state, files_state],
            outputs=[tasks_state, files_state, tasks_html_output, file_output]
        )
        gr.HTML("""
            <script>
              setInterval(function(){
                if(document.getElementById('auto_refresh_toggle').checked){
                  document.getElementById('auto_refresh_btn').click();
                }
              }, 5000);
            </script>
        """)
        auto_refresh_toggle.elem_id = "auto_refresh_toggle"
        
        # Update file dropdown from files state.
        refresh_btn.click(
            update_dropdown,
            inputs=[files_state],
            outputs=[file_dropdown]
        )
        auto_refresh_btn.click(
            update_dropdown,
            inputs=[files_state],
            outputs=[file_dropdown]
        )
        preview_btn.click(
            preview_file,
            inputs=[file_dropdown],
            outputs=[preview_output]
        )
        
    demo.launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    main()
