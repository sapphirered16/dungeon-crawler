"""Map effects for the dungeon crawler game - environmental features like traps, wet areas, etc."""

import random
from typing import Dict, List, Tuple, Any, Optional
from enum import Enum


class MapEffectType(Enum):
    TRAP = "trap"
    WET_AREA = "wet_area"
    POISONOUS_AREA = "poisonous_area"
    ICY_SURFACE = "icy_surface"
    DARK_CORNER = "dark_corner"
    SLIPPERY_FLOOR = "slippery_floor"
    LOUD_FLOOR = "loud_floor"
    MAGNETIC_FIELD = "magnetic_field"


class MapEffect:
    def __init__(self, effect_type: MapEffectType, position: Tuple[int, int, int], 
                 trigger_chance: float = 0.0, triggered: bool = False, 
                 description: str = "", effect_strength: int = 1):
        self.type = effect_type
        self.position = position
        self.trigger_chance = trigger_chance  # Chance of triggering when stepped on (0.0 to 1.0)
        self.triggered = triggered  # Whether the effect has been triggered
        self.description = description
        self.effect_strength = effect_strength  # Strength of the effect (damage, duration, etc.)
        self.visible_on_map = False  # Whether the effect is visible on the map

    def trigger(self, target) -> str:
        """Trigger the effect on a target (player or entity). Returns a description of what happens."""
        if self.triggered:
            return ""
        
        # Some effects only trigger once, others can trigger multiple times
        if self.type in [MapEffectType.TRAP, MapEffectType.POISONOUS_AREA]:
            self.triggered = True
        
        # Apply effect based on type
        if self.type == MapEffectType.TRAP:
            damage = self.effect_strength
            target.health -= damage
            return f"A trap springs forth! You take {damage} damage!"
        elif self.type == MapEffectType.WET_AREA:
            return "The ground here is wet and soggy. Your footsteps make splashing sounds."
        elif self.type == MapEffectType.POISONOUS_AREA:
            poison_damage = self.effect_strength
            target.health -= poison_damage
            # Add poison status effect
            if hasattr(target, 'active_status_effects'):
                target.active_status_effects['poison'] = 3  # Poison for 3 turns
            return f"You step into a poisonous area! You take {poison_damage} poison damage and become poisoned!"
        elif self.type == MapEffectType.ICY_SURFACE:
            # Might slow down movement or cause slipping
            if hasattr(target, 'speed'):
                target.speed = max(1, target.speed - 2)  # Slow down temporarily
            return "The icy surface makes the ground slippery! You slip and slow down."
        elif self.type == MapEffectType.DARK_CORNER:
            return "You enter a dark corner. Visibility is greatly reduced here."
        elif self.type == MapEffectType.SLIPPERY_FLOOR:
            return "The floor here is unusually slippery. Watch your step!"
        elif self.type == MapEffectType.LOUD_FLOOR:
            return "Your footsteps echo loudly on this resonant floor. Nearby creatures may notice you."
        elif self.type == MapEffectType.MAGNETIC_FIELD:
            return "A strange magnetic field tugs at metal objects in your inventory."
        
        return f"You encounter a {self.type.value} effect!"

    def is_active(self) -> bool:
        """Check if the effect is still active."""
        if self.type in [MapEffectType.TRAP, MapEffectType.POISONOUS_AREA]:
            return not self.triggered
        else:
            # Persistent effects are always active
            return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert map effect to dictionary for serialization."""
        return {
            "type": self.type.value,
            "position": self.position,
            "trigger_chance": self.trigger_chance,
            "triggered": self.triggered,
            "description": self.description,
            "effect_strength": self.effect_strength,
            "visible_on_map": self.visible_on_map
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create map effect from dictionary for deserialization."""
        effect = cls(
            effect_type=MapEffectType(data["type"]),
            position=tuple(data["position"]),
            trigger_chance=data["trigger_chance"],
            triggered=data["triggered"],
            description=data["description"],
            effect_strength=data["effect_strength"]
        )
        effect.visible_on_map = data.get("visible_on_map", False)
        return effect


class MapEffectManager:
    def __init__(self):
        self.effects = {}  # {(x, y, z): [MapEffect, ...]}
    
    def add_effect(self, effect: MapEffect):
        """Add a map effect to a position."""
        pos = effect.position
        if pos not in self.effects:
            self.effects[pos] = []
        self.effects[pos].append(effect)
    
    def get_effects_at_position(self, pos: Tuple[int, int, int]) -> List[MapEffect]:
        """Get all map effects at a given position."""
        return self.effects.get(pos, [])
    
    def trigger_effects_at_position(self, pos: Tuple[int, int, int], target) -> List[str]:
        """Trigger all applicable effects at a position. Returns list of effect descriptions."""
        effects = self.get_effects_at_position(pos)
        results = []
        
        for effect in effects:
            if effect.is_active():
                # Check if the effect triggers based on its chance
                if random.random() < effect.trigger_chance:
                    result = effect.trigger(target)
                    if result:
                        results.append(result)
        
        return results
    
    def has_effects_at_position(self, pos: Tuple[int, int, int]) -> bool:
        """Check if there are any effects at a position."""
        return pos in self.effects and len(self.effects[pos]) > 0
    
    def get_effect_descriptions_at_position(self, pos: Tuple[int, int, int]) -> List[str]:
        """Get descriptions of all effects at a position (for room descriptions)."""
        effects = self.get_effects_at_position(pos)
        return [effect.description for effect in effects if effect.is_active()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert map effect manager to dictionary for serialization."""
        return {
            "effects": {
                str(pos): [effect.to_dict() for effect in effect_list]
                for pos, effect_list in self.effects.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create map effect manager from dictionary for deserialization."""
        manager = cls()
        
        for pos_str, effect_list_data in data["effects"].items():
            pos = tuple(int(x) for x in pos_str.strip('()').split(','))
            effect_list = [MapEffect.from_dict(effect_data) for effect_data in effect_list_data]
            manager.effects[pos] = effect_list
        
        return manager