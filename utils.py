import africastalking
import smtplib
import os
from dotenv import load_dotenv
from email.message import EmailMessage

load_dotenv()

def init_sms():
    africastalking.initialize(
        username=os.getenv('AT_USERNAME', 'sandbox'),
        api_key=os.getenv('AT_API_KEY', '')
    )
    return africastalking.SMS

def send_sms(message, recipient=None):
    try:
        phone = recipient or os.getenv('NOTIFY_PHONE', '0763085855')
        if not phone.startswith('+'):
            phone = '+256' + phone.lstrip('0')
        sms = init_sms()
        response = sms.send(message, [phone])
        print(f"SMS sent: {response}")
        return True
    except Exception as e:
        print(f"SMS error: {e}")
        return False

def create_notification(db, Notification, title, message, icon='bell', color='primary', link=None):
    try:
        notif = Notification(
            title=title,
            message=message,
            icon=icon,
            color=color,
            link=link
        )
        db.session.add(notif)
        db.session.commit()
    except Exception as e:
        print(f"Notification error: {e}")

def send_contact_email(recipient_email, sender_name, sender_contact, subject, message):
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME', 'nuwarindaalbertgrande@gmail.com')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    smtp_from = os.getenv('SMTP_FROM_EMAIL', smtp_username)
    use_tls = os.getenv('SMTP_USE_TLS', '1').lower() not in {'0', 'false', 'no'}

    email_message = EmailMessage()
    email_message['Subject'] = f'J&J Soft Aroma Contact: {subject}'
    email_message['From'] = smtp_from
    email_message['To'] = recipient_email
    if sender_contact and '@' in sender_contact:
        email_message['Reply-To'] = sender_contact

    email_message.set_content(
        f"New contact message from J&J Soft Aroma\n\n"
        f"Name: {sender_name}\n"
        f"Contact: {sender_contact}\n"
        f"Subject: {subject}\n\n"
        f"Message:\n{message}\n"
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
        server.ehlo()
        if use_tls:
            server.starttls()
            server.ehlo()
        if smtp_password:
            server.login(smtp_username, smtp_password)
        server.send_message(email_message)

    return True