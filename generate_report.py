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
        self.setFillColor(colors.HexColor("#1A202C"))
        self.drawString(54, 750, "TECHNICAL SPECIFICATION REPORT: HYBRID AI ASSISTANT")
        self.setStrokeColor(colors.HexColor("#1A202C"))
        self.setLineWidth(0.75)
        self.line(54, 742, 558, 742)
        
        # Draw Footer
        self.line(54, 55, 558, 55)
        self.setFont("Helvetica", 8)
        self.drawString(54, 42, "Project Documentation - System Engineering")
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
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Minimalist Professional Black & White Palette
    primary_color = colors.HexColor("#000000")   # Pure Black
    secondary_color = colors.HexColor("#1A202C") # Dark charcoal
    dark_neutral = colors.HexColor("#2D3748")    # Grey-Black body text
    light_bg = colors.HexColor("#F7FAFC")        # Soft grey block background
    border_color = colors.HexColor("#1A202C")    # Sharp black borders
    
    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=primary_color,
        alignment=0,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=dark_neutral,
        spaceAfter=30
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=primary_color,
        spaceBefore=18,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=secondary_color,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=dark_neutral,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    meta_style = ParagraphStyle(
        'Meta_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4A5568")
    )

    # Styles for Flowchart cells
    cell_style = ParagraphStyle(
        'FlowCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=1, # Center
        textColor=primary_color
    )
    
    arrow_style = ParagraphStyle(
        'FlowArrow',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=12,
        alignment=1, # Center
        textColor=primary_color
    )
    
    label_style = ParagraphStyle(
        'FlowLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=10,
        alignment=1, # Center
        textColor=colors.HexColor("#4A5568")
    )

    story = []
    
    # ==================== PAGE 1: COVER PAGE ====================
    story.append(Spacer(1, 100))
    story.append(Paragraph("System Architecture Specification", subtitle_style))
    story.append(Paragraph("Hybrid AI Research Assistant", title_style))
    
    # Clean black divider rule
    d = Table([[""]], colWidths=[200], rowHeights=[2.5])
    d.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), primary_color),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(d)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph(
        "A technical specification for the design and deployment of a cost-optimal "
        "hybrid inference architecture. Combining localized quantized small language models (SLMs) "
        "with cloud API engines (LLMs) to ensure performance scalability, privacy protection, and zero-cost edge operations.",
        subtitle_style
    ))
    story.append(Spacer(1, 180))
    
    # Metadata block
    meta_text = """
    <b>Prepared By:</b> Ashish Singh<br/>
    <b>Project Codebase:</b> github.com/Ashishsingh2005-beep/Hybrid-AI-Research-Assistant<br/>
    <b>Document Version:</b> 1.0.0 (Production Setup)<br/>
    <b>Deployment Target:</b> Streamlit Cloud / On-Device Windows Environments
    """
    story.append(Paragraph(meta_text, meta_style))
    story.append(PageBreak())
    
    # ==================== PAGE 2: SUMMARY & TECH STACK ====================
    story.append(Paragraph("1. System Design Summary", h1_style))
    summary_text = (
        "The <b>Hybrid AI Research Assistant</b> implements a dual-inference architectural pattern "
        "to manage the operational cost and latency profiles of generative AI solutions. By utilizing "
        "on-device Small Language Models (SLMs) for low-complexity inputs, the system ensures offline capability, "
        "absolute data privacy, and zero token costs. When inputs exceed the linguistic capacity of local models "
        "or require document context parsing (e.g. PDF analysis), the system escalates the query to Google Cloud's "
        "commercial Gemini models via secure API communication."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("2. Technical Stack Components", h1_style))
    story.append(Paragraph("The software system compiles several open-source execution libraries and cloud resources into a unified, responsive interface:", body_style))
    story.append(Spacer(1, 5))
    
    # Tech Stack Table (Styled strictly in Black and White)
    tech_data = [
        [Paragraph("<b>Component / Library</b>", body_style), Paragraph("<b>Engineering Role</b>", body_style), Paragraph("<b>Functionality Description</b>", body_style)],
        [Paragraph("<b>Streamlit Framework</b>", body_style), Paragraph("User Interface Panel", body_style), Paragraph("Handles the responsive UI rendering, interactive settings management, and file states.", body_style)],
        [Paragraph("<b>Google Gemini API</b>", body_style), Paragraph("Cloud LLM Controller", body_style), Paragraph("Executes complex semantic searches, high-context PDF summarization, and evaluation.", body_style)],
        [Paragraph("<b>llama-cpp-python</b>", body_style), Paragraph("Local Model Loader", body_style), Paragraph("Injects quantized GGUF models directly into local application memory for private execution.", body_style)],
        [Paragraph("<b>llama-server.exe</b>", body_style), Paragraph("C++ Model Host", body_style), Paragraph("Compiles model binaries for C/C++ acceleration on Windows machines.", body_style)],
        [Paragraph("<b>PyPDF</b>", body_style), Paragraph("Document Parser", body_style), Paragraph("Parses PDFs and converts research papers to clean text strings.", body_style)],
        [Paragraph("<b>Plotly & Pandas</b>", body_style), Paragraph("Diagnostics & Analytics", body_style), Paragraph("Tracks, processes, and displays benchmarks (generation speed, cost, and latency charts).", body_style)]
    ]
    
    t = Table(tech_data, colWidths=[120, 110, 274])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), light_bg),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg]),
        ('GRID', (0,0), (-1,-1), 0.75, colors.HexColor("#1A202C")),
    ]))
    story.append(t)
    story.append(PageBreak())
    
    # ==================== PAGE 3: ARCHITECTURE & FUNCTIONALITIES ====================
    story.append(Paragraph("3. Functional Architecture Design", h1_style))
    story.append(Paragraph("Below is the formal query processing sequence. It describes how queries are intercepted, routed, and resolved dynamically:", body_style))
    story.append(Spacer(1, 10))
    
    # --- Native Flowchart using styled tables (No ASCII art, pure solid styling) ---
    flow_data = [
        # Row 0: User Query
        ["", Paragraph("<b>User Input Query</b><br/><font size=7.5 color='#4A5568'>Prompt typed into chat panel or comparison dashboard</font>", cell_style), ""],
        # Row 1: Arrow Down
        ["", Paragraph("▼", arrow_style), ""],
        # Row 2: Decision Router
        ["", Paragraph("<b>Intelligent Decision Router</b><br/><font size=7.5 color='#4A5568'>Analyzes character length, keywords, and PDF attachments</font>", cell_style), ""],
        # Row 3: Labels for path
        [Paragraph("<i>Short Query (&lt; 50 words) & No PDF</i>", label_style), "", Paragraph("<i>Long Query OR Research PDF Uploaded</i>", label_style)],
        # Row 4: Arrows pointing down from decision
        [Paragraph("▼", arrow_style), "", Paragraph("▼", arrow_style)],
        # Row 5: Endpoint models
        [Paragraph("<b>💻 Local SLM</b><br/>• Quantized GGUF Model<br/>• Local CPU/RAM execution<br/>• 100% Free & Offline", cell_style), "", Paragraph("<b>☁️ Cloud LLM</b><br/>• Google Gemini API<br/>• External cloud engine<br/>• Multi-document logic", cell_style)],
        # Row 6: Merge arrows
        [Paragraph("▼", arrow_style), "", Paragraph("▼", arrow_style)],
        # Row 7: Output response
        ["", Paragraph("<b>Streamed Output Response</b><br/><font size=7.5 color='#4A5568'>Rendered in Streamlit UI via Python yield generator</font>", cell_style), ""]
    ]
    
    flow_table = Table(flow_data, colWidths=[230, 44, 230])
    flow_table.setStyle(TableStyle([
        # Spans
        ('SPAN', (0,0), (2,0)),
        ('SPAN', (0,1), (2,1)),
        ('SPAN', (0,2), (2,2)),
        ('SPAN', (0,7), (2,7)),
        
        # Grid line borders for the flowchart blocks
        ('BOX', (0,0), (2,0), 1, border_color),
        ('BACKGROUND', (0,0), (2,0), colors.white),
        
        ('BOX', (0,2), (2,2), 1, border_color),
        ('BACKGROUND', (0,2), (2,2), colors.white),
        
        ('BOX', (0,5), (0,5), 1, border_color),
        ('BACKGROUND', (0,5), (0,5), colors.white),
        
        ('BOX', (2,5), (2,5), 1, border_color),
        ('BACKGROUND', (2,5), (2,5), colors.white),
        
        ('BOX', (0,7), (2,7), 1, border_color),
        ('BACKGROUND', (0,7), (2,7), colors.white),
        
        # Adjust paddings
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(flow_table)
    story.append(Spacer(1, 15))
    
    # Core Functionalities Section
    story.append(Paragraph("4. Core System Features", h1_style))
    
    story.append(Paragraph("<b>A. Dynamic Query Interception & Routing</b>", h2_style))
    story.append(Paragraph("A routing rule intercepts every prompt at execution time. If the system detects internet-dependent keywords or a parsed file context, it escalates to Cloud LLM. Otherwise, short prompts are directed to local CPU execution.", bullet_style))
    
    story.append(Paragraph("<b>B. Error-Safe Local Simulation</b>", h2_style))
    story.append(Paragraph("To ensure the UI is functional on hosts without model files downloaded (e.g. testing environments), an automatic check triggers Simulated Offline Mode. This allows full prototyping of UI interactions using preconfigured data blocks.", bullet_style))
    
    story.append(Paragraph("<b>C. Performance Metrics Dashboard</b>", h2_style))
    story.append(Paragraph("On-device and cloud models are benchmarked side-by-side. The dashboard extracts generation speed (tokens/second), exact response times, and API cost, presenting comparative charts dynamically.", bullet_style))
    
    story.append(Paragraph("<b>D. Automated AI Critique Scorecard</b>", h2_style))
    story.append(Paragraph("When comparisons are executed, the system issues a prompt to the Cloud LLM to act as a judge. It compares both model responses for logical coherence, detail, and factual accuracy, outputting a review scorecard.", bullet_style))
    
    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print("Report generated successfully as 'Hybrid_AI_Research_Assistant_Report.pdf'!")

if __name__ == '__main__':
    create_report()
