# google-fsi-pattern

This repo is an end-to-end example of FSI 

## Use Case 
The Relative Strength Index, or RSI, is a financial technical indicator that measures the magnitude of recent price changes to evaluate whether an asset is currently overbought or oversold. See https://www.investopedia.com/terms/r/rsi.asp for further details. 

The rule of thumb regarding RSI is:
- When RSI for an asset is less than 30, traders should buy this asset as the price is expected to increase in the near future.
- When RSI for an asset is greater than 70, traders should sell this asset as the price is expected to decrease in the near future.

As this is a rule of thumb, this strategy cannot be trusted to work favorably at all times. Therefore, in these instances (i.e. RSI > 70 or RSI less than 30), it would be useful to know if RSI is a reliable indicator to inform a trade or not.

We propose that, for a given asset, RSI is a reliable indicator when other metrics describing the same asset (e.g. log returns) are behaving as they usually do when RSI > 70 or RSI less than 30. And therefore, RSI is unreliable to inform a trade when these other metrics (describing the same asset) are behaving anomalously.

To detect when RSI is reliable or not for a given asset, the modelling approach is as follows. An anomaly detection model will be trained to learn the expected behaviour of other metrics describing the asset when RSI > 70 or RSI less than 30. When an anomaly is detected (and RSI > 70 or RSI less than 30), the model is informing that these input metrics are behaving differently to how they usually behave when RSI > 70 or RSI less than 30. And so in these instances, RSI is not reliable and a trade is not advised. If no anomaly is detected, then the other metrics are behaving as expected when RSI > 70 or RSI less than 30, so you can trust RSI and make a trade.
 
When predicting Forex market movement there is a tendency for investors to over or under-react to market conditions based on short term fluctuations. Analysing longer term trends in movement is a more rational approach investors can take, however predicting significant upwards and downwards shifts in market movement (market regimes) can be notoriously difficult. Sometimes the market suddenly moves quickly after only a number of days of relative stability and at other times they shift slowly over a number of months with no obvious contributing factors.

Classification and modelling of past market conditions (market regimes) could be used to help predict future market shifts. This will provide FSIs an additional decision support system for their institutional and/or retail investor customers to help inform their market trading and investment decisions which can be applied as part of:
- internal market research
- market research information provided to customers
- near real-time decision support information provided for as part of customer 
- trading applications

## Quick Start
To get running quickly, 
1. Create a new project in GCP
2. Install `gcloud` and `kubectl` and set `PROJECT_ID`
3. Run the `deploy-infra.sh` to create base infrastructure
4. Run the `run-app.sh` to deploy the pipelines and model
5. View the grafana dasbboards

## Components 
### Storage Components
* Three PubSub Topics: prices, metrics, and reconerr
* One BigQuery Dataset with 3 Tables: prices, metrics, and reconerr
* One AI Platform Model
* One Cloud SQL Database for ML Metadata

### Compute Components
* Autopilot GKE Cluster: 
    * price generator deployment
    * grafana deployment
    * tfx retraining pipeline cron job, and a singleton job to start dataflow streaming pipelines
* Dataflow streaming pipelines:
    * Metrics Library (Java) 
    * Inference Pipeline (Python)
    * 3x PubSub-to-BigQuery Pipelines (Python)
* Dataflow batch pipline:
    * Re-training pipeline created dynamically by TFX when the GKE cronjob is run (every hour)

### Visualisation
Grafana is deployed into the GKE cluster and has a default FSI pattern dashboard used to visualise prices, metrics and RSI. Login to the dashboard uses the PROJECT_ID for username and password.
To 

## Grafana

Visualizations for metrics and prices are available in a grafana dashboard which is deployed. This dashboard will be available in your project at the GKE ingress IP for the grafana workloads. To find this IP visit:

# Design Principles
1. Not obsefecating the data within the storage components
2. Hermetic seal
3. Call out to AI Platform

