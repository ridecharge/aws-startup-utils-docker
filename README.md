# aws-startup-utils-docker
AWS Instance Startup Scripts
AWS Statup Scripts to be run as a docker container from cloudinit.

# Build
## bin/install_roles.sh
Installs Ansible role dependencies into ./roles
## bin/build.sh 
Runs bin/install_roles.sh and then builds the docker image gocurb/aws-startup-utils
## bin/push.sh
Pushes the built docker image to a remote registry

# Scripts
## attach_eni.py
Used to attach a existing eni to the instance at startup.  Takes no parameters.

Example: docker run gocurb/aws-startup-scripts ./attach_eni.py
## nat_monitor.py
Configures an instance to be ready for NAT and then continues to monitor is pair in a different availability zone to take over its route when it goes unhealthy.  This is should be run with -d -restart=always docker flags.

Example: docker run -d --restart=always gocurb/aws-startup-scripts ./nat_monitor.py

## register_dns.py
Used to register a dns record at instance startup.  Takes a hosted zone id, and hosted zone name to create a dns record.
The below example from the bastion instance userdata will register bastion-us-east-1a-application.test.gc when deployed into the us-east-1a AvailabilityZone with tag Role = bastion

Example: docker run gocurb/aws-startup-scripts ./register_dns.py Z2FVAJH8FIGE3X Application.test.gc

