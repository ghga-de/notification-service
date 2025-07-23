[![tests](https://github.com/ghga-de/notification-service/actions/workflows/tests.yaml/badge.svg)](https://github.com/ghga-de/notification-service/actions/workflows/tests.yaml)
[![Coverage Status](https://coveralls.io/repos/github/ghga-de/notification-service/badge.svg?branch=main)](https://coveralls.io/github/ghga-de/notification-service?branch=main)

# Notification Service

The Notification Service (NS) handles notification kafka events.

## Description

The Notification Service is a microservice intended to provide general notification capabilities. At this time, notifications are only generated via Kafka events, and they are only issued via email.
However, the architecture of the service would allow for the addition of other submission options, such as REST APIs, as well as new notification channels, such as SMS, with relatively little work.

To send an email notification using this service, publish a kafka event conforming to the Notification event schema to the topic configured under "notification_topic" (see configuration details below). Because email client authentication is handled by the notification service itself, nothing beyond publishing the event is required.


### Typical operation

This service doesn't have a REST API. It is fully stateless and does not require a database.
It's a straightforward service running a Kafka consumer that listens for one kind of event.
Notification events are picked up by the consumer, validated against the Notification event schema, and sent to the Notifier module.
The Notifier looks at the notification event details and determines what to do with it.
Right now, this always means sending an email.
The information is sent to the SMTP client, where a secure connection is established and the email is dispatched.

### Email Templates

In the configuration there are two template requirements: a plaintext email template and an HTML email template. The point of these is to produce consistently formatted emails while keeping the requirements light for microservices trying to send notifications. The templates are both used to make the email. Template variables are denoted with "$", e.g. $recipient_name, and are required to match the notification schema field names defined [here](https://github.com/ghga-de/ghga-event-schemas/blob/8e535ac271e7f27b6132505aad8cf572decc7ab4/ghga_event_schemas/pydantic_.py#L304). Having both HTML and plaintext means everyone should be able to receive the emails without a problem, and most of the time they should look nice. Because email clients like Outlook, Gmail, etc. have differences in the way they render HTML emails, it is recommended that styling be kept to a minimum or to use a pre-made template where these things have been taken into account.


## Installation

We recommend using the provided Docker container.

A pre-built version is available at [docker hub](https://hub.docker.com/repository/docker/ghga/notification-service):
```bash
docker pull ghga/notification-service:5.0.0
```

Or you can build the container yourself from the [`./Dockerfile`](./Dockerfile):
```bash
# Execute in the repo's root dir:
docker build -t ghga/notification-service:5.0.0 .
```

For production-ready deployment, we recommend using Kubernetes, however,
for simple use cases, you could execute the service using docker
on a single server:
```bash
# The entrypoint is preconfigured:
docker run -p 8080:8080 ghga/notification-service:5.0.0 --help
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
- <a id="properties/enable_opentelemetry"></a>**`enable_opentelemetry`** *(boolean)*: If set to true, this will run necessary setup code.If set to false, environment variables are set that should also effectively disable autoinstrumentation. Default: `false`.

- <a id="properties/otel_trace_sampling_rate"></a>**`otel_trace_sampling_rate`** *(number)*: Determines which proportion of spans should be sampled. A value of 1.0 means all and is equivalent to the previous behaviour. Setting this to 0 will result in no spans being sampled, but this does not automatically set `enable_opentelemetry` to False. Minimum: `0`. Maximum: `1`. Default: `1.0`.

- <a id="properties/otel_exporter_protocol"></a>**`otel_exporter_protocol`** *(string)*: Specifies which protocol should be used by exporters. Must be one of: "grpc" or "http/protobuf". Default: `"http/protobuf"`.

- <a id="properties/otel_exporter_endpoint"></a>**`otel_exporter_endpoint`** *(string, format: uri, required)*: Base endpoint URL for the collector that receives content from the exporter. Length must be at least 1.


  Examples:

  ```json
  "http://localhost:4318"
  ```


- <a id="properties/mongo_dsn"></a>**`mongo_dsn`** *(string, format: multi-host-uri, required)*: MongoDB connection string. Might include credentials. For more information see: https://naiveskill.com/mongodb-connection-string/. Length must be at least 1.


  Examples:

  ```json
  "mongodb://localhost:27017"
  ```


- <a id="properties/db_name"></a>**`db_name`** *(string, required)*: Name of the database located on the MongoDB server.


  Examples:

  ```json
  "my-database"
  ```


- <a id="properties/mongo_timeout"></a>**`mongo_timeout`**: Timeout in seconds for API calls to MongoDB. The timeout applies to all steps needed to complete the operation, including server selection, connection checkout, serialization, and server-side execution. When the timeout expires, PyMongo raises a timeout exception. If set to None, the operation will not time out (default MongoDB behavior). Default: `null`.

  - **Any of**

    - <a id="properties/mongo_timeout/anyOf/0"></a>*integer*: Exclusive minimum: `0`.

    - <a id="properties/mongo_timeout/anyOf/1"></a>*null*


  Examples:

  ```json
  300
  ```


  ```json
  600
  ```


  ```json
  null
  ```


- <a id="properties/db_version_collection"></a>**`db_version_collection`** *(string, required)*: The name of the collection containing DB version information for this service.


  Examples:

  ```json
  "ifrsDbVersions"
  ```


- <a id="properties/migration_wait_sec"></a>**`migration_wait_sec`** *(integer, required)*: The number of seconds to wait before checking the DB version again.


  Examples:

  ```json
  5
  ```


  ```json
  30
  ```


  ```json
  180
  ```


- <a id="properties/migration_max_wait_sec"></a>**`migration_max_wait_sec`**: The maximum number of seconds to wait for migrations to complete before raising an error. Default: `null`.

  - **Any of**

    - <a id="properties/migration_max_wait_sec/anyOf/0"></a>*integer*

    - <a id="properties/migration_max_wait_sec/anyOf/1"></a>*null*


  Examples:

  ```json
  null
  ```


  ```json
  300
  ```


  ```json
  600
  ```


  ```json
  3600
  ```


- <a id="properties/log_level"></a>**`log_level`** *(string)*: The minimum log level to capture. Must be one of: "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", or "TRACE". Default: `"INFO"`.

- <a id="properties/service_name"></a>**`service_name`** *(string)*: Default: `"ns"`.

- <a id="properties/service_instance_id"></a>**`service_instance_id`** *(string, required)*: A string that uniquely identifies this instance across all instances of this service. A globally unique Kafka client ID will be created by concatenating the service_name and the service_instance_id.


  Examples:

  ```json
  "germany-bw-instance-001"
  ```


- <a id="properties/log_format"></a>**`log_format`**: If set, will replace JSON formatting with the specified string format. If not set, has no effect. In addition to the standard attributes, the following can also be specified: timestamp, service, instance, level, correlation_id, and details. Default: `null`.

  - **Any of**

    - <a id="properties/log_format/anyOf/0"></a>*string*

    - <a id="properties/log_format/anyOf/1"></a>*null*


  Examples:

  ```json
  "%(timestamp)s - %(service)s - %(level)s - %(message)s"
  ```


  ```json
  "%(asctime)s - Severity: %(levelno)s - %(msg)s"
  ```


- <a id="properties/log_traceback"></a>**`log_traceback`** *(boolean)*: Whether to include exception tracebacks in log messages. Default: `true`.

- <a id="properties/plaintext_email_template"></a>**`plaintext_email_template`** *(string, required)*: The plaintext template to use for email notifications.

- <a id="properties/html_email_template"></a>**`html_email_template`** *(string, required)*: The HTML template to use for email notifications.

- <a id="properties/from_address"></a>**`from_address`** *(string, format: email, required)*: The sender's address.

- <a id="properties/smtp_host"></a>**`smtp_host`** *(string, required)*: The mail server host to connect to.

- <a id="properties/smtp_port"></a>**`smtp_port`** *(integer, required)*: The port for the mail server connection.

- <a id="properties/smtp_auth"></a>**`smtp_auth`**: . Default: `null`.

  - **Any of**

    - <a id="properties/smtp_auth/anyOf/0"></a>: Refer to *[#/$defs/SmtpAuthConfig](#%24defs/SmtpAuthConfig)*.

    - <a id="properties/smtp_auth/anyOf/1"></a>*null*

- <a id="properties/use_starttls"></a>**`use_starttls`** *(boolean)*: Boolean flag indicating the use of STARTTLS. Default: `true`.

- <a id="properties/smtp_timeout"></a>**`smtp_timeout`**: The maximum amount of time (in seconds) to wait for a connection to the SMTP server. If set to `None`, the operation will wait indefinitely. Default: `60`.

  - **Any of**

    - <a id="properties/smtp_timeout/anyOf/0"></a>*number*: Exclusive minimum: `0`.

    - <a id="properties/smtp_timeout/anyOf/1"></a>*null*

- <a id="properties/notification_topic"></a>**`notification_topic`** *(string, required)*: Name of the topic used for notification events.


  Examples:

  ```json
  "notifications"
  ```


- <a id="properties/notification_type"></a>**`notification_type`** *(string, required)*: The type used for notification events.


  Examples:

  ```json
  "notification"
  ```


- <a id="properties/kafka_servers"></a>**`kafka_servers`** *(array, required)*: A list of connection strings to connect to Kafka bootstrap servers.

  - <a id="properties/kafka_servers/items"></a>**Items** *(string)*


  Examples:

  ```json
  [
      "localhost:9092"
  ]
  ```


- <a id="properties/kafka_security_protocol"></a>**`kafka_security_protocol`** *(string)*: Protocol used to communicate with brokers. Valid values are: PLAINTEXT, SSL. Must be one of: "PLAINTEXT" or "SSL". Default: `"PLAINTEXT"`.

- <a id="properties/kafka_ssl_cafile"></a>**`kafka_ssl_cafile`** *(string)*: Certificate Authority file path containing certificates used to sign broker certificates. If a CA is not specified, the default system CA will be used if found by OpenSSL. Default: `""`.

- <a id="properties/kafka_ssl_certfile"></a>**`kafka_ssl_certfile`** *(string)*: Optional filename of client certificate, as well as any CA certificates needed to establish the certificate's authenticity. Default: `""`.

- <a id="properties/kafka_ssl_keyfile"></a>**`kafka_ssl_keyfile`** *(string)*: Optional filename containing the client private key. Default: `""`.

- <a id="properties/kafka_ssl_password"></a>**`kafka_ssl_password`** *(string, format: password, write-only)*: Optional password to be used for the client private key. Default: `""`.

- <a id="properties/generate_correlation_id"></a>**`generate_correlation_id`** *(boolean)*: A flag, which, if False, will result in an error when trying to publish an event without a valid correlation ID set for the context. If True, a new correlation ID will be generated and used in the event header. Default: `true`.


  Examples:

  ```json
  true
  ```


  ```json
  false
  ```


- <a id="properties/kafka_max_message_size"></a>**`kafka_max_message_size`** *(integer)*: The largest message size that can be transmitted, in bytes, before compression. Only services that have a need to send/receive larger messages should set this. When used alongside compression, this value can be set to something greater than the broker's `message.max.bytes` field, which effectively concerns the compressed message size. Exclusive minimum: `0`. Default: `1048576`.


  Examples:

  ```json
  1048576
  ```


  ```json
  16777216
  ```


- <a id="properties/kafka_compression_type"></a>**`kafka_compression_type`**: The compression type used for messages. Valid values are: None, gzip, snappy, lz4, and zstd. If None, no compression is applied. This setting is only relevant for the producer and has no effect on the consumer. If set to a value, the producer will compress messages before sending them to the Kafka broker. If unsure, zstd provides a good balance between speed and compression ratio. Default: `null`.

  - **Any of**

    - <a id="properties/kafka_compression_type/anyOf/0"></a>*string*: Must be one of: "gzip", "snappy", "lz4", or "zstd".

    - <a id="properties/kafka_compression_type/anyOf/1"></a>*null*


  Examples:

  ```json
  null
  ```


  ```json
  "gzip"
  ```


  ```json
  "snappy"
  ```


  ```json
  "lz4"
  ```


  ```json
  "zstd"
  ```


- <a id="properties/kafka_max_retries"></a>**`kafka_max_retries`** *(integer)*: The maximum number of times to immediately retry consuming an event upon failure. Works independently of the dead letter queue. Minimum: `0`. Default: `0`.


  Examples:

  ```json
  0
  ```


  ```json
  1
  ```


  ```json
  2
  ```


  ```json
  3
  ```


  ```json
  5
  ```


- <a id="properties/kafka_enable_dlq"></a>**`kafka_enable_dlq`** *(boolean)*: A flag to toggle the dead letter queue. If set to False, the service will crash upon exhausting retries instead of publishing events to the DLQ. If set to True, the service will publish events to the DLQ topic after exhausting all retries. Default: `false`.


  Examples:

  ```json
  true
  ```


  ```json
  false
  ```


- <a id="properties/kafka_dlq_topic"></a>**`kafka_dlq_topic`** *(string)*: The name of the topic used to resolve error-causing events. Default: `"dlq"`.


  Examples:

  ```json
  "dlq"
  ```


- <a id="properties/kafka_retry_backoff"></a>**`kafka_retry_backoff`** *(integer)*: The number of seconds to wait before retrying a failed event. The backoff time is doubled for each retry attempt. Minimum: `0`. Default: `0`.


  Examples:

  ```json
  0
  ```


  ```json
  1
  ```


  ```json
  2
  ```


  ```json
  3
  ```


  ```json
  5
  ```


## Definitions


- <a id="%24defs/SmtpAuthConfig"></a>**`SmtpAuthConfig`** *(object)*: Model to encapsulate SMTP authentication details.

  - <a id="%24defs/SmtpAuthConfig/properties/username"></a>**`username`** *(string, required)*: The login username or email.

  - <a id="%24defs/SmtpAuthConfig/properties/password"></a>**`password`** *(string, format: password, required and write-only)*: The login password.


### Usage:

A template YAML for configuring the service can be found at
[`./example_config.yaml`](./example_config.yaml).
Please adapt it, rename it to `.ns.yaml`, and place it in one of the following locations:
- in the current working directory where you execute the service (on Linux: `./.ns.yaml`)
- in your home directory (on Linux: `~/.ns.yaml`)

The config yaml will be automatically parsed by the service.

**Important: If you are using containers, the locations refer to paths within the container.**

All parameters mentioned in the [`./example_config.yaml`](./example_config.yaml)
could also be set using environment variables or file secrets.

For naming the environment variables, just prefix the parameter name with `ns_`,
e.g. for the `host` set an environment variable named `ns_host`
(you may use both upper or lower cases, however, it is standard to define all env
variables in upper cases).

To use file secrets, please refer to the
[corresponding section](https://pydantic-docs.helpmanual.io/usage/settings/#secret-support)
of the pydantic documentation.

## HTTP API
An OpenAPI specification for this service can be found [here](./openapi.yaml).

## Architecture and Design:
This is a Python-based service following the Triple Hexagonal Architecture pattern.
It uses protocol/provider pairs and dependency injection mechanisms provided by the
[hexkit](https://github.com/ghga-de/hexkit) library.


### Testing
The only notable thing about the test setup is that it uses a local test server (tests/fixtures/server.py) via [aiosmtpd](https://aiosmtpd.readthedocs.io/en/latest/), which has sort of replaced the old smtpd module. There is a DummyServer, which has an 'expect_email()' method that is used similarly to the [expect_events()](https://github.com/ghga-de/hexkit/blob/7382c19b84136ea5b1652087ba1da4890267b1b5/hexkit/providers/akafka/testutils.py#L368) method from hexkit's kafka testing module. It can perform simple a authentication check so error handling can be tested. When an email is sent to the test server, the connection is closed and the received/expected emails are compared to make sure that the header and body content is intact. This enables testing the flow of sending an email without actually issuing any real emails and without using real credentials.


## Development

For setting up the development environment, we rely on the
[devcontainer feature](https://code.visualstudio.com/docs/remote/containers) of VS Code
in combination with Docker Compose.

To use it, you have to have Docker Compose as well as VS Code with its "Remote - Containers"
extension (`ms-vscode-remote.remote-containers`) installed.
Then open this repository in VS Code and run the command
`Remote-Containers: Reopen in Container` from the VS Code "Command Palette".

This will give you a full-fledged, pre-configured development environment including:
- infrastructural dependencies of the service (databases, etc.)
- all relevant VS Code extensions pre-installed
- pre-configured linting and auto-formatting
- a pre-configured debugger
- automatic license-header insertion

Moreover, inside the devcontainer, a command `dev_install` is available for convenience.
It installs the service with all development dependencies, and it installs pre-commit.

The installation is performed automatically when you build the devcontainer. However,
if you update dependencies in the [`./pyproject.toml`](./pyproject.toml) or the
[`lock/requirements-dev.txt`](./lock/requirements-dev.txt), please run it again.

## License

This repository is free to use and modify according to the
[Apache 2.0 License](./LICENSE).

## README Generation

This README file is auto-generated, please see [.readme_generation/README.md](./.readme_generation/README.md)
for details.
