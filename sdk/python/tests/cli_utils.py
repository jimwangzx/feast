import random
import string
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from textwrap import dedent
from typing import List

from feast import cli
from feast.feature_store import FeatureStore


def get_example_repo(example_repo_py) -> str:
    return (Path(__file__).parent / example_repo_py).read_text()


class CliRunner:
    """
    NB. We can't use test runner helper from click here, since it doesn't start a new Python
    interpreter. And we need a new interpreter for each test since we dynamically import
    modules from the feature repo, and it is hard to clean up that state otherwise.
    """

    def run(self, args: List[str], cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, cli.__file__] + args, cwd=cwd)

    @contextmanager
    def local_repo(self, example_repo_py: str):
        """
        Convenience method to set up all the boilerplate for a local feature repo.
        """
        project_id = "test" + "".join(
            random.choice(string.ascii_lowercase + string.digits) for _ in range(10)
        )

        with tempfile.TemporaryDirectory() as repo_dir_name, tempfile.TemporaryDirectory() as data_dir_name:

            repo_path = Path(repo_dir_name)
            data_path = Path(data_dir_name)

            repo_config = repo_path / "feature_store.yaml"

            repo_config.write_text(
                dedent(
                    f"""
            project: {project_id}
            metadata_store: {data_path / "metadata.db"}
            provider: local
            online_store:
                local:
                    path: {data_path / "online_store.db"}
            """
                )
            )

            repo_example = repo_path / "example.py"
            repo_example.write_text(example_repo_py)

            result = self.run(["apply", str(repo_path)], cwd=repo_path)
            assert result.returncode == 0

            yield FeatureStore(repo_path=str(repo_path), config=None)

            result = self.run(["teardown", str(repo_path)], cwd=repo_path)
            assert result.returncode == 0
