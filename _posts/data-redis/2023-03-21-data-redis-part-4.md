---
layout: post
title: Data & Redis series - part 4
subtitle:  Data Processing with RDI (Hands-on)
thumbnail-img: assets/img/RDI.png
share-img: https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEj0LWaElVc5g_xIC6-sPtXyLIkYgqTm7F6Kk21gWaDQAzdv2ij-RPzmXHZ_iNk26lbrnbJBfAWS5lgRWd-6IVZyHUuzoNmA1TrDswryWl2hmjeUi0HoBHoQqCuTdMyRmGoYbKr5bZDnZKYx0LFcIQnlP1NRworKdN9IjrD7TTLCKPosRMG4yF02akTJ
tags: [RDI,Debezium,Gears,Redis Streams,Hands-On,stream processing,data processing,data transformation,Redis]
comments: true
---

Data processing is at the core of any data architecture. It involves transforming raw data into useful insights through analysis techniques like machine learning algorithms or statistical models depending on what type of problem needs solving within an organization's context. 

We have seen in the past posts that raw data, already extracted from data sources, can be prepared and transformed (using Redis Gears) into the target format required by the downstream systems. In this post, we push this concept further by coupling the event-processing of RedisGears and stream-based ingestion using Redis Data Integration (RDI). Thus, you can imagine that data flowing in your operational systems (e.g., ERPs, CRMs...) will be ingested into Redis using a Change Data Capture (see [Data & Redis - part 1](https://aelkouhen.github.io/2023-02-21-data-redis-part-1/)) and processed with RedisGears to derive rapid operational decisions in near real-time. 

In fact, Redis Data Integration is not only a data integration tool but also a data processing engine that relies on Redis Gears. Therefore, it provides a more straightforward way to implement data transformations (declarative files) to avoid the complexity of Redis Gears.

## Pre-requisites

### 1 - Create a Redis Database 

For this article, you need to install and set up a few things. First, you need to prepare a Redis Enterprise Cluster, which is the target storage support. This storage support will be the target infrastructure for the data transformed in this stage. You can use this [project](https://github.com/amineelkouhen/terramine) to create a Redis Enterprise cluster in the cloud provider of your choice.

Once you have created a Redis Enterprise cluster, you must create a target database that holds the transformed data. Redis Enterprise Software lets you create and distribute databases across a cluster of nodes. To create a new database, follow the instructions [here](https://docs.redis.com/latest/rs/databases/create/). 

For Redis Data Integration, you need two databases: the config database exposed on `redis-12000.cluster.redis-process.demo.redislabs.com:12000` and the target database on:  `redis-13000.cluster.redis-process.demo.redislabs.com:13000`. Don't forget to add the RedisJSON module when you create the target database.

### 2 - Install RedisGears

Now, let's install [RedisGears](https://redis.com/modules/redis-gears/) on the cluster. In case it’s missing, follow [this guide](https://redis-data-integration.docs.dev.redislabs.com/installation/install-redis-gears.html) to install it. 

{% highlight shell linenos %}
mkdir ~/tmp 
curl -s https://redismodules.s3.amazonaws.com/redisgears/redisgears.Linux-ubuntu18.04-x86_64.1.2.5.zip -o ~/tmp/redis-gears.zip
cd ~/tmp 
curl -v -k -s -u "<REDIS_CLUSTER_USER>:<REDIS_CLUSTER_PASSWORD>" -F "module=@./redis-gears.zip" https://<REDIS_CLUSTER_HOST>:9443/v2/modules
{% endhighlight %}

### 3 - Install Redis Data Integration (RDI) 

For the second part of this article, you will need to install Redis Data Integration (RDI). Redis Data Integration installation is done via the RDI CLI. The CLI should have network access to the Redis Enterprise cluster API (port 9443 by default). You need first to download the RDI offline package:

#### UBUNTU20.04

```shell
wget https://qa-onprem.s3.amazonaws.com/redis-di/latest/redis-di-offline-ubuntu20.04-latest.tar.gz -O ~/tmp/redis-di-offline.tar.gz
```    

#### UBUNTU18.04

```shell
wget https://qa-onprem.s3.amazonaws.com/redis-di/latest/redis-di-offline-ubuntu18.04-latest.tar.gz -O ~/tmp/redis-di-offline.tar.gz
```    

#### RHEL8

```shell
wget https://qa-onprem.s3.amazonaws.com/redis-di/latest/redis-di-offline-rhel8-latest.tar.gz -O ~/tmp/redis-di-offline.tar.gz
```    

#### RHEL7
```shell
wget https://qa-onprem.s3.amazonaws.com/redis-di/latest/redis-di-offline-rhel7-latest.tar.gz -O ~/tmp/redis-di-offline.tar.gz 
```

Then Copy and unpack the downloaded `redis-di-offline.tar.gz` into the master node of your Redis Cluster under the `~/tmp` directory:

```shell
tar xvf redis-di-offline.tar.gz
```

Then you install the RDI CLI by unpacking `redis-di.tar.gz` into `/usr/local/bin/` directory:

```shell
sudo tar xvf ~/tmp/redis-di-offline/redis-di-cli/redis-di.tar.gz -C /usr/local/bin/
```

Run `create` command to set up the Redis Data Integration config database (on port `13000`) instance within an existing Redis Enterprise Cluster:

```
redis-di create --silent --cluster-host <CLUSTER_HOST> --cluster-user <CLUSTER_USER> --cluster-password <CLUSTER_PASSWORD> --rdi-port <RDI_PORT> --rdi-password <RDI_PASSWORD>
```

Finally, run the `scaffold` command to generate configuration files for Redis Data Integration and Debezium Redis Sink Connector:

```
redis-di scaffold --db-type <cassandra|mysql|oracle|postgresql|sqlserver> --dir <PATH_TO_DIR>
```    

In our article, we will capture a SQL Server database, so choose (sqlserver). The following files will be created in the provided directory:

```shell
├── debezium
│   └── application.properties
├── jobs
│   └── README.md
└── config.yaml
```
 
*   `config.yaml` - Redis Data Integration configuration file (definitions of target database, applier, etc.)
*   `debezium/application.properties` - Debezium Server configuration file
*   `jobs` - Data transformation jobs, [read here](https://redis-data-integration.docs.dev.redislabs.com/data-transformation/data-transformation-pipeline.html)


To use debezium as a docker container, download the debezium Image

```shell
wget https://qa-onprem.s3.amazonaws.com/redis-di/debezium/debezium_server_2.1.1.Final_offline.tar.gz -O ~/tmp/debezium_server.tar.gz
```

and load it as a docker image.

```shell
docker load < ~/tmp/debezium_server.tar.gz
```

Then tag the image:

{% highlight shell linenos %}
docker tag debezium/server:2.1.1.Final_offline debezium/server:2.1.1.Final
docker tag debezium/server:2.1.1.Final_offline debezium/server:latest
{% endhighlight %}

For the non-containerized deployment, you need to install [Java 11](https://www.oracle.com/java/technologies/downloads/#java11) or [Java 17](https://www.oracle.com/java/technologies/downloads/#java17). Then download Debezium Server 2.1.1.Final from [here](https://repo1.maven.org/maven2/io/debezium/debezium-server-dist/2.1.1.Final/debezium-server-dist-2.1.1.Final.tar.gz).

Unpack Debezium Server:

```shell
tar xvfz debezium-server-dist-2.1.1.Final.tar.gz
```

Copy the scaffolded `application.properties` file (created by the [scaffold command](https://redis-data-integration.docs.dev.redislabs.com/ingest-qsg.html#scaffold-configuration-files)) to the extracted `debezium-server/conf` directory. Verify that you’ve configured this file based on these [instructions](https://redis-data-integration.docs.dev.redislabs.com/ingest-qsg.html#install-the-debezium-server).

If you use `Oracle` as your source DB, please note that Debezium Server does not include the Oracle JDBC driver. You should download it and locate it under the `debezium-server/lib` directory:

{% highlight shell linenos %}
cd debezium-server/lib
wget https://repo1.maven.org/maven2/com/oracle/database/jdbc/ojdbc8/21.1.0.0/ojdbc8-21.1.0.0.jar
{% endhighlight %}

Then, start Debezium Server from the `debezium-server` directory:

```shell 
./run.sh
```

## Data processing using Redis Data Integration

Data transformation is a critical part of the data journey. This process can perform constructive tasks such as adding or copying records and fields, destructive actions like filtering and deleting specific values, aesthetic adjustments to standardize values, or structural changes that include renaming columns, moving them around, and merging them together.

The key functionality offered by RDI is mapping the data coming from [Debezium Server](https://debezium.io/documentation/reference/stable/operations/debezium-server.html) (representing a Source Database row data or row state change) into a Redis key/value pair. The incoming data includes the schema. By default, each source row is converted into one [Hash](https://redis.io/docs/data-types/hashes/) or one [JSON](https://redis.io/docs/stack/json/) key in Redis. RDI will use a set of handlers to automatically convert each source column to a Redis Hash field or a JSON attribute based on the Debezium [type](https://redis-data-integration.docs.dev.redislabs.com/reference/data-types-conversion/data-types-conversion.html) in the schema.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgJGXOFor5FMox77y23oS9sptwD79P1D1jH8D7EuXS9LEHUuTg9RaCy_BXdmHK0qT2t99SN_iQBiT0Yz_cp_2dZTGOTkVYi7U8KElt6bw8pw7Zmc-i89WzDJCXJ_NGpqsU_VUTC1IVKklGeMc6l_u4aa5SIMKr69IqLg-3qdIvxDDmwc0O3sBxkZv00){: .mx-auto.d-block :} *Converting captured streams.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}
   
However, if you want to customize this default mapping or add a new transformation, RDI provides [Declarative Data Transformations](https://redis-data-integration.docs.dev.redislabs.com/data-transformation/data-transformation-pipeline.html) (YAML files). Each YAML file contains a Job, a set of transformations per source table. The source is typically a database table or collection and is specified as the full name of this table/collection. The job contains logical steps to transform data into the desired output and store it in Redis (as Hash or JSON). All of these files will be uploaded to Redis Data Integration using the deploy command when they are available under the jobs folder:

```shell 
├── debezium
│   └── application.properties
├── jobs
│   └── README.md
└── config.yaml
``` 

We've seen in [Data 101 - part 5](https://aelkouhen.github.io/2023-02-05-data-101-part-5/) that the pipelines required to run the transformation processes can be implemented using one of these approaches:

*   **Code-centric tools**: analysis and manipulation libraries built on top of general-purpose programming languages (Scala, Java or Python). These libraries manipulate data using the native data structures of the programming language.
*   **Query-centric tools**: use a querying language like SQL (Structured Query Language) to manage and manipulate datasets. These languages can be used to create, update and delete records, as well as query the data for specific information.
*   **Hybrid tools**: implement SQL on top of general-purpose programming languages. This is the case for libraries like Apache Spark or Apache Kafka, which provides a SQL dialect called KSQL.

Redis Data Integration (RDI) leverages the hybrid approach since all transformation jobs are implemented using a human-readable format (YAML files) that embeds JMESPath and/or SQL.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEj0LWaElVc5g_xIC6-sPtXyLIkYgqTm7F6Kk21gWaDQAzdv2ij-RPzmXHZ_iNk26lbrnbJBfAWS5lgRWd-6IVZyHUuzoNmA1TrDswryWl2hmjeUi0HoBHoQqCuTdMyRmGoYbKr5bZDnZKYx0LFcIQnlP1NRworKdN9IjrD7TTLCKPosRMG4yF02akTJ){: .mx-auto.d-block :} 

The YAML files accept the following blocks/fields: 

`source` - This section describes what is the table that this job works on:
 *   `server_name`: logical server name (optional)
 *   `db`: DB name (optional)
 *   `schema`: DB schema (optional)
 *   `table`: DB table
 *   `row_format`: Format of the data to be transformed: data_only (default) - only payload, full - complete change record 

`transform`: his section includes a series of blocks that the data should go through. See documentation of the [supported blocks](https://redis-data-integration.docs.dev.redislabs.com/reference/data-transformation-block-types.html) and [JMESPath custom functions](https://redis-data-integration.docs.dev.redislabs.com/reference/jmespath-custom-functions.html).

`output` - This section includes the outputs where the data should be written to:

1. Redis:
*   `uses`: `redis.write`: Write to a Redis data structure
    *   `with`:
        *   `connection`: Connection name
        *   `key`: This allows to override the key of the record by applying a custom logic:
            *   `expression`: Expression to execute
            *   `language`: Expression language, JMESPath, or SQL

2. SQL:
*   `uses`: `relational.write`: Write into a SQL-compatible data store
    *   `with`:
        *   `connection`: Connection name
        *   `schema`: Schema
        *   `table`: Target table
        *   `keys`: Array of key columns
        *   `mapping`: Array of mapping columns
        *   `opcode_field`: Name of the field in the payload that holds the operation (c - create, d - delete, u - update) for this record in the DB

I've detailed many data transformations archetypes in [Data 101 - part 5](https://aelkouhen.github.io/2023-02-08-data-101-part-5) and find it interesting to evaluate Redis Data Integration through this list of capabilities. Thus, you can see how to perform different kinds of transformations using RDI.

### 1 - Filtering

This process selects a subset from your dataset (specific columns) that require transformation, viewing, or analysis. This selection can be based on certain criteria, such as specific values in one or more columns, and it typically results in only part of the original data being used. As a result, filtering allows you to quickly identify trends and patterns within your dataset that may not have been visible before. It also lets you focus on particular aspects of interest without sifting through all available information. In addition, this technique can reduce complexity by eliminating unnecessary details while still preserving important insights about the underlying data structure.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhO-MSwT57OBokuO4yjCcYbNJT0aQuQg9lQEo9QW5ADCVM2Z-twE8LZoijKml6sO_I72TdGd4q07SF59upIwS8mjNJUXktsJaKeqYo6Urx4blKDA17oiB31CGiwQ7wdMRxiGwZtPhI_cTM84ygG0T4D_luLgV4su8EbBo72eGjBcYptHBRGhf3RjGiN){: .mx-auto.d-block :} *Filtering a dataset.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Using Redis Data Integration, filtering the Employee's data ([example](https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/mssql_script_emp_filter) above) to keep only people having a salary that exceeds 1,000 can be implemented using the following YAML blocks:

{% highlight yaml linenos %}
source:
  table: Employee
transform:
  - uses: filter
    with:
      language: sql
      expression: SAL>1000
{% endhighlight %}

When you put this YAML file under the `jobs` folder, Redis Data Integration will capture changes from the source table and apply the filter to store only records confirming the filtering expression (see [Data & Redis - part 1](https://aelkouhen.github.io/2023-02-21-data-redis-part-1/) for RDI and SQL Server configuration).

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjkOqC5XKj2n21j7ocaVh4bY8re2MfHv6JPLOjHohe5ZEAF6HjNf_o_dbOUx-Ldx_tHIDG39BxG943_wMn_2361Bx0KjCRya6hRbbV-RLCTe6-f9hWPLzxATwtFXz0FEAwmDDqowiDu0ZADdV64O6LMBgqdWZoRrWN3W4mKNXTnHHzmTx5dDJK8-Bw6){: .mx-auto.d-block :} *Filtering Employees having salaries of more than 1,000.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### 2 - Enriching

This process fills out the basic gaps in the data set. It also enhances existing information by supplementing incomplete or missing data with relevant context. It aims to improve accuracy, quality, and value for better results.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhM02sSpbjKDZRPqW2RAYCTRZmDHdUh6u5UlfCU2BJDpGiHu6VssxHVv3PmlbZzJ8rtWdRV0sjCrYtfYoBh2t7X_ev8Uti3MxLqJ_75tm4DZs4SIrINB73BbPtl_YX-dE9POHcB84sAKifTdCYYZmEYcB8F2_U9vYUH_OEbtp6XbhTabBGj6T6DX3Gm){: .mx-auto.d-block :} *Enriching a dataset.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Let's assume the [example](https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/mssql_script_emp_enrich) above. We need to replace all NULL salaries in the Employee's table with a default value of 0. In SQL, the `COALESCE` function returns the first non-NULL value in the attribute list. Thus `COALESCE(SAL, 0)` returns the salary if it is not null or 0 elsewhere. With RDI, we can implement this enrichment using the following job:

{% highlight yaml linenos %}
source:
    table: Employee
  transform:
    - uses: map
      with:
        expression:
          EMPNO: EMPNO
          ENAME: ENAME
          SAL: COALESCE(SAL, 0)
        language: sql
{% endhighlight %}
    
In this configuration, we used the map block that maps each source record into a new output based on the expressions. Here we changed only the salary field that implements the `COALESCE` expression.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEj7T6ghjj4PSZOFufE_Ie4gD4O_spNMP_XKg04Hs60p6pfH1lrPdGXUFYpz87fIjY_XlvlII1ZYZ8UJLqZzY_oaLQ1cL7rClW7DanrLEHFw5eLI0uMQ7xcJkosM7gre-QIRYLgflQgFXGImzESW1ZB1mWo7RihmIvAqXYNDrjJ6TTomGNvMCdM2sdgH){: .mx-auto.d-block :} *Replacing missing salaries with a default value (0).*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

If you are using SQL Server, another alternative to performing this enrichment is to use the `ISNULL` function. Thus, we can use `ISNULL(SAL, 0)` in the expression block. The `ISNULL` function and the `COALESCE` expression have a similar purpose but can behave differently. Because `ISNULL` is a function, it is evaluated only once. However, the input values for the `COALESCE` expression can be evaluated multiple times. Moreover, the data type determination of the resulting expression is different. `ISNULL` uses the data type of the first parameter, `COALESCE` follows the `CASE` expression rules and returns the data type of value with the highest precedence.  

{% highlight yaml linenos %}
source:
  table: Employee
transform:
  - uses: map
    with:
      expression:
        EMPNO: EMPNO
        ENAME: ENAME
        SAL: ISNULL(SAL, 0)
      language: sql 
{% endhighlight %}

### 3 - Splitting

Splitting fields into multiple ones consists of two atomic operations: adding the new fields according to specific transformation rules, then removing the source field (split column).

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEiXJmd0hkRmD6GW-Pi30AO7G35TzPcRdrW5EQxaH_Ipkrtd48PdK0qq6Jo_fhmw126BSGcxQthVpRRXr5yXZ_9rlGO0igjTaHAnAh3s5BeZ3igZwdcRQRlUIjCWdyfnoJLrJZYVogqLWfU3S3MRckoh9lvusvcPhr-iIzjhBWK4v1Ce_1xguY6S6xBL){: .mx-auto.d-block :} *Splitting a column.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

In the [example](https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/mssql_script_emp_split) above, we split the `EFULLNAME` into two fields: `ELASTNAME` and `EFIRSTNAME`. The following configuration uses the `add_field` block to create the new fields `ELASTNAME` and `EFIRSTNAME`. Then, we can use the `SUBSTRING` function from SQL or the `SPLIT` function from JMESPath. In both cases, we need the additional block `remove_field` to remove the source column `EFULLNAME`.

{% highlight yaml linenos %}
source:
  table: Employee
transform:
  - uses: add_field
    with:
      fields:
        - field: EFIRSTNAME
          language: jmespath
          expression: split(EFULLNAME, ', ')[0]
        - field: ELASTNAME
          language: jmespath
          expression: split(EFULLNAME, ', ')[1]
  - uses: remove_field
    with:
      field: EFULLNAME
{% endhighlight %}
    
The split function breaks down the `EFULLNAME` into an array using the string separators provided as parameters (the comma character as separator). 

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgjYhfVzSRvASVGv1kR2Tc5YhtMGBkabbep2PEvAMD4r2n--uJ5c1qn8pm_nQQ-fIzI1lN49M5Z9ojxPji9eqWjCMyaeLtiBpFAQKz_p0A6onZKksytk_Um13y3o4Usm9lgq-IV7tGDpqdmpt6lW3LDogKTbvZsWlAFZhD7vDbS9J93UB01WKJxNhfO){: .mx-auto.d-block :} *Splitting Full Name into First and Last Name.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

### 4 - Merging

Merging multiple fields into one consists of two atomic operations: adding the new field according to a specific transformation rule, then removing the source fields (merged columns).

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgiat0k47FbzwgNKr0ijKuR-OWT6xilEJxT5fQ1coJ0661af3SQqqggHGEnglr-lm0rYIf1JDxNSKY_B4cK9T92lwhFmgzyS5FJjBg35-GqQtNrIwxmHIydMAD2xg-AUuOn0KAz5mn6a7Fk7MNNfbziWpS9f2AsjXFeOgebrxp468AWeSbwxLx_EB0Y){: .mx-auto.d-block :} *Merging two columns.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

In the [example](https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/mssql_script_emp_merge) above, we merge the `EFIRSTNAME` and `ELASTNAME` into one field: `EFULLNAME`. The following configuration uses the `add_field` block to create the new fields `EFULLNAME` and two `remove_field` blocks to remove the merged columns `EFIRSTNAME` and `ELASTNAME`. To express the transformation rule, we can use the `CONCAT_WS` function from SQL or the `JOIN` / `CONCAT` functions from JMESPath.

{% highlight yaml linenos %}
source:
  table: Employeetransform:
  - uses: add_field
    with:
      fields:
        - field: EFULLNAME
          language: jmespath
          expression: concat([EFIRSTNAME, ' ', ELASTNAME])
          
  - uses: remove_field
    with:
      fields:
        - field: EFIRSTNAME
        - field: ELASTNAME
{% endhighlight %}

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgh4OiMWaTT54PsII8wf8f7Tw2JPsI5qajZgyTfaRmbbZCjTLvvclsqCN8lODE7tdsrT6Wvo_2gNy_EjXE8fZG_aHHY5al-7Fc1jdWWHlsx8OFEDHkxDz1RTuM9pTDNkF6eoMOLppDHyHxc4NX0mMKxeA8lF7oH0l30Evk6_XPmnmWl3U0IEIe3lHW4){: .mx-auto.d-block :} *Merging First Name and Last Name into one field.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

### 5 - Removing

Besides removing specific columns from the source using the `remove_field` block or even avoiding the load of some columns using filtering. We might need to drop parts of data according to a specific condition, such as duplicates. In this case, Redis Data Integration doesn't have a specific block or function to perform the drop of duplicates. However, we can use the key block to create a custom key for the output composed of all fields that form the duplicate.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEh6Vs3ylmlK4-cSlRnBzlLWqSOAhKzH36fcr2lvOHZLydhlyo2p4aPgZsZd6xbvsonJJC2tdJlOVCsDbpGa0LslwBsMuHvHBSZJtfX_JaV4JqdCpnd0eM3m_RakplsNJU3u_AuGyexv__0bRYb0BRS1MYWpTrmy82h8SH95KXfHv1wE2OkS0c0KS7DS){: .mx-auto.d-block :} *Drop duplicates.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

For example, let's assume the use case [above](https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/mssql_script_emp_drop). If we observe the `EMPNO` column, we have a distinct ID for each record. However, three records are duplicates, in fact. So, in this case, we want to drop these duplicates according to the `EFULLNAME` and `SAL` fields and not to `EMPNO`. The solution in RDI is to create a new key that preserves the unicity of records: A key composed of the concatenation of `EFULLNAME` and `SAL`. Thus RDI can drop any duplicates based on the newly created key.

{% highlight yaml linenos %}
source:
  table: Employee
output:
  - uses: redis.write
    with:
      connection: target
      key:
        expression: hash(concat([EFULLNAME, '-', SAL]), 'sha3_512')
        language: jmespath
{% endhighlight %}

In addition, we use the hash function to create an ID instead of a set of concatenated fields. However, beware that It may be possible that two concatenations (different strings) have the same hash values. This may occur because we take modulo 'M' in the final hash value. In that case, two different combinations of (EFULLNAME '-' SAL) may have the same hash values, called a collision. 

However, the chances of random collisions are negligibly small for even billions of assets. Because the SHA-3 series is built to offer 2<sup>n/2</sup> collision resistance. In our transformation, we've chosen SHA3-512, which offers 2<sup>256</sup> (or 1 chance over 115,792,089,237,316,195,423,570,985,008,687,907,853,269,984,665,640,564,039,457,584,007,913,129,639,936 to get another String combination having the same hash!

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgQ1ouIsvsKMovZO-sRG5-U4jqA_YmJYU0y8voran3KlBoD0h0MbQCVLhGvKooMStHcoECai7QI4HM2xFgMYymmCdIkT-u2aQo6bBNdmqjQ6DUsWtMrJtyiGth8Y-LTzxhMRwNrioiBUHqNUaIcvbY2SPtbxFMWhmpaTxWv2gZESAQk5_olim6m_2uA){: .mx-auto.d-block :} *Dropping 3 duplicates.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

### 6 - Derivation

The derivation is cross-column calculations. With RDI, we can easily create a new field based on calculations from existing fields. Let's assume the [example](https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/mssql_script_emp_derivate) below. We need to calculate the total compensation of each employee based on the salaries and bonuses they get.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhFZIwklYRgfjprkrKCguZxWgTQmiAK5uXATrJyjE8amjPZOyAYYV5crn9nQgbXJSLvcgu23cpVTCexBgRxvS5I68Indvv551cqE4YXRvpns49y2Yy7ZEsqnDZsNT1HBA2Nqgtypgd4taE4jiCtBPMrmlIdHJZLhWzhoNxgC7Yw0Ig2Vk3ZHlNZUXN6){: .mx-auto.d-block :} *Derivation.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

The following job implements this kind of derivation using SQL by summing up the `SAL` and `BONUS` fields and storing them into one additional field called `TOTALCOMP`:

{% highlight yaml linenos %}
source:
  table: Employee
transform:
  - uses: add_field
    with:
      fields:
        - field: TOTALCOMP
          language: sql
          expression: SAL + BONUS
{% endhighlight %}

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEizA3KDK1kHPfXSWnJvV4FyvbSpElFK7R2ShFLAbSyfN3dNoUtGOLTUwXa4h_ZrcxIFzr8o9v8L0JMJRfgjf666Z3fBBDncT5EXO-NY0OtPON8tHnMfCaImbpxJ23SFyRi3W_vPcEq5wHys7O6XgvYjuNRqphOyBYjSLADZY9zT4UwtQmR3VJOzDqf9){: .mx-auto.d-block :} *Derivate Total Compensation from Salary and Bonus fields.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

### 7 - Data Denormalization

Redis Data Integration (RDI) has a different approach to performing joins between two tables that have one-to-many or many-to-one relationships. This approach is called the nesting strategy. It consists of organizing data into a logical structure where the parent-children relationship is converted into a schema based on nesting. Denormalized data often contain duplicate values when represented as tables or hashes, increasing storage requirements but making querying faster since all relevant information for a given task may be found within one table instead of having to join multiple tables/hashes together first before running queries on them. 

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEj-cTn3C6ZWksj9NReUp6Kbi0l8XsDkqVt8VBJVIgtXZK58PQy4VsS_60cCzSgFOquDMVGb65PtKwpgyscT_OnQNl2IIx3kyz9TAEE1Cg1OnvVM-3MHHEi00krOh-i9mPt0MqtdQflFfvBDj4RaK0hlDK9xw-kXRcgXezvkpQ380Dw9u_-IpkcHCkfy){: .mx-auto.d-block :} *Duplicate values when denormalizing.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

However, you can choose to perform the denormalization using JSON format. In this case, no duplication will be represented; thus no impact on the storage since the parent-children relationship is just reflected hierarchically.

Let's assume the [two tables](https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/mssql_script_emp_dept_denorm): `Department` and `Employee`. We will create a declarative data transformation that denormalizes these two tables into one nested structure in JSON. The aim is to get the details of employees in each department.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhOamYo3WmONFuLbpc0qdpKoN8W-vzM63UueCowjq12rFmjXYwfu8EAiVQRLCS0FO034suiYyD4xhpU0lcwghHpehFdA9T_SqjZlvU9vBB5YAjCHcIiLbW1Du2HydG0p4t4sLoqawf0rZjd7YhgLh9oVJtYiArLi5VEOpS7KTjcgVN9eqSmCltCDHZw){: .mx-auto.d-block :} *Denormalization using the nest strategy.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

Let's create the following file in the jobs directory. This declarative file merges the two tables into a single JSON object. It also demonstrates how easy to set such a complex transformation using a simple YAML declarative file.

{% highlight yaml linenos %}
source:
  table: Employee
output:
  - uses: redis.write
    with:
      nest:
        parent:
          table: Department
        nesting_key: EMPNO         # cannot be composite
        parent_key: DEPTNO         # cannot be composite
        path: $.Employees          # path must start from root ($)
        structure: map  
{% endhighlight %}

Using the Debezium SQL Server connector is a good practice to have a dedicated user with the minimal required permissions in SQL Server to control blast radius. For that, you need to run the T-SQL script below:

{% highlight sql linenos %}
USE master
GO
CREATE LOGIN dbzuser WITH PASSWORD = 'dbz-password'
GO
USE HR
GO
CREATE USER dbzuser FOR LOGIN dbzuser
GO
{% endhighlight %}

And Grant the Required Permissions to the new User

{% highlight sql linenos %}
USE HR
GO
EXEC sp_addrolemember N'db_datareader', N'dbzuser'
GO
{% endhighlight %}

Then you must enable Change Data Capture (CDC) for each database and table you want to capture.

{% highlight sql linenos %}
EXEC msdb.dbo.rds_cdc_enable_db 'HR'
GO
{% endhighlight %}

Run this T-SQL script for each table in the database and substitute the table name in `@source_name` with the names of the tables (Employee and Department):

{% highlight sql linenos %}
USE HR
GO
EXEC sys.sp_cdc_enable_table
@source_schema = N'dbo',
@source_name   = N'<Table_Name>', 
@role_name     = N'db_cdc',
@supports_net_changes = 0
GO
{% endhighlight %}

Finally, the Debezium user created earlier (dbzuser) needs access to the captured change data, so it must be added to the role created in the previous step.

{% highlight sql linenos %}
USE HR
GO  
EXEC sp_addrolemember N'db_cdc', N'dbzuser'
GO
{% endhighlight %}

You can verify access by running this T-SQL script as user dbzuser:

{% highlight sql linenos %}
USE HR
GO  
EXEC sys.sp_cdc_help_change_data_capture
GO
{% endhighlight %}

In the RDI configuration file config.yaml, you need to add some of the following settings.

{% highlight yaml linenos %}
connections:
  target:
    host: redis-13000.cluster.redis-ingest.demo.redislabs.com
    port: 13000
    user: default
    password: rdi-password  
applier:
  target_data_type: json
  json_update_strategy: merge 
{% endhighlight %}

{: .box-warning}
**Caution:** If you want to execute normalization/denormalization jobs, It is mandatory to load the release 0.99 (at least) of Redis Data Integration.  

#### For UBUNTU18.04

```shell
wget https://qa-onprem.s3.amazonaws.com/redis-di/0.99.0/redis-di-ubuntu18.04-0.99.0.tar.gz -O ~/tmp/redis-di-offline.tar.gz
```

Then you install the RDI CLI by unpacking `redis-di-offline.tar.gz` into the `/usr/local/bin/` directory:

```shell
sudo tar xvf ~/tmp/redis-di-offline.tar.gz -C /usr/local/bin/
```

Upgrade your Redis Data Integration (RDI) engine to comply with the new `redis-di` CLI. For this run:  

```
redis-di upgrade --cluster-host cluster.redis-process.demo.redislabs.com --cluster-user [CLUSTER_ADMIN_USER] --cluster-password [ADMIN_PASSWORD] --rdi-host redis-13000.cluster.redis-process.demo.redislabs.com --rdi-port 13000 --rdi-password rdi-password
```

Then, run the deploy command to deploy the local configuration to the remote RDI config database:

```
redis-di deploy --rdi-host redis-12000.cluster.redis-process.demo.redislabs.com --rdi-port 12000 --rdi-password rdi-password
```

Change directory to your Redis Data Integration configuration folder created by the scaffold command, then run:

```shell
docker run -d --rm --name debezium -v $PWD/debezium:/debezium/conf debezium/server:2.1.1.Final
```

Check the Debezium Server log:

```shell
docker logs debezium --follow
```

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEib_7s9IM2jaxFVNfun6uHGTWyuQtFEhROgp_b-SR69n7Qr3L2g26COucb-azMiQp6SiXO2CXVbiGgr3zDtRnsTbEno7pR_SJ6GLHSt18A8zz_7J5vaojOYWypHaaJXYl5BmdDWXe5kiLagF-yvxheoYoydHfzRX63NSn-vM-jN5tC6JHVVKrpXjPIr){: .mx-auto.d-block :} *Denormalizing Employee and Department tables.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

Redis Data Integration (RDI) performs data denormalization in a performant and complete manner. It is not only structuring the source tables into one single structure, but it can handle in the same way the late arriving data: If the nested data is captured before the parent-level data, RDI creates a JSON structure for the child-level records, and as soon as the parent-level data arrives, RDI creates the structure for the parent-level record, then merges all children (nested) records into their parent structure. For example, let's consider these two tables: [Invoice](https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/mssql_script_invoice_denorm) and [InvoiceLine](https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/mssql_script_invoice_line_denorm). When you try to insert an InvoiceLine contained by an Invoice before this later, RDI will create the JSON structure for InvoiceLine and wait for the Invoice structure. As soon as you insert the containing Invoice, RDI initiates the Invoice JSON structure and merges it with the InvoiceLines created earlier.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhD_iW7bFEVmbwWQGqiE0ZBbYRCtSrcKMGCFe2Kc1sexg7L9IKHAjB-VVGzEOYi0LII-43DluRi7sW-rW86ilZMPyjDwcQO1IBQ7W0Ft1w4xnS25ku06Ak5BpfvjDQuRZAG8RsUf8Nom57TTm8qEDwknBy8P8tcdnoNOsnQKVOyQfmg65bwdoMfUTBm){: .mx-auto.d-block :} *Late arriving data with Redis Data Integration.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 
  
One of the issues observed so far with RDI's denormalization is the nesting limit (limited to one level). It is only possible for the moment to denormalize up to two tables with one-to-many or many-to-one relationships.

### 8 - Data Normalization

In addition to data ingest, Redis Data Integration (RDI) also allows synchronizing the data stored in a Redis DB with some downstream data stores. This scenario is called `Write-Behind`, and you can think about it as a pipeline that starts with Capture Data Change (CDC) events for a Redis DB and then filters, transforms, and maps the data to a target data store (e.g., a relational database). 

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEh7H7BffP1pHVl05XLY5xtz0RlLbBjEHhMQIQiFKT93h83YT1uVwBE4NFPZN_b6VJWtC9tIjgVzVnGQwkNLcxWM4eAf_37z1P4ru-J-FF8apQ0z_jXZ_iLl_LTeSrhmDXRqQRxgb862IoDblYzD8-rRMkGO9Hm1jvimEyajLXTqxXm_Ox-LikmCMyNZ){: .mx-auto.d-block :} *Redis Data Integration use cases.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 
  
We've seen in the last section that we can perform data denormalization to join multiple tables with one-to-many or many-to-one relationships into one single structure in Redis. On the other side, data normalization is one of the transformations we can perform using the Write-Behind use case. Data normalization is organizing data into a logical structure that can be used to improve performance and reduce redundancy. This involves breaking down complex datasets into smaller, more manageable pieces by eliminating redundant information or consolidating related items together. Normalization also helps ensure consistency in storing and accessing data across different systems.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhQO0MGzDlKl-5UC3BkaMhADWptFOBOexWLANY3rQjNeLmc_Vhgm7wPPL7_Ylejg9pdsb6-N_KBBmHOLSl2-fYWG--afAJjiddjte8c1-3frCpso9QJwPdkmSzRYcLXTo8q1ZjIJu0aJ4jcB2kYz47rUyTxu-c1pEj8ca18YWLdMU3XW-XfRAwICkFs){: .mx-auto.d-block :} *Normalization vs. Denormalization.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 
  
Let's assume this [JSON document](https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/invoice.json) is stored in Redis, which consists of an `Invoice` with the details it contains (`InvoiceLines`). We want to normalize this structure into two separate tables: a table including invoices and another containing invoice lines. For example, with a single nested structure (one invoice composed of three invoice lines), we should have in the target two tables containing four records: one in the invoice table and three in the invoice line table. 

In this section, we will use the database `redis-13000.cluster.redis-process.demo.redislabs.com:13000` as a data source. This database must include [RedisGears](https://redis.com/modules/redis-gears/) and [RedisJSON](https://redis.io/docs/stack/json/) modules to execute the following actions.

First, you need to create and install the RDI engine on your Redis source database so it is ready to process data. You need to run the [`configure`](https://redis-data-integration.docs.dev.redislabs.com/reference/cli/redis-di-configure.html) command if you have not used this Redis database with RDI Write Behind before.

```
redis-di configure --rdi-host redis-13000.cluster.redis-process.demo.redislabs.com --rdi-port 13000 --rdi-password rdi-password
```

Then run the [`scaffold`](https://redis-data-integration.docs.dev.redislabs.com/reference/cli/redis-di-scaffold.html) command with the type of data store you want to use, for example:

```
redis-di scaffold --strategy write_behind --dir . --db-type mysql
```    

This will create a template of `config.yaml` and a folder named `jobs` under the current directory. You can specify any folder name with `--dir` or use the `--preview config.yaml` option in order to get the `config.yaml` template to the terminal.

Let's assume that your target MySQL database endpoint is `rdi-wb-db.cluster-cpqlgenz3kvv.eu-west-3.rds.amazonaws.com`. You need to add the connection(s) required for downstream targets in the `connections` section of the `config.yaml`, for example:

{% highlight yaml linenos %}

connections:
  my-sql-target:
    type: mysql
    host: rdi-wb-db.cluster-cpqlgenz3kvv.eu-west-3.rds.amazonaws.com
    port: 3306
    database: sales
    user: admin
    password: rdi-password
{% endhighlight %}

In the MySQL server, you need to create the sales database and the two tables, `Invoice` and `InvoiceLine`:

{% highlight sql linenos %}
USE mysql;
CREATE DATABASE `sales`;

CREATE TABLE `sales`.`Invoice` (
    `InvoiceId` bigint NOT NULL,
    `CustomerId` bigint NOT NULL,
    `InvoiceDate` varchar(100) NOT NULL,
    `BillingAddress` varchar(100) NOT NULL,
    `BillingPostalCode` varchar(100) NOT NULL,
    `BillingCity` varchar(100) NOT NULL,
    `BillingState` varchar(100) NOT NULL,
    `BillingCountry` varchar(100) NOT NULL,
    `Total` int NOT NULL,
    PRIMARY KEY (InvoiceId)
);

CREATE TABLE `sales`.`InvoiceLine` (
    `InvoiceLineId` bigint NOT NULL,
    `TrackId` bigint NOT NULL,
    `InvoiceId` bigint NOT NULL,
    `Quantity` int NOT NULL,
    `UnitPrice` int NOT NULL,
    PRIMARY KEY (InvoiceLineId)
);
{% endhighlight %}

Now, let's create the following file in the jobs directory. This declarative file splits the JSON structure and creates the two tables in a MySQL database called sales. You can define different targets for these two tables by defining other connections in the `config.yaml` file.

{% highlight yaml linenos %}
source:
  keyspace:
    pattern : invoice:*
output:
  - uses: relational.write
    with:
      connection: my-sql-target
      schema: sales
      table: Invoice
      keys:
        - InvoiceId
      mapping:
        - CustomerId
        - InvoiceId
        - InvoiceDate
        - BillingAddress
        - BillingPostalCode
        - BillingCity
        - BillingState
        - BillingCountry
        - Total
  - uses: relational.write
    with:
      connection: my-sql-target
      schema: sales
      table: InvoiceLine
      foreach: "IL: InvoiceLineItems.values(@)"
      keys:
        - IL: InvoiceLineItems.InvoiceLineId
      mapping:
        - UnitPrice: IL.UnitPrice
        - Quantity: IL.Quantity
        - TrackId: IL.TrackId
        - InvoiceId
{% endhighlight %}

To start the pipeline, run the [`deploy`](https://redis-data-integration.docs.dev.redislabs.com/reference/cli/redis-di-deploy.html) command:

```
redis-di deploy
```    

You can check that the pipeline is running, receiving, and writing data using the [`status`](https://redis-data-integration.docs.dev.redislabs.com/reference/cli/redis-di-status.html) command:

```
redis-di status
```    

Once you run the deploy command, the RDI engine registers the job and listens to the keyspace notifications on the pattern `invoice:*` Thus, if you add this [JSON document](https://raw.githubusercontent.com/aelkouhen/aelkouhen.github.io/main/assets/data/invoice.json), RDI will run the job and execute the data transformation accordingly.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhOPa0eLAV8tyztLD3oX0AzgO747nPWslYGNfAQGkeo5pGTZjpjzRsjGOAMMEY_1DDPV8_RbZo2nRgnsyskmX_QRkT3msa9CzttOcqYn1n-g85tTlobC4IlF4uEPSItzllvlBLoE01XAB0xrOy9x9-U-uCRnTo3WqGtTIYR1V3yhbrhi9is2Dxwv1kq){: .mx-auto.d-block :} *Normalizing a nested JSON into Invoice and InvoiceLine tables.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"} 

## Summary

This article illustrates how to perform complex data transformations using Redis Data Integration (RDI). This is my second post on RDI since I presented it in the past as a data ingestion tool. Here, we pushed the data journey further and used RDI as a data processing and transformation engine. 

In the previous sections, I presented a set of data transformation scenarios more often required in any enterprise-grade data platform and tried to assess RDI capabilities accordingly. The tool is still under heavy development and private previews, but it offers many promising capabilities to implement a complete real-time data platform.

## References

*   Redis Data Integration (RDI), [Developer Guide](https://redis-data-integration.docs.dev.redislabs.com/)
