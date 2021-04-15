# SAAF in Research

This material is made available to enable timely dissemination of scholarly and technical work. Copyright and all rights are retained by authors or by other copyright holders. All persons copying this information are expected to adhere to the terms and constraints invoked by each author's copyright. Generally, these works may not be reposted without explicit permission of the copyright holder.

## **The Serverless Application Analytics Framework: Enabling Design Trade-off Evaluation for Serverless Software**

**Abstract-** To help better understand factors that impact performance on Function-as-a-Service (FaaS) platforms we have developed the Serverless Application Analytics Framework (SAAF). SAAF provides a reusable framework supporting multiple programming languages that developers can integrate into a function’s package for deployment to multiple commercial and open source FaaS platforms. SAAF improves the observability of FaaS function deployments by collecting forty-eight distinct metrics to enable developers to profile CPU and memory utilization, monitor infrastructure state, and observe platform scalability. In this paper, we describe SAAF in detail and introduce supporting tools highlighting important features and how to use them. Our client application, FaaS Runner, provides a tool to orchestrate workloads and automate the process of conducting experiments across FaaS platforms. We provide a case study demonstrating the integration of SAAF into an existing open source image processing pipeline built for AWS Lambda. Using FaaS Runner, we automate experiments and acquire metrics from SAAF to profile each function of the pipeline to evaluate performance implications. Finally, we summarize contributions using our tools to evaluate implications of different programming languages for serverless data processing, and to build performance models to predict runtime for serverless workloads.

### [**PDF**](http://faculty.washington.edu/wlloyd/papers/SAAF-Paper24.pdf) [**Slides**](http://faculty.washington.edu/wlloyd/slides/SAAF-WOSC-slides.pdf)

### **Presentation**

[![SAAF Presentation](http://faculty.washington.edu/wlloyd/images/wosc_saaf_video_splash.png)](https://www.youtube.com/watch?v=oRDkHdapmg4)

Cordingly, R., Yu, H., Hoang, V., Sadeghi, Z., Foster, D., Perez, D., Hatchett, R., Lloyd, W., The Serverless Application Analytics Framework: Enabling Design Trade-off Evaluation for Serverless Software, 2020 21st ACM/IFIP International Middleware Conference: 6th International Workshop on Serverless Computing (WoSC '20), Dec 7-11, 2020, to appear.

## **Predicting Performance and Cost of Serverless Computing Functions with SAAF**

**Abstract-** Next generation software built for the cloud has recently embraced serverless computing platforms that leverage containers and microservices to form resilient, loosely coupled systems that are observable, easy to manage, and extend.  Serverless architectures enable decomposing software into independent components packaged and run using isolated containers or microVMs.  This decomposition approach enables application hosting using very fine-grained cloud infrastructure enabling cost savings as deployments are billed granularly for resource use.  Adoption of serverless platforms promise reduced hosting costs while achieving high availability, fault tolerance, and dynamic elasticity. These benefits are offset by pricing obfuscation, as performance variance from CPU heterogeneity, multitenancy, and provisioning variation obscure the true cost of hosting applications with serverless platforms. Where determining hosting costs for traditional VM-based application deployments simply involves accounting for the number of VMs and their uptime, predicting hosting costs for serverless applications can be far more complex. To address these challenges, in this paper we introduce the Serverless Application Analytics Framework (SAAF) that supports profiling FaaS workload performance, resource utilization, and infrastructure to enable accurate performance predictions.  We apply Linux CPU time accounting principles and multiple regression to estimate FaaS function runtime. We predict runtime for a series of increasingly variant compute bound workloads across heterogeneous CPUs, with different memory settings, and to alternate FaaS platforms evaluating our approach for 77 different scenarios.  We determined the mean absolute percentage error of our runtime predictions for these scenarios was just ~3.49% resulting in an average cost error of $6.46 for 1-million FaaS function workloads averaging $150.45 in price.

### [**PDF**](http://faculty.washington.edu/wlloyd/papers/saaf_cbdcom_camera_ready.pdf) [**Slides**](http://faculty.washington.edu/wlloyd/slides/SAAF_slides-2-Up.pdf)

### **Presentation**

[![SAAF Presentation](https://i.imgur.com/1maEN2x.png)](https://drive.google.com/file/d/1YrcrkpKskCltJLJ8gdEGlH_XbutAUjnW/preview)

Cordingly, R., Shu, W., Lloyd, W., Predicting Performance and Cost of Serverless Computing Functions with SAAF, 2020 6th IEEE International Conference on Cloud and Big Data Computing (CBDCOM 2020), Aug 17-24, 2020.

## **Implications of Programming Language Selection for Serverless Data Processing Pipelines**

**Abstract-** Serverless computing platforms have emerged offering software engineers an option for application hosting without the need to configure servers or manage scaling while guaranteeing high availability and fault tolerance. In the ideal scenario, a developer should be able to create a microservice, deploy it to a serverless platform, and never have to manage or configure anything; a truly serverless platform. The current implementation of serverless computing platforms is known as Function-as-a-Service or FaaS. Adoption of FaaS platforms, however, requires developers to address a major question- what programming language should functions be written in? To investigate this question, we implemented identical multi-function data processing pipelines in Java, Python, Go, and Node.js. Using these pipelines as a case study, we ran experiments tailored to investigate FaaS data processing performance. Specifically, we investigate data processing performance implications: for data payloads of varying size, with cold and warm serverless infrastructure, over scaled workloads, and when varying the available function memory. We found that Node.js had up to 94% slower runtime vs. Java for the same workload. In other scenarios, Java had 20% slower runtime than Go resulting from differences in how the cloud provider orchestrates infrastructure for each language with respect to the serverless freeze/thaw lifecycle. We found that no single language provided the best performance for every stage of a data processing pipeline and the fastest pipeline could be derived by combining a hybrid mix of languages to optimize performance.

### [**PDF**](http://faculty.washington.edu/wlloyd/papers/cbdcom_FaaSProgrammingLanguagePaper_camera_ready.pdf) [**Slides**](http://faculty.washington.edu/wlloyd/slides/Lang-slides-2-Up.pdf)

### **Presentation**

[![Languages Presentation](https://i.imgur.com/yEJKP31.png)](https://drive.google.com/file/d/1C1Vau613ehXrctcRSqxVrAwP2WurEG4w/preview)

Cordingly, R., Yu, H., Hoang, V., Perez, D., Foster, D., Sadeghi, Z., Hatchett, R., Lloyd, W., Implications of Programming Language Selection for Serverless Data Processing Pipelines, 2020 6th IEEE International Conference on Cloud and Big Data Computing (CBDCOM 2020), Aug 17-24, 2020.
