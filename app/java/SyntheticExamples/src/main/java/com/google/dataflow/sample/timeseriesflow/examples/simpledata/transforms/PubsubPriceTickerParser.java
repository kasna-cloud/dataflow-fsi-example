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
package com.google.dataflow.sample.timeseriesflow.examples.simpledata.transforms;

import com.google.dataflow.sample.timeseriesflow.TimeSeriesData.Data;
import com.google.dataflow.sample.timeseriesflow.TimeSeriesData.TSDataPoint;
import com.google.dataflow.sample.timeseriesflow.TimeSeriesData.TSKey;
import com.google.protobuf.util.Timestamps;
import java.nio.charset.StandardCharsets;
import org.apache.beam.sdk.io.gcp.pubsub.PubsubMessage;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.DoFn.Timestamp;
import org.joda.time.Instant;
import org.json.JSONException;
import org.json.JSONObject;

public class PubsubPriceTickerParser extends DoFn<PubsubMessage, TSDataPoint> {
  private String priceSymbolKey;
  private String priceValueKey;
  private String secondaryKeyConstant;

  public PubsubPriceTickerParser(PubsubPriceTickerParserOptions options) {
    this.priceSymbolKey = options.getPriceSymbolKey();
    this.priceValueKey = options.getPriceValueKey();
    this.secondaryKeyConstant = options.getSecondaryKeyConstant();
  }

  @ProcessElement
  public void process(
      @Element PubsubMessage msg,
      @Timestamp Instant msgTimestamp,
      OutputReceiver<TSDataPoint> collector)
      throws JSONException {

    String stringPayload = new String(msg.getPayload(), StandardCharsets.UTF_8);
    JSONObject jsonPayload = new JSONObject(stringPayload);

    TSKey priceTickKey =
        TSKey.newBuilder()
            .setMajorKey(jsonPayload.getString(this.priceSymbolKey))
            .setMinorKeyString(this.secondaryKeyConstant)
            .build();
    Data priceValue =
        Data.newBuilder().setDoubleVal(jsonPayload.getDouble(this.priceValueKey)).build();
    TSDataPoint priceTick =
        TSDataPoint.newBuilder()
            .setKey(priceTickKey)
            .setData(priceValue)
            .setTimestamp(Timestamps.fromMillis(msgTimestamp.getMillis()))
            .build();
    collector.output(priceTick);
  }
}
