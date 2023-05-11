---
layout: post
title: Data & Redis series - part 6
subtitle:  Fraud Detection with Redis Enterprise
thumbnail-img: assets/img/fraud.png
share-img: https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgpIJykWzMHqXcycHvB369LO09zNLoe8_sIRrpXMkdPSHM2R0jUFIVMfhhmRlLZ3tjhPmwhtbRNiq3i2apf8Ok55LweD7nySq-mMXwc9R_swbkLmyoGMofvBqilIkb91HKGO5aYjx5ouuo_GurEw78SvSgE6fDNxjVv0TMzySUhaz9f7XY7pd4QKDiv
tags: [AWS,AWS Kinesis,AWS Lambda,false positive,fraud detection,Grafana,latency,Random Cut Forest,Redis,Redis Gears,RedisBloom,RediSearch,RedisJSON,RedisTimeSeries,SageMaker,Serverless Functions,xGBoost]
comments: true
---

In the rest of this series, I will highlight a set of use cases in which using Redis brings a real advantage. In this article, I'll present how Redis Enterprise can help to implement a real-time fraud detection system. 

For any given transaction, this system must decide whether it's fraudulent or not and act accordingly within seconds. Failing to address fraud definitively leads to significant losses, harms organizations' brand image, tarnishes their reputation and inevitably repels customers. 

Unfortunately, fraudsters are evolving fast and are moving in tandem with digital banking transformations, discovering innovative ways to steal or fake customers’ identities and commit fraud. As a result, traditional rules-based fraud detection systems are no longer effective. A significant challenge is to minimize false positives and accurately identify fraud in real time. 

In the following sections, I'll introduce the main challenges of fraud detection and how Redis Enterprise can help to address some of them.

## Fraud Detection Challenges

Fraud detection systems face several challenges that make it difficult to accurately identify fraudulent activities. Some of these challenges are:

*   Evolving Fraud Techniques: Fraudsters continually adapt and develop new techniques to evade detection. As a result, fraud detection systems need to be **_updated regularly_** to keep up with these evolving techniques.
*   Data Quality: The accuracy of fraud detection systems depends on their data quality. If the data is incomplete, incorrect, or inconsistent, it can lead to false positives or false negatives, reducing the effectiveness of the system.
*   Balancing Fraud Detection and User Experience: While fraud detection systems aim to minimize fraud, they must also maintain a good user experience. Overly strict fraud detection rules can result in **_false positives_**, leading to unhappy customers.
*   Cost: Implementing and maintaining a fraud detection system can be expensive. The cost includes acquiring and processing large amounts of data, developing and maintaining the algorithms and models, and hiring personnel to manage the system.
*   Privacy Concerns: Fraud detection systems require access to sensitive customer data, which can raise privacy concerns. Companies must ensure that their fraud detection systems comply with privacy regulations and implement proper security measures to safeguard the data.

In this piece, among the challenges above, we'll focus on the two main ones - false positives and latency. Both yield unhappy customers and substantial losses to sellers. 

### 1 - False Positives

When a legitimate transaction by the user is flagged as fraud by the system, it is known as a **_false positive_**. This situation is highly frustrating for the customer and can prove to be quite costly for the seller. To address this challenge, a multi-layer approach is required to improve detection and continuously learn from evolving fraud patterns. 

The multi-layer approach is a technique used in fraud detection systems to improve the accuracy and effectiveness of fraud detection. It involves using multiple layers of fraud detection methods and techniques to detect fraudulent activity. The multi-layer approach typically includes three layers:

*   **Rule-Based Layer**: The first layer is a rule-based system that uses predefined rules to identify potential fraudulent activity. These rules are based on historical fraud data and are designed to detect known fraud patterns. Some examples of these rules:
      - Blacklisting fraudsters’ IP addresses
      - Deriving and utilizing the latitude and longitude data from users’ IP addresses
      - Utilizing the data on browser type and version, as well as operating system, active plugins, timezone, and language
      - Per user purchase profile: Has this user purchased in these categories before?
      - General purchase profiles: Has this type of user purchased in these categories before?

      The rules can be implemented so that it can start from a "low cost" to "high cost". If a user makes a purchase within already made categories and within min/max amounts, the app can tag the transaction as non-fraudulent and eliminate the cycles to be spent on further rules and the ML layer. 

*   **Anomaly Detection Layer**: The second layer is an anomaly detection system that identifies unusual activity based on statistical analyses of transactional data. This layer uses machine learning algorithms such as **Random Cut Forest** to identify patterns that are not typically seen in legitimate transactions.
*   **Predictive Modeling Layer**: The third layer is a predictive modeling system that uses advanced machine learning algorithms, such as **XGBoost,** to predict the likelihood of fraud. This layer uses historical data to train the models and can detect new fraud patterns that are not detected by the previous layers.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgyJspSmD9ZcUrunyldMrQMyZEFrMDCzSuLMRscQeYli8T-lTrA8s3-LRI7-Y-WJi9m38C3CkkiYRrivybIr4YMgfSZX27v2z-T_Lz92FRbq12mujYz58S3oNJF7dGeT82wM4mfF4gjLMBA6LDCcRX0lcRGNM3IKF7jfA6_s3lMUmb3kbI3soUc2pya){: .mx-auto.d-block :} *Multi-Layered Fraud Detection.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

By using a multi-layer approach, fraud detection systems can minimize false positives and false negatives, improving fraud detection accuracy. The multi-layer approach also helps to detect fraud in real time, enabling prompt action to prevent losses.

### 2 - Latency

As mentioned in the challenges above, fraudsters are evolving and becoming more complex. Therefore, the detection should not fall behind, and enhanced detection should not increase latency. If companies cannot detect whether the transaction is fraudulent or not within a few seconds, by default, it’s considered genuine. This is why latency is a significant challenge in fraud detection. 

To address this issue, organizations can leverage online feature stores to retain and manages the features used by machine learning models in an online or real-time environment. 

Features are the variables or attributes that are used by machine learning models to make predictions or classifications. Examples of features include customer demographics, purchase history, website activity, and product preferences. An online feature store stores these features in a centralized location and provides them to machine learning models in real time. 

The online feature store is designed to solve the challenge of managing and deploying machine learning models in real time. By providing a centralized repository, fraud detection systems can quickly access and reuse features for different models without re-engineering or reprocessing them. This improves the efficiency and reduces the latency of detecting fraud. 

The online feature store can also improve the accuracy of machine learning models by providing real-time feature updates. As new data is collected, the feature store can update the features used by the machine learning models, resulting in more accurate fraud predictions.

## Fraud Detection System using Redis Enterprise & AWS SageMaker

Redis Enterprise has two functions in a Fraud detection solution. First, it’s used as a multi-model primary database that stores and indexes the JSON documents (representing transactions) and as an online feature store operated by a machine learning platform such as AWS SageMaker. A single Redis cluster can serve both of these functions. It doesn’t have to be separate clusters. 

AWS Lambda functions consume the messages from Kinesis (end-user transactions), apply the rules, and sink them into Redis databases. Redis Enterprise can also persist data directly into an S3 bucket via periodic backups. In an ML pipeline, this data is the input to train and improve the models running on SageMaker. 

Remember the two main fraud detection challenges presented above. Redis can address both from different perspectives:

1.  First, by applying the predefined rules to identify potential fraudulent activity (rule-based layer) - using RedisBloom/Cuckoo Filters, you can efficiently implement the blacklisting of the IP addresses. Then, with Redis geospatial native operations like `GEOSEARCH`, `GEORADIUS`, and `GEOPOS`, you can calculate latitude and longitude data from users' IP addresses. In addition, Redis can store and index JSON via its RedisJSON and RediSearch modules. This, along with the other Redis data types, enables the app to implement user and purchase profiling logic.
2.  The machine learning engine needs to quickly read the latest feature values from the online feature store and use them at inference time. Then, based on the real-time features, the ML model will score the transaction. Because of its ultra-low latency, Redis Enterprise is a great fit for online and real-time access to the feature data as part of an online feature store solution/implementation.
3.  Finally, time-series data can be stored in Redis via the RedisTimeSeries module. This is important if you want to implement a real-time dashboard. 

Below depicts the solution architecture implemented with Redis Enterprise and AWS and its data flow details.

![](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgpIJykWzMHqXcycHvB369LO09zNLoe8_sIRrpXMkdPSHM2R0jUFIVMfhhmRlLZ3tjhPmwhtbRNiq3i2apf8Ok55LweD7nySq-mMXwc9R_swbkLmyoGMofvBqilIkb91HKGO5aYjx5ouuo_GurEw78SvSgE6fDNxjVv0TMzySUhaz9f7XY7pd4QKDiv){: .mx-auto.d-block :} *Fraud Detection System with Redis Enterprise and AWS.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

A. As a pre-requisite, you need to put historical datasets of credit card transactions into an Amazon Simple Storage Service (Amazon S3) bucket. These data serve to train and test the machine learning algorithms that detect fraud and anomalies.

B. An Amazon SageMaker notebook instance with different ML models will train on the historical datasets. Amazon SageMaker is a machine learning (ML) workflow service for developing, training, and deploying models. It comes with many predefined algorithms. You can also create your own algorithms by supplying Docker images, a training image to train your model, and an inference model to deploy to a REST endpoint. In our solution, we have chosen Random Cut Forest algorithm for anomaly detection and XGBoost for Fraud prediction:

*   **Random Cut Forest** (RCF) is an unsupervised algorithm that detects anomalous data points in a dataset. Anomalies are data observations that deviate from the expected pattern or structure. They can appear as unexpected spikes in time series data, interruptions in periodicity, or unclassifiable data points. These anomalies are often easily distinguishable from the regular data when viewed in a plot.  
      
    RCF assigns an anomaly score to each data point. Low scores indicate that the data point is normal, while high scores indicate the presence of an anomaly. The threshold for what is considered "low" or "high" depends on the application, but typically scores beyond three standard deviations from the mean are considered anomalous.  
  
*   **xGBoost**, short for eXtreme Gradient Boosting, is a widely used open-source implementation of the gradient-boosted trees algorithm. Gradient boosting is a supervised learning method that aims to predict a target variable by combining estimates from an ensemble of simpler and weaker models. The XGBoost algorithm is highly effective in machine learning competitions due to its ability to handle various data types, distributions, and relationships, as well as the wide range of hyper-parameters that can be fine-tuned.

1\. The data flow starts with end users (mobile and web clients) invoking Amazon API Gateway REST API for predictions using signed HTTP requests.

2\. Amazon Kinesis Data Streams are used to capture real-time event data. Amazon Kinesis is a fully managed service for stream data processing at any scale. It provides a serverless platform that easily collects, processes, and analyzes data in real time so you can get timely insights and react quickly to new information. Kinesis can handle any amount of streaming data and process data from hundreds of thousands of sources with low latencies.

3\. AWS Lambda is a serverless, event-driven compute service that lets you run code for virtually any type of application or backend service without provisioning or managing servers. You can trigger Lambda from over 200 AWS services and Software as a Service (SaaS) applications and only pay for what you use. In our solution, the Lambda function is triggered by kinesis to read the stream and perform the following actions:

4\. Persist transactional data RedisJSON to enable low-latency indexing and querying of transactions.

{% highlight python linenos %}
def persistTransactionalData(payload_dict):
    print("** persistTransactionalData - START")
    now = datetime.datetime.now() # current date and time
    trans_date_trans_time = now.strftime("%Y/%m/%d-%H:%M:%S")
    key = "fraud:" + trans_date_trans_time

    redis_client.json().set(key, Path.root_path(), payload_dict)
    result = redis_client.json().get(key)
    print(result)
    print("** persistTransactionalData - END")
{% endhighlight %}

5\. The first layer in the fraud detection multi-layer approach is a rule-based system that uses predefined rules to identify potential fraudulent activity. The rules can be implemented so that it can start from a "low cost" to "high cost". For example, using RedisBloom/Cuckoo Filters, you can efficiently implement the blacklisting of the IP addresses. Then, with Redis geospatial native operations like `GEOSEARCH`, `GEORADIUS`, and `GEOPOS`, you can identify latitude and longitude data from users' IP addresses and compare it with the user's address in the records. Thus, you can apply preliminary anomaly detection without using ML inference.

5b. When a rule-based anomaly is identified, you can use Redis Gears to trigger further actions.

5c. You can implement a Gears function that notifies the end user and requests validation for the transaction.

6\. To avoid false positives and false negatives, the Lambda function calls the SageMaker models endpoints to assign anomaly scores and classification scores to incoming transactions.

{% highlight python linenos %}
def makeInferences(data_payload):
    print("** makeInferences - START")
    output = {}
    output["anomaly_detector"] = get_anomaly_prediction(data_payload)
    output["fraud_classifier"] = get_fraud_prediction(data_payload)
    print(output)
    print("** makeInferences - END")
    return output
{% endhighlight %}

\- Anomalie detection:  


{% highlight python linenos %}
def get_anomaly_prediction(data):
    sagemaker_endpoint_name = 'random-cut-forest-endpoint'
    sagemaker_runtime = boto3.client('sagemaker-runtime')
    response = sagemaker_runtime.invoke_endpoint(EndpointName=sagemaker_endpoint_name, ContentType='text/csv', Body=data)
    print("response from get_anomaly_prediction=")
    print(response)
    # Extract anomaly score from the endpoint response
    anomaly_score = json.loads(response['Body'].read().decode())["scores"][0]["score"]
    print("anomaly score: {}".format(anomaly_score))
    return {"score": anomaly_score}
    
{% endhighlight %}

\-Fraud Prediction:

{% highlight python linenos %}
def get_fraud_prediction(data, threshold=0.5):
    sagemaker_endpoint_name = 'fraud-detection-endpoint'
    sagemaker_runtime = boto3.client('sagemaker-runtime')
    response = sagemaker_runtime.invoke_endpoint(EndpointName=sagemaker_endpoint_name, ContentType='text/csv', Body=data)
    print("response from get_fraud_prediction=")
    print(response)
    pred_proba = json.loads(response['Body'].read().decode())
    print(pred_proba)
    prediction = 0 if pred_proba < threshold else 1
    # Note: XGBoost returns a float as a prediction, a linear learner would require different handling.
    print("classification pred_proba: {}, prediction: {}".format(pred_proba, prediction))

    return {"pred_proba": pred_proba, "prediction": prediction}
{% endhighlight %}

7\. AWS Lambda function also leverages Redis Enterprise Cloud as a low-latency (Online) feature store.

8\. AWS Lambda function further persists the prediction results to Redis Enterprise. Optionally, the results, along with transactional details, can also be stored in a time-series database for further data visualizations using Grafana.

{% highlight python linenos %}
def persistMLScores(output):
    print("** persistMLScores - START")
    print(output)

    fraud_score = round(random.uniform(0.1, 1.0), 10)
    print ("**** fraud_score = %2.2f" % (fraud_score))

    key = 'fraud-ts'
    now = datetime.datetime.now() # current date and time
    timestamp = int(round(now.timestamp()))
    print(timestamp)

    redis_client.ts().add(key,timestamp,fraud_score,duplicate_policy='last')
    if (fraud_score >= 0.7 ):
        redis_client.ts().add("fraudulent_ts","*",fraud_score,duplicate_policy='last', labels={'type': "fraud_score"})
        print("*** adding to fraudulent series with current timestamp")
    else:
        redis_client.ts().add("non-fraudulent_ts","*",fraud_score,duplicate_policy='last', labels={'type': "fraud_score"})
        print("*** adding to non-fraudulent series with current timestamp")

    print("** persistMLScores - END")
{% endhighlight %}

Below is the Grafana dashboard that shows real-time fraud scores for incoming transactions. For any given transaction, if the score exceeds 0.8, it is considered fraudulent and shown in red. In addition, other charts are used to visualize fraud activity over time or to compare fraudulent vs. non-fraudulent (bottom side).

![](https://lh6.googleusercontent.com/cpabKTP9YhhdOnt22k7vGbX5uyY8PhmmgtwiAR3fEhuY6Cly33Fyif1BeYijOG_OGv8h7sfan0jsJV3xWk4ioy2BCJthWM_meaLWmm3lKbVp7YFa9DuT_DKlNwm--FqSrm8DuCiPOc5nhywxpBuuwz3mGA){: .mx-auto.d-block :} *Real-Time Fraud Monitoring using Grafana.*{:style="display:block; margin-left:auto; margin-right:auto; text-align: center"}

The source code of this Fraud Detection solution is available in the following [Github Repository](https://github.com/Redislabs-Solution-Architects/aws-fraud-detection).

## Summary

The incidence of fraud has reached record levels. The [PwC study](https://www.pwc.com/gx/en/services/forensics/economic-crime-survey.html) revealed that fraud caused losses of $42B in 2020, a figure that continues to rise as transaction volumes increase. However, ensuring an optimal user experience is crucial and should never be compromised in the fight against fraud. 

Companies require real-time data and more accurate detection mechanisms to combat this issue without incurring additional implementation costs and latency. Redis Enterprise is an in-memory database that offers a real-time, cost-effective, and low-latency solution, tightly integrated with AWS services. Here is a brief overview of Redis Enterprise and how it can help combat fraud:

*   Managed as a service via the AWS Marketplace, Redis Enterprise enables seamless scaling up and down without any degradation in performance.
*   High-speed statistical analysis features such as Bloom filters, time series, and other data structures in Redis Enterprise allow efficient transaction checks against known patterns, reducing costs and minimizing the need for extensive forensic analysis.
*   At inference time, the solution supports quick retrieval of the latest feature values from the online feature store, enabling the ML engine, such as SageMaker, to function efficiently.

With high throughput and low latency services from Redis and AWS, the solution meets the strict performance requirements of the financial services sector.

References
----------

*   [Redis Enterprise and AWS Fraud Detection](https://redis.com/wp-content/uploads/2022/05/Redis-Enterprise-and-AWS-Fraud-Detection-Solution-Overview.pdf): Solution Overview.
*   [PwC’s Global Economic Crime and Fraud Survey 2022](https://www.pwc.com/gx/en/services/forensics/economic-crime-survey.html), PwC Surveys.
