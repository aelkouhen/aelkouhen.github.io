---
layout: post
title: Data on GCP series - part 1
subtitle:  Data Ingestion using Google Cloud Services
thumbnail-img: 
share-img: 
tags: []
comments: true
---

Through the “Data on GCP” series, you will learn how to collect, store, process, analyze, and expose data using a wide variety of tools provided by Google Cloud Platform (GCP). Google Cloud is a suite of cloud computing services that provides a series of modular cloud services, including computing, data storage, data analytics, and machine learning, alongside a set of management tools.

In this article, I will illustrate data ingestion and integration using the myriad of tools Google Cloud provides. As you’ve seen earlier, Data ingestion is the first stage of the data lifecycle. This is where data is collected from various internal sources like databases, CRM, ERPs, legacy systems, external ones such as surveys, and third-party providers. This is an important step because it ensures the excellent working of subsequent stages in the data lifecycle.

In this stage, raw data are extracted from one or more data sources, replicated, and then ingested into a landing storage service. We’ve seen that most ingestion tools can handle a high volume of data with a wide range of formats (structured, unstructured…) but differ in how they handle the data velocity. We often distinguish three main categories of data ingestion tools: batch-based, real-time or stream-based, and hybrid ingestion. Within Google Cloud, we will see the different data ingestion services and how they can address the different categories of data ingestion.

## Storage Options Overview

Google Cloud Platform (GCP) offers various storage services designed to cater to different needs and scenarios. Some of the key storage services provided by Google Cloud include:

**1- Object storage** is a data storage architecture for storing unstructured data, which sections data into units (objects) and stores them in a structurally flat data environment. Each object includes the data, metadata, and a unique identifier that applications can use for easy access and retrieval. In Google Cloud, the [**_Cloud Storage_**](https://cloud.google.com/storage) Service is a scalable object storage service that allows you to store and retrieve data globally. It's suitable for a wide range of use cases, including data backup, serving website content, storing large data sets for analysis, and more. Cloud Storage offers different storage classes, such as Standard, Nearline, Coldline, and Archive, each optimized for specific access patterns and cost considerations.

**2- Block storage** is a technology that controls data storage and storage devices. It divides any data, like a file or database entry, into blocks of equal sizes. The block storage system then stores the data block on underlying physical storage in a manner that is optimized for fast access and retrieval. In Google Cloud, several services allow storing the blocks:
- [**_Local SSD_**](https://cloud.google.com/local-ssd): Ephemeral locally attached block storage for virtual machines and containers.
- [**_Persistent disk_**](https://cloud.google.com/persistent-disk) provides durable block storage for Compute Engine virtual machine instances. It offers both standard and SSD persistent disks with different performance characteristics.
- [**_Hyperdisk_**](https://cloud.google.com/compute/docs/disks/hyperdisks): Next generation of block storage delivering higher scale and best in class price/performance.

**3- In File Storage**, data is stored in files, the files are organized in folders, and the folders are organized under a hierarchy of directories and subdirectories. Google Cloud provides several services to storing files:
- [**_Filestore_**](https://cloud.google.com/filestore): A managed file storage service for applications that require a filesystem interface and shared file storage for applications running on Compute Engine or Kubernetes Engine instances.
- [**_Parallelstore_**](https://cloud.google.com/parallelstore): High bandwidth, high IOPS, ultra-low latency, managed parallel file service.
- [**_NetApp Volumes_**](https://cloud.google.com/netapp-volumes): A fully managed, cloud-based data storage service that provides advanced data management capabilities and highly scalable performance.

**4- Databases**: A database is a structured data collection stored on a disk, memory, or both. Databases come in a variety of flavors:
- _In relational databases_, information is stored in tables, rows, and columns, which typically works best for structured data. There are three relational database options in Google Cloud: Cloud SQL, AlloyDB, and Cloud Spanner.
    - [**_Cloud SQL_**](https://cloud.google.com/sql): A fully-managed relational database service that supports MySQL, PostgreSQL, and SQL Server. It's ideal for applications requiring a traditional relational database structure.
    - [**_AlloyDB_**](https://cloud.google.com/alloydb/docs/overview) is a fully managed PostgreSQL-compatible database service for your most demanding enterprise database workloads.
    - [**_Cloud Spanner_**](https://cloud.google.com/spanner): A horizontally scalable, strongly consistent, relational database service designed for global transactions and high availability. It combines the benefits of traditional relational databases with the scalability and global distribution capabilities of NoSQL databases.
- _Non-relational databases_ (or NoSQL databases) store complex, unstructured data such as documents in a non-tabular form. Non-relational databases are often used when large quantities of complex and diverse data need to be organized or where the structure of the data is regularly evolving to meet new business requirements. There are three non-relational databases in Google Cloud:
    - [**_Bigtable_**](https://cloud.google.com/bigtable): A high-performance, fully-managed NoSQL database service suitable for large analytical and operational workloads. It's particularly useful for applications that require high throughput and scalability.
    - [**_Firestore_**](https://cloud.google.com/firestore): A NoSQL document database built for automatic scaling, high performance, and ease of application development. It's suitable for mobile, web, and server-side applications that require real-time updates and offline support.
    - [**_Memorystore_**](https://cloud.google.com/memorystore): Memorystore is a fully managed in-memory data store service for Redis and Memcached at Google Cloud. 

![](https://storage.googleapis.com/gweb-cloudblog-publish/images/Which-Database_v03-22-23.max-2000x2000.jpg){: .mx-auto.d-block :} *Google Cloud database options.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

**5- Data Warehouses**: A data warehouse is a standard OLAP data architecture (don’t dare call it an analytical database; Bill Inmon will be upset). It tends to handle large amounts of data quickly, allowing users to analyze facts according to multiple dimensions in tandem (Cube). In Google Cloud, [**_BigQuery_**](https://cloud.google.com/bigquery) is a fully managed, serverless data warehouse service that enables scalable analysis over petabytes of data.

**6- Date Lakehouses**: A data lakehouse combines the low-cost, scalable storage of a data lake and the structure and management features of a data warehouse. Google Cloud provides [**_BigLake_**](https://cloud.google.com/biglake) as a storage engine that provides a unified interface for analytics and AI engines to query multiformat, multi-cloud, and multimodal data securely, governed, and performantly. It unifies data warehouses and data lakes into a consistent format for faster data analytics across multi-cloud storage and open formats.

**7- Transfert Services**: Google Cloud provides a few transfer services to move data from other cloud providers or from a physical appliance.

These services cater to different storage needs, whether you require object storage, relational databases, NoSQL databases, file storage, or other forms of data storage and management within the Google Cloud Platform. In the next sections, I will dive into each service to demonstrate how to ingest and load data into it.

## Data Ingest according to Google Cloud Services
### 1- Ingest data into Object Storage
Cloud Storage is a service for storing your objects in Google Cloud. An object is an immutable piece of data consisting of a file of any format. You store objects in containers called buckets. All buckets are associated with a project, and you can group your projects under an organization. 

![](https://cloud.google.com/static/storage/images/gcs-intro.svg){: .mx-auto.d-block :} *Cloud Storage Structure.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Each resource has a unique name that identifies it, much like a filename. Buckets have a resource name in the form of `projects/_/buckets/BUCKET_NAME`, where `BUCKET_NAME` is the ID of the bucket. Objects have a resource name in the form of `projects/_/buckets/BUCKET_NAME/objects/OBJECT_NAME`, where `OBJECT_NAME` is the ID of the object.

A `#NUMBER` appended to the end of the resource name indicates a specific generation of the object. `#0` is a special identifier for the most recent version of an object. `#0` is useful to add when the name of the object ends in a string that would otherwise be interpreted as a generation number.

Cloud Storage offers different storage classes:
- The **Standard** storage class provides the highest level of availability and performance and is especially well-suited for frequently accessed or short-lived data.
- **Nearline** offers fast, low-cost, and highly durable storage designed for infrequently accessed data, including long-tail content.
- **Coldline** offers the benefits of Nearline storage while optimizing for colder data use cases, such as disaster recovery.
- **Archive** storage is the lowest-cost, highly durable storage service for data archiving, online backup, and disaster recovery. Unlike the “coldest” storage services offered by other Cloud providers, your data is accessible within milliseconds, not hours or days.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/1*-Yo82u2bjPpDeJemlCED4g.png){: .mx-auto.d-block :} *Cloud Storage Classes.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Here are some basic ways you can import data into Cloud Storage:
- [Console](https://console.cloud.google.com/storage): The Google Cloud console provides a visual interface for you to manage your data in a browser.
- [Google Cloud CLI](https://cloud.google.com/sdk/gcloud): The gcloud CLI allows you to interact with Cloud Storage through a terminal using gcloud storage commands.
- [Client libraries](https://cloud.google.com/storage/docs/reference/libraries): The Cloud Storage client libraries allow you to manage your data using one of your preferred languages, including C++, C#, Go, Java, Node.js, PHP, Python, and Ruby.
- REST APIs: Manage your data using the [JSON](https://cloud.google.com/storage/docs/json_api) or [XML](https://cloud.google.com/storage/docs/xml-api) APIs.
- [Terraform](https://www.terraform.io/): Terraform is an infrastructure-as-code (IaC) tool that you can use to provision the infrastructure for Cloud Storage.
- [Cloud Storage FUSE](https://cloud.google.com/storage/docs/gcs-fuse): Cloud Storage FUSE allows you to mount Cloud Storage buckets to your local file system. This enables your applications to read from a bucket or write to a bucket by using standard file system semantics.

### 2- Sync data into Block Storage
#### 2A. Persistent Disk
By default, each Compute Engine virtual machine (VM) instance has a single boot Persistent Disk volume that contains the operating system. When your apps require additional storage space, one possible solution is to attach additional Persistent Disk volumes to your VM.

Persistent Disk volumes are durable network storage devices that your VMs can access like physical disks in a desktop or a server. The data on each persistent disk is distributed across several physical disks. Compute Engine manages the physical disks and the data distribution for you to ensure redundancy and optimal performance.

Persistent Disk volumes are located independently from your VMs, so you can detach or move the volumes to keep your data even after you delete your instances. Persistent Disk performance scales automatically with size, so you can resize your existing Persistent Disk volumes or add more Persistent Disk volumes to a VM to meet your performance and storage space requirements.

You can create and attach a non-boot zonal disk by using the [Google Cloud console](https://console.cloud.google.com), the [Google Cloud CLI](https://cloud.google.com/compute/docs/gcloud-compute), Terraform or [REST API](https://cloud.google.com/compute/docs/reference/rest/v1/instances).

You should specify a custom device name when attaching the disk to a VM. The name you specify is used to generate a [symlink](https://cloud.google.com/compute/docs/disks/disk-symlinks) for the disk in the guest OS, making identification easier.

#### 2B. Hyperdisk
Google Cloud Hyperdisk is the newest generation of network block storage service in Google Cloud. Designed for the most demanding mission-critical applications, Hyperdisk offers a scalable, high-performance storage service with a comprehensive suite of data persistence and management capabilities. With Hyperdisk you can provision, manage, and scale your Compute Engine workloads without the cost and complexity of a typical on-premises storage area network (SAN).

Hyperdisk volumes are durable network storage devices that your VMs can access, similar to Persistent Disk volumes. The data on each Hyperdisk is distributed across several physical disks. Compute Engine manages the physical disks and the data distribution for you to ensure redundancy and optimal performance.

Hyperdisk volumes are located independently from your VMs, so you can detach or move Hyperdisk volumes to keep your data, even after you delete your VMs. Hyperdisk performance is decoupled from size, so you can dynamically update the performance, resize your existing Hyperdisk volumes or add more Hyperdisk volumes to a VM to meet your performance and storage space requirements.

#### 2C. Local SSD

If your workloads need high performance, low latency temporary storage, consider using Local solid-state drive (Local SSD) disks when you create your virtual machine (VM). Local SSD disks are always-encrypted solid-state storage for Compute Engine VMs.

Local SSD disks are ideal when you need storage for any of the following use cases:
- Caches or storage for transient, low value data
- Scratch processing space for high-performance computing or data analytics
- Temporary data storage like for the tempdb system database for Microsoft SQL Server

Local SSD disks offer superior I/O operations per second (IOPS), and very low latency compared to [Persistent disk](https://cloud.google.com/persistent-disk) and Google Cloud [Hyperdisk](https://cloud.google.com/compute/docs/disks/hyperdisks). This is because Local SSD disks are physically attached to the server that hosts your VM. For this same reason, Local SSD disks can only provide temporary storage. Because Local SSD is suitable only for temporary storage, you must store data that is not temporary or ephemeral in nature on one of our durable storage options.

Once the disk is created and attached to the VM, you have to format and mount it (see details for [Linux](https://cloud.google.com/compute/docs/disks/format-mount-disk-linux) and here for [Windows](https://cloud.google.com/compute/docs/disks/format-mount-disk-windows)). You may wish to transfer files from your a data source to your VM’s remote block volume. This can be simply achieved with `rsync`, a tool for efficiently transferring and copying files. The rsync utility is preinstalled on most Linux distributions and macOS.

```shell
rsync -a hello-world.txt root@<your.VM.IP.address>:/mnt/block-volume
```

### 3- Import data into File Storage
Most data on-premise is stored in file systems, as applications migrate to the cloud, their need for File storage doesn’t change, so file storage is critical to enterprise lift-and-shift and infrastructure modernization. Files are a useful abstraction, and even cloud-native applications are leveraging files.

#### 3A. Filestore

Google Filestore is a fully managed file storage service that enables you to store and access file data on Google Cloud. It is designed for use cases that require fast, scalable, and low-latency access to file data, such as shared file systems and home directories.

Filestore is integrated with other Google Cloud services, such as Compute Engine, Kubernetes Engine, and Cloud Load Balancing, allowing you to easily scale and manage your file storage needs.

Filestore enables application migration to the cloud without requiring you to rewrite or re-architect, accelerating and simplifying your migration. Filestore supports applications that expect to use standard files and directories. If your apps are running on Windows or Linux, most likely they rely on file storage behind the scenes.

A Filestore instance represents physical storage capacity. A share represents an allocated portion of that storage with an individual, unique access point. All service tiers offer storage options with a 1:1 share–to–instance ratio. 

Alternatively, Filestore multishares for GKE, available for enterprise-tier instances only, offers access to multiple shares on a single instance.

Instance names, or instance IDs, are used by administrators to manage instances. File share names are used by clients to connect to the shares exported from those instances.

You can create a Filestore instance by using either the [Google Cloud console](https://console.cloud.google.com/filestore) or the [gcloud CLI](https://cloud.google.com/sdk/gcloud/reference/filestore/instances/create).

Filestore offers three performance tiers: Standard, High Performance, and Extreme Performance. The performance tier you choose depends on your workload requirements and the type of file data you are storing.

![](https://miro.medium.com/v2/resize:fit:1400/format:webp/0*j_Jxd20VF-tnLZjL){: .mx-auto.d-block :} *Filestore Tiers.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

#### 3B. Parallelstore

As businesses continue to grapple with the unique storage and access demands of data-intensive AI workloads, they’re looking to the cloud to deliver highly capable, cost-effective, and easily manageable storage solutions. Google Cloud customers training AI models often turn to GPU/TPUs to get the performance they need. But let’s face it: those resources are limited and an infrastructure asset you want to fully utilize.

Google Cloud Parallelstore, now in private Preview, helps you stop wasting precious GPU resources while you wait for storage I/O by providing a high-performing parallel file storage solution for AI/ML and HPC workloads. By keeping your GPUs saturated with the data you need to optimize the AI/ML training phase, Parallelstore can help you significantly reduce — or even eliminate — costs associated with idle GPUs. 

Based on the next-generation Intel DAOS architecture, all compute nodes in a Parallelstore environment have equal access to storage, so VMs can get immediate access to their data. With up to 6.3x read throughput performance compared to competitive Lustre Scratch offerings., Parallelstore is well suited for cloud-based applications that require extremely high performance (IOPS and throughput) and ultra low latency. 

To deploy DAOS on GCP you may choose one of the following deployment paths.

1- [Cloud HPC Toolkit](https://cloud.google.com/hpc-toolkit) is open-source software offered by Google Cloud which makes it easy for you to deploy high performance computing (HPC) environments. It is designed to be highly customizable and extensible, and intends to address the HPC deployment needs of a broad range of use cases.

The [community examples](https://github.com/GoogleCloudPlatform/hpc-toolkit/tree/main/community/examples/intel) in the [Cloud HPC Toolkit](https://cloud.google.com/hpc-toolkit) use the [DAOS modules](terraform/modules/) in this repository.

2- Deploy DAOS with the [DAOS cluster](https://github.com/daos-stack/google-cloud-daos/tree/main/terraform/examples) example demonstrates how to use the [DAOS modules](https://github.com/daos-stack/google-cloud-daos/tree/main/terraform/modules) in a Terraform configuration to deploy a DAOS cluster consisting of servers and clients.

3- As an alternative to viewing the instructions in [Deploy the DAOS Cluster Example](docs/deploy_daos_cluster_example.md) as a standalone document, you can view it as an in-context tutorial in [Cloud Shell](https://cloud.google.com/shell) by clicking the button below.

[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.png)](https://ssh.cloud.google.com/cloudshell/open?cloudshell_git_repo=https://github.com/daos-stack/google-cloud-daos.git&cloudshell_git_branch=main&shellonly=true&cloudshell_tutorial=docs/deploy_daos_cluster_example.md)

#### 3C. NetApp Volumes

In addition, Google Cloud has partenered with NetApp to offer a fully managed, cloud-native data storage service that provides advanced data management capabilities and highly scalable performance, called [Cloud Volumes Service](https://www.netapp.com/us/cloud-marketplace/google-cloud-platform.aspx).

Whether you are looking to migrate existing enterprise and industry-specific apps to Google Cloud, or to build new machine learning (ML) and Kubernetes-based apps that require persistent storage, you can accelerate deployment times while lowering costs by using Cloud Volumes Service.

NetApp Volumes enables data sharing for Windows/Linux applications, making it useful for user and group shares, application shares for unstructured data, SAP shared files, VDI, shared storage for MS-SQL, binaries, log files, config files, user and group shares, shared machine learning data, EDA-shared chip design data, and PACS images.

Moreover, Google Cloud NetApp Volumes enables easy data recovery if a user or application deletes data accidentally, and scheduled snapshots provide convenient, low RPO/RTO recovery points. Users can access snapshots and self-restore data quickly and easily from within the console. For example, NetApp Volumes enables fast ransomware recovery. Easily revert any volume back to a snapshot taken before the ransomware hit. Recovery time of volume is less than one minute versus restoring from backup which can take hours.

![](https://lh3.googleusercontent.com/7GaEyxS3gm6uX3APRqWRNA15AmxITP59odKUGKDOF4MHcbZrkuQ1uMrY-1zvcJwZmnSIyroIGBm7lQ=s2048-w2048-rw-lo){: .mx-auto.d-block :} *Ransomware Attacks Recovery using NetApp.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Once you mount the File Storage instance (Filestore, Parallelstore or NetApp) to a Compute Engine instance or a Kubernetes Engine cluster as a file system. You can then use it like any other file system on your instances.

### 4- Load data into Google Cloud databases
#### 4A. CloudSQL
#### 4B. Cloud Spanner
#### 4C. BigTable
#### 4D. Firestore
#### 4E. Memorystore
### 5- Load data into Google Cloud BigQuery (Data Warehouse)
### 6- Load data into Google Cloud BigLake (Data Lakehouse)

## Summary

## References
* [Product overview of Cloud Storage, Google Cloud Docs](https://cloud.google.com/storage/docs/introduction)
* [About Persistent Disk, Google Cloud Docs](https://cloud.google.com/compute/docs/disks/persistent-disks)
* [Distributed Asynchronous Object Storage (DAOS)](https://docs.daos.io/)
* [Google Cloud Platform (GCP)](https://cloud.google.com/)
* [Google Cloud HPC Toolkit](https://cloud.google.com/hpc-toolkit)
