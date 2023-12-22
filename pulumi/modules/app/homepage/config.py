import dataclasses




@dataclasses.dataclass
class HomepageSettings:
    title: str
    startUrl: str = ''
    background: HomepageBackground | None = None