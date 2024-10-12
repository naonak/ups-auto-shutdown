import os
import logging
import time
import smtplib
from email.mime.text import MIMEText
import apprise
import argparse
from PyNUTClient.PyNUT import PyNUTClient  # Si la classe est dans un sous-module

# Function to send email alerts
def send_alert_email(subject, body, smtp_server, smtp_user, smtp_password, recipient):
    if smtp_server and smtp_user and smtp_password and recipient:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = recipient

        try:
            with smtplib.SMTP(smtp_server) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            logging.info(f"Alert email sent to {recipient}")
        except Exception as e:
            logging.error(f"Error sending alert email: {e}")
    else:
        logging.info("SMTP details are incomplete. Unable to send alert email.")

# Function to send Apprise alerts
def send_apprise_alert(body, apprise_url):
    if apprise_url:
        apobj = apprise.Apprise()
        apobj.add(apprise_url)
        try:
            apobj.notify(
                body=body,
                title="UPS Alert",
            )
            logging.info("Apprise notification sent successfully.")
        except Exception as e:
            logging.error(f"Error sending Apprise notification: {e}")
    else:
        logging.info("No Apprise URL provided for notifications.")

# Default values (can be overridden by environment variables or arguments)
DEFAULT_BATTERY_RUNTIME_LOW = int(os.getenv('BATTERY_RUNTIME_LOW', 240))
DEFAULT_BATTERY_LOW = int(os.getenv('BATTERY_LOW', 15))
DEFAULT_UPS_ADDRESS = os.getenv('UPS_ADDRESS', 'localhost')
DEFAULT_UPS_PORT = os.getenv('UPS_PORT', '3493')  # Ajout du port par défaut
DEFAULT_UPS_NAME = os.getenv('UPS_NAME', 'ups')
DEFAULT_SHUTDOWN_CMD = os.getenv('SHUTDOWN_CMD', 'systemctl --no-pager halt')
DEFAULT_MAX_FAILS = int(os.getenv('MAX_FAILS', 3))
DEFAULT_CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 60))
DEFAULT_LOAD_THRESHOLD = int(os.getenv('LOAD_THRESHOLD', 80))  # Ajout de la surcharge par défaut (80%)
DEFAULT_VERBOSITY = os.getenv('VERBOSITY', 'ERROR').upper()
DEFAULT_DRY_RUN = os.getenv('DRY_RUN', 'false').lower() in ['true', '1', 'yes']  # Variable d'environnement pour dry-run

# Allowed verbosity levels
VERBOSITY_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR']

def configure_logging(verbosity):
    """Configure the logging level based on verbosity."""
    if verbosity in VERBOSITY_LEVELS:
        logging_level = getattr(logging, verbosity)
    else:
        logging_level = logging.ERROR  # Fallback to ERROR if invalid level
        logging.warning(f"Invalid verbosity level '{verbosity}', defaulting to ERROR.")
    
    logging.basicConfig(level=logging_level, format='%(asctime)s - %(levelname)s - %(message)s')


def parse_arguments():
    """Parse command-line arguments and override default values."""
    parser = argparse.ArgumentParser(description="Monitor UPS status using PyNUTClient and trigger actions on low battery.")
    
    # Adding arguments
    parser.add_argument('--battery-runtime-low', type=int, default=DEFAULT_BATTERY_RUNTIME_LOW,
                        help=f'Battery runtime low threshold in seconds (default: {DEFAULT_BATTERY_RUNTIME_LOW})')
    parser.add_argument('--battery-low', type=int, default=DEFAULT_BATTERY_LOW,
                        help=f'Battery charge low threshold in percentage (default: {DEFAULT_BATTERY_LOW})')
    parser.add_argument('--ups-address', type=str, default=DEFAULT_UPS_ADDRESS,
                        help=f'UPS server address (default: {DEFAULT_UPS_ADDRESS})')
    parser.add_argument('--ups-port', type=str, default=DEFAULT_UPS_PORT,
                        help=f'UPS server port (default: {DEFAULT_UPS_PORT})')  # Ajout du port
    parser.add_argument('--ups-name', type=str, default=DEFAULT_UPS_NAME,
                        help=f'UPS name as listed in NUT (default: "ups" or from UPS_NAME environment variable)')
    parser.add_argument('--load-threshold', type=int, default=DEFAULT_LOAD_THRESHOLD,
                        help=f'Threshold for UPS load percentage to trigger alert (default: {DEFAULT_LOAD_THRESHOLD}%)')  # Seuil de surcharge
    parser.add_argument('--shutdown-cmd', type=str, default=DEFAULT_SHUTDOWN_CMD,
                        help=f'Custom shutdown command (default: "{DEFAULT_SHUTDOWN_CMD}")')
    parser.add_argument('--max-fails', type=int, default=DEFAULT_MAX_FAILS,
                        help=f'Maximum consecutive failures before stopping the script (default: {DEFAULT_MAX_FAILS})')
    parser.add_argument('--check-interval', type=int, default=DEFAULT_CHECK_INTERVAL,
                        help=f'Check interval in seconds (default: {DEFAULT_CHECK_INTERVAL})')
    parser.add_argument('--verbose', type=str, choices=VERBOSITY_LEVELS,
                        help=f'Set verbosity level: {", ".join(VERBOSITY_LEVELS)} (default: {DEFAULT_VERBOSITY})')
    parser.add_argument('--dry-run', action='store_true', help='Enable dry run mode where no shutdown command is executed')  # Ajout de dry-run

    # Arguments for email and Apprise notifications
    parser.add_argument('--alert-apprise-url', help="AppRise URL for notifications (optional)")
    parser.add_argument('--alert-smtp-server', help="SMTP server for email alerts (optional)")
    parser.add_argument('--alert-smtp-user', help="SMTP user for email alerts (optional)")
    parser.add_argument('--alert-smtp-password', help="SMTP password for email alerts (optional)")
    parser.add_argument('--alert-email-recipient', help="Recipient for email alerts (optional)")

    return parser.parse_args()


def trigger_shutdown(shutdown_cmd, dry_run=False, apprise_url=None, smtp_server=None, smtp_user=None, smtp_password=None, recipient=None):
    """Triggers the system shutdown using the custom command."""
    message = "Battery level or runtime is too low - triggering host machine shutdown"
    logging.error(message)

    # Send alerts before shutdown
    send_alert_email(subject="UPS Shutdown Alert", body=message, smtp_server=smtp_server, smtp_user=smtp_user, smtp_password=smtp_password, recipient=recipient)
    send_apprise_alert(body=message, apprise_url=apprise_url)

    if dry_run:
        logging.info("[DRY RUN] Shutdown command not executed.")
    else:
        os.system(shutdown_cmd)


def monitor_ups(battery_runtime_low, battery_low, ups_address, ups_name, ups_port, load_threshold, shutdown_cmd, dry_run, max_fails, check_interval, apprise_url, smtp_server, smtp_user, smtp_password, recipient):
    """Monitors the UPS status in an infinite loop using PyNUTClient."""
    fail_count = 0
    client = PyNUTClient(host=ups_address, port=ups_port)

    while True:
        try:
            # Fetch UPS data
            ups_status_raw = client.GetUPSVars(ups_name)
            # Convertir les clés et valeurs d'octets en chaînes de caractères
            ups_status = {key.decode('utf-8'): value.decode('utf-8') for key, value in ups_status_raw.items()}
            logging.debug(f"Full UPS status data (decoded): {ups_status}")  # Log complet des données UPS

        except Exception as e:
            fail_count += 1
            logging.error(f"Failed to retrieve UPS data: {str(e)}")
            if fail_count >= max_fails:
                logging.error("Maximum consecutive failures reached. Stopping the script.")
                sys.exit(1)
            else:
                logging.warning(f"Attempt {fail_count} of {max_fails} before stopping the script.")
                time.sleep(check_interval)
                continue

        # Reset failure count if the data was retrieved successfully
        fail_count = 0

        # Get UPS status and battery information
        ups_status_value = ups_status.get("ups.status")
        if not ups_status_value:
            logging.error("UPS status is missing from the data.")
            ups_status_value = "Unknown"  # Valeur par défaut si absente

        battery_charge = float(ups_status.get("battery.charge", 100))  # Default to 100% if not available
        battery_runtime = float(ups_status.get("battery.runtime", 9999))  # Default to large value if not available
        ups_load = float(ups_status.get("ups.load", 0))  # Charge de l'UPS

        logging.info(f"UPS Status: {ups_status_value}, Battery charge: {battery_charge}%, Runtime: {battery_runtime} seconds, Load: {ups_load}%")

        # Check if the UPS is on battery
        if ups_status_value.startswith("OB"):
            message = "Power outage detected."
            logging.error(message)
            send_alert_email(subject="UPS Power Outage", body=message, smtp_server=smtp_server, smtp_user=smtp_user, smtp_password=smtp_password, recipient=recipient)
            send_apprise_alert(body=message, apprise_url=apprise_url)

        # Check if the battery charge or runtime is below the thresholds
        if battery_charge <= battery_low or battery_runtime <= battery_runtime_low:
            trigger_shutdown(shutdown_cmd, dry_run, apprise_url, smtp_server, smtp_user, smtp_password, recipient)
            break
        elif battery_charge <= (battery_low + 10):
            warning_message = "Warning: Battery is starting to discharge."
            logging.warning(warning_message)
            send_alert_email(subject="UPS Battery Discharge Warning", body=warning_message, smtp_server=smtp_server, smtp_user=smtp_user, smtp_password=smtp_password, recipient=recipient)
            send_apprise_alert(body=warning_message, apprise_url=apprise_url)
        else:
            logging.debug("Battery level is acceptable.")

        # Check for UPS load (surcharge)
        if ups_load >= load_threshold:
            load_warning_message = f"Warning: UPS load is high at {ups_load}% (threshold: {load_threshold}%)"
            logging.warning(load_warning_message)
            send_alert_email(subject="UPS Load Warning", body=load_warning_message, smtp_server=smtp_server, smtp_user=smtp_user, smtp_password=smtp_password, recipient=recipient)
            send_apprise_alert(body=load_warning_message, apprise_url=apprise_url)

        time.sleep(check_interval)


if __name__ == "__main__":
    # Parse arguments from command line or use environment variables
    args = parse_arguments()

    # Prioritize dry-run argument over environment variable
    dry_run = args.dry_run if args.dry_run else DEFAULT_DRY_RUN

    # Determine verbosity: command-line argument takes precedence over the environment variable
    verbosity = args.verbose if args.verbose else DEFAULT_VERBOSITY

    # Configure logging based on verbosity level
    configure_logging(verbosity)

    logging.info("Starting UPS monitor using PyNUTClient...")

    # Start monitoring UPS with the provided or default parameters
    monitor_ups(
        battery_runtime_low=args.battery_runtime_low,
        battery_low=args.battery_low,
        ups_address=args.ups_address,
        ups_name=args.ups_name,  # Le nom de l'UPS est maintenant personnalisable
        ups_port=args.ups_port,  # Ajout du port personnalisable
        load_threshold=args.load_threshold,  # Seuil de surcharge
        shutdown_cmd=args.shutdown_cmd,
        dry_run=args.dry_run,  # Ajout du paramètre dry_run
        max_fails=args.max_fails,
        check_interval=args.check_interval,
        apprise_url=args.alert_apprise_url,
        smtp_server=args.alert_smtp_server,
        smtp_user=args.alert_smtp_user,
        smtp_password=args.alert_smtp_password,
        recipient=args.alert_email_recipient
    )
