from pathlib import Path

import pytest
from pydantic import ValidationError

from src.common.config import ProjectConfig, load_project_config


def test_load_project_config_resolves_paths() -> None:
    root = Path(__file__).parents[1]

    config = load_project_config(project_root=root)

    assert isinstance(config, ProjectConfig)
    assert config.project.seed == 42
    assert config.paths.dataset_root == (root.parent / "archive/fashion-dataset").resolve()
    assert config.text.codebook_size == 5000
    assert config.vision.codebook_size == 512


def test_configuration_rejects_unknown_keys() -> None:
    config = load_project_config()
    payload = config.model_dump()
    payload["project"]["unknown"] = True

    with pytest.raises(ValidationError):
        ProjectConfig.model_validate(payload)
