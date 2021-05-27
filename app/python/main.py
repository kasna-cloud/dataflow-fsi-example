import argparse
import sys
from logging import Formatter

from absl import logging
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions

import src.pipelines.pubsub_to_bigquery as ps2bq
import src.pipelines.generator as generator
import src.pipelines.inference as inference
import src.pipelines.training as training


# Setup Logging for GCP Logging
logger = logging.get_absl_handler()
logger.setFormatter(Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		prog='google-timeseries-metrics-example-pipelines',
	)
	subparsers = parser.add_subparsers()

	parser_ps2bq = subparsers.add_parser(
		'pubsub_to_bigquery',
		help=""
	)
	ps2bq.setup_parser(parser_ps2bq)
	parser_ps2bq.set_defaults(func=ps2bq.run_pipeline)

	parser_generator = subparsers.add_parser(
		'generator',
		help=""
	)
	generator.setup_parser(parser_generator)
	parser_generator.set_defaults(func=generator.run_pipeline)

	parser_inference = subparsers.add_parser(
		'inference',
		help=""
	)
	inference.setup_parser(parser_inference)
	parser_inference.set_defaults(func=inference.run_pipeline)

	parser_training = subparsers.add_parser(
		'training',
		help=""
	)
	training.setup_parser(parser_training)
	parser_training.set_defaults(func=training.run_pipeline)


	known_args, pipeline_args = parser.parse_known_args()
	# TODO: test if these options are necessary
	# We use the save_main_session option because one or more DoFn's in this
	# workflow rely on global context (e.g., a module imported at module level).
	pipeline_options = PipelineOptions(pipeline_args)
	pipeline_options.view_as(SetupOptions).save_main_session = True

	run_pipeline = known_args.func
	run_options = vars(known_args)
	del run_options['func']
	run_pipeline(pipeline_options, **run_options)
