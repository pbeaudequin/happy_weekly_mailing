"""Module pour envoyer des emails via SMTP."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List


class EmailSender:
    """Envoie des emails via SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        use_tls: bool = True
    ):
        """
        Initialise le sender d'emails.

        Args:
            smtp_host: Adresse du serveur SMTP
            smtp_port: Port du serveur SMTP (généralement 587 pour TLS, 465 pour SSL)
            smtp_user: Nom d'utilisateur SMTP
            smtp_password: Mot de passe SMTP
            use_tls: Utiliser TLS (True) ou SSL (False)
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.use_tls = use_tls

    def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        html_content: str,
        from_address: str | None = None,
        from_name: str = "Happy au Rouret"
    ) -> bool:
        """
        Envoie un email HTML.

        Args:
            to_addresses: Liste des adresses email des destinataires
            subject: Sujet de l'email
            html_content: Contenu HTML de l'email
            from_address: Adresse email de l'expéditeur (par défaut: smtp_user)
            from_name: Nom de l'expéditeur

        Returns:
            True si l'envoi a réussi, False sinon
        """
        if not to_addresses:
            print("Aucun destinataire spécifié")
            return False

        from_address = from_address or self.smtp_user

        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{from_address}>"
            msg['To'] = ', '.join(to_addresses)

            # Ajouter le contenu HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # Se connecter au serveur SMTP et envoyer
            if self.use_tls:
                # Utiliser STARTTLS (port 587)
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                # Utiliser SSL (port 465)
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

            print(f"✓ Email envoyé avec succès à {len(to_addresses)} destinataire(s)")
            return True

        except smtplib.SMTPAuthenticationError:
            print("✗ Erreur d'authentification SMTP - Vérifiez vos identifiants")
            return False
        except smtplib.SMTPException as e:
            print(f"✗ Erreur SMTP : {e}")
            return False
        except Exception as e:
            print(f"✗ Erreur lors de l'envoi de l'email : {e}")
            return False

    def test_connection(self) -> bool:
        """
        Test la connexion au serveur SMTP.

        Returns:
            True si la connexion réussit, False sinon
        """
        try:
            if self.use_tls:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
            else:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10) as server:
                    server.login(self.smtp_user, self.smtp_password)

            print("✓ Connexion SMTP réussie")
            return True

        except smtplib.SMTPAuthenticationError:
            print("✗ Erreur d'authentification SMTP")
            return False
        except Exception as e:
            print(f"✗ Erreur de connexion SMTP : {e}")
            return False
