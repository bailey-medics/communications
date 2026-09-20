import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader


class EmailClient:
    def __init__(self):
        load_dotenv(override=True)
        self.smtp_server = os.getenv("EMAIL_SMTP_SERVER")
        self.smtp_port = os.getenv("EMAIL_SMTP_PORT")
        self.smtp_user = os.getenv("EMAIL_SMTP_BRIDGE_USERNAME")
        self.smtp_password = os.getenv("EMAIL_SMTP_BRIDGE_PASSWORD")
        self.from_email = os.getenv("EMAIL_FROM")

        template_path = os.path.dirname(__file__)
        self.env = Environment(loader=FileSystemLoader(template_path))

    def requirements(self) -> list[str]:
        """Return the list of arguments that the post method takes.

        Returns:
            list[str]: The list of arguments that the post method takes.
        """
        return {
            "post": ["title", "long_blurb", "image"],
        }
        # TODO #6 #5 can you put alt text in an email?

    def name(self) -> str:
        """Return the name of the client.

        Returns:
            str: The name of the client.
        """
        return "Email"

    def post(
        self, title: str, long_blurb: str, image: str, all_mail_list=True
    ) -> None:
        self.send_email(
            subject=title,
            body=long_blurb,
            to_email=os.getenv("EMAIL_SMTP_TEST_EMAIL"),
            image=image,
        )

    def send_email(self, subject, body, to_email, image=None):
        # Create the email message
        msg = MIMEMultipart("alternative")
        msg["From"] = self.from_email
        msg["To"] = to_email
        msg["Subject"] = subject

        template = self.env.get_template("email_template.html")
        html_content = template.render(
            subject=subject, body=f"<pre>{body}</pre>"
        )

        part1 = MIMEText(body, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)

        try:
            # Connect to the SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Secure the connection
            server.login(
                self.smtp_user, self.smtp_password
            )  # Login to the SMTP server

            # Send the email
            server.sendmail(self.from_email, to_email, msg.as_string())

            # Disconnect from the server
            server.quit()

            print(f"Email sent successfully to {to_email}")

        except Exception as e:
            print(f"Failed to send email. Error: {e}")


# Example usage
if __name__ == "__main__":
    email_client = EmailClient()
    email_client.send_email(
        subject="Test Email",
        body="This is a test email from letsdodigital.org.",
        to_email=os.getenv("EMAIL_SMTP_TEST_EMAIL"),
    )
