---
layout: post
title: "Mainframe to Distributed SQL, An Introduction"
subtitle: "What is a Mainframe?"
cover-img: assets/img/mainframe-intro-cover.png
thumbnail-img: assets/img/mainframe-distributed-sql-diagram.png
share-img: assets/img/mainframe-intro-cover.png
tags: [mainframe, distributed SQL, CockroachDB, migration, database, enterprise, legacy systems]
comments: true
---

_This article is the latest in "Mainframe to Distributed SQL", an original series from Cockroach Labs exploring the fundamentals of mainframes and the evolution of today's distributed database architecture._

**Related Articles in Series:**
- Understanding Mainframe Database Architecture
- The Imperative for Change
- Distributed Database Architecture
- Planning Your Data Modernization Strategy
- Transitioning to a Distributed Architecture
- Managing Change

---

## The enduring legacy of mainframe systems and their pivotal role in enterprise computing

For over 60 years, the mainframe computer has been the record system for leading businesses, governmental agencies, and learning institutions. Today, this technology has become pervasive worldwide: 92 of the world's top 100 banks, 10 of the world's top insurers, 18 of the top 25 retailers, and 70% of Fortune 500 Companies rely on the mainframe. If you've shopped, planned a vacation, or made a credit card payment, a mainframe almost certainly processed your transaction.

World War II was a significant catalyst for the development of mainframes. The U.S. government saw this technology as a superior way to calculate weapon and logistics ballistics and crack enemy codes. The development of the Harvard Mark I — the first mainframe, then called "The Big Iron" — began in 1939 and was used first to do calculations for the Manhattan Project, the U.S. effort to build the nuclear bomb.

What is a mainframe? The term "mainframe" emerged later in 1964, although its origin remains unclear. The concept drew inspiration from the telecommunications industry, specifically the central system within a telephone exchange. Over time, it evolved to signify large-scale computer systems capable of handling extensive data processing tasks, primarily tailored for business needs and adept at managing large-scale transactions.

In 1991, the American newspaper columnist and political analyst Stewart Alsop predicted that the last mainframe would be unplugged in 1996. At the time, this prediction was not necessarily controversial. IBM, the largest mainframe vendor, fought fiercely against the rising tide of competitors such as Dell, Compaq, and Sun Microsystems. Speculation swirled about the company's potential demise.

In fact, the death of the mainframe was greatly exaggerated.

While there are challenges surrounding the mainframe, such as the increasing churn of seasoned mainframe staff, the "uncool" factor of the underlying technology, or the hefty costs associated with single-line items compared to the more diversified expenditure in distributed systems — nonetheless, for numerous specific use cases and industries, it remains the optimal choice in terms of value for IT investment. Many companies saw this technology as a must-have for being competitive. They would even showcase their mainframes by placing them in glass rooms at the headquarters.

This technology proved quite durable. The mainframe's reliability, consistency, security, and performance have firmly established its position as the backbone of the digital economy. The continued dependence on this platform shows no indication of waning. By 2002, Alsop admitted his previous mistake, recognizing that corporate clients still prioritize centrally managed, highly reliable computing systems — precisely the expertise that IBM provides.

---

## Why has the mainframe lasted so long?

The enduring legacy of mainframe systems stems from the pivotal role they've held in enterprise computing since their inception. Mainframes have been crucial for decades in shaping the digital landscape, driving innovation, and powering mission-critical operations. A big reason why the mainframe has lasted so long is that it would be incredibly expensive to get rid of it! There is a widely accepted misconception that migrating such systems would be risky: organizations are afraid to run out of business because of outages in mission-critical operations.

One key aspect of the mainframe's enduring legacy is its unparalleled reliability and resilience. Mainframes are known for their exceptional reliability. For example, the IBM z16 can reach an uptime of nine nines (99.9999999%) or less than 32 milliseconds of downtime annually. They are built with redundant components to recover from mishaps quickly and sophisticated error-checking mechanisms built into both the hardware and OS, minimizing the risk of system failures and ensuring continuous operation. This reliability is essential for organizations operating in industries where downtime is not an option, such as banking, healthcare, and telecommunications.

Mainframes provide robust security features, including hardware-built-in encryption, access controls, and audit trails, to protect sensitive data and prevent unauthorized access. The last z-series mainframes have achieved Common Criteria Evaluation Assurance Level 5 (EAL5), the highest degree of security.

Furthermore, mainframes are optimized for high-speed processing and transaction throughput. They have hundreds of processors that can efficiently process large volumes of data and execute complex transactions, making them ideal for demanding workloads. They are designed to handle increasing demands, making them suitable for large enterprises and mission-critical applications.

Despite the emergence of new technologies and computing paradigms, mainframes continue to thrive and evolve thanks to their adaptability and compatibility with legacy systems. Mainframes have extensive support for legacy applications and systems, allowing organizations to leverage existing investments and avoid costly migrations. In addition, the most prominent vendors have heavily invested in innovations by adopting open-source software (e.g., Linux, Python…, etc.) and implementing cutting-edge advances in areas like AI, integrations, and DevOps. Many organizations rely on mainframes to run legacy applications and support core business processes, leveraging their investment in these trusted platforms.

Indeed, mainframes are costly. However, despite the initial investment, they have shown that they can offer long-term cost savings, considering the cost per transaction, due to their security, reliability, and performance. They can consolidate multiple servers and workloads, reducing hardware, maintenance, and operational costs.

Energy costs are the second most considerable expense for an IT department after headcounts. Mainframes can also offer lower energy costs because the processing is centralized. The average watt per million instructions per second (MIPS) is about 0.91, and this is declining every year.

---

## Exploring the challenges and limitations of traditional mainframe database architectures in today's digital landscape

In today's rapidly evolving digital landscape, traditional mainframe database architectures face several challenges and limitations that can hinder their effectiveness and adaptability.

![Mainframe to Distributed SQL diagram](../assets/img/mainframe-distributed-sql-diagram.png)

### Scale

While mainframe databases can scale to support large volumes of data and high transaction throughput, scaling may require additional hardware resources and careful planning. Scaling is vertical. It means that you can only scale up to the mainframe limits. If you have unexpected demand peaks, only a planned hardware upgrade may allow your database to handle the workload. Scaling mainframe databases across multiple servers or partitions can introduce complexity and potential performance bottlenecks.

### Data Access & Integrations

Integrating traditional mainframe databases with modern cloud-based and distributed systems can be complex and cumbersome. Legacy protocols, data formats, and compatibility issues may arise, leading to interoperability challenges and data silos within the organization.

Moreover, accessing and extracting data from traditional mainframe databases may pose challenges, especially for users and applications outside the mainframe environment. Limited support for standard APIs, data formats, and modern query languages can hinder data accessibility and interoperability with other systems.

Furthermore, mainframe databases offer very limited Cloud Compatibility. While IBM offers cloud-based versions of DB2, such as IBM Db2 on Cloud, transitioning existing on-premises DB2 deployments to the cloud may require careful planning and migration strategies. Compatibility issues, data transfer costs, and performance considerations may impact the feasibility of moving DB2 workloads to the cloud.

### Cost

Finally, maintaining and upgrading traditional mainframe database architectures can be expensive. The high upfront costs associated with mainframe hardware, software licenses, and ongoing maintenance can strain IT budgets, especially for organizations with limited resources.

In fact, the most considerable IT expense is related mainly to the shortage of mainframe professionals. Many mainframe professionals are approaching retirement age, leading to a loss of institutional knowledge and expertise. As experienced mainframe professionals retire, there is a shortage of skilled individuals to fill their roles.

This shortage is also deepened by the need for formal training programs and educational opportunities focused on mainframe technology. Mainframe technology is often perceived as outdated or unattractive compared to newer technologies such as cloud computing and mobile development. The rapid pace of technological innovation has led to increased competition for IT talent, with many professionals opting to work with newer technologies perceived as more exciting or innovative than mainframes. As a result, individuals have fewer opportunities to acquire the specialized skills and knowledge required to work with mainframe systems.

But, even when organizations can recruit mainframe professionals, retaining them can be challenging. Mainframe professionals may be lured away by higher salaries or more enticing opportunities in other areas of IT.

---

## About this CockroachDB article series, "Mainframe to Distributed SQL"

This post introduces a new blog series about Mainframe Migration, geared towards embracing a modern distributed database architecture on CockroachDB.

In this series, we will explore the strengths and limitations of traditional mainframe databases, recognizing their historical significance while acknowledging the pressing need for change in response to shifting business demands and technological trends. The risks of inaction are obvious, from decreased agility and innovation to potential financial burdens.

Distributed databases like CockroachDB offer scalability, performance, fault tolerance, and resilience, addressing many of the shortcomings of mainframe database systems. Transitioning to a distributed architecture requires careful consideration of migration approaches, tools, best practices, robust change management, and risk mitigation strategies. However, the rewards are substantial, with opportunities for innovation, agility, and competitive advantage awaiting those who embrace the future of distributed databases.

As we look ahead, the call to action is clear: it's time to embrace the future by harnessing the power of CockroachDB as a backbone for modern distributed architectures. By doing so, organizations can position themselves for success in an increasingly dynamic and digital world.

Are you ready to learn more about successfully migrating from mainframe to a cloud-native distributed database? Visit here to speak with an expert.

---

## References

1. [State of Mainframe, BMC Blog](https://www.bmc.com/blogs/state-of-mainframe/)
2. [Harvard Mark I, Wikipedia](https://en.wikipedia.org/wiki/Harvard_Mark_I)
3. [What Became of Mainframes, Computer History Museum (CHM)](https://computerhistory.org/)
4. [IBM z16, TechChannel](https://techchannel.com/)
5. [IBM z-Series Certifications, IBM](https://www.ibm.com/)
6. Tom Taulli, *Modern Mainframe Development*, O'Reilly Media, 2022
