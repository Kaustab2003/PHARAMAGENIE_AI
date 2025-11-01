# agents/report_generator.py
from fpdf import FPDF
import pandas as pd
import plotly.express as px
import json
from datetime import datetime
import logging
from typing import Optional, Union, Dict, Any

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self):
        self.template = "default"
        
    def generate_pdf(self, analysis_data: Dict[str, Any], output_path: Optional[str] = None) -> bytes:
        """Generate a PDF report from analysis data.
        
        Args:
            analysis_data: Dictionary containing the analysis data
            output_path: Optional path to save the PDF file
            
        Returns:
            bytes: The PDF content as bytes
        """
        try:
            logger.info("Initializing PDF generation...")
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font('Arial', '', 12)

            # Add title
            self._add_metadata(pdf, analysis_data)
            
            # Add sections
            sections = {
                "Market Analysis": analysis_data.get('market_insights', {}),
                "Patent Landscape": analysis_data.get('patent_analysis', {}),
                "Clinical Trials": analysis_data.get('clinical_trials', {})
            }
            
            for title, data in sections.items():
                try:
                    self._add_section(pdf, title, data)
                except Exception as e:
                    logger.error(f"Error adding section '{title}': {str(e)}")
                    self._add_error_section(pdf, f"Error in {title}", str(e))

            # Generate PDF in memory
            logger.info("Generating PDF content...")
            pdf_output = pdf.output(dest='S')
            # Convert to bytes if it's a string, otherwise assume it's already bytes/bytearray
            pdf_data = pdf_output.encode('latin1') if isinstance(pdf_output, str) else bytes(pdf_output)
            
            # Save to file if output path is provided
            if output_path:
                try:
                    with open(output_path, 'wb') as f:
                        f.write(pdf_data)
                    logger.info(f"Successfully saved PDF to {output_path}")
                except Exception as e:
                    logger.error(f"Error saving PDF to {output_path}: {str(e)}")
                    # Don't raise, we still want to return the PDF data
            
            logger.info(f"Successfully generated PDF. Size: {len(pdf_data)} bytes")
            return pdf_data
                
        except Exception as e:
            error_msg = f"Error generating PDF: {str(e)}"
            logger.error(error_msg)
            logger.exception("PDF generation error:")
            
            # Return a simple error PDF
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, 'Error Generating Report', 0, 1)
                pdf.set_font('Arial', '', 12)
                pdf.multi_cell(0, 10, error_msg)
                return pdf.output(dest='S').encode('latin1')
            except Exception as pdf_error:
                logger.error(f"Failed to create error PDF: {str(pdf_error)}")
                # Return a minimal PDF with just the error message
                return f"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/MediaBox[0 0 612 792]/Contents 5 0 R>>endobj\n4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n5 0 obj<</Length 44>>stream\nBT\n/F1 12 Tf\n100 700 Td\n({error_msg[:100]}) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000053 00000 n \n0000000109 00000 n \n0000000226 00000 n \n0000000253 00000 n \ntrailer\n<</Size 6/Root 1 0 R>>\nstartxref\n368\n%%EOF\n".encode('latin1')

    def _add_title(self, pdf: FPDF, title: str) -> None:
        """Add a title to the PDF."""
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, title, 0, 1, 'C')
        pdf.ln(10)

    def _add_metadata(self, pdf: FPDF, data: Dict[str, Any]) -> None:
        """Add metadata to the PDF."""
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f"Drug: {data.get('drug_name', 'N/A')}", ln=True)
        pdf.cell(0, 10, f"Therapeutic Area: {data.get('therapeutic_area', 'N/A')}", ln=True)
        pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.ln(10)
        
    def _add_error_section(self, pdf: FPDF, title: str, error: str) -> None:
        """Add an error section to the PDF."""
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(255, 0, 0)  # Red color for errors
        pdf.cell(0, 10, f"{title} - Error", ln=True)
        pdf.set_text_color(0, 0, 0)  # Reset to black
        pdf.set_font('Arial', 'I', 12)
        pdf.multi_cell(0, 10, f"An error occurred: {error}")
        pdf.ln(5)

    def _add_section(self, pdf: FPDF, title: str, data: Any) -> None:
        """Add a section to the PDF with proper error handling."""
        try:
            if not data or (isinstance(data, (dict, list)) and not data):
                pdf.set_font('Arial', 'I', 12)
                pdf.cell(0, 10, f"{title}: No data available", ln=True)
                pdf.ln(5)
                return

            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, title, ln=True)
            pdf.set_font('Arial', '', 12)

            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (list, dict)):
                        value = self._format_complex_value(value)
                    pdf.multi_cell(0, 10, f"{key}: {value}")
            elif isinstance(data, list):
                for i, item in enumerate(data, 1):
                    if isinstance(item, (dict, list)):
                        item = self._format_complex_value(item)
                    pdf.multi_cell(0, 10, f"{i}. {item}")
            else:
                pdf.multi_cell(0, 10, str(data))

            pdf.ln(5)
        except Exception as e:
            pdf.set_font('Arial', 'I', 10)
            pdf.cell(0, 10, f"Error displaying {title.lower()} data", ln=True)

    def _format_complex_value(self, value: Any) -> str:
        """Format complex values (lists, dicts) for display."""
        if isinstance(value, (list, dict)):
            try:
                return json.dumps(value, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error formatting complex value: {str(e)}")
                return "[Complex data - could not be displayed]"
        return str(value) if value is not None else ""
