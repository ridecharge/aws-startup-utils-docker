# Latest Ubuntu LTS
FROM ubuntu:14.04

# Install Ansible
RUN apt-get update && \
    apt-get install --no-install-recommends -y software-properties-common && \
    apt-add-repository ppa:ansible/ansible && \
    apt-get update && \
    apt-get install -y ansible

# Make sure only ansible host is localhost
RUN echo '[local]\nlocalhost\n' > /etc/ansible/hosts

# Copy our ansible files
COPY playbook.yml /tmp/playbook.yml
COPY roles /tmp/roles/

# Provision the image
RUN /tmp/ansible-playbook --connection=local playbook.yml

# Remove ansible
RUN apt-get purge -y --auto-remove ansible software-properties-common

# Install our aws-util-scripts
COPY scripts /root/aws-util-scripts/
RUN chmod -R 0500 /root/aws-util-scripts/
