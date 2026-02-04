"""Enemy class with AI behavior for the dungeon crawler game."""

import random
from typing import Tuple, List, Dict, Any, TYPE_CHECKING
from .base import Entity, Direction
from .character import Player

if TYPE_CHECKING:
    from .dungeon import SeededDungeon
    from .room import RoomState


class Enemy(Entity):
    """Enemy entity with AI behavior."""
    
    def __init__(self, name: str, health: int, attack: int, defense: int, speed: int = 10):
        super().__init__(name, health, attack, defense, speed)
        self.ai_state = "patrol"  # patrol, hunt, flee, idle
        self.target_position = None
        self.last_known_player_pos = None
        self.position = None  # Will be set by the room when added
    
    def take_turn(self, current_room: 'RoomState', dungeon: 'SeededDungeon', player: Player) -> Dict[str, Any]:
        """
        Perform enemy's turn based on AI logic.
        
        Returns a dictionary with results of the action.
        """
        result = {
            "moved": False,
            "attacked": False,
            "action_description": "",
            "new_position": None
        }
        
        # Check if alive
        if not self.is_alive():
            result["action_description"] = f"{self.name} is defeated and takes no action."
            return result
        
        # Check if player is in same room (for immediate attack)
        if current_room and player.position == current_room.pos:
            # Attack the player
            return self._attack_player(player, current_room)
        
        # Otherwise, decide on AI action based on state
        if self.ai_state == "hunt":
            # Try to move toward player
            return self._hunt_player(current_room, dungeon, player)
        else:
            # Default to hunting if player is known to be nearby
            player_in_line_of_sight = self._is_player_in_line_of_sight(current_room, player, dungeon)
            if player_in_line_of_sight:
                self.ai_state = "hunt"
                return self._hunt_player(current_room, dungeon, player)
            else:
                # Random patrol movement
                return self._patrol(current_room, dungeon)
    
    def _attack_player(self, player: Player, current_room: 'RoomState') -> Dict[str, Any]:
        """Attack the player if in the same room."""
        result = {
            "moved": False,
            "attacked": True,
            "action_description": "",
            "new_position": current_room.pos if current_room else None
        }
        
        # Calculate damage
        damage_to_player = max(1, self.attack - player.get_total_defense())
        damage_to_enemy = max(1, player.get_total_attack() - self.defense)
        
        # Apply damage
        player.take_damage(damage_to_player)
        self.take_damage(damage_to_enemy)
        
        result["action_description"] = f"👹 {self.name} attacks you for {damage_to_player} damage! You counter for {damage_to_enemy} damage."
        
        # Check if enemy died
        if not self.is_alive():
            result["action_description"] += f" 💀 The {self.name} has been defeated!"
            # Remove from room handled by caller
        elif not player.is_alive():
            result["action_description"] += " 💀 You have been defeated by the monster!"
        
        return result
    
    def _hunt_player(self, current_room: 'RoomState', dungeon: 'SeededDungeon', player: Player) -> Dict[str, Any]:
        """Move toward the player's position."""
        result = {
            "moved": False,
            "attacked": False,
            "action_description": "",
            "new_position": current_room.pos if current_room else None
        }
        
        # Find path to player using BFS
        path_to_player = self._find_path_to_player(current_room, player, dungeon)
        
        if path_to_player and len(path_to_player) > 1:
            # Move one step toward player
            next_room_pos = path_to_player[1]  # First step after current position
            next_room = dungeon.room_states.get(next_room_pos)
            
            if next_room:
                result["new_position"] = next_room_pos
                result["moved"] = True
                result["action_description"] = f"{self.name} moves toward the player."
            else:
                # Fallback to patrol if path is blocked
                return self._patrol(current_room, dungeon)
        else:
            # Can't find path, go back to patrol
            self.ai_state = "patrol"
            return self._patrol(current_room, dungeon)
        
        return result
    
    def _patrol(self, current_room: 'RoomState', dungeon: 'SeededDungeon') -> Dict[str, Any]:
        """Random patrol movement."""
        result = {
            "moved": False,
            "attacked": False,
            "action_description": "",
            "new_position": current_room.pos if current_room else None
        }
        
        # Choose a random connected room to move to
        if current_room and current_room.connections:
            random_direction = random.choice(list(current_room.connections.values()))
            next_room = dungeon.room_states.get(random_direction)
            
            if next_room:
                result["new_position"] = random_direction
                result["moved"] = True
                result["action_description"] = f"{self.name} patrols to another room."
        
        return result
    
    def _find_path_to_player(self, current_room: 'RoomState', player: Player, dungeon: 'SeededDungeon') -> List[Tuple[int, int, int]]:
        """Find path to player using BFS."""
        from collections import deque
        
        if not current_room or not player.position:
            return []
        
        start_pos = current_room.pos
        target_pos = player.position
        
        if start_pos == target_pos:
            return [start_pos]
        
        # BFS to find shortest path
        queue = deque([(start_pos, [start_pos])])
        visited = {start_pos}
        
        while queue:
            current_pos, path = queue.popleft()
            
            if current_pos == target_pos:
                return path
            
            # Check all connected rooms
            current_room_obj = dungeon.room_states.get(current_pos)
            if current_room_obj:
                for next_pos in current_room_obj.connections.values():
                    if next_pos not in visited:
                        visited.add(next_pos)
                        new_path = path + [next_pos]
                        queue.append((next_pos, new_path))
        
        # No path found
        return []
    
    def _is_player_in_line_of_sight(self, current_room: 'RoomState', player: Player, dungeon: 'SeededDungeon') -> bool:
        """Check if player is in line of sight from current room."""
        if not current_room or not player.position:
            return False
        
        # For simplicity, check if player is on the same floor and within reasonable distance
        if current_room.pos[2] != player.position[2]:  # Different floors
            return False
        
        # Calculate distance
        dx = abs(current_room.pos[0] - player.position[0])
        dy = abs(current_room.pos[1] - player.position[1])
        distance = dx + dy  # Manhattan distance
        
        # Check if player is within line of sight range (adjust as needed)
        max_sight_distance = 10
        if distance <= max_sight_distance:
            # Check if there's a path between rooms (simple check)
            path = self._find_path_to_player(current_room, player, dungeon)
            return len(path) > 0 and len(path) <= max_sight_distance + 5  # Allow some path flexibility
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert enemy to dictionary for saving."""
        data = super().to_dict()
        data.update({
            "ai_state": self.ai_state,
            "target_position": self.target_position,
            "last_known_player_pos": self.last_known_player_pos,
            "position": self.position
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create enemy from dictionary for loading."""
        enemy = cls(
            name=data["name"],
            health=data["health"],
            attack=data["attack"],
            defense=data["defense"],
            speed=data.get("speed", 10)
        )
        enemy.ai_state = data.get("ai_state", "patrol")
        enemy.target_position = data.get("target_position")
        enemy.last_known_player_pos = data.get("last_known_player_pos")
        enemy.position = data.get("position")
        return enemy