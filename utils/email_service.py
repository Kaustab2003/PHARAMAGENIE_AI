# utils/email_service.py
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
import json
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.ssl_context = ssl.create_default_context()
        
        # Validate configuration on initialization
        if not all([self.smtp_server, self.sender_email, self.sender_password]):
            logger.warning("Email service not fully configured. Some features may not work.")
        
    def test_connection(self) -> Tuple[bool, str]:
        """Test the SMTP server connection and authentication."""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.ehlo()
                if server.has_extn('STARTTLS'):
                    server.starttls(context=self.ssl_context)
                    server.ehlo()
                
                if self.sender_email and self.sender_password:
                    server.login(self.sender_email, self.sender_password)
                    return True, "Successfully connected to SMTP server and authenticated"
                else:
                    return False, "Missing email credentials"
                    
        except smtplib.SMTPAuthenticationError as e:
            return False, f"Authentication failed: {str(e)}"
        except smtplib.SMTPException as e:
            return False, f"SMTP error occurred: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """
        Send an email with optional attachments.
        
        Args:
            to_email: Recipient email address(es) as comma-separated string or list
            subject: Email subject
            body: Email body (HTML)
            attachments: List of dicts with 'data' and 'filename' keys
            cc: List of CC email addresses
            bcc: List of BCC email addresses
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not all([self.smtp_server, self.sender_email, self.sender_password]):
            return False, "Email service not properly configured. Check your environment variables."
            
        if not to_email:
            return False, "No recipient email address provided"

        try:
            # Convert to_email to list if it's a string
            if isinstance(to_email, str):
                to_emails = [email.strip() for email in to_email.split(',')]
            else:
                to_emails = to_email

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add CC and BCC if provided
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            # Add body
            msg.attach(MIMEText(body, 'html'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    try:
                        part = MIMEApplication(
                            attachment.get('data', b''),
                            Name=attachment.get('filename', 'attachment.bin')
                        )
                        part['Content-Disposition'] = f'attachment; filename="{attachment.get("filename", "file")}"'
                        msg.attach(part)
                    except Exception as e:
                        logger.error(f"Error attaching file: {e}")
                        continue
            
            # Connect to server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.ehlo()
                if server.has_extn('STARTTLS'):
                    server.starttls(context=self.ssl_context)
                    server.ehlo()
                
                server.login(self.sender_email, self.sender_password)
                
                # Combine all recipients
                all_recipients = to_emails.copy()
                if cc:
                    all_recipients.extend(cc)
                if bcc:
                    all_recipients.extend(bcc)
                
                server.send_message(msg, from_addr=self.sender_email, to_addrs=all_recipients)
            
            logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return True, "Email sent successfully"
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Authentication failed: {str(e)}. Please check your email credentials and app password settings."
            logger.error(error_msg)
            return False, error_msg
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    def send_analysis_report(
        self,
        to_email: str,
        analysis_data: dict,
        format_type: str = "pdf"
    ) -> bool:
        # Generate report
        if format_type.lower() == "pdf":
            report_data = self._generate_pdf_report(analysis_data)
            filename = f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        else:
            report_data = json.dumps(analysis_data, indent=2).encode('utf-8')
            filename = f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Prepare email
        subject = f"Analysis Report: {analysis_data.get('drug_name', 'Untitled')}"
        body = f"""
        <h2>PharmaGenie AI Analysis Report</h2>
        <p>Please find attached the analysis report for {analysis_data.get('drug_name', 'your drug')}.</p>
        <p>Key findings:</p>
        <ul>
            <li>Score: {analysis_data.get('score', 'N/A')}</li>
            <li>Indication: {analysis_data.get('indication', 'N/A')}</li>
            <li>Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}</li>
        </ul>
        """
        
        # Send email
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            attachments=[{
                'data': report_data,
                'filename': filename
            }]
        )
    
    def _generate_pdf_report(self, analysis_data: dict) -> bytes:
        # This is a placeholder - in a real app, you'd use something like ReportLab
        # or WeasyPrint to generate a proper PDF
        from io import BytesIO
        from reportlab.pdfgen import canvas
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        
        # Add content to PDF
        p.drawString(100, 800, f"Analysis Report: {analysis_data.get('drug_name', 'Untitled')}")
        p.drawString(100, 780, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        p.drawString(100, 760, f"Score: {analysis_data.get('score', 'N/A')}")
        
        # Add more content as needed
        y = 740
        for key, value in analysis_data.items():
            if key not in ['drug_name', 'score']:
                p.drawString(100, y, f"{key}: {value}")
                y -= 20
        
        p.save()
        buffer.seek(0)
        return buffer.getvalue()