import json
import os
import random
import gen_depths

def create_default_ascension():
    """Create default ascension data structure"""
    return {
        "level": 0,
        "boss_kills": 0,  # Track total boss kills for achievements
        "unlocks": {
            "fast_access": False,
            "settlements": False,
            "checkpoints": False,
            "rare_enemies": False,
            "sky_world": False
        },
        "checkpoints": [],  # store up to 5 checkpoint locations
        "checkpoint_names": []  # optional names for checkpoints
    }

def load_ascension_data():
    """Load ascension data from ascension.json"""
    try:
        with open("ascension.json", "r") as file:
            data = json.load(file)
            default_data = create_default_ascension()
            for key in default_data:
                if key not in data:
                    data[key] = default_data[key]
            # Ensure all unlock keys exist
            for unlock_key in default_data["unlocks"]:
                if unlock_key not in data["unlocks"]:
                    data["unlocks"][unlock_key] = False
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # Create new file if it doesn't exist or is corrupted
        return create_default_ascension()

def save_ascension_data(ascension_data):
    """Save ascension data to ascension.json"""
    with open("ascension.json", "w") as file:
        json.dump(ascension_data, file, indent=2)
    return ascension_data

def ascend_player(ascension_data):
    """Ascend player to next level if they have boss kill available"""
    if ascension_data["boss_kills"] > 0:
        ascension_data["boss_kills"] -= 1
        ascension_data["level"] += 1
        
        # Unlock features based on level
        unlock_message, ascension_data = unlock_ascension_feature(ascension_data, ascension_data["level"])
        
        messages = [f"ASCENDED TO LEVEL {ascension_data['level']}!"]
        if unlock_message:
            messages.append(unlock_message)
        
        # Trigger full reset
        messages.append("Progress reset. New features unlocked!")
        reset_needed = True
        
        return messages, reset_needed, ascension_data
    else:
        return ["No ascension points available! Defeat the final boss first."], False, ascension_data

def unlock_ascension_feature(ascension_data, level):
    """Unlock features based on ascension level"""
    unlock_messages = {
        1: ("Fast Access Unlocked! (f/v keys)", "fast_access"),
        2: ("Settlements Unlocked!", "settlements"),
        3: ("Checkpoints Unlocked! (c to place, t to teleport)", "checkpoints"),
        4: ("Rare Enemies Unlocked!", "rare_enemies"),
        5: ("Sky World Unlocked!", "sky_world")
    }
    
    if level in unlock_messages:
        message, unlock_key = unlock_messages[level]
        ascension_data["unlocks"][unlock_key] = True
        return message, ascension_data
    
    return None, ascension_data

def get_final_boss_stats(ascension_level):
    """Get final boss stats scaled by ascension level"""
    base_health = 1000
    base_attack = 100
    
    # Each ascension level makes boss significantly harder
    health_multiplier = 1 + (ascension_level * 1.5)  # 1x, 2.5x, 4x, 5.5x, etc.
    attack_multiplier = 1 + (ascension_level * 0.5)   # 1x, 1.5x, 2x, 2.5x, etc.
    
    final_health = int(base_health * health_multiplier)
    final_attack = int(base_attack * attack_multiplier)
    
    return final_health, final_attack

def get_enemy_scale_multiplier(ascension_level):
    """Get multiplier for regular enemy stats based on ascension level"""
    # Regular enemies also scale but less aggressively than boss
    return 1 + (ascension_level * 0.3)  # 1x, 1.3x, 1.6x, 1.9x, etc.

def add_checkpoint(ascension_data, x, y, grid_id, name=""):
    """Add a checkpoint if checkpoints are unlocked"""
    if not ascension_data["unlocks"]["checkpoints"]:
        return "Checkpoints not unlocked!"
    
    if len(ascension_data["checkpoints"]) >= 5:
        return "Maximum checkpoints (5) reached!"
    
    checkpoint = {
        "x": x,
        "y": y,
        "grid_id": grid_id,
        "name": name if name else f"Checkpoint {len(ascension_data['checkpoints']) + 1}"
    }
    
    ascension_data["checkpoints"].append(checkpoint)
    return f"Checkpoint '{checkpoint['name']}' added!", ascension_data

def remove_checkpoint(ascension_data, index):
    """Remove a checkpoint by index"""
    if 0 <= index < len(ascension_data["checkpoints"]):
        removed = ascension_data["checkpoints"].pop(index)
        return f"Checkpoint '{removed['name']}' removed!", ascension_data
    return "Invalid checkpoint index!", ascension_data

def get_ascension_display_info(ascension_data):
    """Get formatted display information for ascension status"""
    level = ascension_data["level"]
    boss_kills = ascension_data["boss_kills"]
    
    info = f"Ascension Level: {level} | Ascension points: {boss_kills}"
    
    return info