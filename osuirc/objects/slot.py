from typing import Dict, List

from osuirc.objects.osuenums import TeamType, Mods


class Slot(object):
    def __init__(
        self, 
        username: str, 
        user_id: int = None, 
        status: str = "Not Ready", 
        is_host: bool = False, 
        team: TeamType = TeamType.Neutral, 
        enabled_mods: Mods = Mods.NoMod
    ):
        self.username: str = username
        self.user_id: int = user_id
        self.status: str = status
        self.is_host: bool = is_host
        self.team: TeamType = team
        self.enabled_mods: Mods = enabled_mods
        self.need_update: bool = True


class Slots(object):
    _slots: Dict[int, Slot] = {} # 位置
    _username_slot: Dict[str, int] = {} # 使用者索引
    
        
    def get(self, username: str):
        """從username獲取Slot"""
        slot_number = self._username_slot.get(username)
        return self._slots.get(slot_number)
    

    def move(self, username: str, new_slot: int):
        """移動使用者"""
        old_slot = self._username_slot[username] # 獲取使用者的位置
        self._username_slot[username] = new_slot # 變更使用者索引
        self._slots[new_slot] = self._slots.pop(old_slot)

    
    def set(
        self,
        slot_number: int,
        username: str,
        user_id: int = None, 
        status: str = "Not Ready", 
        is_host: bool = False, 
        team: TeamType = TeamType.Neutral, 
        enabled_mods: Mods = Mods.NoMod
    ):
        """新增使用者"""
        self._slots[slot_number] = Slot(username, user_id, status, is_host, team, enabled_mods)
        self._username_slot[username] = slot_number


    def remove(self, slot_number: int):
        """移除使用者"""
        username = self._slots[slot_number].username
        del self._username_slot[username]
        del self._slots[slot_number]

    def remove_from_username(self, username: str):
        del self._slots[self._username_slot.pop(username)] # ???

    def clear(self):
        self._slots = {}
        self._username_slot = {}
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._slots[key]
        elif isinstance(key, str):
            return self._slots[self._username_slot[key]]
        