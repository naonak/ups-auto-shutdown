# naonak/ups-auto-shutdown

This Docker image is designed to monitor the status of an Uninterruptible Power Supply (UPS) using the Network UPS Tools (NUT) and automatically shutdown the host machine in case of power failure or if the battery falls below certain thresholds. Perfect for Raspberry Pi.

## Features

- **Automatic UPS Monitoring**: Continuously monitors the UPS battery charge and runtime.
- **Host Machine Shutdown**: Triggers a safe shutdown of the host system when the battery is low or a power outage is detected.
- **Verbose Logging**: Provides detailed logs when the `VERBOSE_MODE` is enabled.
- **Failure Tolerance**: Handles temporary failures in UPS communication, with a configurable number of retries.
- **Customizable Thresholds**: Allows setting custom battery runtime and charge level thresholds.

## Usage

To use this image, you need to have a UPS configured with NUT accessible from the host where the Docker container will be running. Here's an example of how you can run the container with the required parameters:

```yaml
version: '3'
services:
  ups-auto-shutdown:
    image: naonak/ups-auto-shutdown:latest
    container_name: ups-auto-shutdown
    restart: unless-stopped
    cap_add:
      - SYS_BOOT
    volumes:
      - /run/systemd:/run/systemd
      - /var/run/dbus/system_bus_socket:/var/run/dbus/system_bus_socket
    environment:
      - UPS_NAME=your_ups_name
      - UPS_ADDRESS=your_ups_address:port
      - SHUTDOWN_CMD=systemctl --no-pager halt
      - BATTERY_RUNTIME_LOW=240
      - BATTERY_LOW=15
      - CHECK_INTERVAL=60
      - VERBOSE_MODE=true
      - MAX_FAILS=3
```

Replace `your_ups_name` and `your_ups_address:port` with the actual UPS name and address.

## Environment Variables

- `UPS_NAME`: The name of the UPS as configured in NUT.
- `UPS_ADDRESS`: The network address of the UPS server (NUT server).
- `SHUTDOWN_CMD`: Command to shut down the host machine; defaults to `systemctl --no-pager halt`.
- `BATTERY_RUNTIME_LOW`: The runtime threshold (in seconds) before a shutdown is initiated; defaults to `240`.
- `BATTERY_LOW`: The battery charge threshold before a shutdown is initiated; defaults to `15`.
- `CHECK_INTERVAL`: How often (in seconds) to check the UPS status; defaults to `60`.
- `VERBOSE_MODE`: Set to `true` for verbose logging.
- `MAX_FAILS`: Number of allowed consecutive UPS communication failures before stopping the script; defaults to `3`.

## Notes

- Ensure that your host system's `systemctl` command can be invoked from within the container.
- The image uses the `systemctl --no-pager halt` command for shutdown by default, which requires the container to run with certain privileges.
- It's important to test this setup in a controlled environment before deploying it on a production system to ensure that the host machine shuts down gracefully.
