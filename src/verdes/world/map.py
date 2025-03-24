"""
Oyun dünyası harita yönetimi.
"""
import random
from pathlib import Path
import yaml
import math
from verdes.engine.camera import Camera

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
        self.weather = "sunny"  # Hava durumu (sunny, rainy, cloudy, stormy)
        self.current_season = "spring"  # Mevsim (spring, summer, fall, winter)
        
        # Kamera
        screen_width = config["display"]["width"]
        screen_height = config["display"]["height"]
        self.camera = Camera(screen_width, screen_height)
        
        # Haritayı yükle
        self._load_map()
        
        # Kameranın sınırlarını ayarla
        self.camera.set_bounds(0, 0, self.width * self.tile_size, self.height * self.tile_size)
    
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
                self.crops = data.get("crops", [])
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
            "objects": self.objects,
            "crops": self.crops
        }
        
        # Dizini oluştur
        map_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Dosyaya yaz
        with open(map_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False)
    
    def set_weather(self, weather):
        """Hava durumunu ayarla"""
        valid_weathers = ["sunny", "rainy", "cloudy", "stormy"]
        if weather in valid_weathers:
            self.weather = weather
    
    def set_season(self, season):
        """Mevsimi ayarla"""
        valid_seasons = ["spring", "summer", "fall", "winter"]
        if season in valid_seasons:
            self.current_season = season
    
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
    
    def get_object_at(self, x, y):
        """Belirtilen konumdaki nesneyi döndür"""
        # Piksel konumunu tile konumuna çevir
        tile_x = int(x / self.tile_size)
        tile_y = int(y / self.tile_size)
        
        # Nesneleri kontrol et
        for obj in self.objects:
            if obj["x"] == tile_x and obj["y"] == tile_y:
                return obj
        
        return None
    
    def get_crop_at(self, x, y):
        """Belirtilen konumdaki mahsulü döndür"""
        # Piksel konumunu tile konumuna çevir
        tile_x = int(x / self.tile_size)
        tile_y = int(y / self.tile_size)
        
        # Mahsulleri kontrol et
        for crop in self.crops:
            if crop["x"] == tile_x and crop["y"] == tile_y:
                return crop
        
        return None
    
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
        
        # Mevsim kontrolü (örnek olarak)
        seasons_for_crop = {
            "turnip": ["spring"],
            "potato": ["spring"],
            "tomato": ["summer"],
            "pumpkin": ["fall"],
            # Daha fazla bitki eklenebilir
        }
        
        # Varsayılan olarak tüm mevsimlerde ekilebilir
        valid_seasons = seasons_for_crop.get(crop_type, ["spring", "summer", "fall"])
        if self.current_season not in valid_seasons:
            return False
        
        # Yeni bitki oluştur
        self.crops.append({
            "type": crop_type,
            "x": tile_x,
            "y": tile_y,
            "growth_stage": 0,  # 0-5 arası (olgun için 5)
            "watered": False,
            "days_since_watered": 0,
            "days_growing": 0
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
                    
                    # Ürün ekle
                    harvested_item = None
                    if crop["type"] == "turnip":
                        harvested_item = "turnip"
                    elif crop["type"] == "potato":
                        harvested_item = "potato"
                    elif crop["type"] == "tomato":
                        harvested_item = "tomato"
                    elif crop["type"] == "pumpkin":
                        harvested_item = "pumpkin"
                    
                    if harvested_item:
                        player.add_to_inventory(harvested_item, 1)
                    
                    return True
        
        return False
    
    def update(self, dt):
        """Dünyayı güncelle"""
        # Kamerayı güncelle
        self.camera.update(dt)
        
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
        # Kamera hesaplama (kameranın görüş alanına göre)
        camera_x = self.camera.x - self.camera.width / 2
        camera_y = self.camera.y - self.camera.height / 2
        
        # Görünür tile aralığını hesapla
        visible_x1 = max(0, int(camera_x / self.tile_size))
        visible_y1 = max(0, int(camera_y / self.tile_size))
        visible_x2 = min(self.width, int((camera_x + self.camera.width) / self.tile_size) + 1)
        visible_y2 = min(self.height, int((camera_y + self.camera.height) / self.tile_size) + 1)
        
        # Sadece görünür tile'ları çiz
        for y in range(visible_y1, visible_y2):
            for x in range(visible_x1, visible_x2):
                tile = self.tiles[y][x]
                
                # Ekran koordinatlarını hesapla
                screen_x, screen_y = self.camera.world_to_screen(x * self.tile_size, y * self.tile_size)
                
                # Tile'ı çiz
                tile_image = f"assets/images/tiles/{tile['type']}_{self.current_season}.png"
                try:
                    tile_actor = Actor(tile_image)
                    tile_actor.x = screen_x + self.tile_size/2
                    tile_actor.y = screen_y + self.tile_size/2
                    tile_actor.draw()
                except:
                    # Alternatif tile sprite
                    alt_tile_image = f"assets/images/tiles/{tile['type']}.png"
                    try:
                        tile_actor = Actor(alt_tile_image)
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
            # Görünür aralıkta mı kontrol et
            if visible_x1 <= crop["x"] <= visible_x2 and visible_y1 <= crop["y"] <= visible_y2:
                # Ekran koordinatlarını hesapla
                screen_x, screen_y = self.camera.world_to_screen(crop["x"] * self.tile_size, crop["y"] * self.tile_size)
                
                # Büyüme aşamasına göre sprite
                growth = int(crop["growth_stage"])
                crop_image = f"assets/images/crops/{crop['type']}_{growth}.png"
                
                try:
                    crop_actor = Actor(crop_image)
                    crop_actor.x = screen_x + self.tile_size/2
                    crop_actor.y = screen_y + self.tile_size/2
                    crop_actor.draw()
                except:
                    # Sprite yoksa basit şekil çiz
                    radius = 5 + growth * 2
                    color = (0, 255, 0)  # Yeşil
                    screen.draw.filled_circle((screen_x + self.tile_size/2, screen_y + self.tile_size/2), radius, color)
                
                # Sulama durumu göstergesi
                if crop["watered"]:
                    try:
                        water_actor = Actor("assets/images/tiles/water_overlay.png")
                        water_actor.x = screen_x + self.tile_size/2
                        water_actor.y = screen_y + self.tile_size/2
                        water_actor.draw()
                    except:
                        # Sprite yoksa basit gösterge
                        screen.draw.circle((screen_x + self.tile_size/2, screen_y + self.tile_size/2), 
                                          radius + 2, (0, 0, 255))
        
        # Nesneleri çiz
        for obj in self.objects:
            # Görünür aralıkta mı kontrol et
            if visible_x1 <= obj["x"] <= visible_x2 and visible_y1 <= obj["y"] <= visible_y2:
                # Ekran koordinatlarını hesapla
                screen_x, screen_y = self.camera.world_to_screen(obj["x"] * self.tile_size, obj["y"] * self.tile_size)
                
                # Mevsime ve türe göre nesne sprite
                obj_season = "" if obj["type"] in ["rock", "stump"] else f"_{self.current_season}"
                obj_image = f"assets/images/objects/{obj['type']}{obj_season}.png"
                
                try:
                    obj_actor = Actor(obj_image)
                    obj_actor.x = screen_x + self.tile_size/2
                    obj_actor.y = screen_y + self.tile_size/2
                    obj_actor.draw()
                except:
                    # Alternatif nesne sprite
                    alt_obj_image = f"assets/images/objects/{obj['type']}.png"
                    try:
                        obj_actor = Actor(alt_obj_image)
                        obj_actor.x = screen_x + self.tile_size/2
                        obj_actor.y = screen_y + self.tile_size/2
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
                        
                        screen.draw.filled_circle((screen_x + self.tile_size/2, screen_y + self.tile_size/2), radius, color)
        
        # Hava durumu efektleri
        if self.weather == "rainy":
            self._draw_rain()
        elif self.weather == "stormy":
            self._draw_storm()
    
    def _draw_rain(self):
        """Yağmur efekti çiz"""
        rain_count = 100
        screen_width = self.camera.width
        screen_height = self.camera.height
        
        for _ in range(rain_count):
            x = random.randint(0, screen_width)
            y = random.randint(0, screen_height)
            length = random.randint(5, 10)
            
            # Yağmur damlası
            color = (100, 100, 255, 150)  # Açık mavi, yarı saydam
            end_x = x + length // 2
            end_y = y + length
            
            screen.draw.line((x, y), (end_x, end_y), color)
    
    def _draw_storm(self):
        """Fırtına efekti çiz (yağmur + şimşek)"""
        # Yağmur çiz
        self._draw_rain()
        
        # Rastgele şimşek
        if random.random() < 0.02:  # %2 ihtimalle
            flash_alpha = random.randint(20, 80)  # Parlaklık
            flash_color = (255, 255, 200, flash_alpha)
            
            # Tüm ekranı kaplayan yarı saydam beyaz katman
            screen.draw.filled_rect(
                Rect(0, 0, self.camera.width, self.camera.height),
                flash_color
            )