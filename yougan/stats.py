import typing


class Stats:
    def __init__(self) -> None:
        self.active_players = 0
        self.players = 0

        self.used_memory = 0
        self.free_memory = 0
        self.reservable_memory = 0
        self.allocated_memory = 0

        self.cores = 0
        self.system_load = 0
        self.lavalink_load = 0

        self.uptime = 0

        self.frames_sent = -1
        self.frames_nulled = -1
        self.frames_deficit = -1

    def update(self, payload: typing.Dict[str, typing.Any]) -> None:
        self.active_players = typing.cast(int, payload["playingPlayers"])
        self.players = typing.cast(int, payload["players"])

        memory_data: typing.Dict[str, int] = payload["memory"]
        self.used_memory = memory_data["used"]
        self.free_memory = memory_data["free"]
        self.reservable_memory = memory_data["reservable"]
        self.allocated_memory = memory_data["allocated"]

        cpu_data: typing.Dict[str, int] = payload["cpu"]
        self.cores = cpu_data["cores"]
        self.system_load = cpu_data["systemLoad"]
        self.lavalink_load = cpu_data["lavalinkLoad"]

        self.uptime = payload["uptime"]

        if fs := payload.get("frameStats"):
            self.frames_sent = fs["sent"]
            self.frames_deficit = fs["deficit"]
            self.frames_nulled = fs["nulled"]
