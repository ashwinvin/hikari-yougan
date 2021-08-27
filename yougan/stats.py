import typing


class Stats:
    def __init__(self):
        self.active_players: int = 0
        self.players: int = 0

        self.used_memory: int = 0
        self.free_memory: int = 0
        self.reservable_memory: int = 0
        self.allocated_memory: int = 0

        self.cores: int = 0
        self.system_load: int = 0
        self.lavalink_load: int = 0

        self.uptime: int = 0

        self.frames_sent: int = -1
        self.frames_nulled: int = -1
        self.frames_deficit: int = -1

    def update(self, payload: typing.Mapping[str, int]):
        self.active_players = payload["playingPlayers"]
        self.players = payload["players"]

        self.used_memory = payload["memory"]["used"]
        self.free_memory = payload["memory"]["free"]
        self.reservable_memory = payload["memory"]["reservable"]
        self.allocated_memory = payload["memory"]["allocated"]

        self.cores = payload["cpu"]["cores"]
        self.system_load = payload["cpu"]["systemLoad"]
        self.lavalink_load = payload["cpu"]["lavalinkLoad"]

        self.uptime = payload["uptime"]

        if fs := payload.get("frameStats"):
            self.frames_sent = fs["sent"]
            self.frames_deficit = fs["deficit"]
            self.frames_nulled = fs["nulled"]
