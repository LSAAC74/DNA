"""副本配置：20 / 30 / 40 / 65 / 75 级差异化寻路与战斗流程"""


from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import config





@dataclass(frozen=True)

class MapVariant:

    name: str

    template: str

    move_path: list[dict[str, Any]]





@dataclass(frozen=True)

class GoVariant:

    """按「前往」序号区分的副本（如 75 级 9 个副本）"""



    name: str

    move_path: list[dict[str, Any]]

    skill_first: bool = False

    after_skill_wait_sec: float = 0.0

    placeholder: bool = False  # True 表示尚未配置，保留序号





@dataclass(frozen=True)

class AfkRunConfig:

    move_path: list[dict[str, Any]]

    skill_first: bool

    after_skill_wait_sec: float = 0.0

    variant_name: str = ""





@dataclass(frozen=True)

class DungeonProfile:

    level: int

    go_per_page: int

    move_path: list[dict[str, Any]]

    skill_first: bool = False

    after_skill_wait_sec: float = 0.0   # 按 E 后等待技能生效再走位

    map_variants: tuple[MapVariant, ...] = field(default_factory=tuple)

    go_variants: tuple[GoVariant, ...] = field(default_factory=tuple)



    @property

    def uses_map_detect(self) -> bool:

        return len(self.map_variants) > 0



    @property

    def uses_go_variant(self) -> bool:

        return len(self.go_variants) > 0



    @property

    def max_go_index(self) -> int | None:

        if self.uses_go_variant:

            return len(self.go_variants)

        return None



    def get_go_variant(self, go_index: int) -> GoVariant | None:

        if not self.uses_go_variant:

            return None

        if go_index < 1 or go_index > len(self.go_variants):

            return None

        return self.go_variants[go_index - 1]





# 65 级默认走位

_PATH_65 = [

    {"key": "s", "sec": 1.32},

    {"key": "a", "sec": 6.43},

    {"key": "w", "sec": 11.45},

    {"key": "a", "sec": 31.26},

]



_PATH_75_W258 = [{"key": "w", "sec": 2.58}]

_PATH_75_W764 = [{"key": "w", "sec": 7.64}]

_PATH_75_W1574 = [{"key": "w", "sec": 15.74}]

_PATH_75_COMPLEX = [

    {"key": "w", "sec": 7.56},

    {"key": "a", "sec": 2.18},

    {"key": "w", "sec": 7.29},

    {"key": "a", "sec": 1.52},

]



_AFTER_E_75 = 2.0



DUNGEON_PROFILES: dict[int, DungeonProfile] = {

    20: DungeonProfile(

        level=20,

        go_per_page=4,

        move_path=list(_PATH_65),

        skill_first=False,

    ),

    30: DungeonProfile(

        level=30,

        go_per_page=4,

        move_path=list(_PATH_65),

        skill_first=False,

    ),

    40: DungeonProfile(

        level=40,

        go_per_page=5,

        move_path=[],

        skill_first=True,

        after_skill_wait_sec=2.0,

        map_variants=(

            MapVariant(

                "40-1",

                config._asset_path("assets/maps/40-1.png"),

                [

                    {"key": "d", "sec": 1.2},

                    {"key": "w", "sec": 6.69},

                    {"key": "a", "sec": 1.47},

                ],

            ),

            MapVariant(

                "40-2",

                config._asset_path("assets/maps/40-2.png"),

                [],  # 开完技能不移动

            ),

        ),

    ),

    50: DungeonProfile(
        level=50,
        go_per_page=5,
        move_path=[],
        skill_first=False,
        map_variants=(
            MapVariant(
                "50-1",
                config._asset_path("assets/maps/50-1.png"),
                [
                    {"key": "w", "sec": 8.17},
                    {"key": "d", "sec": 1.21},
                    {"key": "w", "sec": 4.6},
                    {"key": "a", "sec": 1.21},
                    {"key": "w", "sec": 15.8},
                ],
            ),
            MapVariant(
                "50-2",
                config._asset_path("assets/maps/50-2.png"),
                [
                    {"key": "w", "sec": 6.62},
                    {"key": "d", "sec": 4.12},
                    {"key": "w", "sec": 1.21},
                    {"key": "d", "sec": 2.33},
                    {"key": "s", "sec": 0.96},
                    {"key": "d", "sec": 4.85},
                    {"key": "w", "sec": 1.42},
                    {"key": "d", "sec": 15.42},
                    {"key": "w", "sec": 1.16},
                ],
            ),
        ),
    ),

    65: DungeonProfile(
        level=65,
        go_per_page=5,
        move_path=list(_PATH_65),
        skill_first=False,
    ),

    75: DungeonProfile(

        level=75,

        go_per_page=5,

        move_path=[],

        go_variants=(

            GoVariant("75-1", [], placeholder=True),

            GoVariant(

                "75-2",

                list(_PATH_75_W258),

                skill_first=True,

                after_skill_wait_sec=_AFTER_E_75,

            ),

            GoVariant(

                "75-3",

                list(_PATH_75_W764),

                skill_first=True,

                after_skill_wait_sec=_AFTER_E_75,

            ),

            GoVariant("75-4", list(_PATH_75_W1574), skill_first=False),

            GoVariant("75-5", list(_PATH_75_COMPLEX), skill_first=False),

            GoVariant(

                "75-6",

                list(_PATH_75_W258),

                skill_first=True,

                after_skill_wait_sec=_AFTER_E_75,

            ),

            GoVariant(

                "75-7",

                list(_PATH_75_W764),

                skill_first=True,

                after_skill_wait_sec=_AFTER_E_75,

            ),

            GoVariant("75-8", list(_PATH_75_W1574), skill_first=False),

            GoVariant("75-9", list(_PATH_75_COMPLEX), skill_first=False),

        ),

    ),

}





def resolve_afk_config(profile: DungeonProfile, go_index: int) -> AfkRunConfig | None:

    """解析战斗挂机参数（地图识别类副本在进图后另行解析走位）"""

    if profile.uses_go_variant:

        variant = profile.get_go_variant(go_index)

        if variant is None:

            return None

        if variant.placeholder:

            return None

        return AfkRunConfig(

            move_path=list(variant.move_path),

            skill_first=variant.skill_first,

            after_skill_wait_sec=variant.after_skill_wait_sec,

            variant_name=variant.name,

        )



    if profile.uses_map_detect:

        return AfkRunConfig(

            move_path=[],

            skill_first=profile.skill_first,

            after_skill_wait_sec=profile.after_skill_wait_sec,

            variant_name="map-detect",

        )



    return AfkRunConfig(

        move_path=list(profile.move_path),

        skill_first=profile.skill_first,

        after_skill_wait_sec=profile.after_skill_wait_sec,

    )





def get_dungeon_profile(level: int) -> DungeonProfile:

    if level in DUNGEON_PROFILES:

        return DUNGEON_PROFILES[level]

    return DungeonProfile(

        level=level,

        go_per_page=5,

        move_path=list(_PATH_65),

        skill_first=False,

    )


