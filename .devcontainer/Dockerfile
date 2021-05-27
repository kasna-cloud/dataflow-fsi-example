# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.166.0/containers/ubuntu/.devcontainer/base.Dockerfile

# [Choice] Ubuntu version: bionic, focal
ARG VARIANT="focal"
FROM mcr.microsoft.com/vscode/devcontainers/base:0-${VARIANT}

# Install gcloud CLI
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && apt-get update -y && apt-get install google-cloud-sdk -y

# Install java sdk and python
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        openjdk-11-jdk \
        openjdk-11-jre \
        python3.8 \
        python3-pip

# Install beam python libraries
RUN python3.8 -m pip install \
	absl-py==0.12.0 \
	apache-beam[gcp]==2.29.0 \
	google-cloud-pubsub==1.7.0 \
	joblib==0.14.1 \
	pandas==1.2.4 \
	plotly==4.14.3 \
	pytest==6.2.4 \
	numpy==1.19.5 \
	scikit-learn==0.24.2 \
	tfx-bsl==0.29.0 \
	tfx==0.29.0