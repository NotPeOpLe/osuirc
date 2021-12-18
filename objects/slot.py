from typing import Dict, List


class Slot(object):
    def __init__(self, username: str, user_id: int, status: str, flags: List[str] = []) -> None:
        self.username: str = username
        self.user_id: int = user_id
        self.status: str = status
        self.flags:  List[str] = flags


class Slots(object):
    _slots: Dict[int, Slot] = {}
    _username_slot: Dict[str, int] = {}
    
        
    def get(self, username: str):
        slot_number = self._username_slot.get(username)
        return self._slots.get(slot_number)
    
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._slots[key]
        elif isinstance(key, str):
            return self._slots[self._username_slot[key]]
    
    
    def __setitem__(self, slot_number: int, slot: Slot):
        self._slots[slot_number] = slot
        self._username_slot[slot.username] = slot_number
        
    
    def __delitem__(self, slot_number: int):
        username = self._slots[slot_number].username
        del self._username_slot[username]
        del self._slots[slot_number]
        