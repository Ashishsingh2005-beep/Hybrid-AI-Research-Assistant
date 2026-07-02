import pypdf
import io
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_file) -> str:
    """
    Extracts text from a PDF file.
    pdf_file can be a file path or a file-like object (e.g. BytesIO from Streamlit's file_uploader).
    """
    try:
        reader = pypdf.PdfReader(pdf_file)
        text = ""
        num_pages = len(reader.pages)
        logger.info(f"Extracting text from PDF with {num_pages} pages")
        
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting PDF: {str(e)}")
        return f"Error extracting PDF: {str(e)}"

def get_pdf_metadata(pdf_file) -> dict:
    """
    Extracts metadata from a PDF file.
    """
    try:
        reader = pypdf.PdfReader(pdf_file)
        meta = reader.metadata
        return {
            "pages": len(reader.pages),
            "author": meta.get("/Author", "Unknown"),
            "creator": meta.get("/Creator", "Unknown"),
            "producer": meta.get("/Producer", "Unknown"),
            "subject": meta.get("/Subject", "Unknown"),
            "title": meta.get("/Title", "Unknown")
        }
    except Exception as e:
        logger.error(f"Error reading PDF metadata: {str(e)}")
        return {"pages": 0, "error": str(e)}
