from dataclasses import dataclass


@dataclass
class Beatmap:
    id: int
    artist: str
    title: str
    version: str

    @property
    def url(self):
        return f"https://osu.ppy.sh/b/{self.id}"

    def __str__(self):
        return f"{self.artist} - {self.title} [{self.version}]"
