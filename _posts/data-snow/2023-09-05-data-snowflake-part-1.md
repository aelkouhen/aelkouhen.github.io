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

In this article, I will illustrate data ingestion and integration using Snowflake’s first-party methods to meet the different data pipeline needs, from batch to continuous ingestion. These methods include but are not limited to `INSERT`, `COPY INTO`, `Snowpipe`, `Snowpipe Streaming` or the `Kafka Connector`.

# Batch Ingestion
Snowflake supports ingesting data in multiple formats and compression methods at any file volume. Features such as schema detection and schema evolution simplify data loading directly into structured tables without needing to split, merge, or convert files. First-party mechanisms for batch data ingestion are INSERT, COPY INTO, and Snowpipe.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/4edf0d68-ed96-46f3-8c27-ded686305e4a){: .mx-auto.d-block :} *Snowflake's ingestion options.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

## Insert

The `INSERT` command is the most straightforward ingestion mechanism for bringing a small amount of data. It updates a table by inserting one or more rows. The values inserted into each column in the table or the query results can be explicitly specified.
Bellow the syntax of the `INSERT` statement:

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

## COPY INTO

The `COPY INTO` command enables loading batches of data from staged files to an existing table. The files must already be staged in one of the following locations:

- Named internal stage (or table/user stage). Files can be staged using the PUT command.
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

The COPY command relies on a customer-managed warehouse, so there are some elements to consider when choosing the appropriate warehouse size. The most critical aspect is the degree of parallelism, as each thread can ingest a single file simultaneously. The XS Warehouse provides eight threads, and each increment of warehouse size doubles the amount of available threads. The simplified conclusion is that for a significantly large number of files, you would expect optimal parallelism for each given warehouse size, halving the time to ingest the large batch of files for every upsize step. However, this speedup can be limited by factors such as networking or I/O delays in real-life scenarios. These factors should be considered for larger ingestion jobs and might require individual benchmarking during the planning phase.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/ee7bf73b-ac4d-480d-883f-0a66ad29e1d6){: .mx-auto.d-block :} *Parallel loading of files into Snowflake.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

There is a fixed, per-file overhead charge for Snowpipe in addition to compute usage costs. As a result, for smaller single-digit MiB or smaller file sizes, Snowpipe can be less cost-effective (in credits/TiB) than `COPY`, depending on file arrival rate, size of the warehouse, and non-COPY use of the Cloud Services Layer. Correspondingly, larger file sizes of at least 100 MiB are typically more efficient.

Generally, we recommend file sizes above 10 MiB, with the 100 to 250 MiB range typically offering the best price/performance. As a result, we recommend aggregating smaller data files for batch ingestion. We also recommend not exceeding 5 GiB file sizes and splitting into smaller files to take advantage of parallelization. With a larger file, an erroneous record at the end may cause an ingestion job to fail and restart depending on the `ON_ERROR` option.

Finally, using the most explicit path allows `COPY` to list and load data without traversing the entire bucket, thereby saving compute and network usage.






