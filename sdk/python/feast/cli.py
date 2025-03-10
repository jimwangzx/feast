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

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import click
import pkg_resources
import yaml
from pytz import utc

from feast.client import Client
from feast.config import Config
from feast.entity import Entity
from feast.feature_store import FeatureStore
from feast.feature_table import FeatureTable
from feast.loaders.yaml import yaml_loader
from feast.repo_config import load_repo_config
from feast.repo_operations import (
    apply_total,
    cli_check_repo,
    init_repo,
    registry_dump,
    teardown,
)

_logger = logging.getLogger(__name__)

_common_options = [
    click.option("--core-url", help="Set Feast core URL to connect to"),
    click.option("--serving-url", help="Set Feast serving URL to connect to"),
    click.option("--job-service-url", help="Set Feast job service URL to connect to"),
]
DATETIME_ISO = "%Y-%m-%dT%H:%M:%s"


def common_options(func):
    """
    Options that are available for most CLI commands
    """
    for option in reversed(_common_options):
        func = option(func)
    return func


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--client-only", "-c", is_flag=True, help="Print only the version of the CLI"
)
@common_options
def version(client_only: bool, **kwargs):
    """
    Displays version and connectivity information
    """

    try:
        feast_versions_dict = {
            "sdk": {"version": str(pkg_resources.get_distribution("feast"))}
        }

        if not client_only:
            feast_client = Client(**kwargs)
            feast_versions_dict.update(feast_client.version())

        print(json.dumps(feast_versions_dict))
    except Exception as e:
        _logger.error("Error initializing backend store")
        _logger.exception(e)
        sys.exit(1)


@cli.group()
def config():
    """
    View and edit Feast properties
    """
    pass


@config.command(name="list")
def config_list():
    """
    List Feast properties for the currently active configuration
    """
    try:
        print(Config())
    except Exception as e:
        _logger.error("Error occurred when reading Feast configuration file")
        _logger.exception(e)
        sys.exit(1)


@config.command(name="set")
@click.argument("prop")
@click.argument("value")
def config_set(prop, value):
    """
    Set a Feast properties for the currently active configuration
    """
    try:
        conf = Config()
        conf.set(option=prop.strip(), value=value.strip())
        conf.save()
    except Exception as e:
        _logger.error("Error in reading config file")
        _logger.exception(e)
        sys.exit(1)


@cli.group(name="entities")
def entity():
    """
    Create and manage entities
    """
    pass


@entity.command("apply")
@click.option(
    "--filename",
    "-f",
    help="Path to an entity configuration file that will be applied",
    type=click.Path(exists=True),
)
@click.option(
    "--project",
    "-p",
    help="Project that entity belongs to",
    type=click.STRING,
    default="default",
)
def entity_create(filename, project):
    """
    Create or update an entity
    """

    entities = [Entity.from_dict(entity_dict) for entity_dict in yaml_loader(filename)]
    feast_client = Client()  # type: Client
    feast_client.apply(entities, project)


@entity.command("describe")
@click.argument("name", type=click.STRING)
@click.option(
    "--project",
    "-p",
    help="Project that entity belongs to",
    type=click.STRING,
    default="default",
)
def entity_describe(name: str, project: str):
    """
    Describe an entity
    """
    feast_client = Client()  # type: Client
    entity = feast_client.get_entity(name=name, project=project)

    if not entity:
        print(f'Entity with name "{name}" could not be found')
        return

    print(
        yaml.dump(
            yaml.safe_load(str(entity)), default_flow_style=False, sort_keys=False
        )
    )


@entity.command(name="list")
@click.option(
    "--project",
    "-p",
    help="Project that entity belongs to",
    type=click.STRING,
    default="",
)
@click.option(
    "--labels",
    "-l",
    help="Labels to filter for entities",
    type=click.STRING,
    default="",
)
def entity_list(project: str, labels: str):
    """
    List all entities
    """
    feast_client = Client()  # type: Client

    labels_dict = _get_labels_dict(labels)

    table = []
    for entity in feast_client.list_entities(project=project, labels=labels_dict):
        table.append([entity.name, entity.description, entity.value_type])

    from tabulate import tabulate

    print(tabulate(table, headers=["NAME", "DESCRIPTION", "TYPE"], tablefmt="plain"))


@cli.group(name="feature-tables")
def feature_table():
    """
    Create and manage feature tables
    """
    pass


def _get_labels_dict(label_str: str) -> Dict[str, str]:
    """
    Converts CLI input labels string to dictionary format if provided string is valid.

    Args:
        label_str: A comma-separated string of key-value pairs

    Returns:
        Dict of key-value label pairs
    """
    labels_dict: Dict[str, str] = {}
    labels_kv = label_str.split(",")
    if label_str == "":
        return labels_dict
    if len(labels_kv) % 2 == 1:
        raise ValueError("Uneven key-value label pairs were entered")
    for k, v in zip(labels_kv[0::2], labels_kv[1::2]):
        labels_dict[k] = v
    return labels_dict


@feature_table.command("apply")
@click.option(
    "--filename",
    "-f",
    help="Path to a feature table configuration file that will be applied",
    type=click.Path(exists=True),
)
def feature_table_create(filename):
    """
    Create or update a feature table
    """

    feature_tables = [
        FeatureTable.from_dict(ft_dict) for ft_dict in yaml_loader(filename)
    ]
    feast_client = Client()  # type: Client
    feast_client.apply(feature_tables)


@feature_table.command("describe")
@click.argument("name", type=click.STRING)
@click.option(
    "--project",
    "-p",
    help="Project that feature table belongs to",
    type=click.STRING,
    default="default",
)
def feature_table_describe(name: str, project: str):
    """
    Describe a feature table
    """
    feast_client = Client()  # type: Client
    ft = feast_client.get_feature_table(name=name, project=project)

    if not ft:
        print(f'Feature table with name "{name}" could not be found')
        return

    print(yaml.dump(yaml.safe_load(str(ft)), default_flow_style=False, sort_keys=False))


@feature_table.command(name="list")
@click.option(
    "--project",
    "-p",
    help="Project that feature table belongs to",
    type=click.STRING,
    default="",
)
@click.option(
    "--labels",
    "-l",
    help="Labels to filter for feature tables",
    type=click.STRING,
    default="",
)
def feature_table_list(project: str, labels: str):
    """
    List all feature tables
    """
    feast_client = Client()  # type: Client

    labels_dict = _get_labels_dict(labels)

    table = []
    for ft in feast_client.list_feature_tables(project=project, labels=labels_dict):
        table.append([ft.name, ft.entities])

    from tabulate import tabulate

    print(tabulate(table, headers=["NAME", "ENTITIES"], tablefmt="plain"))


@cli.group(name="projects")
def project():
    """
    Create and manage projects
    """
    pass


@project.command(name="create")
@click.argument("name", type=click.STRING)
def project_create(name: str):
    """
    Create a project
    """
    feast_client = Client()  # type: Client
    feast_client.create_project(name)


@project.command(name="archive")
@click.argument("name", type=click.STRING)
def project_archive(name: str):
    """
    Archive a project
    """
    feast_client = Client()  # type: Client
    feast_client.archive_project(name)


@project.command(name="list")
def project_list():
    """
    List all projects
    """
    feast_client = Client()  # type: Client

    table = []
    for project in feast_client.list_projects():
        table.append([project])

    from tabulate import tabulate

    print(tabulate(table, headers=["NAME"], tablefmt="plain"))


@cli.command("apply")
@click.argument(
    "repo_path", type=click.Path(dir_okay=True, exists=True), default=Path.cwd
)
def apply_total_command(repo_path: str):
    """
    Applies a feature repo
    """
    cli_check_repo(Path(repo_path))
    repo_config = load_repo_config(Path(repo_path))

    apply_total(repo_config, Path(repo_path).resolve())


@cli.command("teardown")
@click.argument(
    "repo_path", type=click.Path(dir_okay=True, exists=True), default=Path.cwd
)
def teardown_command(repo_path: str):
    """
    Tear down infra for a feature repo
    """
    cli_check_repo(Path(repo_path))
    repo_config = load_repo_config(Path(repo_path))

    teardown(repo_config, Path(repo_path).resolve())


@cli.command("registry-dump")
@click.argument("repo_path", type=click.Path(dir_okay=True, exists=True))
def registry_dump_command(repo_path: str):
    """
    Prints contents of the metadata registry
    """
    repo_config = load_repo_config(Path(repo_path))

    registry_dump(repo_config)


@cli.command("materialize")
@click.argument("start_ts")
@click.argument("end_ts")
@click.argument(
    "repo_path", type=click.Path(dir_okay=True, exists=True,), default=Path.cwd
)
@click.option(
    "--views", "-v", help="Feature views to materialize", multiple=True,
)
def materialize_command(start_ts: str, end_ts: str, repo_path: str, views: List[str]):
    """
    Run a (non-incremental) materialization job to ingest data into the online store. Feast
    will read all data between START_TS and END_TS from the offline store and write it to the
    online store. If you don't specify feature view names using --views, all registred Feature
    Views will be materialized.

    START_TS and END_TS should be in ISO 8601 format, e.g. '2021-07-16T19:20:01'
    """
    store = FeatureStore(repo_path=repo_path)
    store.materialize(
        feature_views=None if not views else views,
        start_date=datetime.fromisoformat(start_ts).replace(tzinfo=utc),
        end_date=datetime.fromisoformat(end_ts).replace(tzinfo=utc),
    )


@cli.command("init")
@click.option("--minimal", "-m", is_flag=True, help="Only generate the config")
def init_command(minimal: bool):
    repo_path = Path.cwd()
    init_repo(repo_path, minimal)


if __name__ == "__main__":
    cli()
