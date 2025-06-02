import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, DictLoader
from typing import Dict, Optional
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email
        self.from_name = settings.from_name
        
        # Initialize Jinja2 environment for email templates
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Environment:
        """Load email templates"""
        # For now, use in-memory templates
        templates = {
            'critical_response': '''
Subject: Immediate Response Required - Your Recent Experience at {{ restaurant_name }}

Dear {{ customer_name }},

We are deeply concerned about your recent experience at {{ restaurant_name }}. Your feedback is extremely important to us, and we want to address your concerns immediately.

Key Issues Identified:
{% for issue in key_issues %}
• {{ issue }}
{% endfor %}

We would like to:
1. Schedule a personal call with our manager within the next 24 hours
2. Provide a full refund for your visit
3. Invite you back for a complimentary meal to show we can do better

Please reply to this email or call us directly at {{ restaurant_phone }} so we can resolve this matter urgently.

Sincerely,
{{ from_name }}
{{ restaurant_name }}
''',
            
            'food_quality_concern': '''
Subject: Addressing Your Food Quality Concerns - {{ restaurant_name }}

Dear {{ customer_name }},

Thank you for taking the time to share your feedback about your recent dining experience at {{ restaurant_name }}. We sincerely apologize that our food did not meet your expectations.

Your specific concerns:
{% for issue in key_issues %}
• {{ issue }}
{% endfor %}

We take food quality very seriously and have:
• Shared your feedback with our head chef
• Reviewed our preparation processes
• Implemented additional quality checks

We would love the opportunity to show you the quality we're known for. Please accept our invitation for a complimentary return visit.

To arrange this, please reply to this email or call us at {{ restaurant_phone }}.

Best regards,
{{ from_name }}
{{ restaurant_name }}
''',
            
            'service_concern': '''
Subject: Improving Our Service - Your Feedback Matters

Dear {{ customer_name }},

We are sorry to hear that our service did not meet your expectations during your recent visit to {{ restaurant_name }}.

Areas we're addressing based on your feedback:
{% for issue in key_issues %}
• {{ issue }}
{% endfor %}

We have:
• Discussed your feedback with our service team
• Implemented additional training
• Put new processes in place to prevent similar issues

We value your patronage and would appreciate the chance to provide you with the exceptional service experience we're known for. Please accept a complimentary appetizer on your next visit.

Please contact us at {{ restaurant_phone }} to arrange your return visit.

Warm regards,
{{ from_name }}
{{ restaurant_name }}
''',
            
            'general_concern': '''
Subject: Thank You for Your Feedback - {{ restaurant_name }}

Dear {{ customer_name }},

Thank you for sharing your feedback about your experience at {{ restaurant_name }}. We appreciate all customer input as it helps us continuously improve.

We've noted your concerns:
{% for issue in key_issues %}
• {{ issue }}
{% endfor %}

Your feedback has been shared with our management team, and we're taking steps to address these issues. We believe every guest should have an exceptional experience, and we fell short of that standard.

We would welcome the opportunity to earn back your trust. Please accept our invitation for a return visit where we can show you the experience we strive to provide every guest.

Contact us at {{ restaurant_phone }} to arrange your visit.

Sincerely,
{{ from_name }}
{{ restaurant_name }}
'''
        }
        
        return Environment(loader=DictLoader(templates))
    
    async def send_email(
        self,
        to_email: str,
        customer_name: str,
        template_name: str,
        key_issues: list,
        **kwargs
    ) -> bool:
        """Send an email using the specified template"""
        try:
            logger.info(f"📧 Sending {template_name} email to {to_email}")
            
            # Prepare template variables
            template_vars = {
                'customer_name': customer_name,
                'restaurant_name': settings.restaurant_name,
                'restaurant_phone': settings.restaurant_phone,
                'restaurant_email': settings.restaurant_email,
                'from_name': self.from_name,
                'key_issues': key_issues,
                **kwargs
            }
            
            # Render the email template
            template = self.templates.get_template(template_name)
            email_content = template.render(**template_vars)
            
            # Extract subject from content (first line after "Subject:")
            lines = email_content.strip().split('\n')
            subject_line = next((line for line in lines if line.startswith('Subject:')), 'Subject: Follow-up from {{ restaurant_name }}')
            subject = subject_line.replace('Subject: ', '').strip()
            
            # Get email body (everything after the first empty line)
            body_start = next((i for i, line in enumerate(lines) if line.strip() == ''), 0) + 1
            body = '\n'.join(lines[body_start:]).strip()
            
            # Create email message
            message = MIMEMultipart()
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to_email
            message['Subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=True,
                username=self.smtp_user,
                password=self.smtp_password,
            )
            
            logger.info(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            server = aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port)
            await server.connect()
            await server.starttls()
            await server.login(self.smtp_user, self.smtp_password)
            await server.quit()
            logger.info("✅ SMTP connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ SMTP connection test failed: {str(e)}")
            return False


# Global instance
email_service = EmailService() 