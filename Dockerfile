# Latest Ansible Container
FROM ridecharge/ansible

COPY scripts /opt/aws-startup-utils
RUN chmod -R 0500 /opt/aws-startup-utils
WORKDIR /opt/aws-startup-utils
