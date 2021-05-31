from typing import Dict, Text, Any, List

import tensorflow_transform as tft


def preprocessing_fn(inputs: Dict[Text, Any], custom_config) -> Dict[Text, Any]:
    """tf.transform's callback function for preprocessing inputs.
    Args:
      inputs: map from feature keys to raw not-yet-transformed features.
      custom_config:
        timesteps: The number of timesteps in the look back window
        features: Which of the features from the TF.Example to use in the model.
    Returns:
      Map from string feature key to transformed feature operations.
    """
    feature_columns = sorted(custom_config["feature_columns"])
    features = {}

    for feature in feature_columns:
        if feature not in inputs.keys():
            raise ValueError(
                f"Input is missing required feature {feature}. Input has: {inputs.keys()}"
            )

        features[f"{feature}"] = tft.scale_to_z_score(inputs[feature])

    return features
