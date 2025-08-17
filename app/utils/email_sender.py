# app/utils/email_sender.py

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import SMTP_SERVER, SMTP_PORT, EMAIL_USERNAME, EMAIL_PASSWORD

async def send_email(receiver_email: str, subject: str, body: str):
    """
    Fonction utilitaire asynchrone pour envoyer un email via SMTP.
    Utilise les configurations définies dans app.core.config.
    """
    sender_email = EMAIL_USERNAME
    password = EMAIL_PASSWORD

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    # Convertir le corps en HTML pour un email plus riche
    html_body = f"""\
    <html>
    <body>
        <p>Bonjour,</p>
        <p>{body}</p>
        <p>Cordialement,<br>L'équipe FingerTrack</p>
    </body>
    </html>
    """
    part1 = MIMEText(body, "plain")
    part2 = MIMEText(html_body, "html")
    message.attach(part1)
    message.attach(part2)

    context = ssl.create_default_context()
    try:
        # Pour le port 587 (STARTTLS)
        # with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        #     server.starttls(context=context)
        #     server.login(sender_email, password)
        #     server.sendmail(sender_email, receiver_email, message.as_string())
        
        # Pour le port 465 (SMTPS)
        with smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        
        print(f"Email sent successfully to {receiver_email}")
    except Exception as e:
        print(f"Failed to send email to {receiver_email}: {e}")
        # Relancer une exception pour que le service puisse la gérer et la propager au contrôleur
        raise ValueError(f"Échec de l'envoi de l'e-mail de vérification à {receiver_email}. Veuillez vérifier les paramètres SMTP ou réessayer.")

