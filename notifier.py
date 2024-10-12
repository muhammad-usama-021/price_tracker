import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
RECIPIENT_EMAIL_ADDRESS = os.getenv('RECIPIENT_EMAIL')

def send_email(subject, body, to_email):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("Email credentials are not set.")
        return
    
    # Create the email message
    message = MIMEMultipart()
    message['From'] = EMAIL_ADDRESS
    message['To'] = to_email
    message['Subject'] = subject

    # Attach the email body
    message.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Replace with your SMTP server and port
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        # Send the email
        server.sendmail(EMAIL_ADDRESS, to_email, message.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    # Example usage
    subject = "Price Alert!"
    body = "The price of your tracked product has dropped below your target price."
    to_email = RECIPIENT_EMAIL_ADDRESS  # Replace with the recipient's email address
    send_email(subject, body, to_email)
