# UPS Auto Shutdown

## Description

**UPS Auto Shutdown** is a Python script that uses the **PyNUTClient** library to monitor the status of an uninterruptible power supply (UPS) via a NUT (Network UPS Tools) server. It triggers actions like system shutdown or sending notifications when the UPS battery is low, the load is too high, or the main power is lost.

The script supports alerts via email and [Apprise](https://github.com/caronc/apprise) for sending notifications to multiple platforms.

## Features

- Monitors UPS battery and load status.
- Triggers a safe shutdown when the battery is low or the runtime is short.
- Sends alert notifications via email and Apprise.
- Supports **dry-run** mode to test without executing an actual shutdown.
- Customizable via environment variables or command-line arguments. **Command-line arguments take priority over environment variables**.

## Requirements

- Python 3.x
- Running NUT server accessible from the script
- Python libraries:
  - `PyNUTClient`
  - `apprise`

## Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/ups-auto-shutdown.git
cd ups-auto-shutdown
```

2. Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. (Optional) If you're using **Docker**, you can configure the container using the `docker-compose.yml` file.

## Usage

### Running with Python

You can run the script using command-line arguments or environment variables. **Command-line arguments will override the values provided by environment variables**.

#### Basic example:

```bash
python ups-auto-shutdwon.py --ups-address localhost --ups-name ups --check-interval 60
```

#### Example with **dry-run** (simulates execution without performing shutdown):

```bash
python ups-auto-shutdwon.py --dry-run
```

### Available Arguments

- `--battery-runtime-low`: Low battery runtime threshold (in seconds).
- `--battery-low`: Low battery charge threshold (in percentage).
- `--ups-address`: NUT server address (default: `localhost`).
- `--ups-port`: NUT server port (default: `3493`).
- `--ups-name`: UPS name as listed in NUT (default: `ups`).
- `--load-threshold`: Load threshold (in percentage) to trigger a load warning.
- `--shutdown-cmd`: Custom shutdown command (default: `systemctl --no-pager halt`).
- `--max-fails`: Maximum consecutive failures before stopping the script.
- `--check-interval`: Interval between checks in seconds (default: 60).
- `--dry-run`: Enable simulation mode (no actual actions like shutdown are performed).
- `--alert-apprise-url`: Apprise URL for notifications.
- `--alert-smtp-server`: SMTP server for email alerts.
- `--alert-smtp-user`: SMTP user for email alerts.
- `--alert-smtp-password`: SMTP password for email alerts.
- `--alert-email-recipient`: Email recipient for alerts.

### Running with Docker

#### Docker Compose

A `docker-compose.yml` file is included for easy Docker configuration.

```yaml
version: '3'
services:
  ups-auto-shutdown:
    image: ghcr.io/your-username/ups-auto-shutdown:main
    restart: unless-stopped
    volumes:
      - /run/systemd:/run/systemd:ro
      - /var/run/dbus/system_bus_socket:/var/run/dbus/system_bus_socket:ro
    cap_add:
      - SYS_BOOT
    environment:
      - UPS_ADDRESS=your-ups-ip
      - UPS_PORT=3493
      - UPS_NAME=ups
      - BATTERY_RUNTIME_LOW=240
      - BATTERY_LOW=15
      - SHUTDOWN_CMD=systemctl --no-pager halt
      - CHECK_INTERVAL=60
      - MAX_FAILS=3
      - LOAD_THRESHOLD=80
      - DRY_RUN=true
      - VERBOSITY=DEBUG
      - ALERT_SMTP_SERVER=smtp.example.com
      - ALERT_SMTP_USER=user@example.com
      - ALERT_SMTP_PASSWORD=yourpassword
      - ALERT_EMAIL_RECIPIENT=admin@example.com
      - ALERT_APPRISE_URL=apprise://your-apprise-url
```

### Notifications

The script supports notifications via Apprise and SMTP email alerts.

#### Example with Apprise

Add your Apprise URL to send notifications to platforms like Discord, Slack, etc.

```bash
python ups-auto-shutdwon.py --alert-apprise-url "discord://webhook_id/webhook_token"
```

#### Example with Email

Set up email alerts using an SMTP server:

```bash
python ups-auto-shutdwon.py \
  --alert-smtp-server smtp.example.com \
  --alert-smtp-user user@example.com \
  --alert-smtp-password password \
  --alert-email-recipient recipient@example.com
```

## Notes

- Ensure that your host system's `systemctl` command can be invoked from within the container.
- The image uses the `systemctl --no-pager halt` command for shutdown by default, which requires the container to run with certain privileges.
- It's important to test this setup in a controlled environment before deploying it on a production system to ensure that the host machine shuts down gracefully.

## License

This project is licensed under the MIT License.

