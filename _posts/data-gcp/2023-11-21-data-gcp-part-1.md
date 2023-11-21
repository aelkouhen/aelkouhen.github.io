---
layout: post
title: Data on GCP series - part 1
subtitle:  Data Ingestion using Google Cloud Services (Hands-on)
thumbnail-img: 
share-img: 
tags: []
comments: true
---

Through the “Data on GCP” series, you will learn how to collect, store, process, analyze, and expose data using a wide variety of tools provided by Google Cloud Platform (GCP). GCP, offered by Google, is a suite of cloud computing services that provides a series of modular cloud services, including computing, data storage, data analytics, and machine learning, alongside a set of management tools.

In this article, I will illustrate data ingestion and integration using the myriad of tools GCP provides. As you’ve seen earlier, Data ingestion is the first stage of the data lifecycle. This is where data is collected from various internal sources like databases, CRM, ERPs, legacy systems, external ones such as surveys, and third-party providers. This is an important step because it ensures the excellent working of subsequent stages in the data lifecycle.

In this stage, raw data are extracted from one or more data sources, replicated, and then ingested into a landing storage service. We’ve seen that most ingestion tools can handle a high volume of data with a wide range of formats (structured, unstructured…) but differ in how they handle the data velocity. We often distinguish three main categories of data ingestion tools: batch-based, real-time or stream-based, and hybrid ingestion. Within Google Cloud, we will see the different data ingestion services and how they can address the different categories of data ingestion.

## Storage Options Overview

Google Cloud Platform (GCP) offers various storage services designed to cater to different needs and scenarios. Some of the key storage services provided by Google Cloud include:

1. **Object storage** is a data storage architecture for storing unstructured data, which sections data into units (objects) and stores them in a structurally flat data environment. Each object includes the data, metadata, and a unique identifier that applications can use for easy access and retrieval. In Google Cloud, the [**_Cloud Storage_**](https://cloud.google.com/storage) Service is a scalable object storage service that allows you to store and retrieve data globally. It's suitable for a wide range of use cases, including data backup, serving website content, storing large data sets for analysis, and more. Cloud Storage offers different storage classes, such as Standard, Nearline, Coldline, and Archive, each optimized for specific access patterns and cost considerations.
2. **Block storage** is a technology that controls data storage and storage devices. It divides any data, like a file or database entry, into blocks of equal sizes. The block storage system then stores the data block on underlying physical storage in a manner that is optimized for fast access and retrieval. In Google Cloud, several services allow storing the blocks:
- [**_Persistent disk_**](https://cloud.google.com/persistent-disk) provides durable block storage for Compute Engine virtual machine instances. It offers both standard and SSD persistent disks with different performance characteristics.
- [**_Local SSD_**](https://cloud.google.com/local-ssd): Ephemeral locally attached block storage for virtual machines and containers.
- [**_Hyperdisk_**](https://cloud.google.com/compute/docs/disks/hyperdisks): Next generation of block storage delivering higher scale and best in class price/performance.
3. In **File Storage**, data is stored in files, the files are organized in folders, and the folders are organized under a hierarchy of directories and subdirectories. Google Cloud provides several services to storing files:
- [**_Filestore_**](https://cloud.google.com/filestore): A managed file storage service for applications that require a filesystem interface and shared file storage for applications running on Compute Engine or Kubernetes Engine instances.
- [**_Parallelstore_**](https://cloud.google.com/parallelstore): High bandwidth, high IOPS, ultra-low latency, managed parallel file service.
- [**_NetApp Volumes_**](https://cloud.google.com/netapp-volumes): A fully managed, cloud-based data storage service that provides advanced data management capabilities and highly scalable performance.
4. **Databases**: A database is a structured data collection stored on a disk, memory, or both. Databases come in a variety of flavors:
- _In relational databases_, information is stored in tables, rows, and columns, which typically works best for structured data. There are three relational database options in Google Cloud: Cloud SQL, AlloyDB, and Cloud Spanner.
    - [**_Cloud SQL_**](https://cloud.google.com/sql): A fully-managed relational database service that supports MySQL, PostgreSQL, and SQL Server. It's ideal for applications requiring a traditional relational database structure.
    - [**_AlloyDB_**](https://cloud.google.com/alloydb/docs/overview) is a fully managed PostgreSQL-compatible database service for your most demanding enterprise database workloads.
    - [**_Cloud Spanner_**](https://cloud.google.com/spanner): A horizontally scalable, strongly consistent, relational database service designed for global transactions and high availability. It combines the benefits of traditional relational databases with the scalability and global distribution capabilities of NoSQL databases.
- _Non-relational databases_ (or NoSQL databases) store complex, unstructured data such as documents in a non-tabular form. Non-relational databases are often used when large quantities of complex and diverse data need to be organized or where the structure of the data is regularly evolving to meet new business requirements. There are three non-relational databases in Google Cloud:
    - [**_Bigtable_**](https://cloud.google.com/bigtable): A high-performance, fully-managed NoSQL database service suitable for large analytical and operational workloads. It's particularly useful for applications that require high throughput and scalability.
    - [**_Firestore_**](https://cloud.google.com/firestore): A NoSQL document database built for automatic scaling, high performance, and ease of application development. It's suitable for mobile, web, and server-side applications that require real-time updates and offline support.
    - [**_Memorystore_**](https://cloud.google.com/memorystore): Memorystore is a fully managed in-memory data store service for Redis and Memcached at Google Cloud. 

![](https://storage.googleapis.com/gweb-cloudblog-publish/images/Which-Database_v03-22-23.max-2000x2000.jpg){: .mx-auto.d-block :} *Google Cloud database options.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

5. **Data Warehouses**: A data warehouse is a standard OLAP data architecture (don’t dare call it an analytical database; Bill Inmon will be upset). It tends to handle large amounts of data quickly, allowing users to analyze facts according to multiple dimensions in tandem (Cube). In Google Cloud, [**_BigQuery_**](https://cloud.google.com/bigquery) is a fully managed, serverless data warehouse service that enables scalable analysis over petabytes of data.
6. **Date Lakehouses**: A data lakehouse combines the low-cost, scalable storage of a data lake and the structure and management features of a data warehouse. Google Cloud provides [**_BigLake_**](https://cloud.google.com/biglake) as a storage engine that provides a unified interface for analytics and AI engines to query multiformat, multi-cloud, and multimodal data securely, governed, and performantly. It unifies data warehouses and data lakes into a consistent format for faster data analytics across multi-cloud storage and open formats.
7. **Transfert Services**: Google Cloud provides a few transfer services to move data from other cloud providers or from a physical appliance.

These services cater to different storage needs, whether you require object storage, relational databases, NoSQL databases, file storage, or other forms of data storage and management within the Google Cloud Platform. In the next sections, I will dive into each service to demonstrate how to ingest and import data into it.

## Import data into Cloud Storage 
### Import data into Object Storage
### Import data into Block Storage
### Import data into File Storage

## Load data into GCP databases
### Load data into CloudSQL
### Load data into Cloud Spanner
### Load data into BigTable
### Load data into Firestore
### Load data into Memorystore
## Load data into BigQuery
## Load data into BigLake

## Summary

## References
