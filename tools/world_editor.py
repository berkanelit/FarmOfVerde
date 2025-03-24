"""
Dünya editörü aracı - haritaları düzenlemek için.
"""
import sys
import os
import pygame
import yaml
from pathlib import Path

# src klasörünü Python yoluna ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# Gerekli modülleri içe aktar
from verdes.world.map import World
from verdes.systems.time import TimeSystem

# Pygame'i başlat
pygame.init()

# Sabitler
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
TILE_SIZE = 32
TOOLBAR_HEIGHT = 40
STATUSBAR_HEIGHT = 30

# Renkler
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BROWN = (139, 69, 19)

class WorldEditor:
    """Dünya editörü sınıfı"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Verde World Editor")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Editör durumu
        self.current_tool = "tile"  # "tile", "object", "erase"
        self.current_tile_type = "grass"
        self.current_object_type = "tree"
        self.camera_x = 0
        self.camera_y = 0
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Sahte yapılandırma nesnesi
        self.config = {"display": {"width": SCREEN_WIDTH, "height": SCREEN_HEIGHT}}
        
        # Dünya yükle veya oluştur
        self.world = World("farm", self.config)
        
        # Yazı tipi
        self.font = pygame.font.Font(None, 24)
    
    def run(self):
        """Ana editör döngüsü"""
        while self.running:
            # FPS sınırı
            dt = self.clock.tick(60) / 1000.0
            
            # Olayları işle
            self.handle_events()
            
            # Ekranı temizle
            self.screen.fill(BLACK)
            
            # Haritayı çiz
            self.draw_map()
            
            # Araç çubuğunu çiz
            self.draw_toolbar()
            
            # Durum çubuğunu çiz
            self.draw_statusbar()
            
            # Ekranı güncelle
            pygame.display.flip()
    
    def handle_events(self):
        """Kullanıcı girişlerini işle"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.save_map()
                elif event.key == pygame.K_1:
                    self.current_tool = "tile"
                elif event.key == pygame.K_2:
                    self.current_tool = "object"
                elif event.key == pygame.K_3:
                    self.current_tool = "erase"
                elif event.key == pygame.K_g:
                    self.current_tile_type = "grass"
                elif event.key == pygame.K_d:
                    self.current_tile_type = "dirt"
                elif event.key == pygame.K_t:
                    self.current_object_type = "tree"
                elif event.key == pygame.K_r:
                    self.current_object_type = "rock"
                elif event.key == pygame.K_b:
                    self.current_object_type = "bush"
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Sol tıklama
                    # Araç çubuğundaki tıklamaları kontrol et
                    if event.pos[1] < TOOLBAR_HEIGHT:
                        self.handle_toolbar_click(event.pos[0], event.pos[1])
                    else:
                        # Haritayı düzenle
                        self.handle_map_click(event.pos[0], event.pos[1] - TOOLBAR_HEIGHT)
                elif event.button == 3:  # Sağ tıklama
                    # Kamera sürüklemeyi başlat
                    self.dragging = True
                    self.drag_start_x, self.drag_start_y = event.pos
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:  # Sağ tıklama bırakıldı
                    self.dragging = False
            
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    # Kamerayı sürükle
                    dx = event.pos[0] - self.drag_start_x
                    dy = event.pos[1] - self.drag_start_y
                    self.camera_x -= dx
                    self.camera_y -= dy
                    self.drag_start_x, self.drag_start_y = event.pos
    
    def handle_toolbar_click(self, x, y):
        """Araç çubuğundaki tıklamayı işle"""
        # Araç seçimi için basit butonlar
        if 10 <= x < 60:
            self.current_tool = "tile"
        elif 70 <= x < 120:
            self.current_tool = "object"
        elif 130 <= x < 180:
            self.current_tool = "erase"
        
        # Tile türü seçimi
        if self.current_tool == "tile":
            if 200 <= x < 250:
                self.current_tile_type = "grass"
            elif 260 <= x < 310:
                self.current_tile_type = "dirt"
        
        # Nesne türü seçimi
        if self.current_tool == "object":
            if 200 <= x < 250:
                self.current_object_type = "tree"
            elif 260 <= x < 310:
                self.current_object_type = "rock"
            elif 320 <= x < 370:
                self.current_object_type = "bush"
            elif 380 <= x < 430:
                self.current_object_type = "stump"
    
    def handle_map_click(self, x, y):
        """Haritadaki tıklamayı işle"""
        # Ekran koordinatlarını dünya koordinatlarına çevir
        world_x = x + self.camera_x
        world_y = y + self.camera_y
        
        # Tile koordinatlarını hesapla
        tile_x = world_x // TILE_SIZE
        tile_y = world_y // TILE_SIZE
        
        # Geçerli tile sınırlarını kontrol et
        if 0 <= tile_x < self.world.width and 0 <= tile_y < self.world.height:
            if self.current_tool == "tile":
                # Tile türünü değiştir
                self.world.tiles[tile_y][tile_x]["type"] = self.current_tile_type
                self.world.tiles[tile_y][tile_x]["walkable"] = True  # Varsayılan olarak yürünebilir
            
            elif self.current_tool == "object":
                # Objeler için walkable değerini güncelleme
                self.world.tiles[tile_y][tile_x]["walkable"] = False
                
                # Mevcut bir nesne var mı kontrol et
                for i, obj in enumerate(self.world.objects):
                    if obj["x"] == tile_x and obj["y"] == tile_y:
                        # Varsa, türünü değiştir
                        self.world.objects[i]["type"] = self.current_object_type
                        return
                
                # Yoksa, yeni nesne ekle
                self.world.objects.append({
                    "type": self.current_object_type,
                    "x": tile_x,
                    "y": tile_y,
                    "walkable": False
                })
            
            elif self.current_tool == "erase":
                # Nesneleri sil
                self.world.objects = [obj for obj in self.world.objects if obj["x"] != tile_x or obj["y"] != tile_y]
                
                # Tile'ı yürünebilir yap
                self.world.tiles[tile_y][tile_x]["walkable"] = True
    
    def draw_map(self):
        """Haritayı çiz"""
        # Tile'ları çiz
        for y in range(self.world.height):
            for x in range(self.world.width):
                tile = self.world.tiles[y][x]
                
                # Ekran koordinatlarını hesapla
                screen_x = x * TILE_SIZE - self.camera_x
                screen_y = y * TILE_SIZE - self.camera_y + TOOLBAR_HEIGHT
                
                # Sadece ekranda görünenleri çiz
                if (-TILE_SIZE <= screen_x <= SCREEN_WIDTH and 
                    -TILE_SIZE <= screen_y <= SCREEN_HEIGHT):
                    # Tile arka planı
                    if tile["type"] == "grass":
                        color = (100, 200, 100)  # Yeşil
                    else:
                        color = (139, 69, 19)  # Kahverengi
                    
                    pygame.draw.rect(self.screen, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                    
                    # Tile sınırları
                    pygame.draw.rect(self.screen, (50, 50, 50), (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 1)
                    
                    # Yürünebilirlik göstergesi (kırmızı çarpı işareti)
                    if not tile["walkable"]:
                        pygame.draw.line(self.screen, RED, (screen_x, screen_y), (screen_x + TILE_SIZE, screen_y + TILE_SIZE), 2)
                        pygame.draw.line(self.screen, RED, (screen_x + TILE_SIZE, screen_y), (screen_x, screen_y + TILE_SIZE), 2)
        
        # Nesneleri çiz
        for obj in self.world.objects:
            # Ekran koordinatlarını hesapla
            screen_x = obj["x"] * TILE_SIZE - self.camera_x
            screen_y = obj["y"] * TILE_SIZE - self.camera_y + TOOLBAR_HEIGHT
            
            # Sadece ekranda görünenleri çiz
            if (-TILE_SIZE <= screen_x <= SCREEN_WIDTH and 
                -TILE_SIZE <= screen_y <= SCREEN_HEIGHT):
                # Nesne türüne göre görsel
                if obj["type"] == "tree":
                    color = (0, 100, 0)  # Koyu yeşil
                    pygame.draw.circle(self.screen, color, (screen_x + TILE_SIZE//2, screen_y + TILE_SIZE//2), TILE_SIZE//2)
                elif obj["type"] == "rock":
                    color = (128, 128, 128)  # Gri
                    pygame.draw.circle(self.screen, color, (screen_x + TILE_SIZE//2, screen_y + TILE_SIZE//2), TILE_SIZE//3)
                elif obj["type"] == "bush":
                    color = (0, 150, 0)  # Açık yeşil
                    pygame.draw.circle(self.screen, color, (screen_x + TILE_SIZE//2, screen_y + TILE_SIZE//2), TILE_SIZE//3)
                else:  # stump veya diğer
                    color = (101, 67, 33)  # Kahverengi
                    pygame.draw.circle(self.screen, color, (screen_x + TILE_SIZE//2, screen_y + TILE_SIZE//2), TILE_SIZE//4)
                
                # Nesne adı
                text = self.font.render(obj["type"][:1].upper(), True, WHITE)
                text_rect = text.get_rect(center=(screen_x + TILE_SIZE//2, screen_y + TILE_SIZE//2))
                self.screen.blit(text, text_rect)
    
    def draw_toolbar(self):
        """Araç çubuğunu çiz"""
        # Arka plan
        pygame.draw.rect(self.screen, GRAY, (0, 0, SCREEN_WIDTH, TOOLBAR_HEIGHT))
        
        # Araç butonları
        tools = [("Tile", "tile"), ("Object", "object"), ("Erase", "erase")]
        for i, (label, tool) in enumerate(tools):
            x = 10 + i * 60
            color = GREEN if self.current_tool == tool else WHITE
            pygame.draw.rect(self.screen, color, (x, 5, 50, 30), 0 if self.current_tool == tool else 2)
            text = self.font.render(label, True, BLACK if self.current_tool == tool else WHITE)
            text_rect = text.get_rect(center=(x + 25, 20))
            self.screen.blit(text, text_rect)
        
        # Tile türü butonları (sadece tile aracı seçiliyse)
        if self.current_tool == "tile":
            tile_types = [("Grass", "grass"), ("Dirt", "dirt")]
            for i, (label, tile_type) in enumerate(tile_types):
                x = 200 + i * 60
                color = GREEN if self.current_tile_type == tile_type else WHITE
                pygame.draw.rect(self.screen, color, (x, 5, 50, 30), 0 if self.current_tile_type == tile_type else 2)
                text = self.font.render(label, True, BLACK if self.current_tile_type == tile_type else WHITE)
                text_rect = text.get_rect(center=(x + 25, 20))
                self.screen.blit(text, text_rect)
        
        # Nesne türü butonları (sadece object aracı seçiliyse)
        if self.current_tool == "object":
            object_types = [("Tree", "tree"), ("Rock", "rock"), ("Bush", "bush"), ("Stump", "stump")]
            for i, (label, obj_type) in enumerate(object_types):
                x = 200 + i * 60
                color = GREEN if self.current_object_type == obj_type else WHITE
                pygame.draw.rect(self.screen, color, (x, 5, 50, 30), 0 if self.current_object_type == obj_type else 2)
                text = self.font.render(label, True, BLACK if self.current_object_type == obj_type else WHITE)
                text_rect = text.get_rect(center=(x + 25, 20))
                self.screen.blit(text, text_rect)
        
        # Kaydet butonu
        save_text = self.font.render("Save (Ctrl+S)", True, WHITE)
        save_rect = save_text.get_rect(right=SCREEN_WIDTH - 20, centery=20)
        self.screen.blit(save_text, save_rect)
    
    def draw_statusbar(self):
        """Durum çubuğunu çiz"""
        # Arka plan
        pygame.draw.rect(self.screen, GRAY, (0, SCREEN_HEIGHT - STATUSBAR_HEIGHT, SCREEN_WIDTH, STATUSBAR_HEIGHT))
        
        # Fare koordinatları
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_x = mouse_x + self.camera_x
        world_y = mouse_y - TOOLBAR_HEIGHT + self.camera_y
        tile_x = world_x // TILE_SIZE
        tile_y = world_y // TILE_SIZE
        
        if 0 <= mouse_y - TOOLBAR_HEIGHT < SCREEN_HEIGHT - TOOLBAR_HEIGHT - STATUSBAR_HEIGHT:
            coords_text = f"Tile: ({tile_x}, {tile_y}), Pixel: ({world_x}, {world_y})"
            text = self.font.render(coords_text, True, WHITE)
            self.screen.blit(text, (10, SCREEN_HEIGHT - STATUSBAR_HEIGHT + 5))
        
        # Geçerli araç ve tür
        tool_text = f"Tool: {self.current_tool.capitalize()}"
        if self.current_tool == "tile":
            tool_text += f", Type: {self.current_tile_type.capitalize()}"
        elif self.current_tool == "object":
            tool_text += f", Type: {self.current_object_type.capitalize()}"
        
        text = self.font.render(tool_text, True, WHITE)
        text_rect = text.get_rect(right=SCREEN_WIDTH - 20, centery=SCREEN_HEIGHT - STATUSBAR_HEIGHT//2)
        self.screen.blit(text, text_rect)
    
    def save_map(self):
        """Haritayı kaydet"""
        try:
            # Haritayı YAML formatında kaydet
            map_path = Path(f"data/maps/{self.world.name}.yaml")
            
            # Dizini oluştur
            map_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Verileri hazırla
            data = {
                "width": self.world.width,
                "height": self.world.height,
                "tiles": self.world.tiles,
                "objects": self.world.objects
            }
            
            # Dosyaya yaz
            with open(map_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False)
            
            print(f"Map saved to {map_path}")
        except Exception as e:
            print(f"Error saving map: {e}")

if __name__ == "__main__":
    editor = WorldEditor()
    editor.run()