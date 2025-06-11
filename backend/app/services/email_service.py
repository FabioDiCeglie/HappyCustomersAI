import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    **kwargs
) -> bool:
    """Send an email using the specified template"""
    try:
        logger.info(f"📧 Sending email to {to_email}")
        
        # Create email message
        message = MIMEMultipart()
        message['From'] = f"{settings.from_name} <{settings.from_email}>"
        message['To'] = to_email
        message['Subject'] = subject    
        
        # Add body
        message.attach(MIMEText(body.strip(), "plain"))
        
        # Send email
        kwargs = {
            "hostname": settings.smtp_host,
            "port": settings.smtp_port,
            "username": settings.smtp_user,
            "password": settings.smtp_password,
        }
        # Use direct TLS for port 465, STARTTLS for 587
        if settings.smtp_port == 465:
            kwargs["use_tls"] = True
        elif settings.smtp_port == 587:
            kwargs["start_tls"] = True

        await aiosmtplib.send(message, **kwargs)
        
        logger.info(f"✅ Email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send email: {str(e)}")
        return False


async def test_email_connection() -> bool:
    """Test SMTP connection"""
    try:
        
        # Use direct TLS for port 465, STARTTLS for 587
        use_tls = settings.smtp_port == 465
        
        server = aiosmtplib.SMTP(
            hostname=settings.smtp_host, 
            port=settings.smtp_port, 
            use_tls=use_tls
        )
        await server.connect()
        
        # If not using direct TLS, we need to upgrade the connection
        if not use_tls:
            await server.starttls()
            
        await server.login(settings.smtp_user, settings.smtp_password)
        await server.quit()
        logger.info("✅ SMTP connection test successful")
        return True
    except Exception as e:
        logger.error(f"❌ SMTP connection test failed: {str(e)}")
        return False 