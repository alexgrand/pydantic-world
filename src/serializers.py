"""This module describes main pydantic serializers."""
from enum import StrEnum
from pydantic import BaseModel, SecretStr, Field, AnyHttpUrl, PlainSerializer, field_serializer

from typing_extensions import Annotated


class DBMS(StrEnum):
    pg = "PostgreSQL"
    mdb = "MariaDB"


class Credentials(BaseModel):
    username: str
    # here we exclude password from both __repr__ and model dump
    # `exclude` takes priority over the exclude/include
    # on model_dump and model_dump_json
    password: SecretStr = Field(repr=False, exclude=True)


class ExposedCredentials(Credentials):
    password: SecretStr = Field(repr=False)

    # serialize concrete field
    @field_serializer("password", when_used="json")
    def parse_password(self, value):
        return value.get_secret_value()


class Connector(BaseModel):
    creds: Credentials | ExposedCredentials
    # add Annotated PlainSerializer
    url: Annotated[AnyHttpUrl, PlainSerializer(lambda x: x.host, return_type=str, when_used="json")] = Field(
        serialization_alias="host"
    )
    dbms: DBMS


class PostgresConnector(Connector):
    creds: ExposedCredentials
    database: str = Field(default="postgres")
    schema_name: str | None = Field(default=None, alias="schema")


if __name__ == "__main__":
    creds = Credentials(username="postgres", password="b3$t_p@$Sw0r9-3v3r")
    pg_connector = Connector(
        creds=creds,
        url="https://my-postgres.com",
        dbms=DBMS.pg,
    )

    print(pg_connector.model_dump())
    # {'creds': {'username': 'postgres'}, 'url': Url('https://my-postgres.com/'), 'dbms': <DBMS.pg: 'PostgreSQL' >}
    print(dict(pg_connector))
    # {'creds': Credentials(username='postgres'), 'url': Url('https://my-postgres.com/'),
    # 'dbms': <DBMS.pg: 'PostgreSQL'>}
    print(pg_connector.model_dump(by_alias=True, mode="json"))
    # {'creds': {'username': 'postgres'}, 'host': 'my-postgres.com', 'dbms': 'PostgreSQL'}
    print("password:", dict(pg_connector)["creds"].password.get_secret_value())
    # password: b3$t_p@$Sw0r9-3v3r
    print("password:", pg_connector.model_dump()["creds"].get("password"))
    # password: None

    # use creds with serializable password
    exposed_creds = ExposedCredentials.model_validate(
        dict(username=creds.username, password=creds.password.get_secret_value())
    )
    exposed_pg_connector = Connector.model_validate(
        dict(**pg_connector.model_dump(exclude={"creds"}), creds=exposed_creds)
    )

    print(exposed_pg_connector)
    # creds=ExposedCredentials(username='postgres') url=Url('https://my-postgres.com/') dbms=<DBMS.pg: 'PostgreSQL'>
    print(exposed_pg_connector.model_dump())
    # {'creds': {'username': 'postgres', 'password': SecretStr('**********')}, 'url': Url('https://my-postgres.com/'),
    # 'dbms': <DBMS.pg: 'PostgreSQL'>}
    print(exposed_pg_connector.model_dump(mode="json", by_alias=True))
    # {'creds': {'username': 'postgres', 'password': 'b3$t_p@$Sw0r9-3v3r'}, 'host': 'my-postgres.com',
    # 'dbms': 'PostgreSQL'}

    full_pg_connector = PostgresConnector.model_validate(
        dict(**pg_connector.model_dump(exclude={"creds"}), creds=exposed_creds)
    )
    # include only creds
    print(full_pg_connector.model_dump_json(include={"creds"}))
    # {"creds":{"username":"postgres","password":"b3$t_p@$Sw0r9-3v3r"}}

    # exclude unset database and schema fields
    print(full_pg_connector.model_dump_json(exclude_unset=True))
    # {"creds":{"username":"postgres","password":"b3$t_p@$Sw0r9-3v3r"},"url":"my-postgres.com","dbms":"PostgreSQL"}

    # exclude only None fields (schema)
    print(full_pg_connector.model_dump_json(exclude_none=True))
    # {"creds":{"username":"postgres","password":"b3$t_p@$Sw0r9-3v3r"},"url":"my-postgres.com","dbms":"PostgreSQL",
    # "database":"postgres"}

    # exclude only password in the inner ExposedCredentials model
    print(full_pg_connector.model_dump_json(exclude={"creds": {"password"}}, by_alias=True))
    # {"creds":{"username":"postgres"},"host":"my-postgres.com","dbms":"PostgreSQL","database":"postgres","schema":null}
