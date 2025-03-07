# Copyright 2019 The Feast Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import time
from datetime import timedelta
from tempfile import mkstemp

import pytest
from pytest_lazyfixture import lazy_fixture

from feast.data_format import ParquetFormat
from feast.data_source import FileSource
from feast.entity import Entity
from feast.feature import Feature
from feast.feature_store import FeatureStore
from feast.feature_view import FeatureView
from feast.protos.feast.types import Value_pb2 as ValueProto
from feast.repo_config import LocalOnlineStoreConfig, OnlineStoreConfig, RepoConfig
from feast.value_type import ValueType


class TestFeatureStore:
    @pytest.fixture
    def feature_store_with_local_registry(self):
        fd, registry_path = mkstemp()
        fd, online_store_path = mkstemp()
        return FeatureStore(
            config=RepoConfig(
                metadata_store=registry_path,
                project="default",
                provider="local",
                online_store=OnlineStoreConfig(
                    local=LocalOnlineStoreConfig(path=online_store_path)
                ),
            )
        )

    @pytest.fixture
    def feature_store_with_gcs_registry(self):
        from google.cloud import storage

        storage_client = storage.Client()
        bucket_name = f"feast-registry-test-{int(time.time())}"
        bucket = storage_client.bucket(bucket_name)
        bucket = storage_client.create_bucket(bucket)
        bucket.add_lifecycle_delete_rule(
            age=14
        )  # delete buckets automatically after 14 days
        bucket.patch()
        bucket.blob("metadata.db")

        return FeatureStore(
            config=RepoConfig(
                metadata_store=f"gs://{bucket_name}/metadata.db",
                project="default",
                provider="gcp",
            )
        )

    @pytest.mark.parametrize(
        "test_feature_store", [lazy_fixture("feature_store_with_local_registry")],
    )
    def test_apply_entity_success(self, test_feature_store):

        entity = Entity(
            name="driver_car_id",
            description="Car driver id",
            value_type=ValueType.STRING,
            labels={"team": "matchmaking"},
        )

        # Register Entity with Core
        test_feature_store.apply([entity])

        entities = test_feature_store.list_entities()

        entity = entities[0]
        assert (
            len(entities) == 1
            and entity.name == "driver_car_id"
            and entity.value_type == ValueType(ValueProto.ValueType.STRING)
            and entity.description == "Car driver id"
            and "team" in entity.labels
            and entity.labels["team"] == "matchmaking"
        )

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "test_feature_store", [lazy_fixture("feature_store_with_gcs_registry")],
    )
    def test_apply_entity_integration(self, test_feature_store):

        entity = Entity(
            name="driver_car_id",
            description="Car driver id",
            value_type=ValueType.STRING,
            labels={"team": "matchmaking"},
        )

        # Register Entity with Core
        test_feature_store.apply([entity])

        entities = test_feature_store.list_entities()

        entity = entities[0]
        assert (
            len(entities) == 1
            and entity.name == "driver_car_id"
            and entity.value_type == ValueType(ValueProto.ValueType.STRING)
            and entity.description == "Car driver id"
            and "team" in entity.labels
            and entity.labels["team"] == "matchmaking"
        )

        entity = test_feature_store.get_entity("driver_car_id")
        assert (
            entity.name == "driver_car_id"
            and entity.value_type == ValueType(ValueProto.ValueType.STRING)
            and entity.description == "Car driver id"
            and "team" in entity.labels
            and entity.labels["team"] == "matchmaking"
        )

    @pytest.mark.parametrize(
        "test_feature_store", [lazy_fixture("feature_store_with_local_registry")],
    )
    def test_apply_feature_view_success(self, test_feature_store):

        # Create Feature Views
        batch_source = FileSource(
            file_format=ParquetFormat(),
            file_url="file://feast/*",
            event_timestamp_column="ts_col",
            created_timestamp_column="timestamp",
            date_partition_column="date_partition_col",
        )

        fv1 = FeatureView(
            name="my_feature_view_1",
            features=[
                Feature(name="fs1_my_feature_1", dtype=ValueType.INT64),
                Feature(name="fs1_my_feature_2", dtype=ValueType.STRING),
                Feature(name="fs1_my_feature_3", dtype=ValueType.STRING_LIST),
                Feature(name="fs1_my_feature_4", dtype=ValueType.BYTES_LIST),
            ],
            entities=["fs1_my_entity_1"],
            tags={"team": "matchmaking"},
            input=batch_source,
            ttl=timedelta(minutes=5),
        )

        # Register Feature View
        test_feature_store.apply([fv1])

        feature_views = test_feature_store.list_feature_views()

        # List Feature Views
        assert (
            len(feature_views) == 1
            and feature_views[0].name == "my_feature_view_1"
            and feature_views[0].features[0].name == "fs1_my_feature_1"
            and feature_views[0].features[0].dtype == ValueType.INT64
            and feature_views[0].features[1].name == "fs1_my_feature_2"
            and feature_views[0].features[1].dtype == ValueType.STRING
            and feature_views[0].features[2].name == "fs1_my_feature_3"
            and feature_views[0].features[2].dtype == ValueType.STRING_LIST
            and feature_views[0].features[3].name == "fs1_my_feature_4"
            and feature_views[0].features[3].dtype == ValueType.BYTES_LIST
            and feature_views[0].entities[0] == "fs1_my_entity_1"
        )

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "test_feature_store", [lazy_fixture("feature_store_with_gcs_registry")],
    )
    def test_apply_feature_view_integration(self, test_feature_store):

        # Create Feature Views
        batch_source = FileSource(
            file_format=ParquetFormat(),
            file_url="file://feast/*",
            event_timestamp_column="ts_col",
            created_timestamp_column="timestamp",
            date_partition_column="date_partition_col",
        )

        fv1 = FeatureView(
            name="my_feature_view_1",
            features=[
                Feature(name="fs1_my_feature_1", dtype=ValueType.INT64),
                Feature(name="fs1_my_feature_2", dtype=ValueType.STRING),
                Feature(name="fs1_my_feature_3", dtype=ValueType.STRING_LIST),
                Feature(name="fs1_my_feature_4", dtype=ValueType.BYTES_LIST),
            ],
            entities=["fs1_my_entity_1"],
            tags={"team": "matchmaking"},
            input=batch_source,
            ttl=timedelta(minutes=5),
        )

        # Register Feature View
        test_feature_store.apply([fv1])

        feature_views = test_feature_store.list_feature_views()

        # List Feature Views
        assert (
            len(feature_views) == 1
            and feature_views[0].name == "my_feature_view_1"
            and feature_views[0].features[0].name == "fs1_my_feature_1"
            and feature_views[0].features[0].dtype == ValueType.INT64
            and feature_views[0].features[1].name == "fs1_my_feature_2"
            and feature_views[0].features[1].dtype == ValueType.STRING
            and feature_views[0].features[2].name == "fs1_my_feature_3"
            and feature_views[0].features[2].dtype == ValueType.STRING_LIST
            and feature_views[0].features[3].name == "fs1_my_feature_4"
            and feature_views[0].features[3].dtype == ValueType.BYTES_LIST
            and feature_views[0].entities[0] == "fs1_my_entity_1"
        )

        feature_view = test_feature_store.get_feature_view("my_feature_view_1")
        assert (
            feature_view.name == "my_feature_view_1"
            and feature_view.features[0].name == "fs1_my_feature_1"
            and feature_view.features[0].dtype == ValueType.INT64
            and feature_view.features[1].name == "fs1_my_feature_2"
            and feature_view.features[1].dtype == ValueType.STRING
            and feature_view.features[2].name == "fs1_my_feature_3"
            and feature_view.features[2].dtype == ValueType.STRING_LIST
            and feature_view.features[3].name == "fs1_my_feature_4"
            and feature_view.features[3].dtype == ValueType.BYTES_LIST
            and feature_view.entities[0] == "fs1_my_entity_1"
        )

        test_feature_store.delete_feature_view("my_feature_view_1")
        feature_views = test_feature_store.list_feature_views()
        assert len(feature_views) == 0
