# Latest Ansible Container
FROM registry.gocurb.internal:80/ansible

COPY scripts /opt/aws-startup-utils
RUN chmod -R 0500 /opt/aws-startup-utils
WORKDIR /opt/aws-startup-utils
