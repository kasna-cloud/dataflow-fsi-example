from absl import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions, GoogleCloudOptions
from googleapiclient import discovery

from src.serialisers.pubsub import PubSubSerialiser
from src.beam_components.window import window_elements
from src.beam_components.inference import run_windowed_inference


def setup_parser(parser):
	parser.add_argument(
		"--input_metrics",
		required=True,
		help=("PubSub to listen to input metrics from. A string in the form of either: "
            "a PubSub topic of the form 'projects/<PROJECT>/topics/<TOPIC>' "
			"or a PubSub subscription of the form 'projects/<PROJECT>/subscriptions/<SUBSCRIPTION>'."
        )
	)
	parser.add_argument(
		"--output_alerts",
		required=True,
		help=("PubSub topic to publish the output alerts to. A string in the form of "
			"'projects/<PROJECT>/topics/<TOPIC>'."
        )
	)
	parser.add_argument(
		'--symbol',
		default="GBPAUD",
		help=("Forex symbol to run ML inference on.")
	)
	parser.add_argument(
		'--window_length',
		required=True,
		type=int,
		help="Length of window to input into model inference."
	),
	parser.add_argument(
		'--bootstrap_model_gs_prefix',
		help="Location of pretrained bootstrap models in gs. Pipeline will only bootstrap a model if this argument is given, an existing model in ai platform does not already exist, and the symbol is GBPAUD"
	)
	parser.add_argument(
		'--timestamp_key',
		default="timestamp",
		help="Key under which timestamp is included in input PubSub metadata, and added to output BigQuery Table.",
	),
	parser.add_argument(
		'--rsi_lower_threshold',
		default=30,
		type=float,
		help="Lower RSI threshold"
	),
	parser.add_argument(
		'--rsi_upper_threshold',
		default=70,
		type=float,
		help="Upper RSI threshold"
	)

def ai_platform_model_exists(project_id: str, model_name: str):
	project_prefix = f"projects/{project_id}"
	full_model_name = f"{project_prefix}/models/{model_name}"
	ml = discovery.build('ml','v1')
	request = ml.projects().models().list(parent=project_prefix)
	response = request.execute()
	if 'models' not in response:
		return False
	existing_model_names = [m['name'] for m in response['models']]
	return full_model_name in existing_model_names

def bootstrap_initial_ai_platform_model(project_id: str, model_name: str, gs_bootstrap_model_dir: str):
	project_prefix = f"projects/{project_id}"
	model_prefix = f"{project_prefix}/models/{model_name}"
	ml = discovery.build('ml','v1')
	model_create_request = ml.projects().models().create(parent=project_prefix, body={
		'name': model_name
	})
	model_create_request.execute()

	version_create_request = ml.projects().models().versions().create(parent=model_prefix, body={
		'name': 'initial_pretrained_bootstrap_model',
		'runtimeVersion': '2.4',
		'framework': "TENSORFLOW",
		'pythonVersion': '3.7', #Is there a reason for using a sepeate python version than defined in the dockerfile etc?
		'deploymentUri': gs_bootstrap_model_dir,
	})
	version_create_request.execute()


def run_pipeline(
	pipeline_options: PipelineOptions,
	input_metrics: str,
	output_alerts: str,
	symbol: str,
	window_length: int,
	bootstrap_model_gs_prefix: str,
	timestamp_key: str,
	rsi_lower_threshold: float,
	rsi_upper_threshold: float,
):
	pipeline_options.view_as(StandardOptions).streaming = True
	gcp_project_id = pipeline_options.view_as(GoogleCloudOptions).project
	pubsub_serialiser = PubSubSerialiser(timestamp_key)
	model_name = f"autoencoder{symbol}"

	feature_metrics = [
		"LOG_RTN",
		"SIMPLE_MOVING_AVERAGE",
		"EXPONENTIAL_MOVING_AVERAGE",
		"STANDARD_DEVIATION",
	]

	# Currently, if the ai platform model does not exist, the beam runtime will try to scale indefinitely
	# to hold all elements instead of erroring cleaning.
	# As a workaround, we check to see if the model exists manually and throw an error before creating
	# the beam pipeline. This will cause the job to fail in GKE and kubernetes will automatically retry
	# the job until the model exists.
	if not ai_platform_model_exists(project_id=gcp_project_id, model_name=model_name):
		logging.warn("Model does yet not exist in Ai platform")
		if bootstrap_model_gs_prefix is not None and symbol == 'GBPAUD':
			# We have a pre-trained model for GBPAUD to speed up initial deployment, so deploy that:
			logging.warn("Deploying initial pretrained bootstrap model")
			bootstrap_initial_ai_platform_model(
				project_id=gcp_project_id,
				model_name=model_name,
				gs_bootstrap_model_dir=f"{bootstrap_model_gs_prefix}/{symbol}"
			)
		else:
			logging.error("Not configured to bootstrap initial model, exiting with error to prompt k8s to retry later. This is expected if you are running with a symbol!=GBPAUD, the training pipeline will need to complete successfully before inference can begin.")
			raise ValueError("Model does not yet exist in Ai Platform - short circuiting.")

	def calc_reconstruction_err(prediction_output):
		error = 0
		
		for inputs, preprocessed, outputs in zip(
			prediction_output['input_features'],
			prediction_output['preprocessed_features'],
			prediction_output['output_features'],
		):  
			error += (sum([(preprocessed[f] - outputs[f]) ** 2 for f in feature_metrics]))
		
		logging.warning({
			**prediction_output,
			'error': error
		})
		return error

	with beam.Pipeline(options=pipeline_options) as pipeline:
		(pipeline
			| "ReadFromPubSub" >> beam.io.ReadFromPubSub(
				topic=input_metrics,
				timestamp_attribute=timestamp_key,
			)
			| "DeserialiseJSON" >> beam.Map(pubsub_serialiser.to_json)
			| "FilterSymbol" >> beam.Filter(lambda m: m['symbol'] == symbol)
			| "FilterRSIThreshold" >> beam.Filter(lambda m: \
				m['RELATIVE_STRENGTH_INDICATOR'] > rsi_upper_threshold or m['RELATIVE_STRENGTH_INDICATOR'] < rsi_lower_threshold)
			| "WindowElements" >> window_elements(window_length)
			| "RunAutoencoder" >> run_windowed_inference(
				gcp_project_id,
				model_name,
				window_length,
				{ f: "FLOAT" for f in feature_metrics },
			)
			| "CalcReconError" >> beam.Map(calc_reconstruction_err)
			| "ToJSON" >> beam.Map(lambda re: { "symbol": symbol, "reconstruction_error": re })
			| "SerialiseJSON" >> beam.Map(pubsub_serialiser.from_json)
			| "WriteToPubSub" >> beam.io.WriteToPubSub(
				topic=output_alerts,
				timestamp_attribute=timestamp_key,
			)
		)
