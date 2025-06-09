import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, DictLoader
from typing import Dict, Optional
import logging
from functools import lru_cache

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_email_config() -> Dict[str, str]:
    """Get email configuration"""
    return {
        'smtp_host': settings.smtp_host,
        'smtp_port': settings.smtp_port,
        'smtp_user': settings.smtp_user,
        'smtp_password': settings.smtp_password,
        'from_email': settings.from_email,
        'from_name': settings.from_name,
    }


@lru_cache(maxsize=1)
def get_email_templates() -> Environment:
    """Load email templates"""
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
        
        'quality_concern': '''
Subject: Addressing Your Quality Concerns - {{ restaurant_name }}

Dear {{ customer_name }},

Thank you for taking the time to share your feedback about your recent experience with {{ restaurant_name }}. We sincerely apologize that our quality did not meet your expectations.

Your specific concerns:
{% for issue in key_issues %}
• {{ issue }}
{% endfor %}

We take quality very seriously and have:
• Shared your feedback with our quality team
• Reviewed our processes
• Implemented additional quality checks

We would love the opportunity to show you the quality we're known for. Please accept our invitation for a complimentary return experience.

To arrange this, please reply to this email or contact us at {{ restaurant_phone }}.

Best regards,
{{ from_name }}
{{ restaurant_name }}
''',
        
        'service_concern': '''
Subject: Improving Our Service - Your Feedback Matters

Dear {{ customer_name }},

We are sorry to hear that our service did not meet your expectations during your recent experience with {{ restaurant_name }}.

Areas we're addressing based on your feedback:
{% for issue in key_issues %}
• {{ issue }}
{% endfor %}

We have:
• Discussed your feedback with our service team
• Implemented additional training
• Put new processes in place to prevent similar issues

We value your patronage and would appreciate the chance to provide you with the exceptional service experience we're known for. Please accept a complimentary service on your next visit.

Please contact us at {{ restaurant_phone }} to arrange your return visit.

Warm regards,
{{ from_name }}
{{ restaurant_name }}
''',

        'delivery_concern': '''
Subject: Addressing Your Delivery Experience - {{ restaurant_name }}

Dear {{ customer_name }},

We sincerely apologize for the delivery issues you experienced with your recent order from {{ restaurant_name }}.

Delivery concerns you raised:
{% for issue in key_issues %}
• {{ issue }}
{% endfor %}

We have:
• Reviewed your delivery with our logistics team
• Implemented improved tracking and communication
• Enhanced our delivery processes

We would like to make this right. Please accept a complimentary delivery credit and priority handling on your next order.

Contact us at {{ restaurant_phone }} to arrange your next order.

Best regards,
{{ from_name }}
{{ restaurant_name }}
''',

        'support_concern': '''
Subject: Improving Our Support - We Hear You

Dear {{ customer_name }},

Thank you for your feedback regarding your support experience with {{ restaurant_name }}. We apologize that we didn't provide the assistance you needed.

Support areas we're improving:
{% for issue in key_issues %}
• {{ issue }}
{% endfor %}

We have:
• Enhanced our support training
• Improved our response processes
• Added additional support resources

We're committed to providing excellent support. Please give us another chance to assist you properly.

Contact us at {{ restaurant_phone }} for immediate support assistance.

Sincerely,
{{ from_name }}
{{ restaurant_name }}
''',
        
        'general_concern': '''
Subject: Thank You for Your Feedback - {{ restaurant_name }}

Dear {{ customer_name }},

Thank you for sharing your feedback about your experience with {{ restaurant_name }}. We appreciate all customer input as it helps us continuously improve.

We've noted your concerns:
{% for issue in key_issues %}
• {{ issue }}
{% endfor %}

Your feedback has been shared with our management team, and we're taking steps to address these issues. We believe every customer should have an exceptional experience, and we fell short of that standard.

We would welcome the opportunity to earn back your trust. Please accept our invitation for a return experience where we can show you the service we strive to provide every customer.

Contact us at {{ restaurant_phone }} to arrange your visit.

Sincerely,
{{ from_name }}
{{ restaurant_name }}
'''
    }
    
    return Environment(loader=DictLoader(templates))


async def send_email(
    to_email: str,
    customer_name: str,
    template_name: str,
    key_issues: list,
    **kwargs
) -> bool:
    """Send an email using the specified template"""
    try:
        logger.info(f"📧 Sending {template_name} email to {to_email}")
        
        config = get_email_config()
        templates = get_email_templates()
        
        # Prepare template variables
        template_vars = {
            'customer_name': customer_name,
            'restaurant_name': settings.restaurant_name,
            'restaurant_phone': settings.restaurant_phone,
            'restaurant_email': settings.restaurant_email,
            'from_name': config['from_name'],
            'key_issues': key_issues,
            **kwargs
        }
        
        # Render the email template
        template = templates.get_template(template_name)
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
        message['From'] = f"{config['from_name']} <{config['from_email']}>"
        message['To'] = to_email
        message['Subject'] = subject
        
        # Add body
        message.attach(MIMEText(body, 'plain'))
        
        # Send email
        await aiosmtplib.send(
            message,
            hostname=config['smtp_host'],
            port=config['smtp_port'],
            start_tls=True,
            username=config['smtp_user'],
            password=config['smtp_password'],
        )
        
        logger.info(f"✅ Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
        return False


async def test_email_connection() -> bool:
    """Test SMTP connection"""
    try:
        config = get_email_config()
        server = aiosmtplib.SMTP(hostname=config['smtp_host'], port=config['smtp_port'])
        await server.connect()
        await server.starttls()
        await server.login(config['smtp_user'], config['smtp_password'])
        await server.quit()
        logger.info("✅ SMTP connection test successful")
        return True
    except Exception as e:
        logger.error(f"❌ SMTP connection test failed: {str(e)}")
        return False 