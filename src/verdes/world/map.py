"""
Oyun dünyası harita yönetimi.
"""
import random
from pathlib import Path
import yaml

class World:
    """Oyun dünyası sınıfı"""
    
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.width = 40  # Tile sayısı
        self.height = 30  # Tile sayısı
        self.tile_size = 32  # Piksel
        self.tiles = []  # 2D tile dizisi
        self.objects = []  # Dünya nesneleri (ağaçlar, kayalar vs.)
        self.crops = []  # Ekilmiş bitkiler
        self.weather = "sunny"  # Hava durumu
        
        # Haritayı yükle
        self._load_map()
    
    def _load_map(self):
        """Harita dosyasını yükle veya yeni bir harita oluştur"""
        map_path = Path(f"data/maps/{self.name}.yaml")
        
        if map_path.exists():
            # Haritayı dosyadan yükle
            with open(map_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.width = data.get("width", self.width)
                self.height = data.get("height", self.height)
                self.tiles = data.get("tiles", [])
                self.objects = data.get("objects", [])
        else:
            # Yeni bir harita oluştur
            self._generate_map()
            
            # Haritayı dosyaya kaydet
            self._save_map(map_path)
    
    def _generate_map(self):
        """Rastgele bir harita oluştur"""
        self.tiles = []
        
        # Basit bir harita oluştur
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Çiftlik alanı merkeze yakın olsun
                distance_from_center = ((x - self.width/2)**2 + (y - self.height/2)**2)**0.5
                farm_radius = min(self.width, self.height) / 3
                
                if distance_from_center < farm_radius:
                    # Çiftlik alanı (daha çok toprak)
                    if random.random() < 0.8:
                        tile_type = "dirt"
                    else:
                        tile_type = "grass"
                else:
                    # Çevreleyen alan (daha çok çimen ve ağaçlar)
                    if random.random() < 0.8:
                        tile_type = "grass"
                    else:
                        tile_type = "dirt"
                
                row.append({
                    "type": tile_type,
                    "walkable": True
                })
            self.tiles.append(row)
        
        # Rastgele nesneler ekle
        for _ in range(50):  # 50 nesne
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            
            # Çiftlik alanından uzakta daha fazla nesne olsun
            distance_from_center = ((x - self.width/2)**2 + (y - self.height/2)**2)**0.5
            farm_radius = min(self.width, self.height) / 3
            
            if distance_from_center > farm_radius:
                obj_type = random.choice(["tree", "rock", "bush", "stump"])
                self.objects.append({
                    "type": obj_type,
                    "x": x,
                    "y": y,
                    "walkable": False
                })
                
                # Nesnenin olduğu tile'ı yürünemez yap
                self.tiles[y][x]["walkable"] = False
    
    def _save_map(self, map_path):
        """Haritayı dosyaya kaydet"""
        data = {
            "width": self.width,
            "height": self.height,
            "tiles": self.tiles,
            "objects": self.objects
        }
        
        # Dizini oluştur
        map_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Dosyaya yaz
        with open(map_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False)
    
    def is_walkable(self, x, y):
        """Belirtilen konumda yürünebilir mi kontrol et"""
        # Piksel konumunu tile konumuna çevir
        tile_x = int(x / self.tile_size)
        tile_y = int(y / self.tile_size)
        
        # Harita dışında mı?
        if tile_x < 0 or tile_x >= self.width or tile_y < 0 or tile_y >= self.height:
            return False
        
        # Tile yürünebilir mi?
        return self.tiles[tile_y][tile_x]["walkable"]
    
    def get_tile(self, x, y):
        """Belirtilen konumdaki tile'ı döndür"""
        # Piksel konumunu tile konumuna çevir
        tile_x = int(x / self.tile_size)
        tile_y = int(y / self.tile_size)
        
        # Harita dışında mı?
        if tile_x < 0 or tile_x >= self.width or tile_y < 0 or tile_y >= self.height:
            return None
        
        return self.tiles[tile_y][tile_x]
    
    def plant_crop(self, crop_type, x, y, player):
        """Belirtilen konuma bitki ek"""
        # Piksel konumunu tile konumuna çevir
        tile_x = int(x / self.tile_size)
        tile_y = int(y / self.tile_size)
        
        # Harita dışında mı?
        if tile_x < 0 or tile_x >= self.width or tile_y < 0 or tile_y >= self.height:
            return False
        
        # Tile uygun mu? (toprak olmalı)
        tile = self.tiles[tile_y][tile_x]
        if tile["type"] != "dirt":
            return False
        
        # Bitki zaten var mı?
        for crop in self.crops:
            if crop["x"] == tile_x and crop["y"] == tile_y:
                return False
        
        # Yeni bitki oluştur
        self.crops.append({
            "type": crop_type,
            "x": tile_x,
            "y": tile_y,
            "growth_stage": 0,  # 0-5 arası (olgun için 5)
            "watered": False,
            "days_since_watered": 0
        })
        
        return True
    
    def water_crop(self, x, y, player):
        """Belirtilen konumdaki bitkiyi sula"""
        # Piksel konumunu tile konumuna çevir
        tile_x = int(x / self.tile_size)
        tile_y = int(y / self.tile_size)
        
        # Bitki bul
        for crop in self.crops:
            if crop["x"] == tile_x and crop["y"] == tile_y:
                # Enerji tüket
                if player.use_energy(1.0):
                    crop["watered"] = True
                    crop["days_since_watered"] = 0
                    return True
        
        return False
    
    def harvest_crop(self, x, y, player):
        """Belirtilen konumdaki bitkiyi hasat et"""
        # Piksel konumunu tile konumuna çevir
        tile_x = int(x / self.tile_size)
        tile_y = int(y / self.tile_size)
        
        # Bitki bul
        for i, crop in enumerate(self.crops):
            if crop["x"] == tile_x and crop["y"] == tile_y and crop["growth_stage"] >= 5:
                # Enerji tüket
                if player.use_energy(0.5):
                    # Bitkiyi kaldır
                    self.crops.pop(i)
                    
                    # Ürün ekle (daha sonra envanter sistemi ekleyeceğiz)
                    return True
        
        return False
    
    def update(self, dt):
        """Dünyayı güncelle"""
        # Bitkileri güncelle
        for crop in self.crops:
            if crop["watered"]:
                # Büyüme ilerlemesi (gerçek oyunda gün sonunda olabilir)
                # Burada sadece basit bir örnek
                crop["growth_stage"] += dt * 0.1
                if crop["growth_stage"] > 5:
                    crop["growth_stage"] = 5
    
    def draw(self):
        """Dünyayı çiz"""
        # Kamera hesaplama (oyuncu merkezli) - burada basitleştirilmiş
        camera_x = 0
        camera_y = 0
        
        # Tile'ları çiz
        for y in range(self.height):
            for x in range(self.width):
                tile = self.tiles[y][x]
                
                # Ekran konumu
                screen_x = x * self.tile_size - camera_x
                screen_y = y * self.tile_size - camera_y
                
                # Sadece ekranda görünenleri çiz
                if (0 <= screen_x <= WIDTH and 0 <= screen_y <= HEIGHT):
                    # Sprite'ı çiz
                    tile_image = f"assets/images/tiles/{tile['type']}.png"
                    try:
                        tile_actor = Actor(tile_image)
                        tile_actor.x = screen_x + self.tile_size/2
                        tile_actor.y = screen_y + self.tile_size/2
                        tile_actor.draw()
                    except:
                        # Sprite yoksa basit renk kullan
                        color = (100, 200, 100) if tile["type"] == "grass" else (139, 69, 19)
                        rect = Rect((screen_x, screen_y), (self.tile_size, self.tile_size))
                        screen.draw.filled_rect(rect, color)
        
        # Bitkileri çiz
        for crop in self.crops:
            # Ekran konumu
            screen_x = crop["x"] * self.tile_size - camera_x + self.tile_size/2
            screen_y = crop["y"] * self.tile_size - camera_y + self.tile_size/2
            
            # Büyüme aşamasına göre sprite
            growth = int(crop["growth_stage"])
            crop_image = f"assets/images/crops/{crop['type']}_{growth}.png"
            
            try:
                crop_actor = Actor(crop_image)
                crop_actor.x = screen_x
                crop_actor.y = screen_y
                crop_actor.draw()
            except:
                # Sprite yoksa basit şekil çiz
                radius = 5 + growth * 2
                color = (0, 255, 0)  # Yeşil
                screen.draw.filled_circle((screen_x, screen_y), radius, color)
        
        # Nesneleri çiz
        for obj in self.objects:
            # Ekran konumu
            screen_x = obj["x"] * self.tile_size - camera_x + self.tile_size/2
            screen_y = obj["y"] * self.tile_size - camera_y + self.tile_size/2
            
            # Nesne türüne göre sprite
            obj_image = f"assets/images/objects/{obj['type']}.png"
            
            try:
                obj_actor = Actor(obj_image)
                obj_actor.x = screen_x
                obj_actor.y = screen_y
                obj_actor.draw()
            except:
                # Sprite yoksa basit şekil çiz
                if obj["type"] == "tree":
                    color = (0, 100, 0)  # Koyu yeşil
                    radius = 15
                elif obj["type"] == "rock":
                    color = (128, 128, 128)  # Gri
                    radius = 10
                elif obj["type"] == "bush":
                    color = (0, 150, 0)  # Yeşil
                    radius = 8
                else:
                    color = (100, 100, 100)  # Gri
                    radius = 8
                
                screen.draw.filled_circle((screen_x, screen_y), radius, color)