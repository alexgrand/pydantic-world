"""This module shows main pydantic Fields and its parameters."""
from pydantic import BaseModel, Field, AliasPath, AliasChoices


# Field aliases
class Artist(BaseModel):
    nick_name: str = Field(alias="NickName")
    genres: set[str] = Field(serialization_alias="MusicCategory")
    albums: set[str] = Field(validation_alias="work")
    first_name: str = Field(validation_alias=AliasPath("birth_name", 1))
    last_name: str = Field(validation_alias=AliasPath("birth_name", 0))
    band: str = Field(validation_alias=AliasChoices("band", "group"))


class Foo(BaseModel):
    positive: int = Field(gt=0, lt=10)
    negative: int = Field(le=-1, ge=-10)
    even: int = Field(multiple_of=2)
    love_for_pydantic: float = Field(allow_inf_nan=True)
    long_str: str = Field(min_length=3)
    short_str: str = Field(max_length=3)


if __name__ == "__main__":
    artist = Artist(
        NickName="Jamala",
        work={"For Every Heart", "All or Nothing"},
        genres={"pop", "electro", "minimal"},
        birth_name=("Jamaladinova", "Susanna"),
        group="Single",
    )

    print(artist)
    """
    Artist(
        nick_name='Jamala'
        genres={'pop', 'electro', 'minimal'}
        albums={'For Every Heart', 'All or Nothing'}
        first_name='Susanna'
        last_name='Jamaladinova'
        band='Single'
    )
    """
    print(artist.model_dump())
    """
    {
        'nick_name': 'Jamala',
        'genres': {'pop', 'electro', 'minimal'},
        'albums': {'All or Nothing', 'For Every Heart'},
        'first_name': 'Susanna',
        'last_name': 'Jamaladinova',
        'band': 'Single'
    }
    """
    print(artist.model_dump(by_alias=True))
    """
    {
        'NickName': 'Jamala',
        'MusicCategory': {'pop', 'electro', 'minimal'},
        'albums': {'All or Nothing', 'For Every Heart'},
        'first_name': 'Susanna',
        'last_name': 'Jamaladinova',
        'band': 'Single'
    }
    """

    foo = Foo(
        positive=1, negative=-1, even=4, love_for_pydantic=float("inf"), long_str="pydantic power", short_str="ok"
    )

    print(foo)
    """
    Foo(
        positive=1
        negative=-1
        even=4
        love_for_pydantic=inf
        long_str='pydantic power'
        short_str='ok'
    )
    """
