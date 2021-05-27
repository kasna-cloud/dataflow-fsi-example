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

import com.google.dataflow.sample.timeseriesflow.TimeSeriesData.TSDataPoint;
import com.google.protobuf.util.Timestamps;
import org.apache.beam.sdk.annotations.Experimental;
import org.apache.beam.sdk.extensions.protobuf.ProtoMessageSchema;
import org.apache.beam.sdk.schemas.Schema;
import org.apache.beam.sdk.transforms.MapElements;
import org.apache.beam.sdk.transforms.PTransform;
import org.apache.beam.sdk.transforms.SerializableFunction;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.values.Row;
import org.apache.beam.sdk.values.TypeDescriptors;

@Experimental
/** Convert {@link TSDataPoint} to {@link Row} */
public class TsDataPointToRow extends PTransform<PCollection<TSDataPoint>, PCollection<Row>> {

  public static final String MAJOR_KEY = "major_key";
  public static final String MINOR_KEY = "minor_key";
  public static final String DATA = "data";
  public static final String TIMESTAMP_MILLISECONDS = "ts_ms";

  @Override
  public PCollection<Row> expand(PCollection<TSDataPoint> input) {

    input
        .getPipeline()
        .getSchemaRegistry()
        .registerSchemaProvider(TSDataPoint.class, new ProtoMessageSchema());

    return input
        .apply(MapElements.into(TypeDescriptors.rows()).via(toRow()))
        .setRowSchema(tsDataPointRowSchema());
  }

  public static SerializableFunction<TSDataPoint, Row> toRow() {

    return new SerializableFunction<TSDataPoint, Row>() {
      @Override
      public Row apply(TSDataPoint input) {
        Row.FieldValueBuilder row =
            Row.withSchema(tsDataPointRowSchema())
                .withFieldValue(MAJOR_KEY, input.getKey().getMajorKey())
                .withFieldValue(MINOR_KEY, input.getKey().getMinorKeyString())
                .withFieldValue(DATA, input.getData().getDoubleVal())
                .withFieldValue(TIMESTAMP_MILLISECONDS, Timestamps.toMillis(input.getTimestamp()));

        return row.build();
      }
    };
  }

  public static Schema tsDataPointRowSchema() {

    return Schema.builder()
        .addStringField(MAJOR_KEY)
        .addStringField(MINOR_KEY)
        .addDoubleField(DATA)
        .addInt64Field(TIMESTAMP_MILLISECONDS)
        .build();
  }
}
