import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Email configuration from environment variables
smtp_server = os.getenv('MAIL_SERVER')
smtp_port = int(os.getenv('MAIL_PORT'))
smtp_username = os.getenv('MAIL_USERNAME')
smtp_password = os.getenv('MAIL_PASSWORD')
sender_email = os.getenv('MAIL_DEFAULT_SENDER')
recipient_email = 'sanysk615@gmail.com'  # Replace with the recipient's email address for testing

# Create the email content
subject = "SMTP Configuration Test"
body = "This is a test email to verify SMTP configuration."

# Create the email message
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = recipient_email
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain'))

try:
    # Connect to the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Secure the connection
    server.login(smtp_username, smtp_password)  # Log in to the server
    text = msg.as_string()
    server.sendmail(sender_email, recipient_email, text)  # Send the email
    server.quit()
    print("Email sent successfully.")
except Exception as e:
    print(f"Failed to send email: {e}")
