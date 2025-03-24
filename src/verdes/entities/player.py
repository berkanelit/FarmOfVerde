"""
Oyuncu varlık sınıfı.
"""
from verdes.entities.actor import Actor
from verdes.systems.inventory import Inventory, ItemDatabase
import math

class Player(Actor):
    """Oyuncu sınıfı - oyuncunun kontrol ettiği ana karakter"""
    
    def __init__(self, x, y):
        super().__init__("player", x, y)
        self.speed = 150  # Biraz daha hızlı
        self.max_energy = 100
        self.energy = self.max_energy
        self.money = 500
        self.inventory = Inventory(size=24)  # 24 yuvalı envanter
        self.item_db = ItemDatabase()
        self.active_tool = None
        self.interaction_range = 50  # Piksel
        self.name = "Farmer"  # Oyuncu ismi
        
        # Oyuncu becerileri
        self.skills = {
            "farming": 0,  # 0-10 arası seviye
            "mining": 0,
            "foraging": 0,
            "fishing": 0
        }
        
        # Temel aletleri ekle
        self._add_starter_items()
    
    def _add_starter_items(self):
        """Başlangıç eşyalarını ekle"""
        starter_items = {
            "hoe": 1,
            "watering_can": 1,
            "axe": 1,
            "turnip_seed": 5
        }
        
        for item_id, count in starter_items.items():
            item = self.item_db.get_item(item_id)
            if item:
                self.inventory.add_item(item, count)
    
    def update(self, dt):
        """Oyuncuyu güncelle"""
        super().update(dt)
        
        # Klavye girişi ile hareket
        dx, dy = 0, 0
        
        if keyboard.left:
            dx -= 1
        if keyboard.right:
            dx += 1
        if keyboard.up:
            dy -= 1
        if keyboard.down:
            dy += 1
        
        # Köşegenler için normalize et
        if dx != 0 and dy != 0:
            dx *= 0.7071  # 1/sqrt(2)
            dy *= 0.7071
        
        # Hareket ettir
        if dx != 0 or dy != 0:
            # Harita ve nesnelerle çarpışma kontrolü yap
            new_x = self.x + dx * self.speed * dt
            new_y = self.y + dy * self.speed * dt
            
            # Eğer world varsa (bu nesnedeki bir fonksiyonda değil dışarıdan erişilebilir)
            if 'world' in globals() and world and hasattr(world, 'is_walkable'):
                # X ekseninde hareket kontrolü
                if world.is_walkable(new_x, self.y):
                    self.x = new_x
                
                # Y ekseninde hareket kontrolü
                if world.is_walkable(self.x, new_y):
                    self.y = new_y
            else:
                # World yoksa (test veya dünya oluşturulmadan önce), doğrudan hareket et
                self.x = new_x
                self.y = new_y
            
            # Hareket durumunu güncelle
            self.moving = dx != 0 or dy != 0
            
            # Yönü güncelle
            if abs(dx) > abs(dy):
                self.direction = "right" if dx > 0 else "left"
            else:
                self.direction = "down" if dy > 0 else "up"
            
            # Hareket için enerji tüket (çok az)
            self.use_energy(0.05 * dt)
    
    def use_energy(self, amount):
        """Enerji tüket"""
        self.energy = max(0, self.energy - amount)
    
    def restore_energy(self, amount):
        """Enerji yenile"""
        self.energy = min(self.max_energy, self.energy + amount)
    
    def use_tool(self, tool_name=None):
        """Alet kullan"""
        # Belirtilmediyse, aktif aleti kullan
        if not tool_name and self.active_tool:
            tool_name = self.active_tool.id
        
        if not tool_name:
            return False
        
        # Aleti envanterde bul
        selected_slot = self.inventory.slots[self.inventory.selected_slot]
        if selected_slot.item and selected_slot.item.category == "tool" and selected_slot.item.id == tool_name:
            # Enerji maliyeti
            energy_cost = selected_slot.item.energy_cost
            
            # Yeterli enerji var mı?
            if self.energy >= energy_cost:
                # Enerji tüket
                self.use_energy(energy_cost)
                
                # Fareye göre kullanım yönü
                mouse_x, mouse_y = mouse_pos = (0, 0)  # Gerçek uygulamada pygame.mouse.get_pos() kullanılır
                
                # Oyuncudan fareye olan vektör
                dx = mouse_x - self.x
                dy = mouse_y - self.y
                
                # Yeni yön hesapla (interaksiyon için)
                if abs(dx) > abs(dy):
                    self.direction = "right" if dx > 0 else "left"
                else:
                    self.direction = "down" if dy > 0 else "up"
                
                # Kullanım pozisyonu - oyuncunun önünde
                tool_x, tool_y = self._get_front_position()
                
                # Alete göre dünya üzerinde farklı etkiler
                if tool_name == "hoe":
                    # Çapa - toprağı sür
                    if 'world' in globals() and world:
                        # Tile'ın X ve Y'sini hesapla
                        tile_x = int(tool_x / world.tile_size)
                        tile_y = int(tool_y / world.tile_size)
                        
                        # Eğer bu bir çimen tile'ı ise, toprak yap
                        if 0 <= tile_x < world.width and 0 <= tile_y < world.height:
                            if world.tiles[tile_y][tile_x]["type"] == "grass":
                                world.tiles[tile_y][tile_x]["type"] = "dirt"
                
                elif tool_name == "watering_can":
                    # Sulama kabı - bitkileri sula
                    if 'world' in globals() and world:
                        world.water_crop(tool_x, tool_y, self)
                
                elif tool_name == "axe":
                    # Balta - ağaçları kes
                    # Bu kısım daha sonra eklenecek
                    pass
                
                return True
        
        return False
    
    def plant_seed(self, seed_id=None):
        """Tohum ek"""
        # Belirtilmediyse, seçili yuva kontrolü
        if not seed_id:
            selected_slot = self.inventory.slots[self.inventory.selected_slot]
            if selected_slot.item and selected_slot.item.category == "seed":
                seed_id = selected_slot.item.id
            else:
                return False
        
        # Ekme pozisyonu - oyuncunun önünde
        plant_x, plant_y = self._get_front_position()
        
        # Dünya haritasında ekme
        if 'world' in globals() and world:
            seed_item = self.item_db.get_item(seed_id)
            if seed_item and hasattr(seed_item, 'crop_type'):
                # Tohumu azalt
                if self.inventory.remove_item(seed_id, 1) > 0:
                    # Bitki türünü belirle
                    crop_type = seed_item.crop_type
                    
                    # Dünyada ekme işlemi
                    if world.plant_crop(crop_type, plant_x, plant_y, self):
                        # Beceri puanı kazanma
                        self._gain_skill("farming", 0.2)
                        return True
        
        return False
    
    def harvest(self):
        """Hasat yap"""
        # Hasat pozisyonu - oyuncunun önünde
        harvest_x, harvest_y = self._get_front_position()
        
        # Dünya haritasında hasat
        if 'world' in globals() and world:
            if world.harvest_crop(harvest_x, harvest_y, self):
                # Beceri puanı kazanma
                self._gain_skill("farming", 1.0)
                return True
        
        return False
    
    def interact(self, object_id=None):
        """Nesne ile etkileşim"""
        # Etkileşim pozisyonu - oyuncunun önünde
        interact_x, interact_y = self._get_front_position()
        
        # Dünya objeleriyle etkileşim
        # Bu kısım daha sonra eklenecek
        return False
    
    def _get_front_position(self):
        """Oyuncunun önündeki pozisyonu hesapla"""
        # Yöne göre x ve y ofsetini hesapla
        offset_x, offset_y = 0, 0
        
        if self.direction == "up":
            offset_y = -self.height
        elif self.direction == "down":
            offset_y = self.height
        elif self.direction == "left":
            offset_x = -self.width
        elif self.direction == "right":
            offset_x = self.width
        
        return self.x + offset_x, self.y + offset_y
    
    def add_to_inventory(self, item_id, count=1):
        """Envantere eşya ekle"""
        item = self.item_db.get_item(item_id)
        if item:
            return self.inventory.add_item(item, count)
        return count  # Eklenemeyen miktar
    
    def remove_from_inventory(self, item_id, count=1):
        """Envanterden eşya çıkar"""
        return self.inventory.remove_item(item_id, count)
    
    def add_money(self, amount):
        """Para ekle"""
        self.money += amount
    
    def spend_money(self, amount):
        """Para harca"""
        if self.money >= amount:
            self.money -= amount
            return True
        return False
    
    def _gain_skill(self, skill_name, amount):
        """Beceri puanı kazan"""
        if skill_name in self.skills:
            # Beceri seviyesi kazan
            self.skills[skill_name] += amount
            
            # Üst limit
            max_level = 10
            if self.skills[skill_name] > max_level:
                self.skills[skill_name] = max_level