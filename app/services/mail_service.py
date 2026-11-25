# import logging
# import os
# import smtplib
# from email.message import EmailMessage
# from typing import Iterable, Optional

# # Adjust if your settings module path differs
# from app.core.config import settings

# logger = logging.getLogger(__name__)

# ADMIN_NOTIFY_EMAIL = os.getenv(
#     "ADMIN_NOTIFY_EMAIL",
#     getattr(settings, "ADMIN_NOTIFY_EMAIL", "info@pseudoteam.com"),
# )


# def _get_smtp_config() -> dict:
#     return {
#         "host": os.getenv("SMTP_HOST", getattr(settings, "SMTP_HOST", "")),
#         "port": int(os.getenv("SMTP_PORT", getattr(settings, "SMTP_PORT", 587))),
#         "user": os.getenv("SMTP_USER", getattr(settings, "SMTP_USER", "")),
#         "password": os.getenv("SMTP_PASSWORD", getattr(settings, "SMTP_PASSWORD", "")),
#         "from_addr": os.getenv(
#             "MAIL_FROM",
#             getattr(settings, "MAIL_FROM", "noreply@pseudoteam.com"),
#         ),
#         "use_tls": str(
#             os.getenv("SMTP_TLS", getattr(settings, "SMTP_TLS", "true"))
#         ).lower()
#         in ("1", "true", "yes"),
#     }


# def send_email(
#     *,
#     to_email: Optional[str],
#     subject: str,
#     body: str,
#     cc_emails: Optional[Iterable[str]] = None,
# ) -> bool:
#     """
#     Sends a plain-text email via SMTP. Logs and returns False if unconfigured
#     or if delivery fails, without breaking core API transactions.
#     """
#     if not to_email or not to_email.strip():
#         logger.warning("Skipped email '%s' because recipient email is empty.", subject)
#         return False

#     cfg = _get_smtp_config()
#     if not cfg["host"]:
#         logger.warning(
#             "SMTP_HOST not configured; logging email to %s | Subject: %s",
#             to_email,
#             subject,
#         )
#         logger.info("Email body to %s:\n%s", to_email, body)
#         return False

#     msg = EmailMessage()
#     msg["From"] = cfg["from_addr"]
#     msg["To"] = to_email.strip()
#     if cc_emails:
#         clean_cc = [addr.strip() for addr in cc_emails if addr and addr.strip()]
#         if clean_cc:
#             msg["Cc"] = ", ".join(clean_cc)
#     msg["Subject"] = subject
#     msg.set_content(body)

#     try:
#         with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as server:
#             if cfg["use_tls"]:
#                 server.starttls()
#             if cfg["user"] and cfg["password"]:
#                 server.login(cfg["user"], cfg["password"])
#             server.send_message(msg)
#         logger.info("Email sent to %s | Subject: %s", to_email, subject)
#         return True
#     except Exception as exc:
#         logger.exception("Failed to send email to %s (%s): %s", to_email, subject, exc)
#         return False


# def send_customer_verification_email(
#     *,
#     name: str,
#     email: str,
#     verification_link: str,
#     created_at_str: str,
#     expire_hours: int = 24,
# ) -> None:
#     send_email(
#         to_email=email,
#         subject="Verify Your Email & Set Password - PseudoTeam",
#         body=(
#             f"Hello {name},\n\n"
#             f"Thank you for signing up with PseudoTeam.\n"
#             f"Please verify your email and set your password using the link below:\n\n"
#             f"{verification_link}\n\n"
#             f"This link will expire in {expire_hours} hours.\n\n"
#             f"Best regards,\n"
#             f"PseudoTeam"
#         ),
#     )

#     if ADMIN_NOTIFY_EMAIL:
#         send_email(
#             to_email=ADMIN_NOTIFY_EMAIL,
#             subject="New Customer Sign Up - PseudoTeam",
#             body=(
#                 f"New Customer Signup:\n"
#                 f"Name: {name}\n"
#                 f"Email: {email}\n"
#                 f"Registered At: {created_at_str}\n"
#             ),
#         )


# def send_project_uploaded_email(
#     *,
#     customer_email: Optional[str],
#     customer_name: Optional[str],
#     project_id: str | int,
#     project_name: str,
#     project_code: Optional[str] = None,
# ) -> None:
#     display_name = customer_name or "Customer"
#     code_line = f"Project Code: {project_code}\n" if project_code else ""

#     if customer_email:
#         send_email(
#             to_email=customer_email,
#             subject=f"Project Uploaded: {project_name} - PseudoTeam",
#             body=(
#                 f"Hello {display_name},\n\n"
#                 f"Your project has been uploaded successfully.\n\n"
#                 f"Project Name: {project_name}\n"
#                 f"{code_line}"
#                 f"Project ID: {project_id}\n\n"
#                 f"You can track its progress anytime in your PseudoTeam portal.\n\n"
#                 f"Best regards,\n"
#                 f"PseudoTeam"
#             ),
#         )

#     if ADMIN_NOTIFY_EMAIL:
#         send_email(
#             to_email=ADMIN_NOTIFY_EMAIL,
#             subject=f"New Project Uploaded (#{project_id}) - PseudoTeam",
#             body=(
#                 f"A new project was uploaded:\n"
#                 f"Customer: {display_name} ({customer_email or 'N/A'})\n"
#                 f"Project Name: {project_name}\n"
#                 f"{code_line}"
#                 f"Project ID: {project_id}\n"
#             ),
#         )


# def send_order_placed_email(
#     *,
#     customer_email: Optional[str],
#     customer_name: Optional[str],
#     orders_count: int,
#     order_numbers: Optional[list[str]] = None,
#     items_summary: Optional[list[str]] = None,
# ) -> None:
#     display_name = customer_name or "Customer"
#     orders_text = ", ".join(order_numbers) if order_numbers else f"{orders_count} order(s) placed"
#     items_text = (
#         "\n".join(f"- {line}" for line in items_summary)
#         if items_summary
#         else "- Items included in your requisition"
#     )

#     if customer_email:
#         send_email(
#             to_email=customer_email,
#             subject="Order Confirmation - PseudoTeam",
#             body=(
#                 f"Hello {display_name},\n\n"
#                 f"Thank you for your requisition. Your order has been placed successfully.\n\n"
#                 f"Orders Placed: {orders_count}\n"
#                 f"Reference(s): {orders_text}\n"
#                 f"Items:\n{items_text}\n\n"
#                 f"You can view order status anytime in the Orders section.\n\n"
#                 f"Best regards,\n"
#                 f"PseudoTeam"
#             ),
#         )

#     if ADMIN_NOTIFY_EMAIL:
#         send_email(
#             to_email=ADMIN_NOTIFY_EMAIL,
#             subject=f"New Spares Order Placed ({orders_count}) - PseudoTeam",
#             body=(
#                 f"A customer placed a new spare parts order:\n"
#                 f"Customer: {display_name} ({customer_email or 'N/A'})\n"
#                 f"Orders Count: {orders_count}\n"
#                 f"Reference(s): {orders_text}\n"
#                 f"Items:\n{items_text}\n"
#             ),
#         )


# def send_help_ticket_email(
#     *,
#     customer_email: Optional[str],
#     customer_name: Optional[str],
#     ticket_number: Optional[str],
#     subject: str,
#     description: str,
#     project_name: Optional[str] = None,
# ) -> None:
#     display_name = customer_name or "Customer"
#     ticket_label = ticket_number or "Submitted"
#     project_line = f"Project: {project_name}\n" if project_name else ""

#     if customer_email:
#         send_email(
#             to_email=customer_email,
#             subject=f"Support Request Received [{ticket_label}] - PseudoTeam",
#             body=(
#                 f"Hello {display_name},\n\n"
#                 f"We have received your support/help request.\n\n"
#                 f"Ticket Reference: {ticket_label}\n"
#                 f"{project_line}"
#                 f"Subject: {subject}\n"
#                 f"Details:\n{description}\n\n"
#                 f"Our team will review and get back to you shortly.\n\n"
#                 f"Best regards,\n"
#                 f"PseudoTeam"
#             ),
#         )

#     if ADMIN_NOTIFY_EMAIL:
#         send_email(
#             to_email=ADMIN_NOTIFY_EMAIL,
#             subject=f"New Help / Support Ticket [{ticket_label}] - PseudoTeam",
#             body=(
#                 f"New support/help submission:\n"
#                 f"From: {display_name} ({customer_email or 'N/A'})\n"
#                 f"Ticket Reference: {ticket_label}\n"
#                 f"{project_line}"
#                 f"Subject: {subject}\n"
#                 f"Details:\n{description}\n"
#             ),
#         )


# def send_password_changed_email(
#     *,
#     user_email: Optional[str],
#     user_name: Optional[str],
# ) -> None:
#     if not user_email:
#         return
#     display_name = user_name or "User"
#     send_email(
#         to_email=user_email,
#         subject="Your Password Was Changed - PseudoTeam",
#         body=(
#             f"Hello {display_name},\n\n"
#             f"This is a confirmation that the password for your PseudoTeam account was recently changed.\n\n"
#             f"If you did not make this change, please contact support immediately.\n\n"
#             f"Best regards,\n"
#             f"PseudoTeam"
#         ),
#     )

