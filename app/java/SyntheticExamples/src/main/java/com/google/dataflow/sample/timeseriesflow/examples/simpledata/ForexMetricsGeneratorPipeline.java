/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.google.dataflow.sample.timeseriesflow.examples.simpledata;

import com.google.dataflow.sample.timeseriesflow.examples.simpledata.transforms.KVMetricsFlattener;
import com.google.dataflow.sample.timeseriesflow.examples.simpledata.transforms.PubsubPriceTickerParser;
import com.google.dataflow.sample.timeseriesflow.metrics.utils.AllMetricsWithDefaults;
import com.google.dataflow.sample.timeseriesflow.transforms.GenerateComputations;
import com.google.dataflow.sample.timeseriesflow.transforms.PerfectRectangles;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.io.gcp.pubsub.PubsubIO;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.ParDo;

public class ForexMetricsGeneratorPipeline {
  public static void main(String[] args) {
    ForexMetricsGeneratorOptions options =
        PipelineOptionsFactory.fromArgs(args).as(ForexMetricsGeneratorOptions.class);

    // Setup options for the Metrics Library
    GenerateComputations metricLibraryComputations =
        GenerateComputations.fromPiplineOptions(options)
            .setType1NumericComputations(AllMetricsWithDefaults.getAllType1Combiners())
            .setType2NumericComputations(AllMetricsWithDefaults.getAllType2Computations())
            .setPerfectRectangles(
                PerfectRectangles.fromPipelineOptions(options).enablePreviousValueFill())
            .build();

    // Our Metrics Generator Pipeline!
    Pipeline p = Pipeline.create(options);
    p.apply(
            "Pull Prices from Pub/Sub",
            PubsubIO.readMessagesWithAttributes()
                .fromTopic(options.getInputPricesTopic())
                .withTimestampAttribute(options.getPubsubTimestampMetadataKey()))
        .apply("Convert to TSDataPoint", ParDo.of(new PubsubPriceTickerParser(options)))
        .apply("Run Timeseries Metrics Library", metricLibraryComputations)
        .apply("Flatten Metrics", ParDo.of(new KVMetricsFlattener()))
        .apply(
            "Publish to Metrics Topic",
            PubsubIO.writeStrings()
                .to(options.getOutputMetricsTopic())
                .withTimestampAttribute(options.getPubsubTimestampMetadataKey()));
    p.run();
  }
}
