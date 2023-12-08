"""This module describes pydantic BaseSettings casual use cases."""
import pathlib
import os
from typing import Any

import yaml
from pydantic.fields import FieldInfo
from typing_extensions import Annotated
from pydantic import BaseModel, HttpUrl, Field, SecretStr, PlainSerializer
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource


class Vault(BaseModel):
    url: HttpUrl
    token: Annotated[SecretStr, PlainSerializer(lambda x: x.get_secret_value(), return_type=str, when_used="json")]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="best_app.",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        env_file=pathlib.Path(__file__).parent.joinpath(".env"),
        secrets_dir=pathlib.Path(__file__).parent.joinpath("secrets"),
    )

    env_name: str = Field(
        default="development",
    )
    vault: Vault

    # common source priority: init, env, dotenv, secret file, default
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return init_settings, env_settings, dotenv_settings, file_secret_settings


class YamlSettingsSource(PydanticBaseSettingsSource):
    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        pass

    def __call__(self):
        yaml_file = pathlib.Path(self.config["yaml_file"] or "")
        if not yaml_file.is_file() or not yaml_file.exists():
            return {}
        with open(yaml_file, "r") as fl:
            return yaml.safe_load(fl)


class NewSettingsConfigDict(SettingsConfigDict):
    yaml_file: pathlib.Path | str


class NewSettings(Settings):
    model_config = NewSettingsConfigDict(yaml_file=pathlib.Path(__file__).parent.joinpath("config.yaml"))

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            YamlSettingsSource(settings_cls),
            env_settings,
            dotenv_settings,
            init_settings,
        )


if __name__ == "__main__":
    # set Settings via init vars
    secret_env_path = Settings.model_config["secrets_dir"].joinpath("best_app.env_name")
    dotenv_file_path = Settings.model_config["env_file"]
    yaml_file_path = NewSettings.model_config["yaml_file"]
    try:
        # create settings via init
        settings = Settings(env_name="test", vault=Vault(url="https://my-vault.com", token="some_token"))
        print(settings.model_dump(mode="json"))
        # {'env_name': 'test', 'vault': {'url': 'https://my-vault.com/', 'token': 'some_token'}}

        # create env_name in secrets file
        with open(secret_env_path, "w") as fl:
            fl.write("secret_env")
        settings = Settings(vault=Vault(url="https://my-vault.com", token="some_token"))
        print(settings.model_dump(mode="json"))
        # {'env_name': 'secret_env', 'vault': {'url': 'https://my-vault.com/', 'token': 'some_token'}}

        # create vault env variables in dotenv file
        with open(dotenv_file_path, "w") as fl:
            fl.write("BEST_APP.VAULT__URL=https://my-secret-vault.com\nBEST_APP.VAULT__TOKEN=super_secret_token")
        settings = Settings()
        print(settings.model_dump(mode="json"))
        # {'env_name': 'secret_env', 'vault': {'url': 'https://my-secret-vault.com/', 'token': 'super_secret_token'}}

        # create env variables
        os.environ.update({"BEST_APP.VAULT__TOKEN": "qa_token", "BEST_APP.ENV_NAME": "qa"})
        settings = Settings()
        print(settings.model_dump(mode="json"))
        # {'env_name': 'qa', 'vault': {'url': 'https://my-secret-vault.com/', 'token': 'qa_token'}}

        # >> Add settings source and change priority << #
        yaml_settings = yaml.safe_dump(data=dict(env_name="stage_env", vault=dict(token="stage_token")))
        with open(yaml_file_path, "w") as fl:
            fl.write(yaml_settings)
        settings = NewSettings(env_name="dummy_env")
        print(settings.model_dump(mode="json"))
        # {'env_name': 'stage_env', 'vault': {'url': 'https://my-secret-vault.com/', 'token': 'stage_token'}}

        # test that env variable has lower priority
        os.environ["BEST_APP.ENV_NAME"] = "PROD"
        settings = NewSettings()
        print(settings.model_dump(mode="json"))
        # {'env_name': 'stage_env', 'vault': {'url': 'https://my-secret-vault.com/', 'token': 'stage_token'}}

    finally:
        # remove files
        secret_env_path.unlink()
        dotenv_file_path.unlink()
        yaml_file_path.unlink()
