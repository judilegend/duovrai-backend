import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import aiosmtplib
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def is_mock_enabled() -> bool:
        return (
            not settings.SMTP_PASSWORD 
            or settings.SMTP_USERNAME == "mock_username"
        )

    async def send_report_email(self, recipient_email: str, p1: str, p2: str, pdf_path: str):
        """
        Asynchronously sends the love compatibility report PDF to the customer.
        Includes premium styled email HTML copy.
        """
        logger.info(f"Preparing to send love analysis PDF to {recipient_email}")

        if self.is_mock_enabled():
            logger.warning(
                f"SMTP configuration is in MOCK mode. Email to {recipient_email} "
                f"for couple {p1} & {p2} is marked as SENT (Simulated)."
            )
            return

        # Create email container
        msg = MIMEMultipart()
        msg["From"] = f'"{settings.SMTP_FROM_NAME}" <{settings.SMTP_FROM_EMAIL}>'
        msg["To"] = recipient_email
        msg["Subject"] = f"❤️ Votre Analyse de Compatibilité Amoureuse : {p1} & {p2} est prête !"

        # HTML Email content
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333333; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #f0f0f0; border-radius: 8px; }}
                .header {{ text-align: center; padding-bottom: 20px; border-bottom: 2px solid #fff5f5; }}
                .logo {{ font-family: Georgia, serif; font-size: 28px; font-weight: bold; color: #e53e3e; text-decoration: none; }}
                .logo span {{ color: #4a154b; }}
                .content {{ padding: 20px 0; }}
                .btn {{ display: inline-block; padding: 12px 24px; background-color: #e53e3e; color: white !important; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 15px; }}
                .footer {{ text-align: center; font-size: 12px; color: #a0aec0; border-top: 1px solid #f0f0f0; padding-top: 20px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <a href="https://duovrai.com" class="logo">Duo<span>vrai</span></a>
                </div>
                <div class="content">
                    <h2>Félicitations pour votre lecture !</h2>
                    <p>Bonjour,</p>
                    <p>L'univers a parlé... L'analyse de compatibilité amoureuse personnalisée pour le couple <strong>{p1} et {p2}</strong> a été générée par notre intelligence artificielle avec le plus grand soin.</p>
                    <p>Votre rapport premium de 8 à 12 pages est joint à cet e-mail sous format PDF. Vous y découvrirez des analyses fouillées sur :</p>
                    <ul>
                        <li>Votre pilier émotionnel et la fusion de vos cœurs</li>
                        <li>Votre alchimie physique et intellectuelle</li>
                        <li>Les défis karmiques et points de tension de votre relation</li>
                        <li>Un plan d'action personnalisé composé de 10 clés de réussite</li>
                    </ul>
                    <p>Nous vous souhaitons une lecture inspirante qui, nous l'espérons, guidera votre union vers des sommets d'harmonie.</p>
                    <p>Chaleureusement,<br>L'équipe Duovrai</p>
                </div>
                <div class="footer">
                    &copy; 2026 Duovrai. Tous droits réservés.<br>
                    Vous recevez cet e-mail suite à votre commande sur duovrai.com.
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, "html"))

        # Attach PDF Report
        pdf_name = os.path.basename(pdf_path)
        try:
            with open(pdf_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=pdf_name)
                part['Content-Disposition'] = f'attachment; filename="{pdf_name}"'
                msg.attach(part)
        except Exception as e:
            logger.error(f"Failed to attach PDF file {pdf_path}: {str(e)}")
            raise

        # Send asynchronously using aiosmtplib
        try:
            use_tls = settings.SMTP_PORT == 465
            smtp = aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                use_tls=use_tls
            )
            
            await smtp.connect()
            
            # Start TLS if port is 587
            if settings.SMTP_PORT == 587:
                await smtp.starttls()
                
            await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            await smtp.send_message(msg)
            await smtp.quit()
            logger.info("PDF report successfully sent via email.")
            
        except Exception as e:
            logger.error(f"Failed to send email through SMTP server: {str(e)}")
            # In a production B2C flow, we might want to schedule a retry here
            raise

email_service = EmailService()
