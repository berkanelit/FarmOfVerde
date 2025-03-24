"""
Tüm oyun karakterlerinin temel sınıfı.
"""
import math
import pygame
from pathlib import Path

class Actor:
    """Oyuncu ve NPC'lerin temel sınıfı"""
    
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.width = 32  # Piksel
        self.height = 32  # Piksel
        self.speed = 100  # Piksel/saniye
        self.direction = "down"  # "up", "down", "left", "right"
        self.moving = False
        self.frame = 0
        self.animation_time = 0
        self.animation_delay = 0.1  # Saniye
        
        # Sprite yükleme
        self.sprites = self._load_sprites()
    
    def _load_sprites(self):
        """Karakterin spritelarını yükle"""
        sprites = {}
        base_path = Path(f"assets/images/characters/{self.name}")
        
        # Her yön için sprite dosyasını arayalım
        for direction in ["up", "down", "left", "right"]:
            sprite_path = base_path / f"{direction}.png"
            
            if sprite_path.exists():
                # Pygame Zero Actor kullanarak sprite yükle
                sprites[direction] = str(sprite_path)
            else:
                # Varsayılan sprite kullan
                default_path = Path(f"assets/images/characters/default_{direction}.png")
                if default_path.exists():
                    sprites[direction] = str(default_path)
        
        return sprites
    
    def move(self, dx, dy, dt):
        """Aktörü belirtilen yönde hareket ettir"""
        # Hareket yönünü belirle
        if abs(dx) > abs(dy):
            self.direction = "right" if dx > 0 else "left"
        elif dy != 0:
            self.direction = "down" if dy > 0 else "up"
        
        # Hareket durumunu güncelle
        self.moving = dx != 0 or dy != 0
        
        # Konumu güncelle
        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt
    
    def update(self, dt):
        """Aktörü güncelle"""
        # Animasyon güncelleme
        if self.moving:
            self.animation_time += dt
            if self.animation_time >= self.animation_delay:
                self.animation_time = 0
                self.frame = (self.frame + 1) % 4  # 4 karelik animasyon varsayalım
        else:
            self.frame = 0
    
    def draw(self):
        """Aktörü çiz"""
        sprite_name = self.sprites.get(self.direction)
        
        if sprite_name:
            # Pygame Zero Actor kullanarak çiz
            actor = Actor(sprite_name)
            actor.x = self.x
            actor.y = self.y
            actor.draw()
        else:
            # Sprite yoksa basit bir dikdörtgen çiz
            rect = Rect((self.x - self.width/2, self.y - self.height/2), (self.width, self.height))
            screen.draw.filled_rect(rect, (255, 0, 0))  # Kırmızı dikdörtgen