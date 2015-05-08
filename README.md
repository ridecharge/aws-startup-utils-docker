# aws-startup-utils-docker
AWS Instance Startup Scripts
AWS Statup Scripts to be run as a docker container from cloudinit.

# Build
we use `make` to handle the project build.

# Scripts
## attach_eni.py
Used to attach a existing eni to the instance at startup.  Takes no parameters.

Example: `docker run gocurb/aws-startup-scripts ./attach_eni.py`
## nat_monitor.py
This script handles nat instance startup and configuration.

Example: `docker run -d --restart=always gocurb/aws-startup-scripts ./nat_monitor.py`

