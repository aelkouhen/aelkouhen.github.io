---
layout: post
title: Data & Snowflake series - part 1
subtitle:  Data Ingestion with Snowflake
thumbnail-img: 
share-img: 
tags: []
comments: true
---

Organizations are experiencing significant data asset growth and leveraging Snowflake to gather data insights to grow their businesses. This data includes structured, semi-structured, and unstructured data coming in batches or streams.

As you’ve seen in previous posts, Data ingestion is the first stage of the data lifecycle. Here, data is collected from various internal sources like databases, CRMs, ERPs, legacy systems, external ones such as surveys, and third-party providers. This is an important step because it ensures the excellent working of subsequent stages in the data lifecycle.

In this stage, raw data are extracted from one or more data sources, replicated, and then ingested into a storage location called `stage`. Once data is integrated into Snowflake, you can use powerful features such as Snowpark, Data Sharing, and more to derive value from data to send to reporting tools, partners, and customers. 

In this article, I will illustrate data ingestion and integration using Snowflake’s first-party methods to meet the different data pipeline needs, from batch to continuous ingestion. These methods include but are not limited to `INSERT`, `COPY`, `Snowpipe`, `Snowpipe Streaming`, or the `Dynamic Tables`.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/4edf0d68-ed96-46f3-8c27-ded686305e4a){: .mx-auto.d-block :} *Snowflake's ingestion options.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

# Batch Ingestion
Snowflake supports ingesting data in multiple formats and compression methods at any file volume. Features such as schema detection and schema evolution simplify data loading directly into structured tables without needing to split, merge, or convert files. First-party mechanisms for batch data ingestion are `INSERT`, `COPY`, and `Snowpipe`.

## Insert

The `INSERT` command is the most straightforward ingestion mechanism for bringing a small amount of data. It updates a table by inserting one or more rows. The values inserted into each column in the table or the query results can be explicitly specified. Bellow the syntax of the `INSERT` statement:

{% highlight sql linenos %}
INSERT [ OVERWRITE ] INTO <target_table> [ ( <target_col_name> [ , ... ] ) ]
       {
VALUES ( { <value> | DEFAULT | NULL } [ , ... ] ) [ , ( ... ) ]  |  <query>
       }
{% endhighlight %}

You can insert multiple rows using explicitly specified values in a comma-separated list in the `VALUES` clause:

{% highlight sql linenos %}
INSERT INTO employees
  VALUES
  ('Lysandra','Reeves','1-212-759-3751','New York',10018),
  ('Michael','Arnett','1-650-230-8467','San Francisco',94116);

SELECT * FROM employees;

+------------+-----------+----------------+---------------+-------------+
| FIRST_NAME | LAST_NAME | WORKPHONE      | CITY          | POSTAL_CODE |
|------------+-----------+----------------+---------------+-------------|
| Lysandra   | Reeves    | 1-212-759-3751 | New York      | 10018       |
| Michael    | Arnett    | 1-650-230-8467 | San Francisco | 94116       |
+------------+-----------+----------------+---------------+-------------
{% endhighlight %}

You can also insert multiple rows using a `select` Query. For example:

{% highlight sql linenos %}
SELECT * FROM contractors;

+------------------+-----------------+----------------+---------------+----------+
| CONTRACTOR_FIRST | CONTRACTOR_LAST | WORKNUM        | CITY          | ZIP_CODE |
|------------------+-----------------+----------------+---------------+----------|
| Bradley          | Greenbloom      | 1-650-445-0676 | San Francisco | 94110    |
| Cole             | Simpson         | 1-212-285-8904 | New York      | 10001    |
| Laurel           | Slater          | 1-650-633-4495 | San Francisco | 94115    |
+------------------+-----------------+----------------+---------------+----------+

INSERT INTO employees(first_name, last_name, workphone, city,postal_code)
  SELECT
    contractor_first,contractor_last,worknum,NULL,zip_code
  FROM contractors
  WHERE CONTAINS(worknum,'650');

SELECT * FROM employees;

+------------+------------+----------------+---------------+-------------+
| FIRST_NAME | LAST_NAME  | WORKPHONE      | CITY          | POSTAL_CODE |
|------------+------------+----------------+---------------+-------------|
| Lysandra   | Reeves     | 1-212-759-3751 | New York      | 10018       |
| Michael    | Arnett     | 1-650-230-8467 | San Francisco | 94116       |
| Bradley    | Greenbloom | 1-650-445-0676 | NULL          | 94110       |
| Laurel     | Slater     | 1-650-633-4495 | NULL          | 94115       |
+------------+------------+----------------+---------------+-------------+
{% endhighlight %}

You can also insert multiple JSON objects into a VARIANT column in a table:
{% highlight sql json linenos %}
INSERT INTO prospects
  SELECT PARSE_JSON(column1)
  FROM VALUES
  ('{
    "_id": "57a37f7d9e2b478c2d8a608b",
    "name": {
      "first": "Lydia",
      "last": "Williamson"
    },
    "company": "Miralinz",
    "email": "lydia.williamson@miralinz.info",
    "phone": "+1 (914) 486-2525",
    "address": "268 Havens Place, Dunbar, Rhode Island, 7725"
  }')
  , ('{
    "_id": "57a37f7d622a2b1f90698c01",
    "name": {
      "first": "Denise",
      "last": "Holloway"
    },
    "company": "DIGIGEN",
    "email": "denise.holloway@digigen.net",
    "phone": "+1 (979) 587-3021",
    "address": "441 Dover Street, Ada, New Mexico, 5922"
  }');
{% endhighlight %}

Finally, if you use the `OVERWRITE` clause with a multi-row insert, the statement rebuilds and overrides the table with the content of the `VALUES` clause. 

As you can see, the `INSERT` statement is the simplest way to ingest data into Snowflake, however, it has scalability and error-handling limitations when dealing with data sets exceeding the single-digit MiB range. For larger data sets, data engineers typically leverage the option to use an ETL/ELT tool to ingest data, or preferably use object storage as an intermediate step alongside `COPY INTO` or `Snowpipe`. 

## COPY

The `COPY` command enables loading batches of data from staged files to an existing table. The files must already be staged in one of the following locations:

- Named internal stage (or table/user stage). Files can be staged using the `PUT` command.
- Named external stage that references an external location (Amazon S3, Google Cloud Storage, or Microsoft Azure).
- External location (Amazon S3, Google Cloud Storage, or Microsoft Azure).

`COPY INTO` provides increased control than `INSERT` but requires the customer to manage the compute (via settings such as warehouse size and job duration). In fact, this command uses a predefined, customer-managed virtual warehouse to read the data from the remote storage, optionally transform its structure, and write it to native Snowflake tables.

These on-the-fly transformations may include:

- Column reordering
- Column omission
- Casts
- Text truncation

COPY fits nicely in an existing infrastructure where one or more warehouses are managed for size and suspension/resumption to achieve peak price to performance of various workloads, such as `SELECT` queries or data transformations. Here is the syntax of a simple `COPY INTO` command:

{% highlight sql json linenos %}
COPY INTO [<namespace>.]<table_name>
     FROM { internalStage | externalStage | externalLocation }
[ FILES = ( '<file_name>' [ , '<file_name>' ] [ , ... ] ) ]
[ PATTERN = '<regex_pattern>' ]
[ FILE_FORMAT = ( { FORMAT_NAME = '[<namespace>.]<file_format_name>' |
                    TYPE = { CSV | JSON | AVRO | ORC | PARQUET | XML } [ formatTypeOptions ] } ) ]
[ copyOptions ]
[ VALIDATION_MODE = RETURN_<n>_ROWS | RETURN_ERRORS | RETURN_ALL_ERRORS ]
{% endhighlight %}

Where:

{% highlight sql linenos %}
internalStage ::=
    @[<namespace>.]<int_stage_name>[/<path>]
  | @[<namespace>.]%<table_name>[/<path>]
  | @~[/<path>]
{% endhighlight %}

For example, to load files from a named internal stage into a table the command is:

{% highlight sql linenos %}
COPY INTO mytable
FROM @my_int_stage;
{% endhighlight %}

You can load files from a named external stage you created using the `CREATE STAGE` command. The named external stage references an external location (Amazon S3, Google Cloud Storage, or Microsoft Azure). For example:

{% highlight sql linenos %}
COPY INTO mytable
  FROM s3://mybucket/data/files
  CREDENTIALS=(AWS_KEY_ID='$AWS_ACCESS_KEY_ID' AWS_SECRET_KEY='$AWS_SECRET_ACCESS_KEY')
  STORAGE_INTEGRATION = myint
  ENCRYPTION=(MASTER_KEY = 'eSx...')
  FILE_FORMAT = (FORMAT_NAME = my_csv_format);
{% endhighlight %}

{% highlight sql linenos %}
COPY INTO mytable
  FROM 'gcs://mybucket/data/files'
  STORAGE_INTEGRATION = myint
  FILE_FORMAT = (FORMAT_NAME = my_csv_format);
{% endhighlight %}

{% highlight sql linenos %}
COPY INTO mytable
  FROM 'azure://myaccount.blob.core.windows.net/mycontainer/data/files'
  CREDENTIALS=(AZURE_SAS_TOKEN='?sv=2016-05-31&ss=b&srt=sco&sp=rwdl&se=2018-06-27T10:05:50Z&st=2017-06-27T02:05:50Z&spr=https,http&sig=bgqQwoXwxzuD2GJfagRg7VOS8hzNr3QLT7rhS8OFRLQ%3D')
  ENCRYPTION=(TYPE='AZURE_CSE' MASTER_KEY = 'kPx...')
  FILE_FORMAT = (FORMAT_NAME = my_csv_format);
{% endhighlight %}

For data load with transformation, the command syntax is as follows:

{% highlight sql linenos %}
COPY INTO [<namespace>.]<table_name> [ ( <col_name> [ , <col_name> ... ] ) ]
     FROM ( SELECT [<alias>.]$<file_col_num>[.<element>] [ , [<alias>.]$<file_col_num>[.<element>] ... ]
            FROM { internalStage | externalStage } )
[ FILES = ( '<file_name>' [ , '<file_name>' ] [ , ... ] ) ]
[ PATTERN = '<regex_pattern>' ]
[ FILE_FORMAT = ( { FORMAT_NAME = '[<namespace>.]<file_format_name>' |
                    TYPE = { CSV | JSON | AVRO | ORC | PARQUET | XML } [ formatTypeOptions ] } ) ]
[ copyOptions ]
{% endhighlight %}

The `COPY` command relies on a customer-managed warehouse, so there are some elements to consider when choosing the appropriate warehouse size. The most critical aspect is the degree of parallelism, as each thread can ingest a single file simultaneously. The XS Warehouse provides eight threads, and each increment of warehouse size doubles the amount of available threads. The simplified conclusion is that for a significantly large number of files, you would expect optimal parallelism for each given warehouse size, halving the time to ingest the large batch of files for every upsize step. However, this speedup can be limited by factors such as networking or I/O delays in real-life scenarios. These factors should be considered for larger ingestion jobs and might require individual benchmarking during the planning phase.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/ee7bf73b-ac4d-480d-883f-0a66ad29e1d6){: .mx-auto.d-block :} *Parallel loading of files into Snowflake.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

There is a fixed, per-file overhead charge for Snowpipe in addition to compute usage costs. As a result, for smaller single-digit MiB or smaller file sizes, Snowpipe can be less cost-effective (in credits/TiB) than `COPY`, depending on file arrival rate, size of the warehouse, and non-COPY use of the Cloud Services Layer. Correspondingly, larger file sizes of at least 100 MiB are typically more efficient.

Generally, we recommend file sizes above 10 MiB, with the 100 to 250 MiB range typically offering the best price/performance. As a result, we recommend aggregating smaller data files for batch ingestion. We also recommend not exceeding 5 GiB file sizes and splitting into smaller files to take advantage of parallelization. With a larger file, an erroneous record at the end may cause an ingestion job to fail and restart depending on the `ON_ERROR` option.

Finally, using the most explicit path allows `COPY` to list and load data without traversing the entire bucket, thereby saving compute and network usage.

# Continuous Data Ingestion

This option is designed to load small volumes of data (i.e. micro-batches) and incrementally make them available for analysis. For example, Snowpipe loads data within minutes after files are added to a stage and submitted for ingestion. This ensures users have the latest results, as soon as the raw data is available.

## Snowpipe

Snowpipe is a serverless service that enables loading data from files as soon as they’re available in a Snowflake stage (locations where data files are stored for loading/unloading). With Snowpipe, data can be loaded from files in micro-batches rather than executing `COPY` statements on a schedule. Unlike `COPY INTO`, which is a synchronous process that returns the load status, Snowpipe file ingestion is asynchronous, and processing status needs to be observed explicitly.

Snowpipe uses compute resources provided by Snowflake (a serverless compute model). These Snowflake-provided resources are automatically resized and scaled up or down as required, and they are charged and itemized using per-second billing. Data ingestion is charged based upon the actual workloads.

A pipe is a named, first-class Snowflake object that contains a `COPY` statement used by Snowpipe. The `COPY` statement identifies the source location of the data files (i.e., a stage) and a target table and supports the same transformation options as when bulk loading data. All data types are supported, including semi-structured data types such as JSON and Avro.

In addition, data pipelines can leverage Snowpipe to continuously load micro-batches of data into staging tables for transformation and optimization using automated tasks and the change data capture (CDC) information in streams. For instance, auto-ingesting Snowpipe is the preferred approach. This approach continuously loads new data to the target table by reacting to newly created files in the source bucket.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/ccc7186f-f8bf-470e-b974-6cdb90f46fbb){: .mx-auto.d-block :} *Auto-ingest Snowpipe setup.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

In the example above, Snowpipe relies on the cloud vendor-specific system for event distribution, such as AWS SQS or SNS, Azure Event Grid, or GCP Pub/Sub. This setup requires corresponding privileges to the cloud account to deliver event notifications from the source bucket to Snowpipe.

The following example creates a stage named `mystage` in the active schema for the user session. The cloud storage URL includes the path files. The stage references a storage integration named `my_storage_int`. First, we create the S3 storage integration and the stage:

{% highlight sql linenos %}
CREATE STORAGE INTEGRATION my_storage_int
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::001234567890:role/myrole'
  STORAGE_ALLOWED_LOCATIONS = ('s3://mybucket1/mypath1/', 's3://mybucket2/mypath2/')
  STORAGE_BLOCKED_LOCATIONS = ('s3://mybucket1/mypath1/sensitivedata/', 's3://mybucket2/mypath2/sensitivedata/');
{% endhighlight %}

{% highlight sql linenos %}
USE SCHEMA snowpipe_db.public;

CREATE STAGE mystage
  URL = 's3://mybucket/load/files'
  STORAGE_INTEGRATION = my_storage_int;
{% endhighlight %}

Then, we create a pipe named `mypipe` in the active schema for the user session. The pipe loads the data from files staged in the `mystage` stage into the `mytable` table and subscribes to the `SNS` topic ARN that propagates the notification:

{% highlight sql linenos %}
create pipe snowpipe_db.public.mypipe
  auto_ingest=true
  aws_sns_topic='<sns_topic_arn>'
  as
    copy into snowpipe_db.public.mytable
    from @snowpipe_db.public.mystage
  file_format = (type = 'JSON');
{% endhighlight %}

But in cases where an event service can not be set up or an existing data pipeline infrastructure is in place, a REST API-triggered Snowpipe is a suitable alternative. It is also currently the only option if an internal stage is used for storing the raw files. Most commonly, the REST API approach is used by ETL/ELT tools that don’t want to put the burden of creating object storage on the end user and instead use a Snowflake-managed Internal Stage.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/cea02511-e0b3-4b98-8e1a-c115d23f0c64){: .mx-auto.d-block :} *API-triggered Snowpipe setup.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Similarly to the Auto-ingest setup, you need here to create a stage, and an integration to S3 storage. The pipe is created without the SNS topic arn and the `auto_ingest` keyword.  

{% highlight sql linenos %}
create pipe snowpipe_db.public.mypipe as
    copy into snowpipe_db.public.mytable
    from @snowpipe_db.public.mystage
  file_format = (type = 'JSON');
{% endhighlight %}

Then, we create a user with key-pair authentication. The user credentials will be used when calling the Snowpipe API endpoints:

{% highlight sql linenos %}
use role securityadmin;

create user snowpipeuser 
  login_name = 'snowpipeuser'
  default_role = SYSADMIN
  default_namespace = snowpipe_test.public
  rsa_public_key = '<RSA Public Key value>' ;
{% endhighlight %}

You can validate that the user has been successfully created by connecting via SnowSQL. Use the `--private-key-path` switch to tell SnowSQL to use key-pair authentication.

```bash
snowsql -a sedemo.us-east-1-gov.aws -u snowpipeuser --private-key-path rsa_key.p8
```

Authentication via the REST endpoint expects a valid JSON Web Token (JWT). These tokens are generally valid for about 60 minutes and then need to be regenerated. If you want to test the REST API using `Postman` or `curl`, you must generate one from the RSA certificate.

Once you generate the JWT, the REST endpoint should reference your Snowflake account and the fully qualified pipe name. The call you’re testing is a `POST` to the `insertFiles` method.

```bash
curl -H 'Accept: application/json' -H "Authorization: Bearer ${TOKEN}" -d @path/to/data.csv https://sedemo.us-east-1-gov.aws.snowflakecomputing.com/v1/data/pipes/snowpipe_db.public.mypipe/insertFiles
```

The responseCode should be `SUCCESS`. It’s important to remember that Snowpipe will not ingest the same file twice. The call will succeed, but no data will be ingested. This is by design. To retest, either use a different filename or drop and recreate the table.

The ingestion should already be finished, so you can return to the Snowflake UI and run a select statement on the table.

## Snowpipe Streaming

Snowpipe Streaming enables serverless streaming data ingestion directly into Snowflake tables without requiring staging files (bypassing cloud object storage) with exact-once and ordered delivery. This architecture results in lower latencies and correspondingly lower costs for loading any volume of data, making it a powerful tool for handling near real-time data streams.

The API is intended to complement Snowpipe, not replace it. Use the Snowpipe Streaming API in streaming scenarios where data is streamed via rows (for example, Apache Kafka topics) instead of writing to files. The API fits into an ingest workflow including an existing custom Java application that produces or receives records. The API removes the need to create files to load data into Snowflake tables and enables the automatic, continuous loading of data streams into Snowflake as the data becomes available. You also get new functionality, such as exactly-once delivery, ordered ingestion, and error handling with dead-letter queue (DLQ) support.

Snowpipe Streaming is also available for the Snowflake Connector for Kafka, which offers an easy upgrade path to take advantage of the lower latency and lower cost loads.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/b80c58c5-749e-4661-930f-fa5133a63a86){: .mx-auto.d-block :} *Snowpipe Streaming API.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

The API ingests rows through one or more channels. A channel represents a logical, named streaming connection to Snowflake for loading data into a table. A single channel maps to exactly one table in Snowflake; however, multiple channels can point to the same table. The Client SDK can open multiple channels to multiple tables; however, the SDK cannot open channels across accounts. The ordering of rows and their corresponding offset tokens are preserved within a channel but not across channels that point to the same table.

Channels are meant to be long-lived when a client actively inserts data and should be reused as offset token information is retained. Data inside the channel is automatically flushed every 1 second by default and doesn't need to be closed.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/ebb8d629-c17a-4002-a732-bd60c9f6525c){: .mx-auto.d-block :} *Streaming channels.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Ingesting Kafka topics into Snowflake tables

Files are a common denominator across processes that produce data—whether they’re on-premises or in the cloud. Most ingestion happens in batches, where a file forms a physical and sometimes logical batch. Today, file-based ingestion utilizing COPY or auto-ingest Snowpipe is the primary source for data that is ingested into Snowflake. 

Kafka (or its cloud-specific equivalents) provides an additional data collection and distribution infrastructure to write and read streams of records. If event records need to be distributed to multiple sinks—mostly as streams—then such an arrangement makes sense. Stream processing (in contrast to batch processing) typically allows for lower data volumes at more frequent intervals for near real-time latency.

In the case of the Snowflake Connector for Kafka, the same file size consideration mentioned earlier still applies due to its use of Snowpipe for data ingestion. However, there may be a trade-off between the desired maximum latency and a larger file size for cost optimization. The right file size for your application may not fit the above guidance, and that is acceptable as long as the cost implications are measured and considered. 

In addition, the amount of memory available in a Kafka Connect cluster node may limit the buffer size and, therefore, the file size. In that case, it is still a good idea to configure the timer value (buffer.flush.time) to ensure that files smaller than the buffer size are less likely.

Two elements—Buffer.flush.time and Buffer.flush.size—decide the total number of files per minute that you are sending to Snowflake via the Kafka connector. So tuning these parameters is very beneficial in terms of performance. Here’s a look at two examples:
- If you set buffer.flush.time to 240 seconds instead of 120 seconds without changing anything else, it will reduce the base files/minute rate by a factor of 2 (reaching buffer size earlier than time will affect these calculations).
- If you increase the Buffer.flush.size to 100 MB without changing anything else, the base files/minute rate will be reduced by a factor of 20 (reaching the max buffer size earlier than the max buffer time will affect these calculations).

For testing this setup locally, we will need:
- open-source Apache Kafka 2.13-3.1.0 installed locally,
- Snowflake Kafka Connector 1.9.1.jar (or new version),
- OpenJDK <= 15.0.2,
- a Snowflake user for streaming Snowpipe with an SSH key defined as the authentication method.

First, you need to create a separate user that you are going to use for Streaming Snowpipe. Please remember to replace <YOURPUBLICKEY> with the corresponding details. Note, in this case, you need to remove the begin/end comment lines from the key file (e.g. —–BEGIN PUBLIC KEY—–), but please keep the new-line characters.

{% highlight sql linenos %}
create user snowpipe_streaming_user password='',  default_role = accountadmin, rsa_public_key='<YOURPUBLICKEY>';

grant role accountadmin  to user snowpipe_streaming_user;
{% endhighlight %}

Here, you will create the database you will use later on.

{% highlight sql linenos %}
CREATE OR REPLACE DATABASE hol_streaming;

USE DATABASE hol_streaming;

CREATE OR REPLACE WAREHOUSE hol_streaming_wh WITH WAREHOUSE_SIZE = 'XSMALL' MIN_CLUSTER_COUNT = 1 MAX_CLUSTER_COUNT = 1 AUTO_SUSPEND = 60;
{% endhighlight %}

Then, let's open the terminal and run the following commands to download Kafka and Snowflake Kafka connector:

```bash
mkdir HOL_kafka
cd HOL_kafka

curl https://archive.apache.org/dist/kafka/3.3.1/kafka_2.13-3.3.1.tgz --output kafka_2.13-3.3.1.tgz
tar -xzf kafka_2.13-3.3.1.tgz

cd kafka_2.13-3.3.1/libs
curl https://repo1.maven.org/maven2/com/snowflake/snowflake-kafka-connector/1.9.1/snowflake-kafka-connector-1.9.1.jar --output snowflake-kafka-connector-1.9.1.jar
```

Create the configuration file `config/SF_connect.properties` with the following parameters. Remember to replace `<YOURACCOUNT>` & `<YOURPRIVATEKEY>` with the corresponding details. Also, please note when adding a private key, you need to remove all new line characters as well as beginning and ending comments (e.g., —–BEGIN PRIVATE KEY—–):

```properties
name=snowpipe_streaming_ingest
connector.class=com.snowflake.kafka.connector.SnowflakeSinkConnector
tasks.max=1
topics=customer_data_topic
snowflake.topic2table.map=customer_data_topic:customer_data_stream_stg
buffer.count.records=1
buffer.flush.time=10
buffer.size.bytes=20000000
snowflake.url.name=<YOURACCOUNT>.snowflakecomputing.com:443
snowflake.user.name=SNOWPIPE_STREAMING_USER
snowflake.private.key=<YOURPRIVATEKEY>
snowflake.database.name=HOL_STREAMING
snowflake.schema.name=PUBLIC
snowflake.role.name=ACCOUNTADMIN
snowflake.ingestion.method=SNOWPIPE_STREAMING
key.converter=org.apache.kafka.connect.json.JsonConverter
value.converter=org.apache.kafka.connect.json.JsonConverter
key.converter.schemas.enable=false
value.converter.schemas.enable=false
```

Now, this is out of the way. Let's start this all together. Please note that you might get errors for this step if you use JDK>=v15. And you might need a few separate terminal sessions for this:

Session 1:
```bash
bin/zookeeper-server-start.sh config/zookeeper.properties
```
Session 2:
```bash
bin/kafka-server-start.sh config/server.properties
```
Session 3:
```bash
bin/connect-standalone.sh ./config/connect-standalone.properties ./config/SF_connect.properties
```

Now, open another terminal session (Session 4) and run the kafka-console-producer. This utility is a simple way to put some data into the topic manually.

```bash
bin/kafka-console-producer.sh --topic customer_data_topic --bootstrap-server localhost:9092
```

Let's get back to Snowsight and run the following query to generate some sample customer data in JSON format:

```sql
SELECT object_construct(*)
  FROM snowflake_sample_data.tpch_sf10.customer limit 200;
```

As you can see, Snowpipe Streaming is a fantastic new capability that can significantly reduce integration latency and improve pipeline efficiency. It also opens up new opportunities for your business, providing near-real-time insights and operational reporting, among other benefits.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/45297412-ed21-4725-b641-3a39f722e6f0)

### Snowpipe Streaming and Dynamic Tables for Real-Time Ingestion

[Dynamic tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-about) are the building blocks of declarative data transformation pipelines. They significantly simplify data engineering in Snowflake and provide a reliable, cost-effective, and automated way to transform your data for consumption. Instead of defining data transformation steps as a series of tasks and having to monitor dependencies and scheduling, you can determine the end state of the transformation using dynamic tables and leave the complex pipeline management to Snowflake.

![](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/0ce85521-7009-49bc-937e-25446bfd6960){: .mx-auto.d-block :} *Dynamic tables.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

Hereafter, we will take you through a scenario of using Snowflake's Snowpipe Streaming to ingest a simulated stream. Then, we will utilize Dynamic tables to transform and prepare the raw ingested JSON payloads into ready-for-analytics datasets. These are two of Snowflake's powerful Data Engineering innovations for ingestion and transformation.

The simulated datafeed will be Stock Limit Orders, with new, changed, and cancelled orders represented as RDBMS transaction logs captured from INSERT, UPDATE, and DELETE database events. These events will be transmitted as JSON payloads and land into a Snowflake table with a variant data column. This is the same type of stream ingestion typically created by Change-Data-Capture (CDC) agents that parse transaction logs of a database or event notification mechanisms of modern applications. However, this could simulate any type of stream in any industry. This streaming ingestion use case was modeled similarly to one previously handled with Snowflake's Kafka Connector, but no Kafka is necessary for this use case as a Snowpipe Streaming client can enable replacing the Kafka middleware infrastructure, saving cost & complexity. Once landed, Dynamic Tables are purpose-built Snowflake objects for Data Engineering to transform the raw data into data ready for insights.

Our Source ‘database' has stock trades for the Dow Jones Industrials, [30 US stocks](https://www.nyse.com/quote/index/DJI). On average 200M-400M stock trades are executed per day. Our agent will be capturing Limit Order transaction events for these 30 stocks, which are new orders, updates to orders (changes in quantity or the limit price), and orders that are canceled. For this simulation, there are 3 new orders for every 2 updates, and then one cancellation. This scenario's datastream will first reproduce a heavy workload of an initial market opening session and, secondly, a more modest continuous flow. Snowflake data consumers want to see three perspectives on limit orders: what is the "current" list of orders that filters out stale and canceled orders, a historical table showing every event on the source (in a traditional slowly changing dimension format), and current orders summarized by stock ticker symbol and by long or short position. Latency needs to be minimized, 1-2 minutes would be ideal for the end-to-end process.

More Snowflake capabilities can further enrich your incoming data using Snowflake Data Marketplace data, train and deploy machine learning models, perform fraud detection, and other use cases. We will cover these in future posts.

First, you need to extract this [file](/assets/java/CDCSimulatorApp.zip), which will create a CDCSimulatorApp directory and many files within it. 

From your terminal, navigate to your working directory, then the directory extracted (CDCSimulatorApp) and run these two commands:

{% highlight shell linenos %}
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
{% endhighlight %}

In Snowflake, create a dedicated role for your Streaming Application. For this, run these commands, using the Public Key generated in the previous step (the content of `rsa_key.pub`):

{% highlight sql linenos %}
create role if not exists VHOL_CDC_AGENT;
create or replace user vhol_streaming1 COMMENT="Creating for VHOL";
alter user vhol_streaming1 set rsa_public_key='<Paste Your Public Key Here>';
{% endhighlight %}

You will need to edit the snowflake.properties file to match your Snowflake account name (two places):

{% highlight properties linenos %}
user=vhol_streaming1
role=VHOL_CDC_AGENT
account=<MY_SNOWFLAKE_ACCOUNT>
warehouse=VHOL_CDC_WH
private_key_file=rsa_key.p8
host=<ACCOUNT_IDENTIFIER>.snowflakecomputing.com
database=VHOL_ENG_CDC
schema=ENG
table=CDC_STREAMING_TABLE
channel_name=channel_1
AES_KEY=O90hS0k9qHdsMDkPe46ZcQ==
TOKEN_KEY=11
DEBUG=FALSE
SHOW_KEYS=TRUE
NUM_ROWS=1000000
{% endhighlight %}

Create new roles for this tutorial and grant permissions:

{% highlight sql linenos %}
use role ACCOUNTADMIN;
set myname = current_user();
create role if not exists VHOL;
grant role VHOL to user identifier($myname);
grant role VHOL_CDC_AGENT to user vhol_streaming1;
{% endhighlight %}

Create a dedicated virtual compute warehouse (size XS), then create the database used throughout this tutorial:

{% highlight sql linenos %}
create or replace warehouse VHOL_CDC_WH WAREHOUSE_SIZE = XSMALL, AUTO_SUSPEND = 5, AUTO_RESUME= TRUE;
grant all privileges on warehouse VHOL_CDC_WH to role VHOL;
{% endhighlight %}

{% highlight sql linenos %}
create database VHOL_ENG_CDC;
use database VHOL_ENG_CDC;
grant ownership on schema PUBLIC to role VHOL;
revoke all privileges on database VHOL_ENG_CDC from role ACCOUNTADMIN;
grant ownership on database VHOL_ENG_CDC to role VHOL;
{% endhighlight %}

{% highlight sql linenos %}
use role VHOL;
use database VHOL_ENG_CDC;
create schema ENG;
use VHOL_ENG_CDC.ENG;
use warehouse VHOL_CDC_WH;
grant usage on database VHOL_ENG_CDC to role VHOL_CDC_AGENT;
grant usage on schema ENG to role VHOL_CDC_AGENT;
grant usage on database VHOL_ENG_CDC to role PUBLIC;
grant usage on schema PUBLIC to role PUBLIC;
{% endhighlight %}

Create a Staging/Landing Table, where all incoming data will land initially. Each row will contain a transaction, but JSON will be stored as a VARIANT datatype within Snowflake.

{% highlight sql linenos %}
create or replace table ENG.CDC_STREAMING_TABLE (RECORD_CONTENT variant);
grant insert on table ENG.CDC_STREAMING_TABLE to role VHOL_CDC_AGENT;
select * from CDC_STREAMING_TABLE;
select count(*) from CDC_STREAMING_TABLE;
{% endhighlight %}

You can run `Test.sh` to ensure that everything is set correctly. Snowflake is ready for ingestion now!

















 

















