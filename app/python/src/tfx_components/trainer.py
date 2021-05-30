import logging
import os
from typing import List

import absl
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import tensorflow_transform as tft
from tfx.components.trainer.executor import TrainerFnArgs
from tfx_bsl.tfxio import dataset_options


class LSTMAutoencoderModel(keras.Model):
    def __init__(
            self,
            input_features: List[str],
            timesteps: int,
            outer_units: int,
            inner_units: int,
    ):
        super(LSTMAutoencoderModel, self).__init__()
        self.encoded_features = input_features
        self.encoder = self._build_encoder(input_features, timesteps, outer_units, inner_units)
        self.decoder = self._build_decoder(input_features, timesteps, outer_units, inner_units)

    def _build_encoder(self, input_features, timesteps, outer_units, inner_units):
        inputs = [layers.Input(name=f, shape=(timesteps, 1))
                  for f in input_features]
        input_concat = layers.Concatenate()(inputs)
        outer_lstm = layers.LSTM(outer_units, activation='selu',
                                 recurrent_dropout=0.05, return_sequences=True,
                                 kernel_initializer='he_uniform')(input_concat)
        outer_bn = layers.BatchNormalization()(outer_lstm)
        inner_lstm = layers.LSTM(inner_units, activation='selu', return_sequences=False,
                                 kernel_initializer='he_uniform')(outer_bn)
        inner_bn = layers.BatchNormalization()(inner_lstm)
        return keras.Model(name="encoder", inputs=inputs, outputs=inner_bn)

    def _build_decoder(self, input_features, timesteps, outer_units, inner_units):
        _input = layers.Input(shape=(inner_units))
        input_repeated = layers.RepeatVector(timesteps)(_input)
        inner_lstm = layers.LSTM(inner_units, activation='selu', return_sequences=True,
                                 kernel_initializer='he_uniform')(input_repeated)
        inner_bn = layers.BatchNormalization()(inner_lstm)
        outer_lstm = layers.LSTM(outer_units, activation='selu', return_sequences=True,
                                 kernel_initializer='he_uniform')(inner_bn)
        outer_bn = layers.BatchNormalization()(outer_lstm)
        outputs = [
            layers.TimeDistributed(layers.Dense(1), name=f)(outer_bn)
            for f in input_features
        ]
        return keras.Model(name="decoder", inputs=_input, outputs=outputs)

    def call(self, inputs):
        encoded = self.encoder(inputs)
        decoded = self.decoder(encoded)

        truth = tf.stack([inputs[f] for f in self.encoded_features])[:, :, :, None]
        mse = tf.math.reduce_mean(
            tf.math.reduce_sum(
                tf.math.squared_difference(decoded, truth), axis=[0, 2, 3]
            )
        )
        self.add_loss(mse)
        self.add_metric(mse, name="mse")

        return decoded


def build_model(
        input_features: List[str],
        timesteps: int,
        outer_units: int,
        inner_units: int,
) -> keras.Model:
    model = LSTMAutoencoderModel(
        input_features,
        timesteps,
        outer_units,
        inner_units,
    )
    model.compile(
        optimizer=keras.optimizers.Adam()
    )

    model.encoder.summary(print_fn=absl.logging.info)
    model.decoder.summary(print_fn=absl.logging.info)

    model.output_names = input_features

    return model


def run_fn(fn_args: TrainerFnArgs):
    """Train the model based on given args.

    Args:
    fn_args: Holds args used to train the model as name/value pairs.
    """

    # get transform component output
    tf_transform_output = tft.TFTransformOutput(fn_args.transform_output)

    # read input data
    train_dataset = fn_args.data_accessor.tf_dataset_factory(
        fn_args.train_files,
        dataset_options.TensorFlowDatasetOptions(
            batch_size=fn_args.custom_config['batch_size'],
        ),
        tf_transform_output.transformed_metadata.schema,
    )
    eval_dataset = fn_args.data_accessor.tf_dataset_factory(
        fn_args.eval_files,
        dataset_options.TensorFlowDatasetOptions(
            batch_size=fn_args.custom_config['batch_size'],
        ),
        tf_transform_output.transformed_metadata.schema,
    )

    # instantiate model
    model = build_model(
        fn_args.custom_config['input_features'],
        fn_args.custom_config['window_size'],
        fn_args.custom_config['outer_units'],
        fn_args.custom_config['inner_units'],
    )

    # tf callbacks for tensorboard
    tensorboard_callback = tf.keras.callbacks.TensorBoard(
        log_dir=fn_args.model_run_dir,
        update_freq='batch',
    )

    # validation_data = list(eval_dataset.as_numpy_iterator())
    # train model
    model.fit(
        train_dataset,
        # train_dataset.as_numpy_iterator(),
        steps_per_epoch=fn_args.train_steps,
        validation_data=eval_dataset,
        validation_steps=fn_args.eval_steps,
        callbacks=[tensorboard_callback],
    )

    # Build signatures
    model.tft_layer = tf_transform_output.transform_features_layer()

    @tf.function
    def _serve_tf_examples_fn(**input_features):
        # """Returns the output to be used in the serving signature."""
        preprocessed_features = model.tft_layer(input_features)
        autoencoded_features = model(preprocessed_features)

        return {
            **{ f"input_features::{f}":
               input_features[f] for f in input_features.keys() },
            **{ f"preprocessed_features::{f}":
               preprocessed_features[f] for f in preprocessed_features.keys() },
            # Output tensor names are of the form:
            # lstm_autoencoder_model/decoder/{feature_name}/Reshape_1:0
            **{ f"output_features::{f.name.split('/')[2]}":
               f for f in autoencoded_features },
        }

    _input_tf_specs = {
        f: tf.TensorSpec(
            shape=[None, fn_args.custom_config['window_size']], dtype=tf.float32, name=f
        ) for f in fn_args.custom_config['input_features']
    }

    signatures = {
        'serving_default': _serve_tf_examples_fn.get_concrete_function(**_input_tf_specs)
    }

    # Save model (this is the effective output of this function)
    model.save(fn_args.serving_model_dir, save_format='tf', signatures=signatures)
