import csv
from openpyxl import Workbook
from fpdf import FPDF
import matplotlib.pyplot as plt

def generate_csv_report(filename="report.csv", subject=None):
    """Generate a CSV report with dynamic content based on the subject."""
    if subject is None:
        subject = "Default Report"
    data = [
        ["Subject", subject],
        ["Metric", "Value"],
        ["Metric 1", len(subject) * 2],
        ["Metric 2", len(subject) * 3],
        ["Metric 3", len(subject) * 4],
        ["Remarks", "Auto-generated CSV report based on subject."]
    ]
    with open(filename, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(data)
    return filename

def generate_xlsx_report(filename="report.xlsx", subject=None):
    """Generate an XLSX report with dynamic content based on the subject."""
    if subject is None:
        subject = "Default Report"
    wb = Workbook()
    ws = wb.active
    ws.append(["Subject", subject])
    ws.append(["Metric", "Value"])
    ws.append(["Metric 1", len(subject) * 2])
    ws.append(["Metric 2", len(subject) * 3])
    ws.append(["Metric 3", len(subject) * 4])
    ws.append(["Remarks", "Auto-generated XLSX report based on subject."])
    wb.save(filename)
    return filename

def generate_pdf_report(filename="report.pdf", subject=None):
    """Generate a PDF report with dynamic content based on the subject."""
    if subject is None:
        subject = "Default Report"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # Header
    pdf.cell(200, 10, txt=f"Report on: {subject}", ln=True)
    pdf.ln(10)
    # Dynamic content
    content = (
        f"This report covers the subject: {subject}.\n\n"
        f"Key Data Points:\n"
        f" - Data Point 1: {len(subject) * 2}\n"
        f" - Data Point 2: {len(subject) * 3}\n"
        f" - Data Point 3: {len(subject) * 4}\n\n"
        "Analysis: The metrics above are derived from the length of the subject string as a placeholder for real data. "
        "In a real application, this section would include in-depth analysis and relevant charts."
    )
    pdf.multi_cell(0, 10, txt=content)
    pdf.output(filename)
    return filename

def generate_diagram_report(filename="diagram.png"):
    """Generate a sample diagram using matplotlib and return its filename."""
    labels = ["A", "B", "C", "D"]
    values = [10, 24, 36, 18]
    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color='skyblue')
    plt.title("Sample Diagram")
    plt.xlabel("Category")
    plt.ylabel("Value")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return filename
