---
layout: post
title: Data on GCP series - part 1
subtitle:  Data Ingestion using Google Cloud Services
thumbnail-img: 
share-img: 
tags: []
comments: true
---

Through the “Data on GCP” series, you will learn how to collect, store, process, analyze, and expose data using various tools the Google Cloud Platform (GCP) provides. Google Cloud is a suite of cloud computing services that offers a series of modular cloud services, including computing, data storage, data analytics, and machine learning, alongside a set of management tools.

In this article, I will illustrate data ingestion and integration using the myriad of tools Google Cloud provides. As you’ve seen earlier, Data ingestion is the first stage of the data lifecycle. This is where data is collected from various internal sources like databases, CRM, ERPs, legacy systems, external ones such as surveys, and third-party providers. This is an essential step because it ensures the excellent working of subsequent stages in the data lifecycle.

In this stage, raw data are extracted from one or more data sources, replicated, and then ingested into a landing storage service. We’ve seen that most ingestion tools can handle a high volume of data with a wide range of formats (structured, unstructured…) but differ in how they handle the data velocity. We often distinguish three main categories of data ingestion tools: batch-based, real-time or stream-based, and hybrid ingestion. Within Google Cloud, we will see the different data ingestion services and how they can address the various categories of data ingestion.

## Storage Options Overview

Google Cloud Platform (GCP) offers various storage services that cater to different needs and scenarios. Some of the key storage services provided by Google Cloud include:

**1- Object storage** is a data storage architecture for storing unstructured data, which sections data into units (objects) and stores them in a structurally flat data environment. Each object includes the data, metadata, and a unique identifier that applications can use for easy access and retrieval. In Google Cloud, the [**_Cloud Storage_**](https://cloud.google.com/storage) Service is a scalable object storage service that allows storing and retrieving data globally. It's suitable for many use cases, including data backup, serving website content, storing large data sets for analysis, and more. Cloud Storage offers different storage classes, such as Standard, Nearline, Coldline, and Archive, each optimized for specific access patterns and cost considerations.

**2- Block storage** is a technology that controls data storage and storage devices. It divides any data, like a file or database entry, into blocks of equal sizes. The block storage system then stores the data block on underlying physical storage in a manner optimized for fast access and retrieval. In Google Cloud, several services allow storing the blocks:
- [**_Local SSD_**](https://cloud.google.com/local-ssd): Ephemeral locally attached block storage for virtual machines and containers.
- [**_Persistent disk_**](https://cloud.google.com/persistent-disk) provides durable block storage for Compute Engine virtual machine instances. It offers both standard and SSD persistent disks with different performance characteristics.
- [**_Hyperdisk_**](https://cloud.google.com/compute/docs/disks/hyperdisks): Next generation of block storage delivering higher scale and best in class price/performance.

**3- In File Storage**, data is stored in files, the files are organized in folders, and the folders are organized under a hierarchy of directories and subdirectories. Google Cloud provides several services for storing files:
- [**_Filestore_**](https://cloud.google.com/filestore): A managed file storage service for applications that require a filesystem interface and shared file storage for applications running on Compute Engine or Kubernetes Engine instances.
- [**_Parallelstore_**](https://cloud.google.com/parallelstore): High bandwidth, high IOPS, ultra-low latency, managed parallel file service.
- [**_NetApp Volumes_**](https://cloud.google.com/netapp-volumes): A fully managed, cloud-based data storage service that provides advanced data management capabilities and highly scalable performance.

**4- Databases**: A database is a structured data collection stored on a disk, memory, or both. Databases come in a variety of flavors:
- _In relational databases_, information is stored in tables, rows, and columns, which typically works best for structured data. There are three relational database options in Google Cloud: Cloud SQL, AlloyDB, and Cloud Spanner.
    - [**_Cloud SQL_**](https://cloud.google.com/sql): A fully-managed relational database service that supports MySQL, PostgreSQL, and SQL Server. It's ideal for applications requiring a traditional relational database structure.
    - [**_AlloyDB_**](https://cloud.google.com/alloydb/docs/overview) is a fully managed PostgreSQL-compatible database service for your most demanding enterprise database workloads.
    - [**_Cloud Spanner_**](https://cloud.google.com/spanner): A horizontally scalable, strongly consistent, relational database service designed for global transactions and high availability. It combines the benefits of traditional relational databases with the scalability and global distribution capabilities of NoSQL databases.
- _Non-relational databases_ (or NoSQL databases) store complex, unstructured data, such as documents, in a non-tabular form. Non-relational databases are often used when large quantities of complex and diverse data need to be organized or where the data structure is regularly evolving to meet new business requirements. There are three non-relational databases in Google Cloud:
    - [**_Bigtable_**](https://cloud.google.com/bigtable): A high-performance, fully-managed NoSQL database service suitable for large analytical and operational workloads. It's particularly useful for applications that require high throughput and scalability.
    - [**_Firestore_**](https://cloud.google.com/firestore): A NoSQL document database built for automatic scaling, high performance, and ease of application development. It's suitable for mobile, web, and server-side applications that require real-time updates and offline support.
    - [**_Memorystore_**](https://cloud.google.com/memorystore): Memorystore is a fully managed in-memory data store service for Redis and Memcached at Google Cloud. 

![](https://storage.googleapis.com/gweb-cloudblog-publish/images/Which-Database_v03-22-23.max-2000x2000.jpg){: .mx-auto.d-block :} *Google Cloud database options.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

**5- Data Warehouses**: A data warehouse is a standard OLAP data architecture (don’t dare call it an analytical database; Bill Inmon will be upset). It tends to handle large amounts of data quickly, allowing users to analyze facts according to multiple dimensions in tandem (Cube). In Google Cloud, [**_BigQuery_**](https://cloud.google.com/bigquery) is a fully managed, serverless data warehouse service that enables scalable analysis over petabytes of data.

**6- Date Lakehouses**: A data lakehouse combines the low-cost, scalable storage of a data lake and the structure and management features of a data warehouse. Google Cloud provides [**_BigLake_**](https://cloud.google.com/biglake) as a storage engine that provides a unified interface for analytics and AI engines to query multiformat, multi-cloud, and multimodal data securely, governed, and performantly. It unifies data warehouses and data lakes into a consistent format for faster data analytics across multi-cloud storage and open formats.

**7- Transfert Services**: Google Cloud provides a few transfer services to move data from other cloud providers or a physical appliance.

These services cater to different storage needs, whether you require object storage, relational databases, NoSQL databases, file storage, or other forms of data storage and management within the Google Cloud Platform. In the following sections, I will dive into each service to demonstrate how to ingest and load data into it.

## Ingest data into Object Storage
Cloud Storage is a service for storing your objects in Google Cloud. An object is an immutable piece of data consisting of a file of any format. You store objects in containers called buckets. All buckets are associated with a project; you can group your projects under an organization. 

![](https://cloud.google.com/static/storage/images/gcs-intro.svg){: .mx-auto.d-block :} *Cloud Storage Structure.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Each resource has a unique name that identifies it, much like a filename. Buckets have a resource name in the form of `projects/_/buckets/BUCKET_NAME`, where `BUCKET_NAME` is the ID of the bucket. Objects have a resource name in the form of `projects/_/buckets/BUCKET_NAME/objects/OBJECT_NAME`, where `OBJECT_NAME` is the object's ID.

A `#NUMBER` appended to the end of the resource name indicates a specific generation of the object. `#0` is a special identifier for the most recent version of an object. `#0` is useful to add when the object's name ends in a string that would otherwise be interpreted as a generation number.

Cloud Storage offers different storage classes:
- The **Standard** storage class provides the highest availability and performance level and is especially well-suited for frequently accessed or short-lived data.
- **Nearline** offers fast, low-cost, and highly durable storage designed for infrequently accessed data, including long-tail content.
- **Coldline** offers the benefits of Nearline storage while optimizing for colder data use cases, such as disaster recovery.
- **Archive** storage is the lowest-cost, highly durable storage service for data archiving, online backup, and disaster recovery. Unlike the “coldest” storage services other Cloud providers offer, your data is accessible within milliseconds, not hours or days.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*-Yo82u2bjPpDeJemlCED4g.png){: .mx-auto.d-block :} *Cloud Storage Classes.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Here are some basic ways you can import data into Cloud Storage:
- [Console](https://console.cloud.google.com/storage): The Google Cloud console provides a visual interface for managing your data in a browser.

![](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/980450c4-dd8e-4885-9eff-aa5973b51b8c){: .mx-auto.d-block :} *Importing Data using Console.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}
  
- [Google Cloud CLI](https://cloud.google.com/sdk/gcloud): The gcloud CLI allows you to interact with Cloud Storage through a terminal using gcloud storage commands.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/03177189-e8e8-4db7-8cc7-4661c8cc489d){: .mx-auto.d-block :} *Importing Data using Command Line.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}
  
- [Client libraries](https://cloud.google.com/storage/docs/reference/libraries): The Cloud Storage client libraries allow you to manage your data using one of your preferred languages, including C++, C#, Go, Java, Node.js, PHP, Python, and Ruby.

{% highlight python linenos %}
from google.cloud import storage

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    # The path to your file to upload
    # source_file_name = "local/path/to/file"
    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Optional: set a generation-match precondition to avoid potential race conditions
    # and data corruptions. The request to upload is aborted if the object's
    # generation number does not match your precondition. For a destination
    # object that does not yet exist, set the if_generation_match precondition to 0.
    # If the destination object already exists in your bucket, set instead a
    # generation-match precondition using its generation number.
    generation_match_precondition = 0

    blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)

    print(
        f"File {source_file_name} uploaded to {destination_blob_name}."
    )
{% endhighlight %}
  
- REST APIs: Manage your data using the [JSON](https://cloud.google.com/storage/docs/json_api) or [XML](https://cloud.google.com/storage/docs/xml-api) APIs. These APIs are used by many other service such as [PubSub](https://cloud.google.com/pubsub/docs/create-cloudstorage-subscription), [Dataflow](https://cloud.google.com/dataflow/docs/guides/write-to-cloud-storage), [Dataproc](https://cloud.google.com/dataproc/docs/tutorials/gcs-connector-spark-tutorial) (Apache Spark to Cloud Storage Connector), and many other connectors (e.g., Kafka, Confluent...) to import batch and Streaming data into Cloud Storage.

```
POST /OBJECT_NAME HTTP/2
Host: BUCKET_NAME.storage.googleapis.com
Date: DATE
Content-Length: REQUEST_BODY_LENGTH
Content-Type: MIME_TYPE
X-Goog-Resumable: start
Authorization: AUTHENTICATION_STRING
```

- With Infrastructure-as-Code (IaC) tools, you can provision the infrastructure for Cloud Storage and run jobs to import/sync data into it.

{% highlight yaml linenos %}
- name: "Creating a Bucket on GCP"
  hosts: localhost
  tasks:

    - name: "Creating the Bucket"
      google.cloud.gcp_storage_bucket:
        name: "The_bucket_name"
        project: "The_project_name"
        auth_kind: "serviceaccount"
        service_account_file: "/your/service/account/file.json"
        state: present
      register: bucket
{% endhighlight %}


- [Cloud Storage FUSE](https://cloud.google.com/storage/docs/gcs-fuse): Cloud Storage FUSE allows you to mount Cloud Storage buckets to your local file system. Standard file system semantics enable your applications to read from a bucket or write to a bucket.

## Ingest data into Block Storage
### 2A. Persistent Disk
By default, each Compute Engine virtual machine (VM) instance has a single boot Persistent Disk volume that contains the operating system. When your apps require additional storage space, one possible solution is to attach additional Persistent Disk volumes to your VM.

Persistent Disk volumes are durable network storage devices that your VMs can access, like physical disks in a desktop or a server. The data on each persistent disk is distributed across several physical disks. Compute Engine manages the physical disks and the data distribution for you to ensure redundancy and optimal performance.

Persistent Disk volumes are located independently from your VMs, so you can detach or move the volumes to keep your data even after you delete your instances. Persistent Disk performance scales automatically with size, so you can resize your existing Persistent Disk volumes or add more Persistent Disk volumes to a VM to meet your performance and storage space requirements.

You can create and attach a non-boot zonal disk by using the [Google Cloud console](https://console.cloud.google.com), the [Google Cloud CLI](https://cloud.google.com/compute/docs/gcloud-compute), Terraform or [REST API](https://cloud.google.com/compute/docs/reference/rest/v1/instances).

You should specify a custom device name when attaching the disk to a VM. The name you specify is used to generate a [symlink](https://cloud.google.com/compute/docs/disks/disk-symlinks) for the disk in the guest OS, making identification easier.

### 2B. Hyperdisk
Google Cloud Hyperdisk is the newest generation of network block storage service in Google Cloud. Designed for the most demanding mission-critical applications, Hyperdisk offers a scalable, high-performance storage service with a comprehensive data persistence and management capabilities suite. With Hyperdisk, you can provision, manage, and scale your Compute Engine workloads without the cost and complexity of a typical on-premises storage area network (SAN).

The new variant of Persistent Disks allows users to make independent workload-based performance tuning using three metrics- IOPS, throughput and capacity. The Persistent Disks are divided into three categories – Hyperdisk Throughput, Hyperdisk Balanced and Hyperdisk Extreme.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/19f069a7-2907-405c-9d14-3fa71f7991b3){: .mx-auto.d-block :} *Cloud Hyperdisk Categories.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Hyperdisk volumes are durable network storage devices that your VMs can access, similar to Persistent Disk volumes. The data on each Hyperdisk is distributed across several physical disks. Compute Engine manages the physical disks and the data distribution for you to ensure redundancy and optimal performance.

Hyperdisk volumes are located independently from your VMs, so you can detach or move Hyperdisk volumes to keep your data, even after you delete your VMs. Hyperdisk performance is decoupled from size, so you can dynamically update the performance, resize your existing Hyperdisk volumes, or add more Hyperdisk volumes to a VM to meet your performance and storage space requirements.

### 2C. Local SSD

If your workloads need high-performance, low-latency temporary storage, consider using Local solid-state drive (Local SSD) disks when you create your virtual machine (VM). Local SSD disks are always-encrypted solid-state storage for Compute Engine VMs.

Local SSD disks are ideal when you need storage for any of the following use cases:
- Caches or storage for transient, low-value data
- Scratch processing space for high-performance computing or data analytics
- Temporary data storage like for the tempdb system database for Microsoft SQL Server

Local SSD disks offer superior I/O operations per second (IOPS) and very low latency compared to [Persistent disk](https://cloud.google.com/persistent-disk) and Google Cloud [Hyperdisk](https://cloud.google.com/compute/docs/disks/hyperdisks). This is because Local SSD disks are physically attached to the server that hosts your VM. For this same reason, Local SSD disks can only provide temporary storage. Because Local SSD is suitable only for temporary storage, you must store data that is not temporary or ephemeral on one of our durable storage options.

Once the disk is created and attached to the VM, you have to format and mount it (see details for [Linux](https://cloud.google.com/compute/docs/disks/format-mount-disk-linux) and here for [Windows](https://cloud.google.com/compute/docs/disks/format-mount-disk-windows)). You may wish to transfer files from your data source to your VM’s remote block volume. This can be achieved with `rsync`, a tool for efficiently transferring and copying files. The rsync utility is preinstalled on most Linux distributions and macOS.

```shell
rsync -a hello-world.txt root@<your.VM.IP.address>:/mnt/block-volume
```

## Ingest data into File Storage
Most data on-premise is stored in file systems, and as applications migrate to the cloud, their need for File storage doesn’t change, so file storage is critical to enterprise lift-and-shift and infrastructure modernization. Files are a useful abstraction, and even cloud-native applications are leveraging files.

### 3A. Filestore

Google Filestore is a fully managed file storage service enabling you to store and access data on Google Cloud. It is designed for use cases that require fast, scalable, and low-latency access to file data, such as shared file systems and home directories.

Filestore is integrated with other Google Cloud services, such as Compute Engine, Kubernetes Engine, and Cloud Load Balancing, allowing you to scale and manage your file storage needs efficiently.

Filestore enables application migration to the cloud without requiring you to rewrite or re-architect, accelerating and simplifying your migration. Filestore supports applications that expect to use standard files and directories. If your apps run on Windows or Linux, they most likely rely on file storage behind the scenes.

A Filestore instance represents physical storage capacity. A share represents an allocated portion of that storage with an individual, unique access point. All service tiers offer storage options with a 1:1 share–to–instance ratio. 

Alternatively, Filestore multishares for GKE, available for enterprise-tier instances only, offer access to multiple shares on a single instance.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/24db35ff-71a1-4734-835b-5a3705755447){: .mx-auto.d-block :} *Transfer data sets from Cloud Engine to Filestore.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Instance names, or instance IDs, are used by administrators to manage instances. Clients use file share names to connect to the shares exported from those instances.

You can create a Filestore instance by using either the [Google Cloud console](https://console.cloud.google.com/filestore) or the [gcloud CLI](https://cloud.google.com/sdk/gcloud/reference/filestore/instances/create).

Filestore offers three performance tiers: Standard, High Performance, and Extreme Performance. The performance tier you choose depends on your workload requirements and the type of file data you are storing.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/0*j_Jxd20VF-tnLZjL){: .mx-auto.d-block :} *Filestore Tiers.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### 3B. Parallelstore

As businesses continue to grapple with the unique storage and access demands of data-intensive AI workloads, they’re looking to the cloud to deliver highly capable, cost-effective, and easily manageable storage solutions. Google Cloud customers training AI models often turn to GPU/TPUs for the needed performance. But let’s face it: Those resources are limited and are an infrastructure asset you want to utilize fully.

Google Cloud Parallelstore, now in private Preview, helps you stop wasting precious GPU resources. At the same time, you wait for storage I/O by providing a high-performing parallel file storage solution for AI/ML and HPC workloads. By keeping your GPUs saturated with the data you need to optimize the AI/ML training phase, Parallelstore can help you significantly reduce — or even eliminate — costs associated with idle GPUs. 

Based on the next-generation Intel DAOS architecture, all compute nodes in a Parallelstore environment have equal access to storage so that VMs can get immediate access to their data. With up to 6.3x read throughput performance compared to competitive Lustre Scratch offerings., Parallelstore is well suited for cloud-based applications that require extremely high performance (IOPS and throughput) and ultra-low latency. 

To deploy DAOS on GCP, you may choose one of the following deployment paths.

1- [Cloud HPC Toolkit](https://cloud.google.com/hpc-toolkit) is open-source software offered by Google Cloud, which makes it easy for you to deploy high-performance computing (HPC) environments. It is designed to be highly customizable and extensible and intends to address the HPC deployment needs of a broad range of use cases.

The [community examples](https://github.com/GoogleCloudPlatform/hpc-toolkit/tree/main/community/examples/intel) in the [Cloud HPC Toolkit](https://cloud.google.com/hpc-toolkit) use the [DAOS modules](terraform/modules/) in this repository.

2- Deploy DAOS with the [DAOS cluster](https://github.com/daos-stack/google-cloud-daos/tree/main/terraform/examples) example demonstrates how to use the [DAOS modules](https://github.com/daos-stack/google-cloud-daos/tree/main/terraform/modules) in a Terraform configuration to deploy a DAOS cluster consisting of servers and clients.

3- As an alternative to viewing the instructions in [Deploy the DAOS Cluster Example](docs/deploy_daos_cluster_example.md) as a standalone document, you can view it as an in-context tutorial in [Cloud Shell](https://cloud.google.com/shell) by clicking the button below.

[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.png)](https://ssh.cloud.google.com/cloudshell/open?cloudshell_git_repo=https://github.com/daos-stack/google-cloud-daos.git&cloudshell_git_branch=main&shellonly=true&cloudshell_tutorial=docs/deploy_daos_cluster_example.md)

### 3C. NetApp Volumes

In addition, Google Cloud has partnered with NetApp to offer a fully managed, cloud-native data storage service that provides advanced data management capabilities and highly scalable performance, called [Cloud Volumes Service](https://www.netapp.com/us/cloud-marketplace/google-cloud-platform.aspx).

Whether you want to migrate existing enterprise and industry-specific apps to Google Cloud or build new machine learning (ML) and Kubernetes-based apps that require persistent storage, you can accelerate deployment times while lowering costs by using Cloud Volumes Service.

NetApp Volumes enables data sharing for Windows/Linux applications, making it useful for user and group shares, application shares for unstructured data, SAP shared files, VDI, shared storage for MS-SQL, binaries, log files, config files, user and group shares, shared machine learning data, EDA-shared chip design data, and PACS images.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/1a20a63a-9627-4cd4-8b9c-3ececa4dd73c){: .mx-auto.d-block :} *NetApp Storage on Compute Engine.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Moreover, Google Cloud NetApp Volumes enable easy data recovery if a user or application deletes data accidentally, and scheduled snapshots provide convenient, low RPO/RTO recovery points. Users can access snapshots and self-restore data quickly and easily from within the console. For example, NetApp Volumes enables fast ransomware recovery. Quickly revert any volume back to a snapshot taken before the ransomware hit. Volume recovery time is less than one minute versus restoring from backup, which can take hours.

![](https://lh3.googleusercontent.com/7GaEyxS3gm6uX3APRqWRNA15AmxITP59odKUGKDOF4MHcbZrkuQ1uMrY-1zvcJwZmnSIyroIGBm7lQ=s2048-w2048-rw-lo){: .mx-auto.d-block :} *Ransomware Attacks Recovery using NetApp.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Once you mount the File Storage instance (Filestore, Parallelstore or NetApp) to a Compute Engine instance or a Kubernetes Engine cluster as a file system, you can use it like any other file system on your instances.

### Ingest data into Google Cloud databases
### 4A. CloudSQL
Cloud SQL supports the most popular open source and commercial engines, including MySQL, PostgreSQL, and SQL Server with rich support for extensions, configuration flags, and popular developer tools. 

Ingesting data into these database engines are more often used to migrate local databases to managed ones (lift and shift). Depending on the source data velocity, you might consider different migration strategies:

1\- For Batch data, you can use SQL dump files or CSV dump files to import data into CloudSQL. SQL dump files are plain text files with a sequence of SQL commands. CSV dump files contain one line for each row of data fields. 

To import data from Cloud Storage, the Cloud SQL instance service account or user must have one of the following sets of roles:
- The Cloud SQL Admin role and the `roles/storage.legacyObjectReader` IAM role
- A **custom role** including the following permissions:
    - `cloudsql.instances.get`
    - `cloudsql.instances.import`
    - `storage.buckets.get`
    - `storage.objects.get`

To ingest data into CloudSQL, using the SQL/CSV dump files you can use either:
- [Console](https://console.cloud.google.com/sql): The Google Cloud console provides a visual interface for importing your data in your database instance.

![](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/1701f8cf-8e32-41a7-a116-ff3d41b9675f){: .mx-auto.d-block :} *Importing SQL dump files using Console.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}
  
- [Google Cloud CLI](https://cloud.google.com/sdk/gcloud): The gcloud CLI allows you to interact with CloudSQL database instance through a terminal using gcloud storage commands.

CSV dump file import command:
```shell
gcloud sql import csv INSTANCE_NAME gs://BUCKET_NAME/FILE_NAME \
--database=DATABASE_NAME \
--table=TABLE_NAME
```

SQL dump file import command:
```shell
gcloud sql import sql INSTANCE_NAME gs://BUCKET_NAME/IMPORT_FILE_NAME \
--database=DATABASE_NAME
```

- REST APIs: Manage your data using the [JSON](https://cloud.google.com/storage/docs/json_api) API.

HTTP method and URL:
```shell
POST https://sqladmin.googleapis.com/v1/projects/project-id/instances/instance-id/import
```

Request JSON body:
{% highlight json linenos %}
{
 "importContext":
   {
      "fileType": "CSV",
      "uri": "gs://bucket_name/path_to_csv_file",
      "database": ["DATABASE_NAME"],
      "csvImportOptions":
       {
           "table": "TABLE_NAME",
           "escapeCharacter":  "5C",
           "quoteCharacter": "22",
           "fieldsTerminatedBy": "2C",
           "linesTerminatedBy": "0A"
       }
   }
}
{% endhighlight %}

2\- For both Batch and Streaming data, you can use the Database Migration Service (DMS) to create migration jobs. 

Database Migration Service provides options for one-time and continuous jobs to migrate data to Cloud SQL using different connectivity options, including IP allowlists, VPC peering, and reverse SSH tunnels (see documentation on connectivity options [here](https://cloud.google.com/database-migration/docs/postgresql/configure-connectivity).

Migrating a database via Database Migration Service requires some preparation of the source database, including creating a dedicated user with replication rights, adding a few extensions (e.g., pglogical for PostgreSQL) to the source database and granting rights to the schema and tables in the database to be migrated, as well as the database, to that user. The following steps are mandatory to to configure a continuous Database Migration Service job to migrate databases from a PostgreSQL instance to Cloud SQL for PostgreSQL.

A\- Verify that the Database Migration API is enabled in GCP console.
B\- Prepare the source database for migration: In this step, you will install and configure the pglogical database extension. 

In your PostgreSQL VM, you have to install the pglogical extension:

```
sudo apt install postgresql-13-pglogical
sudo systemctl restart postgresql@13-main
```

In `pg_hba.conf` these commands added a rule to allow access to all hosts:

```
#GSP918 - allow access to all hosts
host    all all 0.0.0.0/0   md5
```

In `postgresql.conf`, these commands set the minimal configuration for pglogical to configure it to listen on all addresses:

```properties
#GSP918 - added configuration for pglogical database extension

wal_level = logical         # minimal, replica, or logical
max_worker_processes = 10   # one per database needed on provider node
                            # one per node needed on subscriber node
max_replication_slots = 10  # one per node needed on provider node
max_wal_senders = 10        # one per node needed on provider node
shared_preload_libraries = 'pglogical'
max_wal_size = 1GB
min_wal_size = 80MB

listen_addresses = '*'         # what IP address(es) to listen on, '*' is all
The above code snippets were appended to the relevant files and the PostgreSQL service restarted.
```

Then, launch the psql tool:

```shell
sudo su - postgres
psql
```

And, add the pglogical database extension to the postgres (default database), and all databases you want to migrate (e.g., orders database).

{% highlight SQL linenos %}
\c postgres;
CREATE EXTENSION pglogical;
\c orders;
CREATE EXTENSION pglogical;
{% endhighlight %}

C\- Create the database migration user: In this step you will create a dedicated user for managing database migration.

In psql, enter the commands below to create a new user with the replication role:

{% highlight SQL linenos %}
CREATE USER migration_admin PASSWORD 'DMS_1s_cool!';
ALTER DATABASE orders OWNER TO migration_admin;
ALTER ROLE migration_admin WITH REPLICATION;
{% endhighlight %}

D\- Assign permissions to the migration user: In this step you will assign the necessary permissions to the migration_admin user to enable Database Migration Service to migrate your database. 

In `psql`, grant permissions to the pglogical schema and tables for the postgres database.

{% highlight SQL linenos %}
\c postgres;

GRANT USAGE ON SCHEMA pglogical TO migration_admin;
GRANT ALL ON SCHEMA pglogical TO migration_admin;

GRANT SELECT ON pglogical.tables TO migration_admin;
GRANT SELECT ON pglogical.depend TO migration_admin;
GRANT SELECT ON pglogical.local_node TO migration_admin;
GRANT SELECT ON pglogical.local_sync_status TO migration_admin;
GRANT SELECT ON pglogical.node TO migration_admin;
GRANT SELECT ON pglogical.node_interface TO migration_admin;
GRANT SELECT ON pglogical.queue TO migration_admin;
GRANT SELECT ON pglogical.replication_set TO migration_admin;
GRANT SELECT ON pglogical.replication_set_seq TO migration_admin;
GRANT SELECT ON pglogical.replication_set_table TO migration_admin;
GRANT SELECT ON pglogical.sequence_state TO migration_admin;
GRANT SELECT ON pglogical.subscription TO migration_admin;
{% endhighlight %}

In `psql`, grant permissions to the pglogical schema and tables for the orders database.

{% highlight SQL linenos %}
\c orders;

GRANT USAGE ON SCHEMA pglogical TO migration_admin;
GRANT ALL ON SCHEMA pglogical TO migration_admin;

GRANT SELECT ON pglogical.tables TO migration_admin;
GRANT SELECT ON pglogical.depend TO migration_admin;
GRANT SELECT ON pglogical.local_node TO migration_admin;
GRANT SELECT ON pglogical.local_sync_status TO migration_admin;
GRANT SELECT ON pglogical.node TO migration_admin;
GRANT SELECT ON pglogical.node_interface TO migration_admin;
GRANT SELECT ON pglogical.queue TO migration_admin;
GRANT SELECT ON pglogical.replication_set TO migration_admin;
GRANT SELECT ON pglogical.replication_set_seq TO migration_admin;
GRANT SELECT ON pglogical.replication_set_table TO migration_admin;
GRANT SELECT ON pglogical.sequence_state TO migration_admin;
GRANT SELECT ON pglogical.subscription TO migration_admin;

GRANT USAGE ON SCHEMA public TO migration_admin;
GRANT ALL ON SCHEMA public TO migration_admin;

GRANT SELECT ON public.distribution_centers TO migration_admin;
GRANT SELECT ON public.inventory_items TO migration_admin;
GRANT SELECT ON public.order_items TO migration_admin;
GRANT SELECT ON public.products TO migration_admin;
GRANT SELECT ON public.users TO migration_admin;
{% endhighlight %}

The source databases are now prepared for migration. The permissions you have granted to the migration_admin user are all that is required for Database Migration Service to migrate the postgres and orders databases.

Make the migration_admin user the owner of the tables in the orders database, so that you can edit the source data later, when you test the migration.

{% highlight SQL linenos %}
\c orders;
\dt
ALTER TABLE public.distribution_centers OWNER TO migration_admin;
ALTER TABLE public.inventory_items OWNER TO migration_admin;
ALTER TABLE public.order_items OWNER TO migration_admin;
ALTER TABLE public.products OWNER TO migration_admin;
ALTER TABLE public.users OWNER TO migration_admin;
\dt
{% endhighlight %}

E\- Create a Database Migration Service connection profile for a stand-alone PostgreSQL database: In this task, you will create a connection profile for the PostgreSQL source instance. For Connection profile name, enter `postgres-vm`, for Hostname or IP address, enter the internal IP for the PostgreSQL source instance that you copied in the previous task (e.g., 10.128.0.2), and for Port, enter `5432`. Then, enter `migration_admin` and `DMS_1s_cool!` as username and password.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/c3b569d3-cbbe-46a7-a78c-b8bb537cad34){: .mx-auto.d-block :} *Creating a DMS connection profile.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

F\- Create and start a continuous migration job: When you create a new migration job, you first define the source database instance using a previously created connection profile. For Source connection profile, select `postgres-vm`.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/7834f1eb-58c7-43c6-8f86-2185a81e07ca){: .mx-auto.d-block :} *Creating a migration job.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Then you create a new destination database instance and configure connectivity between the source and destination instances.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/003f4271-363e-4283-94b0-7be5e082bda5){: .mx-auto.d-block :} *Creating the destination database.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

G\- Test and start the continuous migration job: In the Database Migration Service tab you open earlier, review the details of the migration job. Click Test Job. After a successful test, click Create & Start Job.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/15de85e8-8c53-4437-8603-2a56e0476b3a){: .mx-auto.d-block :} *Testing and Running the migration job.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

After the job has started, the status will show as Starting and then transition to Running Full dump in progress to indicate that the initial database dump is in progress. After the initial database dump has been completed, the status will transition to Running CDC in progress to indicate that continuous migration is active.

![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/1aab4136-c9a7-43d3-a387-4fe8ae5dd478){: .mx-auto.d-block :} *Checking migration status.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

After you create and run the migration job, you confirm that an initial copy of your database has been successfully migrated from sourse database to your Cloud SQL target instance. You also explore how continuous migration jobs apply data updates from your source database to your Cloud SQL instance. 

### 4B. Cloud Spanner
### 4C. BigTable
### 4D. Firestore
### 4E. Memorystore
## Load data into Google Cloud BigQuery (Data Warehouse)
## Load data into Google Cloud BigLake (Data Lakehouse)
## Load data using Transfert Appliance
![image](https://github.com/aelkouhen/aelkouhen.github.io/assets/22400454/6fd675ca-ec0e-4623-9f6b-b1e6c1ec2d57)


## Summary

## References
* [Product overview of Cloud Storage, Google Cloud Docs](https://cloud.google.com/storage/docs/introduction)
* [About Persistent Disk, Google Cloud Docs](https://cloud.google.com/compute/docs/disks/persistent-disks)
* [Distributed Asynchronous Object Storage (DAOS)](https://docs.daos.io/)
* [Google Cloud Platform (GCP)](https://cloud.google.com/)
* [Google Cloud HPC Toolkit](https://cloud.google.com/hpc-toolkit)
