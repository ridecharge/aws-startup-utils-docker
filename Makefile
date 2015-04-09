CONTAINER=ridecharge/aws-startup-utils

all: build push clean

build:
	ansible-galaxy install -r requirements.yml -f
	docker build -t $(CONTAINER):latest . 

push:
	docker push $(CONTAINER)

clean:
	rm -r roles