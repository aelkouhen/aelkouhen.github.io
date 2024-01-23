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

Finally, if you use the `OVERWRITE` clause with a multi-row insert, the statement rebuilds and overrides the table with the content of the VALUES clause. 
As you can see, the `INSERT` statement is the simplest way to ingest data into Snowflake, however, it has scalability and error-handling limitations when dealing with data sets exceeding the single-digit MiB range. For larger data sets, data engineers typically leverage the option to use an ETL/ELT tool to ingest data, or preferably use object storage as an intermediate step alongside `COPY INTO` or `Snowpipe`. 


