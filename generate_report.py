import os
import sys
import time

# Install reportlab if not present
try:
    import reportlab
except ImportError:
    print("Installing reportlab...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Cover page (Page 1) doesn't get headers/footers
        if self._pageNumber == 1:
            self.restoreState()
            return
            
        # Draw Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#4A5568"))
        self.drawString(54, 750, "PROJECT REPORT: HYBRID AI RESEARCH ASSISTANT")
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Draw Footer
        self.line(54, 55, 558, 55)
        self.setFont("Helvetica", 8)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 42, page_str)
        self.restoreState()

def create_report():
    pdf_filename = "Hybrid_AI_Research_Assistant_Report.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    primary_color = colors.HexColor("#1A365D")   # Deep navy blue
    secondary_color = colors.HexColor("#2B6CB0") # Medium blue
    dark_neutral = colors.HexColor("#2D3748")    # Charcoal
    light_bg = colors.HexColor("#F7FAFC")        # Soft grey
    border_color = colors.HexColor("#E2E8F0")    # Divider grey
    
    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=30,
        leading=36,
        textColor=primary_color,
        alignment=0, # Left aligned
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=18,
        textColor=secondary_color,
        spaceAfter=25
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=secondary_color,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.0,
        leading=12.5,
        textColor=dark_neutral,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=2
    )
    
    meta_style = ParagraphStyle(
        'Meta_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#718096")
    )

    story = []
    
    # ==================== PAGE 1: COVER PAGE ====================
    story.append(Spacer(1, 80))
    story.append(Paragraph("Hybrid AI Research<br/>Assistant", title_style))
    
    # Colored accent line
    d = Table([[""]], colWidths=[150], rowHeights=[3])
    d.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), secondary_color),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(d)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("A production-ready multi-tier web application integrating local Edge intelligence (SLMs) with commercial Cloud services (LLMs) for cost-optimal and high-performance cognitive computing.", subtitle_style))
    story.append(Spacer(1, 120))
    
    # Metadata block
    meta_text = """
    <b>Author:</b> Ashish Singh<br/>
    <b>Repository:</b> <font color="#2B6CB0">github.com/Ashishsingh2005-beep/Hybrid-AI-Research-Assistant</font><br/>
    <b>Date:</b> July 2026<br/>
    <b>Frameworks:</b> Streamlit, Llama.cpp, Google Gemini API
    """
    story.append(Paragraph(meta_text, meta_style))
    story.append(PageBreak())
    
    # ==================== PAGE 2: EXECUTIVE SUMMARY & TECH STACK ====================
    story.append(Paragraph("1. Executive Summary", h1_style))
    summary_text = (
        "The <b>Hybrid AI Research Assistant</b> is a software solution designed to solve the critical trade-off "
        "between operating costs, data privacy, and cognitive reasoning capabilities in large-scale AI applications. "
        "By utilizing a <b>Dual-Inference Engine (Hybrid Architecture)</b>, the application handles routine, low-complexity "
        "tasks locally using a <b>Small Language Model (SLM)</b> running directly on standard CPU hardware without "
        "any API costs. For complex reasoning, multi-document research, or long-form analysis, the system dynamically "
        "routes queries to a commercial <b>Cloud Large Language Model (LLM)</b> via API."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 4))
    
    story.append(Paragraph("2. Technology Stack & Tools Used", h1_style))
    story.append(Paragraph("The application leverages open-source local inference engines alongside cloud APIs to form a unified interface. Below is the list of core tools used in the development of this project:", body_style))
    story.append(Spacer(1, 2))
    
    # Tech Stack Table
    tech_data = [
        [Paragraph("<b>Technology / Tool</b>", body_style), Paragraph("<b>Domain</b>", body_style), Paragraph("<b>Key Role in Project</b>", body_style)],
        [Paragraph("<b>Streamlit</b>", body_style), Paragraph("Frontend UI Layer", body_style), Paragraph("Renders interactive dashboard, chat components, file upload, and custom styling.", body_style)],
        [Paragraph("<b>Google Gemini API</b>", body_style), Paragraph("Cloud LLM Engine", body_style), Paragraph("Performs complex reasoning, multi-document PDF analysis, and automated evaluation.", body_style)],
        [Paragraph("<b>llama-cpp-python</b>", body_style), Paragraph("Local SLM Loader", body_style), Paragraph("Loads quantized GGUF models directly into Python memory for low-latency offline inference.", body_style)],
        [Paragraph("<b>llama-server.exe</b>", body_style), Paragraph("Local C++ Server", body_style), Paragraph("Compiles and runs model server utilizing highly optimized C/C++ backend for Windows systems.", body_style)],
        [Paragraph("<b>PyPDF (pypdf)</b>", body_style), Paragraph("PDF Parser", body_style), Paragraph("Extracts textual contents from scientific research papers and reports for document QA.", body_style)],
        [Paragraph("<b>Plotly & Pandas</b>", body_style), Paragraph("Analytics Dashboard", body_style), Paragraph("Processes inference benchmarks (tokens/sec, cost, latency) and renders comparison bar charts.", body_style)],
        [Paragraph("<b>psutil</b>", body_style), Paragraph("System Diagnostics", body_style), Paragraph("Monitors background execution states and manages active local llama servers.", body_style)]
    ]
    
    t = Table(tech_data, colWidths=[110, 110, 284])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), border_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))
    
    # ==================== CORE FEATURES & HYBRID ARCHITECTURE ====================
    story.append(Paragraph("3. Core Application Features", h1_style))
    
    story.append(KeepTogether([
        Paragraph("<b>A. Intelligent Routing (Auto-Routing Mode)</b>", h2_style),
        Paragraph("A custom decision-making router evaluates every user query before execution based on rules:", bullet_style),
        Paragraph("• <i>Word Count Threshold:</i> Short questions (e.g., &lt; 50 words) are handled locally by the SLM to reduce cloud API billing.", bullet_style),
        Paragraph("• <i>Capability Detection:</i> Queries requiring real-time/latest data (e.g., 'news', 'weather') or uploaded PDF context are automatically escalated to the Cloud LLM.", bullet_style),
    ]))
    
    story.append(KeepTogether([
        Paragraph("<b>B. Offline Capability & Simulated Mode</b>", h2_style),
        Paragraph("• The local engine works entirely offline without internet, preventing sensitive data leakage.", bullet_style),
        Paragraph("• Built-in <i>Simulated Offline Mode</i> automatically intercepts file-missing errors and provides lightweight mocks to allow design prototyping and UI evaluation on systems without model files downloaded.", bullet_style),
    ]))
    
    story.append(KeepTogether([
        Paragraph("<b>C. Side-by-Side Model Comparison</b>", h2_style),
        Paragraph("• Developers can run parallel inference on Local SLM vs. Cloud LLM for the same prompt.", bullet_style),
        Paragraph("• Outputs live metrics (latency, speed in tokens/second, and exact API costs).", bullet_style),
    ]))
    
    story.append(KeepTogether([
        Paragraph("<b>D. Automated AI Critique (Auto-Evaluation)</b>", h2_style),
        Paragraph("• The Cloud LLM acts as an independent judge on the comparison screen, evaluating both generated answers for logical consistency, accuracy, and grammar, outputting a professional scorecard.", bullet_style),
    ]))
    
    story.append(Spacer(1, 4))
    story.append(Paragraph("4. Key Architectural Flow", h1_style))
    story.append(Paragraph("Below is a conceptual representation of the query routing workflow in the hybrid assistant:", body_style))
    story.append(Spacer(1, 2))
    
    # Simple ASCII Diagram represented inside a light grey table for formatting
    diagram_text = """
                   [ User Input Prompt ]
                             │
                      [ Streamlit UI ]
                             │
            ┌────────────────┴────────────────┐
      (Short Query)                     (PDF / Complex Query)
            ▼                                 ▼
      [ Local SLM ]                     [ Cloud LLM ]
       - On-Device                       - Google Gemini API
       - 100% Free & Private             - High Reasoning Power
       - Quantized GGUF Model            - Summarization / Search
            │                                 │
            └────────────────┬────────────────┘
                             ▼
                      [ Final Streamed Answer ]
    """
    
    diag_table = Table([[diagram_text]], colWidths=[504])
    diag_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Courier'),
        ('FONTSIZE', (0,0), (-1,-1), 7.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LEADPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
    ]))
    story.append(diag_table)
    
    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print("Report generated successfully as 'Hybrid_AI_Research_Assistant_Report.pdf'!")

if __name__ == '__main__':
    create_report()
