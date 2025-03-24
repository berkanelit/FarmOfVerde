"""
Kamera sistemi - harita görünümü ve izleme.
"""
from typing import Tuple

class Camera:
    """Oyun kamerası - haritayı oyuncuya göre görüntüler"""
    
    def __init__(self, width: int, height: int):
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.target_x = 0
        self.target_y = 0
        self.smooth = True
        self.smooth_factor = 5.0  # Daha büyük değerler, daha yavaş takip
        self.bounds = None  # (min_x, min_y, max_x, max_y)
    
    def set_position(self, x: int, y: int) -> None:
        """Kamerayı belirtilen konuma taşır"""
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
    
    def set_target(self, x: int, y: int) -> None:
        """Kameranın hedefini belirtilen konuma ayarlar"""
        self.target_x = x
        self.target_y = y
    
    def set_bounds(self, min_x: int, min_y: int, max_x: int, max_y: int) -> None:
        """Kameranın sınırlarını ayarlar"""
        self.bounds = (min_x, min_y, max_x, max_y)
    
    def update(self, dt: float) -> None:
        """Kamerayı günceller"""
        if self.smooth:
            # Hedef konuma doğru yumuşak hareket
            self.x += (self.target_x - self.x) * min(1.0, dt * self.smooth_factor)
            self.y += (self.target_y - self.y) * min(1.0, dt * self.smooth_factor)
        else:
            # Anında hedef konuma geç
            self.x = self.target_x
            self.y = self.target_y
        
        # Sınırları uygula
        if self.bounds:
            min_x, min_y, max_x, max_y = self.bounds
            
            # Kamera genişliği/yüksekliği hesaba katılır
            self.x = max(min_x + self.width / 2, min(max_x - self.width / 2, self.x))
            self.y = max(min_y + self.height / 2, min(max_y - self.height / 2, self.y))
    
    def follow(self, entity, offset_x: int = 0, offset_y: int = 0) -> None:
        """Belirtilen varlığı takip eder"""
        self.set_target(entity.x + offset_x, entity.y + offset_y)
    
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """Dünya koordinatlarını ekran koordinatlarına dönüştürür"""
        screen_x = world_x - self.x + self.width / 2
        screen_y = world_y - self.y + self.height / 2
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Ekran koordinatlarını dünya koordinatlarına dönüştürür"""
        world_x = screen_x + self.x - self.width / 2
        world_y = screen_y + self.y - self.height / 2
        return world_x, world_y