"""
New inventory system for the Verde game.
"""
import json
import os
import random
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class ItemType(Enum):
    """Types of items in the game"""
    SEED = 0
    CROP = 1
    TOOL = 2
    FOOD = 3
    MATERIAL = 4
    FURNITURE = 5
    DECORATION = 6
    GIFT = 7


class ItemQuality(Enum):
    """Quality levels for items"""
    NORMAL = 0
    SILVER = 1
    GOLD = 2
    IRIDIUM = 3


@dataclass
class Item:
    """Base class for all items"""
    id: str
    name: str
    description: str
    item_type: ItemType
    value: int = 0
    stack_size: int = 1
    icon_path: str = ""
    quality: ItemQuality = ItemQuality.NORMAL
    
    def get_sell_price(self) -> int:
        """Calculate the sell price based on quality"""
        quality_multiplier = {
            ItemQuality.NORMAL: 1.0,
            ItemQuality.SILVER: 1.25,
            ItemQuality.GOLD: 1.5,
            ItemQuality.IRIDIUM: 2.0
        }
        return int(self.value * quality_multiplier[self.quality])


# Simple version with minimal fields to avoid any ordering issues
class Seed(Item):
    """Seed item that can be planted"""
    def __init__(self, id, name, description, item_type, crop_id, grow_time, 
                 value=0, stack_size=1, icon_path="", quality=ItemQuality.NORMAL,
                 regrow_time=0, season=None):
        super().__init__(id, name, description, item_type, value, stack_size, icon_path, quality)
        self.crop_id = crop_id
        self.grow_time = grow_time
        self.regrow_time = regrow_time
        self.season = season or []  # Default to empty list


# Simple version with minimal fields to avoid any ordering issues
class Crop(Item):
    """Harvested crop item"""
    def __init__(self, id, name, description, item_type, seed_id, grow_time,
                 value=0, stack_size=1, icon_path="", quality=ItemQuality.NORMAL,
                 energy_restore=0, health_restore=0, is_regrowable=False,
                 regrow_time=0, seasons=None):
        super().__init__(id, name, description, item_type, value, stack_size, icon_path, quality)
        self.seed_id = seed_id
        self.grow_time = grow_time
        self.energy_restore = energy_restore
        self.health_restore = health_restore
        self.is_regrowable = is_regrowable
        self.regrow_time = regrow_time
        self.seasons = seasons or []  # Default to empty list


@dataclass
class Tool(Item):
    """Tool for farming, mining, etc."""
    tool_level: int = 1
    energy_cost: int = 2
    
    def __post_init__(self):
        if not self.item_type == ItemType.TOOL:
            self.item_type = ItemType.TOOL


@dataclass
class Food(Item):
    """Food items that can be consumed"""
    energy_restore: int = 10
    health_restore: int = 5
    buffs: Dict[str, int] = field(default_factory=dict)
    buff_duration: int = 0  # Seconds
    
    def __post_init__(self):
        if not self.item_type == ItemType.FOOD:
            self.item_type = ItemType.FOOD


class InventorySlot:
    """A slot in the inventory containing an item and its quantity"""
    
    def __init__(self, item: Optional[Item] = None, quantity: int = 0):
        self.item = item
        self.quantity = quantity
    
    def is_empty(self) -> bool:
        """Check if the slot is empty"""
        return self.item is None or self.quantity <= 0
    
    def can_add(self, item: Item) -> bool:
        """Check if the given item can be added to this slot"""
        if self.is_empty():
            return True
        
        if self.item.id == item.id and self.item.quality == item.quality:
            return self.quantity < self.item.stack_size
        
        return False
    
    def add(self, item: Item, quantity: int = 1) -> int:
        """
        Add item to this slot.
        Returns the number of items that couldn't be added due to stack size.
        """
        if self.is_empty():
            self.item = item
            self.quantity = min(quantity, item.stack_size)
            return max(0, quantity - item.stack_size)
        
        if self.item.id == item.id and self.item.quality == item.quality:
            space_left = self.item.stack_size - self.quantity
            amount_to_add = min(space_left, quantity)
            self.quantity += amount_to_add
            return quantity - amount_to_add
        
        return quantity  # Can't add to this slot
    
    def remove(self, quantity: int = 1) -> int:
        """
        Remove items from this slot.
        Returns the actual number of items removed.
        """
        if self.is_empty():
            return 0
        
        amount_to_remove = min(self.quantity, quantity)
        self.quantity -= amount_to_remove
        
        if self.quantity <= 0:
            self.item = None
            self.quantity = 0
        
        return amount_to_remove


class Inventory:
    """Player's inventory with multiple slots"""
    
    def __init__(self, size: int = 24):
        self.size = size
        self.slots = [InventorySlot() for _ in range(size)]
        self.selected_slot_index = 0
    
    def get_selected_slot(self) -> InventorySlot:
        """Get the currently selected inventory slot"""
        return self.slots[self.selected_slot_index]
    
    def select_slot(self, index: int) -> bool:
        """Select a specific slot by index"""
        if 0 <= index < self.size:
            self.selected_slot_index = index
            return True
        return False
    
    def add_item(self, item: Item, quantity: int = 1) -> int:
        """
        Add an item to the inventory.
        Returns the number of items that couldn't be added.
        """
        remaining = quantity
        
        # First try to add to existing stacks
        for slot in self.slots:
            if not slot.is_empty() and slot.item.id == item.id and slot.item.quality == item.quality:
                remaining = slot.add(item, remaining)
                if remaining <= 0:
                    return 0
        
        # Then try to add to empty slots
        for slot in self.slots:
            if slot.is_empty():
                remaining = slot.add(item, remaining)
                if remaining <= 0:
                    return 0
        
        return remaining  # Returns how many items couldn't be added
    
    def remove_item(self, item_id: str, quantity: int = 1, quality: ItemQuality = ItemQuality.NORMAL) -> int:
        """
        Remove an item from the inventory.
        Returns the actual number of items removed.
        """
        remaining = quantity
        removed = 0
        
        for slot in self.slots:
            if not slot.is_empty() and slot.item.id == item_id and slot.item.quality == quality:
                amount_removed = slot.remove(remaining)
                removed += amount_removed
                remaining -= amount_removed
                
                if remaining <= 0:
                    break
        
        return removed
    
    def has_item(self, item_id: str, quantity: int = 1, quality: Optional[ItemQuality] = None) -> bool:
        """Check if the inventory has the required quantity of an item"""
        count = 0
        
        for slot in self.slots:
            if not slot.is_empty() and slot.item.id == item_id:
                if quality is None or slot.item.quality == quality:
                    count += slot.quantity
                    if count >= quantity:
                        return True
        
        return False
    
    def count_item(self, item_id: str, quality: Optional[ItemQuality] = None) -> int:
        """Count how many of a specific item are in the inventory"""
        count = 0
        
        for slot in self.slots:
            if not slot.is_empty() and slot.item.id == item_id:
                if quality is None or slot.item.quality == quality:
                    count += slot.quantity
        
        return count
    
    def get_items(self) -> List[tuple[Item, int]]:
        """Get a list of all non-empty items and their quantities"""
        items = []
        
        for slot in self.slots:
            if not slot.is_empty():
                items.append((slot.item, slot.quantity))
        
        return items
    
    def is_full(self) -> bool:
        """Check if the inventory is completely full"""
        for slot in self.slots:
            if slot.is_empty():
                return False
        return True


class ItemDatabase:
    """Database for all game items"""
    
    def __init__(self):
        self.items: Dict[str, Item] = {}
        self.seeds: Dict[str, Seed] = {}
        self.crops: Dict[str, Crop] = {}
        self.tools: Dict[str, Tool] = {}
        self.foods: Dict[str, Food] = {}
        
        # Load item data
        self._load_data()
    
    def _load_data(self):
        """Load item data from files"""
        data_path = Path("data/items")
        
        # Create the directory if it doesn't exist
        data_path.mkdir(parents=True, exist_ok=True)
        
        # Try to load from files
        if (data_path / "items.json").exists():
            self._load_from_files(data_path)
        else:
            # Create default items
            self._create_default_items()
            # Save to files
            self._save_to_files(data_path)
    
    def _load_from_files(self, data_path: Path):
        """Load item data from files"""
        try:
            # Load general items
            with open(data_path / "items.json", "r", encoding="utf-8") as f:
                items_data = json.load(f)
                for item_data in items_data:
                    item = Item(
                        id=item_data["id"],
                        name=item_data["name"],
                        description=item_data["description"],
                        item_type=ItemType[item_data["item_type"]],
                        value=item_data["value"],
                        stack_size=item_data["stack_size"],
                        icon_path=item_data["icon_path"]
                    )
                    self.items[item.id] = item
            
            # Load seeds
            with open(data_path / "seeds.json", "r", encoding="utf-8") as f:
                seeds_data = json.load(f)
                for seed_data in seeds_data:
                    seed = Seed(
                        id=seed_data["id"],
                        name=seed_data["name"],
                        description=seed_data["description"],
                        item_type=ItemType.SEED,
                        crop_id=seed_data["crop_id"],
                        grow_time=seed_data["grow_time"],
                        value=seed_data["value"],
                        stack_size=seed_data["stack_size"],
                        icon_path=seed_data["icon_path"],
                        regrow_time=seed_data.get("regrow_time", 0),
                        season=seed_data["season"]
                    )
                    self.seeds[seed.id] = seed
                    self.items[seed.id] = seed
            
            # Load crops
            with open(data_path / "crops.json", "r", encoding="utf-8") as f:
                crops_data = json.load(f)
                for crop_data in crops_data:
                    crop = Crop(
                        id=crop_data["id"],
                        name=crop_data["name"],
                        description=crop_data["description"],
                        item_type=ItemType.CROP,
                        seed_id=crop_data["seed_id"],
                        grow_time=crop_data["grow_time"],
                        value=crop_data["value"],
                        stack_size=crop_data["stack_size"],
                        icon_path=crop_data["icon_path"],
                        energy_restore=crop_data.get("energy_restore", 0),
                        health_restore=crop_data.get("health_restore", 0),
                        is_regrowable=crop_data.get("is_regrowable", False),
                        regrow_time=crop_data.get("regrow_time", 0),
                        seasons=crop_data.get("seasons", [])
                    )
                    self.crops[crop.id] = crop
                    self.items[crop.id] = crop
            
            # Load tools
            with open(data_path / "tools.json", "r", encoding="utf-8") as f:
                tools_data = json.load(f)
                for tool_data in tools_data:
                    tool = Tool(
                        id=tool_data["id"],
                        name=tool_data["name"],
                        description=tool_data["description"],
                        item_type=ItemType.TOOL,
                        value=tool_data["value"],
                        stack_size=1,  # Tools don't stack
                        icon_path=tool_data["icon_path"],
                        tool_level=tool_data.get("tool_level", 1),
                        energy_cost=tool_data.get("energy_cost", 2)
                    )
                    self.tools[tool.id] = tool
                    self.items[tool.id] = tool
            
            # Load foods
            with open(data_path / "foods.json", "r", encoding="utf-8") as f:
                foods_data = json.load(f)
                for food_data in foods_data:
                    food = Food(
                        id=food_data["id"],
                        name=food_data["name"],
                        description=food_data["description"],
                        item_type=ItemType.FOOD,
                        value=food_data["value"],
                        stack_size=food_data["stack_size"],
                        icon_path=food_data["icon_path"],
                        energy_restore=food_data.get("energy_restore", 10),
                        health_restore=food_data.get("health_restore", 5),
                        buffs=food_data.get("buffs", {}),
                        buff_duration=food_data.get("buff_duration", 0)
                    )
                    self.foods[food.id] = food
                    self.items[food.id] = food
        
        except Exception as e:
            print(f"Error loading item data: {e}")
            # Create default items if loading fails
            self._create_default_items()
    
    def _create_default_items(self):
        """Create default items if no data files exist"""
        # Create basic seeds
        seeds = [
            Seed(
                id="seed_turnip",
                name="Turnip Seeds",
                description="Plant these in spring. Takes 5 days to mature.",
                item_type=ItemType.SEED,
                crop_id="crop_turnip",
                grow_time=5,
                value=20,
                stack_size=99,
                icon_path="assets/images/items/seeds/turnip_seed.png",
                season=["Spring"]
            ),
            Seed(
                id="seed_potato",
                name="Potato Seeds",
                description="Plant these in spring. Takes 6 days to mature.",
                item_type=ItemType.SEED,
                crop_id="crop_potato",
                grow_time=6,
                value=50,
                stack_size=99,
                icon_path="assets/images/items/seeds/potato_seed.png",
                season=["Spring"]
            ),
            Seed(
                id="seed_tomato",
                name="Tomato Seeds",
                description="Plant these in summer. Takes 11 days to mature, but keeps producing after that.",
                item_type=ItemType.SEED,
                crop_id="crop_tomato",
                grow_time=11,
                value=50,
                stack_size=99,
                icon_path="assets/images/items/seeds/tomato_seed.png",
                regrow_time=4,
                season=["Summer"]
            ),
            Seed(
                id="seed_corn",
                name="Corn Seeds",
                description="Plant these in summer or fall. Takes 14 days to mature, but keeps producing after that.",
                item_type=ItemType.SEED,
                crop_id="crop_corn",
                grow_time=14,
                value=150,
                stack_size=99,
                icon_path="assets/images/items/seeds/corn_seed.png",
                regrow_time=4,
                season=["Summer", "Fall"]
            ),
            Seed(
                id="seed_pumpkin",
                name="Pumpkin Seeds",
                description="Plant these in fall. Takes 13 days to mature.",
                item_type=ItemType.SEED,
                crop_id="crop_pumpkin",
                grow_time=13,
                value=100,
                stack_size=99,
                icon_path="assets/images/items/seeds/pumpkin_seed.png",
                season=["Fall"]
            )
        ]
        
        # Create crops
        crops = [
            Crop(
                id="crop_turnip",
                name="Turnip",
                description="A spring crop.",
                item_type=ItemType.CROP,
                seed_id="seed_turnip",
                grow_time=5,
                value=35,
                stack_size=99,
                icon_path="assets/images/items/crops/turnip.png",
                energy_restore=15,
                health_restore=5,
                is_regrowable=False,
                seasons=["Spring"]
            ),
            Crop(
                id="crop_potato",
                name="Potato",
                description="A starchy tuber.",
                item_type=ItemType.CROP,
                seed_id="seed_potato",
                grow_time=6,
                value=80,
                stack_size=99,
                icon_path="assets/images/items/crops/potato.png",
                energy_restore=25,
                health_restore=10,
                is_regrowable=False,
                seasons=["Spring"]
            ),
            Crop(
                id="crop_tomato",
                name="Tomato",
                description="A juicy summer fruit.",
                item_type=ItemType.CROP,
                seed_id="seed_tomato",
                grow_time=11,
                value=60,
                stack_size=99,
                icon_path="assets/images/items/crops/tomato.png",
                energy_restore=20,
                health_restore=8,
                is_regrowable=True,
                regrow_time=4,
                seasons=["Summer"]
            ),
            Crop(
                id="crop_corn",
                name="Corn",
                description="A tall grain with high yield.",
                item_type=ItemType.CROP,
                seed_id="seed_corn",
                grow_time=14,
                value=50,
                stack_size=99,
                icon_path="assets/images/items/crops/corn.png",
                energy_restore=18,
                health_restore=5,
                is_regrowable=True,
                regrow_time=4,
                seasons=["Summer", "Fall"]
            ),
            Crop(
                id="crop_pumpkin",
                name="Pumpkin",
                description="A fall crop with many uses.",
                item_type=ItemType.CROP,
                seed_id="seed_pumpkin",
                grow_time=13,
                value=320,
                stack_size=99,
                icon_path="assets/images/items/crops/pumpkin.png",
                energy_restore=45,
                health_restore=20,
                is_regrowable=False,
                seasons=["Fall"]
            )
        ]
        
        # Create basic tools
        tools = [
            Tool(
                id="tool_hoe",
                name="Hoe",
                description="Used to till soil for planting.",
                item_type=ItemType.TOOL,
                value=500,
                stack_size=1,
                icon_path="assets/images/items/tools/hoe.png",
                tool_level=1,
                energy_cost=2
            ),
            Tool(
                id="tool_watering_can",
                name="Watering Can",
                description="Used to water crops.",
                item_type=ItemType.TOOL,
                value=500,
                stack_size=1,
                icon_path="assets/images/items/tools/watering_can.png",
                tool_level=1,
                energy_cost=1
            ),
            Tool(
                id="tool_axe",
                name="Axe",
                description="Used to chop down trees.",
                item_type=ItemType.TOOL,
                value=500,
                stack_size=1,
                icon_path="assets/images/items/tools/axe.png",
                tool_level=1,
                energy_cost=4
            ),
            Tool(
                id="tool_pickaxe",
                name="Pickaxe",
                description="Used to break rocks.",
                item_type=ItemType.TOOL,
                value=500,
                stack_size=1,
                icon_path="assets/images/items/tools/pickaxe.png",
                tool_level=1,
                energy_cost=4
            ),
            Tool(
                id="tool_scythe",
                name="Scythe",
                description="Used to harvest crops and cut grass.",
                item_type=ItemType.TOOL,
                value=500,
                stack_size=1,
                icon_path="assets/images/items/tools/scythe.png",
                tool_level=1,
                energy_cost=1
            )
        ]
        
        # Create foods
        foods = [
            Food(
                id="food_bread",
                name="Bread",
                description="A simple loaf of bread.",
                item_type=ItemType.FOOD,
                value=60,
                stack_size=99,
                icon_path="assets/images/items/foods/bread.png",
                energy_restore=50,
                health_restore=20
            ),
            Food(
                id="food_salad",
                name="Salad",
                description="A fresh garden salad.",
                item_type=ItemType.FOOD,
                value=110,
                stack_size=99,
                icon_path="assets/images/items/foods/salad.png",
                energy_restore=80,
                health_restore=45
            ),
            Food(
                id="food_vegetable_stew",
                name="Vegetable Stew",
                description="A hearty stew made from vegetables.",
                item_type=ItemType.FOOD,
                value=200,
                stack_size=99,
                icon_path="assets/images/items/foods/vegetable_stew.png",
                energy_restore=160,
                health_restore=70,
                buffs={"farming": 1},
                buff_duration=120
            )
        ]
        
        # Add all items to the database
        for seed in seeds:
            self.seeds[seed.id] = seed
            self.items[seed.id] = seed
        
        for crop in crops:
            self.crops[crop.id] = crop
            self.items[crop.id] = crop
        
        for tool in tools:
            self.tools[tool.id] = tool
            self.items[tool.id] = tool
        
        for food in foods:
            self.foods[food.id] = food
            self.items[food.id] = food
    
    def _save_to_files(self, data_path: Path):
        """Save item data to files"""
        try:
            # Save general items (that are not seeds, crops, tools, or foods)
            general_items = [item for item in self.items.values() 
                             if item.item_type not in [ItemType.SEED, ItemType.CROP, 
                                                      ItemType.TOOL, ItemType.FOOD]]
            
            # Convert items to dictionaries
            items_dict = [self._item_to_dict(item) for item in general_items]
            seeds_dict = [self._item_to_dict(seed) for seed in self.seeds.values()]
            crops_dict = [self._item_to_dict(crop) for crop in self.crops.values()]
            tools_dict = [self._item_to_dict(tool) for tool in self.tools.values()]
            foods_dict = [self._item_to_dict(food) for food in self.foods.values()]
            
            # Save to files
            with open(data_path / "items.json", "w", encoding="utf-8") as f:
                json.dump(items_dict, f, indent=4)
            
            with open(data_path / "seeds.json", "w", encoding="utf-8") as f:
                json.dump(seeds_dict, f, indent=4)
            
            with open(data_path / "crops.json", "w", encoding="utf-8") as f:
                json.dump(crops_dict, f, indent=4)
            
            with open(data_path / "tools.json", "w", encoding="utf-8") as f:
                json.dump(tools_dict, f, indent=4)
            
            with open(data_path / "foods.json", "w", encoding="utf-8") as f:
                json.dump(foods_dict, f, indent=4)
        
        except Exception as e:
            print(f"Error saving item data: {e}")
    
    def _item_to_dict(self, item: Item) -> dict:
        """Convert an item to a dictionary for JSON serialization"""
        item_dict = {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "item_type": item.item_type.name,
            "value": item.value,
            "stack_size": item.stack_size,
            "icon_path": item.icon_path
        }
        
        # Add specific properties based on item type
        if isinstance(item, Seed):
            item_dict.update({
                "crop_id": item.crop_id,
                "grow_time": item.grow_time,
                "regrow_time": item.regrow_time,
                "season": item.season
            })
        
        elif isinstance(item, Crop):
            item_dict.update({
                "seed_id": item.seed_id,
                "grow_time": item.grow_time,
                "energy_restore": item.energy_restore,
                "health_restore": item.health_restore,
                "is_regrowable": item.is_regrowable,
                "regrow_time": item.regrow_time,
                "seasons": item.seasons
            })
        
        elif isinstance(item, Tool):
            item_dict.update({
                "tool_level": item.tool_level,
                "energy_cost": item.energy_cost
            })
        
        elif isinstance(item, Food):
            item_dict.update({
                "energy_restore": item.energy_restore,
                "health_restore": item.health_restore,
                "buffs": item.buffs,
                "buff_duration": item.buff_duration
            })
        
        return item_dict
    
    def get_item(self, item_id: str) -> Optional[Item]:
        """Get an item by its ID"""
        return self.items.get(item_id)
    
    def get_seed(self, seed_id: str) -> Optional[Seed]:
        """Get a seed by its ID"""
        return self.seeds.get(seed_id)
    
    def get_crop(self, crop_id: str) -> Optional[Crop]:
        """Get a crop by its ID"""
        return self.crops.get(crop_id)
    
    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """Get a tool by its ID"""
        return self.tools.get(tool_id)
    
    def get_food(self, food_id: str) -> Optional[Food]:
        """Get a food by its ID"""
        return self.foods.get(food_id)
    
    def get_crop_from_seed(self, seed_id: str) -> Optional[Crop]:
        """Get the crop that grows from a seed"""
        seed = self.get_seed(seed_id)
        if seed:
            return self.get_crop(seed.crop_id)
        return None
    
    def get_seed_from_crop(self, crop_id: str) -> Optional[Seed]:
        """Get the seed that produces a crop"""
        crop = self.get_crop(crop_id)
        if crop:
            return self.get_seed(crop.seed_id)
        return None
    
    def get_seeds_for_season(self, season: str) -> List[Seed]:
        """Get all seeds that can be planted in a specific season"""
        return [seed for seed in self.seeds.values() 
                if season in seed.season]
    
    def get_crops_for_season(self, season: str) -> List[Crop]:
        """Get all crops that grow in a specific season"""
        return [crop for crop in self.crops.values() 
                if season in crop.seasons]