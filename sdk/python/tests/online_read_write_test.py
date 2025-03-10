from datetime import datetime, timedelta

from feast.feature_store import FeatureStore
from feast.protos.feast.types.EntityKey_pb2 import EntityKey as EntityKeyProto
from feast.protos.feast.types.Value_pb2 import Value as ValueProto


def basic_rw_test(store: FeatureStore, view_name: str) -> None:
    """
    This is a provider-independent test suite for reading and writing from the online store, to
    be used by provider-specific tests.
    """
    registry = store._get_registry()
    table = registry.get_feature_view(project=store.project, name=view_name)

    provider = store._get_provider()

    entity_key = EntityKeyProto(
        entity_names=["driver"], entity_values=[ValueProto(int64_val=1)]
    )

    def _driver_rw_test(event_ts, created_ts, write, expect_read):
        """ A helper function to write values and read them back """
        write_lat, write_lon = write
        expect_lat, expect_lon = expect_read
        provider.online_write_batch(
            project=store.project,
            table=table,
            data=[
                (
                    entity_key,
                    {
                        "lat": ValueProto(double_val=write_lat),
                        "lon": ValueProto(string_val=write_lon),
                    },
                    event_ts,
                    created_ts,
                )
            ],
            progress=None,
        )

        read_rows = provider.online_read(
            project=store.project, table=table, entity_keys=[entity_key]
        )
        assert len(read_rows) == 1
        _, val = read_rows[0]
        assert val["lon"].string_val == expect_lon
        assert abs(val["lat"].double_val - expect_lat) < 1e-6

    """ 1. Basic test: write value, read it back """

    time_1 = datetime.utcnow()
    _driver_rw_test(
        event_ts=time_1, created_ts=time_1, write=(1.1, "3.1"), expect_read=(1.1, "3.1")
    )

    """ Values with an older event_ts should not overwrite newer ones """
    time_2 = datetime.utcnow()
    _driver_rw_test(
        event_ts=time_1 - timedelta(hours=1),
        created_ts=time_2,
        write=(-1000, "OLD"),
        expect_read=(1.1, "3.1"),
    )

    """ Values with an new event_ts should overwrite older ones """
    time_3 = datetime.utcnow()
    _driver_rw_test(
        event_ts=time_1 + timedelta(hours=1),
        created_ts=time_3,
        write=(1123, "NEWER"),
        expect_read=(1123, "NEWER"),
    )

    """ created_ts is used as a tie breaker, using older created_ts here so no overwrite """
    _driver_rw_test(
        event_ts=time_1 + timedelta(hours=1),
        created_ts=time_3 - timedelta(hours=1),
        write=(54321, "I HAVE AN OLDER created_ts SO I LOSE"),
        expect_read=(1123, "NEWER"),
    )

    """ created_ts is used as a tie breaker, using older created_ts here so no overwrite """
    _driver_rw_test(
        event_ts=time_1 + timedelta(hours=1),
        created_ts=time_3 + timedelta(hours=1),
        write=(96864, "I HAVE A NEWER created_ts SO I WIN"),
        expect_read=(96864, "I HAVE A NEWER created_ts SO I WIN"),
    )
