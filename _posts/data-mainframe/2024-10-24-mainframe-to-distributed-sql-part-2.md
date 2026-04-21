---
layout: post
title: "Mainframe to Distributed SQL, Part 2"
subtitle: "The Imperative for Change"
cover-img: /assets/img/cover-mainframe-p2-final.webp
thumbnail-img: /assets/img/cover-mainframe-p2-final.webp
share-img: /assets/img/cover-mainframe-p2-final.webp
tags: [mainframe, CockroachDB, migration, modernization, cloud]
author: "Amine El Kouhen"
author-avatar: "/assets/img/amine_elkouhen.jpg"
comments: true
---

In today's rapidly evolving digital landscape, traditional mainframe database architectures have unique challenges and considerations for organizations that rely on conventional mainframe databases. Mainframe databases, while robust and capable of handling substantial volumes of data and high transaction throughput, face limitations in scaling, integration with modern systems, and cost efficiency.

The fast-changing business demands and tech trends necessitate a shift towards more agile and innovative database solutions. In this article, we'll delve into the urgency of mainframe modernization by exploring:

- the driving forces behind this shift
- the risks of inaction
- the cost considerations associated with maintaining traditional mainframe architectures.

Through a comprehensive analysis, we'll highlight the critical need for organizations to adapt to distributed database solutions like CockroachDB to stay competitive and responsive in the modern digital landscape.

---

## The Need for Change

All the challenges presented previously confirm one obvious truth: the need for change, or in other words, the need for mainframe migration.

All IT migrations, including mainframe ones, turn on three goals: **making money, saving money,** or **mitigating risks**. For instance, the reason behind an organization's decision to undertake a mainframe migration may meet all these criteria:

### Making Money

Historically, many business leaders have been resistant to investing in modernization. After all, these legacy systems were rigid and carried risks for changing mission-critical functions. However, the COVID-19 pandemic drove an urgency to change the status quo — a directive that came from senior IT executives and managers. The pandemic has shown humans' exceptional abilities for innovation and creativity: Significant changes in approaches to global supply chains have occurred in a short time. There has also been an acceleration of digital transformation.

Mainframe environments are often perceived as less agile and innovative than modern IT architectures. Organizations looking to accelerate their pace of innovation and adopt emerging technologies may choose to migrate from mainframes to platforms that offer greater flexibility and scalability. Mainframe systems may face limitations in scaling to meet the growing demands of modern digital businesses. Migrating to cloud-based or distributed systems can provide organizations with the scalability to support dynamic workloads and accommodate future financial growth.

### Saving Money

Mainframe hardware, software, and maintenance costs can be substantial. Organizations may reduce their IT expenditure by migrating from expensive mainframe environments to more cost-effective alternatives, such as cloud-based or commodity hardware solutions.

Economists believe the most significant organizational cost is undoubtedly the opportunity cost. What is opportunity cost? "Opportunity cost" refers to the potential benefits an organization foregoes when choosing one alternative over the best one.

In simpler terms, opportunity cost is what you give up not to choose the best option. For example, if you decide to invest your money in stocks, the opportunity cost could be the potential returns you would have earned if you had invested in bonds instead. Similarly, if you spend your IT budget making a new mainframe application, the opportunity cost could be the value of the cloud-native applications you could have deployed instead if you have made a mainframe migration.

### Mitigating Risks

Mainframe systems may pose risks related to hardware failures, security vulnerabilities, and vendor lock-in. Migrating to alternative platforms reduces technical debt and enables better integration with other systems and services. It can also help organizations mitigate these risks by diversifying their IT infrastructure and reducing reliance on single-vendor solutions.

Furthermore, the main risk to mitigate while dealing with mainframe technologies is the shortage of skilled professionals. Organizations may struggle to recruit and retain qualified mainframe personnel, leading to challenges in maintaining and supporting mainframe systems. Migrating to platforms with broader talent pools and modern skill sets can address this issue.

In addition to these three criteria, many other motivators can push organizations to migrate their legacy mainframe to new technologies.

---

## Risks of Inaction: The Innovator's Dilemma

In their groundbreaking article ["Disruptive Technologies: Catching the Wave"](https://hbr.org/1995/01/disruptive-technologies-catching-the-wave), Joseph L. Bower and Clayton M. Christensen outlined the fundamental reasons why a technology can disrupt an industry. One of their central observations was that even robust companies could be susceptible to disruption.

The authors called this ["the innovator's dilemma"](https://www.hbs.edu/faculty/Pages/item.aspx?num=46). In this scenario, an established company (called an incumbent) typically invests in sustainable innovations for its existing products to sustain revenue and profit growth. However, a startup, unburdened by existing products, has the freedom to take significant risks and pursue revolutionary innovations. If these innovations resonate with customers, the impacts can be devastating for incumbents.

<img src="/assets/img/mainframe-p2-innovators-dilemma.png" alt="The Innovator's Dilemma curve" style="width:100%">
{: .mx-auto.d-block :}
**The Innovator's Dilemma curve**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Today, the innovator's dilemma is a tangible concern for numerous large companies, many of which rely on mainframe systems. There's a prevailing belief that failure to embrace more innovative technologies could lead to the eventual triumph of upstart competitors. This fear of disruption is a significant driver for change within the mainframe industry and underscores the enduring demand for legacy modernization through mainframe migration.

To better understand this fear, Jamie Dimon, CEO of JPMorgan Chase, pointed out in the [2020 shareholder letter](https://reports.jpmorganchase.com/investor-relations/2020/ar-ceo-letters.htm) that disruptive technologies represent one of the biggest threats to his company. Dimon noted, "Banks have other weaknesses, born somewhat out of their success—for example, inflexible 'legacy systems' that need to be moved to the cloud to remain competitive."

He subsequently highlighted the threat posed by new fintech startups that are revolutionizing financial services, mainly through the use of mobile apps: "From loans to payment systems to investing, they have done a great job in developing easy-to-use, intuitive, fast and smart products. We have spoken about this for years, but this competition now is everywhere. Fintech's ability to merge social media, use data smartly, and integrate with other platforms rapidly (often without the disadvantages of being an actual bank) will help these companies win significant market share."

His example will inspire numerous other executives to take proactive measures. It will amplify the urgency for modernizing legacy systems, resulting in a growing demand for disruptive technologies and developers skilled in these arenas.

---

## Shifting Business Demands: The Shift Toward Distributed Database Architectures

The history of programming languages, paradigms, and software architectures has been characterized in the last few decades by a progressive shift toward distribution. Distribution, Modularization, and loose coupling have emerged as transformative trends in modern software development, including mainframe modernization efforts. The idea of microservices and DevOps stems out from this widespread and recognized need.

Monolithic architectures, characterized by large, tightly coupled applications, have traditionally dominated the mainframe landscape. In a monolithic architecture, an entire application is built as a single, interconnected unit, with all components tightly coupled. This architecture can lead to challenges with scalability, maintainability, and deployment flexibility. Additionally, any changes or updates to the application require redeployment of the entire monolith, which can be time-consuming and risky.

On the other hand, microservices architecture decomposes applications into smaller, loosely coupled services, each responsible for a specific business function. These services communicate with each other via well-defined APIs, enabling teams to develop, deploy, and scale them independently. This architecture allows for horizontal scaling of individual services, enabling organizations to handle increased workloads more efficiently. It allows better resource utilization and improved performance, particularly in dynamic or unpredictable environments.

The need for distribution was pushed further to cover every aspect of the application, including data storage. As organizations seek to leverage the flexibility, scalability, and agility offered by microservices architectures, embracing a modern distributed architecture involves transitioning from legacy centralized databases to distributed systems that span multiple servers, data centers, or cloud environments.

Similarly to the application layer, the primary motivation for embracing distributed database architectures is the need for scalability. Traditional mainframe databases may struggle to handle the growing volumes of data and transactional workloads that organizations face in today's digital landscape. Distributing data across multiple nodes allows distributed databases to scale horizontally, accommodating increased demand without sacrificing performance or reliability.

Furthermore, distributed database architectures offer greater flexibility and resilience than centralized mainframe databases. Organizations can achieve fault tolerance and high availability with data distributed across multiple nodes by replicating data and implementing redundant architectures. Thus, it ensures that applications remain accessible and responsive even during hardware failures or network outages.

Distributed databases are also meticulously crafted to help organizations meet stringent regulatory standards while ensuring unparalleled durability and availability. For example, CockroachDB, a modern distributed SQL database, empowers users with control over data residency and isolation. Within the same cluster, you can specify where your data is stored at different kinds of granularity: at the node level, at the database level, at the table level, or even at the row level!

Indeed, one of the unique capabilities of this database is its ability to tie data to a location. First, this allows localizing data for users to a specific location or region, leading to lower latencies and thus creating a better user experience.

Moreover, distributed database architectures like CockroachDB enable organizations to take advantage of cloud computing and hybrid cloud environments. By distributing data across on-premises data centers and cloud platforms, organizations can leverage the scalability and cost-effectiveness of cloud infrastructure while maintaining control over sensitive data and compliance requirements (European GDPR, China Cybersecurity Law, Russia Data Law, etc.).

---

## Shifting Business Demands: The Shift Toward Cloud Computing

The shift towards cloud computing has become a pivotal strategy for mainframe modernization as organizations seek to leverage cloud-native technologies' scalability, resiliency, and cost-effectiveness. Embracing a cloud-native approach involves redesigning and refactoring mainframe applications and workloads to run natively on cloud platforms, such as Amazon Web Services (AWS), Microsoft Azure, or Google Cloud Platform (GCP).

The primary benefit of migrating to the cloud is the shift from capital expenditures (CapEx) to operating expenditures (OpEx). What is CapEx vs OpEx? In this case, instead of investing upfront in hardware, software, and infrastructure (CapEx), organizations pay for cloud services on a subscription or pay-as-you-go basis (OpEx). This allows for more predictable and flexible cost management, as expenses are aligned with usage and can be adjusted based on business needs.

The advantages of cloud computing offer several benefits over traditional mainframe environments. Firstly, cloud computing advantages include enabling organizations to scale resources dynamically based on demand, allowing for more efficient resource utilization and cost savings. Cloud-native applications are inherently resilient and fault-tolerant, with built-in redundancy and failover mechanisms to ensure high availability.

Furthermore, cloud-native technologies facilitate rapid development and deployment cycles, enabling organizations to innovate and iterate more quickly. By leveraging containerization and microservices architecture, mainframe applications can be decomposed into smaller, more manageable components, making them easier to develop, deploy, and maintain.

Migration to the cloud also provides opportunities to modernize legacy mainframe applications by incorporating modern development practices, such as DevOps and continuous integration/continuous deployment (CI/CD). These practices enable automated testing, deployment, and monitoring of applications, resulting in faster time-to-market and improved software quality.

For data storage, there are many "cloud" databases available, but very few of them really deliver the agility and scale required by these modern applications. Some migration initiatives try to use a legacy relational database in the cloud by running it as is, but they can only scale as far as the hardware instance they run on. They were only designed to scale vertically.

<img src="/assets/img/mainframe-p2-cloud-native-scale.png" alt="Cloud-Native Distributed SQL vs legacy databases" style="width:100%">
{: .mx-auto.d-block :}
**Cloud-Native Distributed SQL vs legacy databases**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

Other initiatives try to use NoSQL databases but struggle with ACID transactions at scale. They tried to push NoSQL everywhere, even if the workload didn't fit this technology. Most mainframe workloads are designed to perform online transactional processing (OLTP), so migrating from mainframe traditional databases to NoSQL is neither relevant nor accurate.

Some cloud "augmented" legacy databases have also been created, where only one database layer was redesigned to be distributed. These, too, struggle with consistency and scale.

None of these initiatives were architected for the cloud. That is why, in 2015, three ex-Googlers, Spencer Kimball, Peter Mattis, and Ben Darnell, co-founded Cockroach Labs. The database that their new company created, CockroachDB, was inspired by frustration with the available open-source databases and cloud DBaaS offerings and the lack of capabilities that meet the requirements of today's applications. In addition to enterprise-grade capabilities, CockroachDB emerged to combine the elasticity of the cloud, the consistency of relational databases, and the scaling and resiliency of NoSQL databases.

<img src="/assets/img/mainframe-p2-cockroachdb-venn.png" alt="CockroachDB: Relational, NoSQL, Cloud Native, and Enterprise Ready" style="width:100%">
{: .mx-auto.d-block :}
**CockroachDB: Relational, NoSQL, Cloud Native, and Enterprise Ready**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

---

## Financial Implications

### High Upfront and Ongoing Costs

Maintaining legacy mainframe infrastructure incurs significant financial burdens. The high initial costs of mainframe hardware, expensive software licenses, and continuous maintenance can strain IT budgets. These expenses are often exacerbated by the need for specialized mainframe professionals, whose scarcity drives up salaries and recruitment costs. Additionally, as these professionals retire, organizations face the costly challenge of replacing them, often requiring substantial investments in training and development for new hires.

In contrast, modernizing to distributed database solutions like CockroachDB offers substantial cost benefits. Distributed databases leverage more affordable and scalable hardware, reducing the need for large, upfront investments. Furthermore, CockroachDB and similar solutions are designed to scale horizontally, allowing organizations to add resources incrementally and align costs more closely with actual demand. This flexibility can lead to significant savings, particularly during periods of fluctuating workloads.

### Reduced Overall Costs

Operational costs associated with legacy mainframes can be substantial due to their complexity and the need for continuous, specialized maintenance. Modern distributed databases simplify operations with more intuitive management tools and automated features, reducing the need for extensive manual intervention. This simplicity reduces operational expenses and allows IT teams to focus on more strategic initiatives rather than routine maintenance tasks.

While financial costs are critical, the opportunity cost of maintaining legacy systems can be even more significant. Legacy mainframes often limit an organization's ability to innovate and adapt quickly to changing market demands. This lack of agility can result in missed business opportunities and a slower response to competitive pressures. By contrast, modern distributed databases like CockroachDB support rapid development cycles and seamless integration with cloud-native applications, enabling organizations to innovate more freely and maintain a competitive edge.

<img src="/assets/img/mainframe-p2-real-cost.png" alt="The real cost of mainframe: operating cost plus opportunity cost" style="width:100%">
{: .mx-auto.d-block :}
**The real cost of mainframe: operating cost plus opportunity cost**{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

### Cost of Transition and Integration

It must be acknowledged that transitioning from legacy mainframes to modern distributed databases involves upfront migration costs. These can include data transfer, application re-engineering, and temporary downtime during the transition period. However, the long-term savings and modernizing-gained efficiencies offset these costs. Careful planning and execution of the migration process can further minimize these transitional expenses, ensuring a smoother shift to a more cost-effective and scalable infrastructure.

For instance, the financial benefits of modernizing legacy mainframe databases towards distributed solutions like CockroachDB far outweigh the initial investment. Organizations can achieve lower total cost of ownership (TCO) through reduced hardware and operational costs, enhanced scalability, and improved resource utilization. Moreover, the increased agility and innovation capabilities fostered by modern databases can drive revenue growth and business expansion, providing a substantial return on investment (ROI).

---

## References

1. Joseph L. Bower and Clayton M. Christensen, [Disruptive Technologies: Catching the Wave](https://hbr.org/1995/01/disruptive-technologies-catching-the-wave), Harvard Business Review, 1995.
2. Clayton M. Christensen, [The Innovator's Dilemma: When New Technologies Cause Great Firms to Fail](https://www.hbs.edu/faculty/Pages/item.aspx?num=46), Harvard Business School Press, 1997.
3. Jamie Dimon, [Chairman & CEO letter to shareholders](https://reports.jpmorganchase.com/investor-relations/2020/ar-ceo-letters.htm), JPMorgan Chase Annual Report, 2020.
