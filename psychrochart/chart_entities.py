import logging
from uuid import uuid4

from matplotlib.artist import Artist
from pydantic import BaseModel, ConfigDict, Field
from slugify import slugify


def random_internal_value() -> float:
    """Generate random 'internal_value' for unnamed curves."""
    return float(int(f"0x{str(uuid4())[-4:]}", 16))


def make_item_gid(
    kind: str, family_label: str | None = None, name: str | None = None
) -> str:
    """Generate slugified ids for 'Artist' objects in matplotlib plot."""
    unique_gid = f"{kind}_"
    if family_label is not None:
        unique_gid += family_label + "_"
    if name is not None:
        unique_gid += name
    else:
        logging.warning("Unnamed item: %s", unique_gid)
        unique_gid += f"{random_internal_value()}"
    return slugify(unique_gid, separator="_")


def reg_artist(gid: str, artist: Artist, group: dict[str, Artist]):
    """Set GID to plot item and add it to given group."""
    artist.set_gid(gid)
    group[gid] = artist


class ChartRegistry(BaseModel):
    """Artist collection of psychrochart, by kind and unique name."""

    # psychro curves
    saturation: dict[str, Artist] = Field(default_factory=dict)
    constant_dry_temp: dict[str, Artist] = Field(default_factory=dict)
    constant_humidity: dict[str, Artist] = Field(default_factory=dict)
    constant_rh: dict[str, Artist] = Field(default_factory=dict)
    constant_h: dict[str, Artist] = Field(default_factory=dict)
    constant_v: dict[str, Artist] = Field(default_factory=dict)
    constant_wbt: dict[str, Artist] = Field(default_factory=dict)
    # info overlay
    zones: dict[str, Artist] = Field(default_factory=dict)
    annotations: dict[str, Artist] = Field(default_factory=dict)
    # axes artists
    layout: dict[str, Artist] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def render_tree(self) -> str:  # pragma: no cover
        """Helper method to show all IDs in plot."""

        def _section(name):
            return f"* {name}:\n   - " + "\n   - ".join(
                getattr(self, name).keys()
            )

        return "\n".join(
            _section(group)
            for group in self.__fields__
            if getattr(self, group)
        )
