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
import com.google.dataflow.sample.timeseriesflow.TimeSeriesData.Data.DataPointCase;
import com.google.dataflow.sample.timeseriesflow.TimeSeriesData.TSAccum;
import com.google.dataflow.sample.timeseriesflow.TimeSeriesData.TSAccumSequence;
import java.util.Iterator;
import org.apache.beam.sdk.transforms.DoFn;
import org.json.JSONException;
import org.json.JSONObject;

public class IterableTSAccumSequenceFlattener extends DoFn<Iterable<TSAccumSequence>, String> {
  @ProcessElement
  public void process(
      @Element Iterable<TSAccumSequence> majorKeys, OutputReceiver<String> collector)
      throws JSONException {
    Iterator<TSAccumSequence> majorKeyIterator = majorKeys.iterator();
    while (majorKeyIterator.hasNext()) {
      TSAccumSequence majorKey = majorKeyIterator.next();
      JSONObject flat =
          new JSONObject()
              .put("symbol", majorKey.getKey().getMajorKey())
              .put("endTimestamp", majorKey.getUpperWindowBoundary().getSeconds());

      Iterator<TSAccum> minorKeyIterator = majorKey.getAccumsList().iterator();
      while (minorKeyIterator.hasNext()) {
        TSAccum metricsForMinorKey = minorKeyIterator.next();
        metricsForMinorKey
            .getDataStoreMap()
            .forEach(
                (String metric, Data value) -> {
                  DataPointCase valueType = value.getDataPointCase();
                  try {
                    if (valueType == DataPointCase.FLOAT_VAL) {
                      flat.put(metric, value.getFloatVal());
                    } else if (valueType == DataPointCase.DOUBLE_VAL) {
                      flat.put(metric, value.getDoubleVal());
                    } else if (valueType == DataPointCase.INT_VAL) {
                      flat.put(metric, value.getIntVal());
                    } else if (valueType == DataPointCase.CATEGORICAL_VAL) {
                      flat.put(metric, value.getCategoricalVal());
                    } else if (valueType == DataPointCase.LONG_VAL) {
                      flat.put(metric, value.getLongVal());
                    } else if (valueType == DataPointCase.NUM_AS_STRING) {
                      flat.put(metric, value.getNumAsString());
                    } else if (valueType == DataPointCase.DATAPOINT_NOT_SET) {
                      flat.put(metric, JSONObject.NULL);
                    }
                  } catch (JSONException e) {
                    // TODO: use a proper logger here
                    System.out.print("Error serialising metric '" + metric + "' as JSON: ");
                    System.out.println(e.toString());
                  }
                });
      }
      collector.output(flat.toString());
    }
  }
}
