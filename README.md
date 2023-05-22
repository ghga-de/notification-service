
[![tests](https://github.com/ghga-de/notification-service/actions/workflows/unit_and_int_tests.yaml/badge.svg)](https://github.com/ghga-de/notification-service/actions/workflows/unit_and_int_tests.yaml)
[![Coverage Status](https://coveralls.io/repos/github/ghga-de/notification-service/badge.svg?branch=main)](https://coveralls.io/github/ghga-de/notification-service?branch=main)

# Notification Service

The Notification Service (NS) handles notification kafka events.

## Description

The Notification Service is a microservice intended to provide general notification capabilities. At this time, notifications are only generated via Kafka events, and they are only issued via email.
However, the architecture of the service would allow for the addition of other event sourcing options, like API submission, as well as new notification channels, such as SMS, with relatively little work.

To send an email notification using this service, publish a kafka event conforming to the Notification event schema to the 'notifications' topic. Because email client authentication is handled by the notification service itself, nothing beyond publishing the event is required.


## Installation
We recommend using the provided Docker container.

A pre-build version is available at [docker hub](https://hub.docker.com/repository/docker/ghga/notification-service):
```bash
docker pull ghga/notification-service:0.1.0
```

Or you can build the container yourself from the [`./Dockerfile`](./Dockerfile):
```bash
# Execute in the repo's root dir:
docker build -t ghga/notification-service:0.1.0 .
```

For production-ready deployment, we recommend using Kubernetes, however,
for simple use cases, you could execute the service using docker
on a single server:
```bash
# The entrypoint is preconfigured:
docker run -p 8080:8080 ghga/notification-service:0.1.0 --help
```

If you prefer not to use containers, you may install the service from source:
```bash
# Execute in the repo's root dir:
pip install .

# To run the service:
ns --help
```

## Configuration
### Parameters

The service requires the following configuration parameters:
- **`plaintext_email_template`** *(string)*: The plaintext template to use for email notifications.

- **`html_email_template`** *(string)*: The HTML template to use for email notifications.

- **`from_address`** *(string)*: The sender's address.

- **`smtp_host`** *(string)*: The mail server host to connect to.

- **`smtp_port`** *(integer)*: The port for the mail server connection.

- **`login_user`** *(string)*: The login username or email.

- **`login_password`** *(string)*: The login password.

- **`notification_event_topic`** *(string)*: Name of the event topic used to track notification events.

- **`notification_event_type`** *(string)*: The type to use for events containing content to be sent.

- **`service_name`** *(string)*: Default: `ns`.

- **`service_instance_id`** *(string)*: A string that uniquely identifies this instance across all instances of this service. A globally unique Kafka client ID will be created by concatenating the service_name and the service_instance_id.

- **`kafka_servers`** *(array)*: A list of connection strings to connect to Kafka bootstrap servers.

  - **Items** *(string)*


### Usage:

A template YAML for configurating the service can be found at
[`./example-config.yaml`](./example-config.yaml).
Please adapt it, rename it to `.ns.yaml`, and place it into one of the following locations:
- in the current working directory were you are execute the service (on unix: `./.ns.yaml`)
- in your home directory (on unix: `~/.ns.yaml`)

The config yaml will be automatically parsed by the service.

**Important: If you are using containers, the locations refer to paths within the container.**

All parameters mentioned in the [`./example-config.yaml`](./example-config.yaml)
could also be set using environment variables or file secrets.

For naming the environment variables, just prefix the parameter name with `ns_`,
e.g. for the `host` set an environment variable named `ns_host`
(you may use both upper or lower cases, however, it is standard to define all env
variables in upper cases).

To using file secrets please refer to the
[corresponding section](https://pydantic-docs.helpmanual.io/usage/settings/#secret-support)
of the pydantic documentation.

## HTTP API
An OpenAPI specification for this service can be found [here](./openapi.yaml).

## Architecture and Design:
This is a Python-based service following the Triple Hexagonal Architecture pattern.
It uses protocol/provider pairs and dependency injection mechanisms provided by the
[hexkit](https://github.com/ghga-de/hexkit) library.

### Typical operation

This service doesn't have a REST API or use a database for anything.
It's a straightforward service running a Kafka consumer that listens for one kind of event.
Notification events are picked up by the consumer, validated against the Notification event schema, and sent to the Notifier module.
The Notifier looks at the notification event details and determines what to do with it.
Right now, this always means sending an email.
The information is sent to the SMTP client, where a secure connection is established and the email is dispatched.

### Testing
The only notable thing about the test setup is that it uses a local test server (tests/fixtures/server.py) via aiosmtpd, which has sort of replaced the old smtpd module. There is a DummyServer, which has an 'expect_email()' method that is used similarly to the expect_events() method from hexkit's kafka testing module. It can perform simple a authentication check so error handling can be tested. When an email is sent to the test server, the connection is closed and the received/expected emails are compared to make sure that the header and body content is intact. This enables testing the flow of sending an email without actually issuing any real emails and without using real credentials.


## Development
For setting up the development environment, we rely on the
[devcontainer feature](https://code.visualstudio.com/docs/remote/containers) of vscode
in combination with Docker Compose.

To use it, you have to have Docker Compose as well as vscode with its "Remote - Containers"
extension (`ms-vscode-remote.remote-containers`) installed.
Then open this repository in vscode and run the command
`Remote-Containers: Reopen in Container` from the vscode "Command Palette".

This will give you a full-fledged, pre-configured development environment including:
- infrastructural dependencies of the service (databases, etc.)
- all relevant vscode extensions pre-installed
- pre-configured linting and auto-formating
- a pre-configured debugger
- automatic license-header insertion

Moreover, inside the devcontainer, a convenience commands `dev_install` is available.
It installs the service with all development dependencies, installs pre-commit.

The installation is performed automatically when you build the devcontainer. However,
if you update dependencies in the [`./setup.cfg`](./setup.cfg) or the
[`./requirements-dev.txt`](./requirements-dev.txt), please run it again.

## License
This repository is free to use and modify according to the
[Apache 2.0 License](./LICENSE).

## Readme Generation
This readme is autogenerate, please see [`readme_generation.md`](./readme_generation.md)
for details.
