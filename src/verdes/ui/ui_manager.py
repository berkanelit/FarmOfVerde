"""
UI Yöneticisi - arayüz öğelerini ve ekranları yönetir.
"""
from typing import Dict, List, Callable, Optional, Any, Tuple
import pygame
import os
from pathlib import Path

class UIElement:
    """UI öğesi temel sınıfı"""
    
    def __init__(self, x: int, y: int, width: int, height: int, visible: bool = True):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = visible
        self.enabled = True
        self.parent = None
    
    def set_position(self, x: int, y: int) -> None:
        """Öğenin konumunu ayarla"""
        self.x = x
        self.y = y
    
    def set_size(self, width: int, height: int) -> None:
        """Öğenin boyutunu ayarla"""
        self.width = width
        self.height = height
    
    def contains_point(self, x: int, y: int) -> bool:
        """Belirtilen nokta bu öğenin içinde mi?"""
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)
    
    def update(self, dt: float) -> None:
        """Öğeyi güncelle"""
        pass
    
    def draw(self, surface) -> None:
        """Öğeyi çiz"""
        pass
    
    def handle_event(self, event) -> bool:
        """Olayı işle, işlenirse True döndür"""
        return False

class Button(UIElement):
    """Düğme UI öğesi"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str = "",
                 text_color: Tuple[int, int, int] = (255, 255, 255),
                 bg_color: Tuple[int, int, int] = (100, 100, 100),
                 hover_color: Tuple[int, int, int] = (150, 150, 150),
                 disabled_color: Tuple[int, int, int] = (50, 50, 50),
                 border_radius: int = 5,
                 on_click: Optional[Callable[[], None]] = None):
        super().__init__(x, y, width, height)
        self.text = text
        self.text_color = text_color
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.disabled_color = disabled_color
        self.border_radius = border_radius
        self.on_click = on_click
        self.hovered = False
        self.font = None
        self._init_font()
    
    def _init_font(self) -> None:
        """Yazı tipini başlat"""
        try:
            self.font = pygame.font.Font(None, 24)  # Pygame'in varsayılan yazı tipi, 24pt
        except:
            pass
    
    def update(self, dt: float) -> None:
        """Düğmeyi güncelle, hover durumunu kontrol et"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.hovered = self.enabled and self.contains_point(mouse_x, mouse_y)
    
    def draw(self, surface) -> None:
        """Düğmeyi çiz"""
        if not self.visible:
            return
        
        # Arka plan rengi
        color = self.bg_color
        if not self.enabled:
            color = self.disabled_color
        elif self.hovered:
            color = self.hover_color
        
        # Düğme arka planı
        pygame.draw.rect(surface, color, 
                         (self.x, self.y, self.width, self.height),
                         0, self.border_radius)
        
        # Düğme metni
        if self.text and self.font:
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=(self.x + self.width/2, self.y + self.height/2))
            surface.blit(text_surf, text_rect)
    
    def handle_event(self, event) -> bool:
        """Fare olaylarını işle"""
        if not self.visible or not self.enabled:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Sol fare tıklaması
            if self.contains_point(event.pos[0], event.pos[1]):
                if self.on_click:
                    self.on_click()
                return True
        
        return False

class Panel(UIElement):
    """Panel UI öğesi, diğer öğeleri içerebilir"""
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 bg_color: Optional[Tuple[int, int, int]] = (50, 50, 50, 200),
                 border_color: Optional[Tuple[int, int, int]] = None,
                 border_width: int = 0,
                 border_radius: int = 0):
        super().__init__(x, y, width, height)
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_width = border_width
        self.border_radius = border_radius
        self.children: List[UIElement] = []
    
    def add_child(self, element: UIElement) -> None:
        """Panel'e çocuk öğe ekle"""
        element.parent = self
        self.children.append(element)
    
    def update(self, dt: float) -> None:
        """Panel ve tüm çocuklarını güncelle"""
        if not self.visible:
            return
        
        for child in self.children:
            child.update(dt)
    
    def draw(self, surface) -> None:
        """Panel ve tüm çocuklarını çiz"""
        if not self.visible:
            return
        
        # Panel arka planı
        if self.bg_color:
            pygame.draw.rect(surface, self.bg_color, 
                            (self.x, self.y, self.width, self.height),
                            0, self.border_radius)
        
        # Panel sınırı
        if self.border_color and self.border_width > 0:
            pygame.draw.rect(surface, self.border_color, 
                            (self.x, self.y, self.width, self.height),
                            self.border_width, self.border_radius)
        
        # Çocuk öğeleri çiz
        for child in self.children:
            # Çocuğun global konumunu hesapla
            original_x, original_y = child.x, child.y
            child.x += self.x
            child.y += self.y
            
            child.draw(surface)
            
            # Çocuğun orijinal konumunu geri yükle
            child.x, child.y = original_x, original_y
    
    def handle_event(self, event) -> bool:
        """Panel ve tüm çocukları için olayları işle"""
        if not self.visible or not self.enabled:
            return False
        
        # Fare olayları için konum kontrolü
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            if not self.contains_point(event.pos[0], event.pos[1]):
                return False
        
        # Çocuklara olayı ilet (tersten, üstteki öğeler önce)
        for child in reversed(self.children):
            # Olay konumunu çocuğun koordinat sistemine çevir
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                original_pos = event.pos
                modified_event = pygame.event.Event(event.type, 
                                                   pos=(event.pos[0] - self.x, event.pos[1] - self.y),
                                                   **{k: v for k, v in event.__dict__.items() if k != 'pos'})
                if child.handle_event(modified_event):
                    return True
            else:
                if child.handle_event(event):
                    return True
        
        return False

class Label(UIElement):
    """Etiket UI öğesi"""
    
    def __init__(self, x: int, y: int, text: str = "",
                 text_color: Tuple[int, int, int] = (255, 255, 255),
                 font_size: int = 24,
                 font_name: Optional[str] = None,
                 align: str = "left"):  # "left", "center", "right"
        super().__init__(x, y, 0, 0)  # Boyut, metnin boyutuna göre otomatik ayarlanacak
        self.text = text
        self.text_color = text_color
        self.font_size = font_size
        self.font_name = font_name
        self.align = align
        self.font = None
        self._init_font()
        self._update_size()
    
    def _init_font(self) -> None:
        """Yazı tipini başlat"""
        try:
            if self.font_name and os.path.exists(f"assets/fonts/{self.font_name}"):
                self.font = pygame.font.Font(f"assets/fonts/{self.font_name}", self.font_size)
            else:
                self.font = pygame.font.Font(None, self.font_size)  # Pygame'in varsayılan yazı tipi
        except:
            pass
    
    def _update_size(self) -> None:
        """Metin boyutuna göre öğe boyutunu güncelle"""
        if self.font and self.text:
            text_surf = self.font.render(self.text, True, self.text_color)
            self.width, self.height = text_surf.get_size()
    
    def set_text(self, text: str) -> None:
        """Etiketteki metni değiştir"""
        self.text = text
        self._update_size()
    
    def draw(self, surface) -> None:
        """Etiketi çiz"""
        if not self.visible or not self.text or not self.font:
            return
        
        text_surf = self.font.render(self.text, True, self.text_color)
        
        if self.align == "center":
            text_rect = text_surf.get_rect(center=(self.x + self.width/2, self.y + self.height/2))
        elif self.align == "right":
            text_rect = text_surf.get_rect(topright=(self.x + self.width, self.y))
        else:  # "left" veya diğer
            text_rect = text_surf.get_rect(topleft=(self.x, self.y))
        
        surface.blit(text_surf, text_rect)

class UIManager:
    """UI yöneticisi sınıfı"""
    
    def __init__(self):
        self.elements: Dict[str, UIElement] = {}
        self.active_screens: List[str] = []  # Aktif ekranlar (üst üste gösterme için)
    
    def add_element(self, name: str, element: UIElement) -> None:
        """UI öğesi ekle"""
        self.elements[name] = element
    
    def get_element(self, name: str) -> Optional[UIElement]:
        """Belirtilen adlı UI öğesini döndür"""
        return self.elements.get(name)
    
    def show_screen(self, screen_name: str) -> None:
        """Belirtilen ekranı göster"""
        if screen_name in self.elements:
            if screen_name not in self.active_screens:
                self.active_screens.append(screen_name)
    
    def hide_screen(self, screen_name: str) -> None:
        """Belirtilen ekranı gizle"""
        if screen_name in self.active_screens:
            self.active_screens.remove(screen_name)
    
    def toggle_screen(self, screen_name: str) -> None:
        """Belirtilen ekranı aç/kapat"""
        if screen_name in self.active_screens:
            self.hide_screen(screen_name)
        else:
            self.show_screen(screen_name)
    
    def update(self, dt: float) -> None:
        """Tüm aktif UI öğelerini güncelle"""
        for screen_name in self.active_screens:
            screen = self.elements.get(screen_name)
            if screen and screen.visible:
                screen.update(dt)
    
    def draw(self, surface) -> None:
        """Tüm aktif UI öğelerini çiz"""
        for screen_name in self.active_screens:
            screen = self.elements.get(screen_name)
            if screen and screen.visible:
                screen.draw(surface)
    
    def handle_event(self, event) -> bool:
        """Tüm aktif UI öğeleri için olayları işle"""
        # Olayları tersten işle (en üstteki ekrandan başla)
        for screen_name in reversed(self.active_screens):
            screen = self.elements.get(screen_name)
            if screen and screen.visible and screen.enabled:
                if screen.handle_event(event):
                    return True
        
        return False
    
    def create_inventory_ui(self, inventory, item_db, 
                           x: int = 100, y: int = 100, 
                           cols: int = 5, rows: int = 4,
                           slot_size: int = 40, padding: int = 4) -> Panel:
        """Envanter UI'ı oluştur"""
        inv_width = cols * (slot_size + padding) + padding
        inv_height = rows * (slot_size + padding) + padding
        
        panel = Panel(x, y, inv_width, inv_height, bg_color=(50, 50, 50, 220), 
                     border_color=(100, 100, 100), border_width=2, border_radius=5)
        
        # Envanteri doldurmak için bir konum fonksiyonu eklenebilir
        
        return panel