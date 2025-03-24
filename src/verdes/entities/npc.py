"""
NPC (non-player character) varlık sınıfı.
"""
import random
import math
from verdes.entities.actor import Actor

class NPC(Actor):
    """NPC sınıfı - AI destekli karakterler"""
    
    def __init__(self, name, x, y):
        super().__init__(name, x, y)
        self.schedule = {}  # Günlük program
        self.mood = "neutral"  # Ruh hali
        self.friendship = 0  # Oyuncu ile arkadaşlık seviyesi (0-1000)
        self.dialogue_state = "idle"  # Konuşma durumu
        self.ai_controlled = True  # AI tarafından kontrol ediliyor mu
        self.behavior_timer = 0  # AI davranış zamanı
        self.behavior_interval = 1.0  # AI davranış aralığı (saniye)
        self.target_x = None  # Hedef X konumu
        self.target_y = None  # Hedef Y konumu
    
    def update(self, dt):
        """NPC'yi güncelle"""
        super().update(dt)
        
        # AI kontrolü
        if self.ai_controlled:
            # Davranış güncellemesi zamanı
            self.behavior_timer += dt
            if self.behavior_timer >= self.behavior_interval:
                self.behavior_timer = 0
                self._update_behavior()
            
            # Hedef varsa hareket et
            if self.target_x is not None and self.target_y is not None:
                self._move_to_target(dt)
    
    def _update_behavior(self):
        """AI davranışlarını güncelle"""
        # Basit rastgele davranış
        behavior = random.choice(["idle", "wander", "work"])
        
        if behavior == "idle":
            # Hareketsiz dur
            self.target_x = None
            self.target_y = None
            self.moving = False
        
        elif behavior == "wander":
            # Rastgele bir noktaya yürü
            self.target_x = self.x + random.randint(-100, 100)
            self.target_y = self.y + random.randint(-100, 100)
        
        elif behavior == "work":
            # Çalışma animasyonu veya davranışı
            # Burada gerçek bir oyun için daha kompleks mantık olabilir
            pass
    
    def _move_to_target(self, dt):
        """Hedefe doğru hareket et"""
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Hedefe vardık mı?
        if distance < 5:
            self.target_x = None
            self.target_y = None
            self.moving = False
            return
        
        # Hareketi normalize et
        dx = dx / distance
        dy = dy / distance
        
        # Hareket et
        self.move(dx, dy, dt)
    
    def talk(self, player, dialogue_system=None):
        """Oyuncu ile konuş"""
        # Eğer AI diyalog sistemi varsa kullan
        if dialogue_system:
            # Burada AI diyalog sistemi entegrasyonu olabilir
            return dialogue_system.get_response(self.name, "greeting")
        
        # Basit diyalog
        greetings = [
            f"Merhaba {player.name}!",
            "Güzel bir gün, değil mi?",
            "Çiftliğin nasıl gidiyor?",
            "Bugün hava çok güzel."
        ]
        return random.choice(greetings)
    
    def receive_gift(self, item):
        """Hediye al ve arkadaşlık puanı güncelle"""
        # İtem tercihlerine göre arkadaşlık değişimi
        # Gerçek bir oyunda daha kompleks olabilir
        self.friendship += 10
        
        if self.friendship > 1000:
            self.friendship = 1000
        
        if self.friendship < 0:
            self.friendship = 0
        
        # Arkadaşlık seviyesine göre tepki
        if self.friendship > 800:
            return "Bu hediyeyi çok sevdim! Teşekkür ederim!"
        elif self.friendship > 500:
            return "Çok teşekkür ederim, bu güzel bir hediye."
        elif self.friendship > 200:
            return "Teşekkürler."
        else:
            return "Hmm, tamam."