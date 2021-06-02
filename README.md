# Dataflow Financial Services Time-Series Example

This project is an example of how to detect anomalies in financial, technical indicators by modeling their expected distribution and thus inform when the Relative Strength Indicator (RSI) is unreliable. RSI is a popular indicator for traders of financial assets, and it can be helpful to understand when it is reliable or not. This example will show how to implement a RSI model using realistic foreign exchange market data, Google Cloud Platform and the Dataflow time-series sample library. 

![Dashboards](docs/Dataflow-FSI-Example-Dashboards.png)

## Table of content

- [Quickstart](#quickstart)
    - [Install](#run-locally)
    - [Cloud Shell](#run-on-cloud-shell)
- [Problem Domain](#problem-domain)
- [Repo Layout](#repo-layout)
- [Components](#components)
- [Deployment](#deployment)
- [License](#license)
- [Links](#links)

The Dataflow samples library is a fast, flexible library for processing time-series data -- particularly for financial market data due to its large volume. Its ability to generate useful metrics in real-time significantly reduces the time and effort to build machine learning models and solve problems in the finance domain. This library is used in the metrics generator component of this example and detailed information on it's usage can be found in [docs](/docs).

The GCP infrastructure used in this example includes Dataflow, Pub/Sub, BigQuery, Kubernetes Engine, and AI Platform. Further information on [components](./docs/COMPONENTS.md), [flows](./docs/FLOWS.md) and [diagrams](./docs/Dataflow-FSI-Example-Real-time.png) can be found in the [docs](./docs/) directory.

## Quickstart

### Run Locally

To install:
1. Create a new project in GCP
1. Install `gcloud` and set PROJECT_ID
1. Execute this script to create base infrastructure. _This will take about 5-10mins_  
`./deploy-infra.sh`
1. After this has completed, deploy the pipelines and model by executing the run-app script. _This will take about 5mins_  
`./run-app.sh`
1. View the grafana dashboard. The username and password is your PROJECT_ID and the location is found in the Cloud Console and output in the build log.

### Run on Cloud Shell

You can also run this example using Cloud Shell. To begin, login to the GCP console and select the “Activate Cloud Shell” icon in the top right of your project dashboard. Then run the following:
1. Clone the repo:  
`git clone https://github.com/kasna-cloud/dataflow-fsi-example.git && cd dataflow-fsi-example`
1. Execute this script to create base infrastructure. _This will take about 5-10mins_  
`./deploy-infra.sh` 
1. After this has completed, deploy the pipelines and model by executing the run-app script. _This will take about 5mins_  
`./run-app.sh`
1. View the grafana dashboard. The username and password is your PROJECT_ID and the location is found in the Cloud Console and output in the build log.

## Problem Domain 

The Relative Strength Index, or RSI, is a popular financial technical indicator that measures the magnitude of recent price changes to evaluate whether an asset is currently overbought or oversold.

To detect when RSI is reliable or not for a given asset, the modelling approach is as follows. We train an anomaly detection model to learn the expected behaviour of metrics describing the asset when RSI is greater than 70 or RSI is less than 30. When an anomaly is detected, the model is informing that these input metrics are behaving differently to how they usually behave when RSI is greater than 70 or RSI is less than 30. And so in these instances, RSI is not reliable and a trade is not advised. If no anomaly is detected, then the metrics are behaving as expected, so you can trust RSI and make a trade. _NOTE_

> _This blog contains general advice only. It was prepared without taking into account your objectives, financial situation, or needs. You should speak to a financial planner before making a financial decision, and you should speak to a licensed ML practitioner before making an ML decision._

More information on the problem domain, data science and model creation are in AI Notebooks which you can run yourself, or view. 
* [Example Data Exploration](./notebooks/example_data_exploration.ipynb)
* [Example TFX Model Training](./notebooks/example_tfx_training_pipeline.ipynb)

## Repo Layout

This repo is organised into folders containing logical functions of the example. A brief description of these are below:

* [app](./app/README.md)
    * [app/bootstrap_models](./app/bootstrap_models) This is the LSTM TFX model pre-populated with the RSI example so that dashboards can immediately render RSI values. During the `run-app.sh` deployment of components, this model will be uploaded into GCS and a new Cloud Machine Learning model version will be created for the `inference` pipeline to use. This model is then updated by the re-training data pipeline.
    * [app/grafana](./app/grafana) Contains visualization configuration used in the grafana dashboards.
    * [app/java](./app/java) This holds the Dataflow pipeline code using the Dataflow samples library. This pipeline creates metrics from the prices stream.
    * [app/kubernetes](./app/kubernetes) Directory of deployment manifests for starting the Dataflow pipelines, prices generator and retraining job.
    * [app/python](./app/python) This is a containerized python program for:
        * inference and retraining pipelines
        * pubsub to bigquery pipeline 
        * forex generator to create realistic prices
* [docs](./docs) This folder contains further example information and diagrams
* [infra](./infra/README.md) Contains the cloudbuild and terraform code to deploy this example GCP infrastructure.
* [notebooks](./notebooks) This folder has detailed AI Notebooks which step through the RSI use case from a Data Science perspective. 

Further information is available in the directory READMEs and the [docs](./docs/) directory.

## Components 

This example can be thought of in two distinct, logical functions. One for real-time ingestion of prices and determination of RSI presence, and another for the re-training of the model to improve prediction.

The logical diagram for the real-time and training in GCP components is below.

![Logical diagram](./docs/Dataflow-FSI-Example-Logical.png)

### Storage Components
* Three PubSub Topics: 
    * prices
    * metrics
    * reconerr
* One BigQuery Dataset with 3 Tables, schema defined in [table_schemas](./infra/table_schemas):
    * prices
    * metrics
    * reconerr
* One AI Platform Model
* One Cloud SQL Database for ML Metadata

### Compute Components
* Autopilot GKE Cluster: 
    * price generator deployment
    * grafana deployment
    * tfx retraining pipeline cron job, and a singleton job to start dataflow streaming pipelines
* Dataflow streaming pipelines:
    * [Metrics Library (Java)](./app/java/TimeSeriesPipeline)
    * [Inference Pipeline (Python)](./app/python/src/pipelines/inference.py)
    * 3x [PubSub-to-BigQuery Pipelines (Python)](./app/python/src/pipelines/pubsub_to_bigquery.py)
* Dataflow batch pipline:
    * [Re-training pipeline](./app/python/src/pipelines/training.py) created dynamically by TFX when the GKE cronjob is run (every hour)

### Deployment
This repo uses java, python, cloudbuild, terraform and other technologies which require configuration. For this example we have chosen to store all configuration values in the [config.sh](./config.sh) file. You can change any values in this file to modfiy the behaviour or deployment of the example.

Deployment of this example is done in two steps:
1. infrastructure into GCP by CloudBuild and terraform
2. application and pipeline deployment using CloudBuild

Both of these CloudBuild steps can be triggered using the `deploy-infra.sh` and `run-app.sh` scripts and require only a [gcloud](https://cloud.google.com/sdk) Google Cloud SDK to be installed locally.

To install this example repo into your Google Cloud project, follow the instructions in the [Quickstart](#quickstart) section.
If needed, this example can be run using GCP Cloud Shell. 

Further information is available in the [app](./app/README.md) and [infra](./infra/README.md) directories.

## License
This code is [licensed](./LICENSE) under the terms of the MIT license and is available for free.

## Links
This repo has been built with the support of Google, [Kasna](http://www.kasna.com.au) and [Eliiza](http://www.eliiza.com.au). Links the relevant doco, libraries and resources are below:

* [Relative Strength Index](https://www.investopedia.com/terms/r/rsi.asp)
* [Dataflow time-series sample library](https://github.com/GoogleCloudPlatform/dataflow-sample-applications/tree/master/timeseries-streaming)
* [Kasna](http://www.kasna.com.au/about)
* [Eliiza](http://www.eliiza.com.au/about)


