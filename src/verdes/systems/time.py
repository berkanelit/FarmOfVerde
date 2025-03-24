"""
Oyun zaman sistemi.
"""

class TimeSystem:
    """Zaman, gün ve mevsim yönetimi"""
    
    def __init__(self):
        self.minute = 0
        self.hour = 6  # Oyun 6:00'da başlar
        self.day = 1
        self.season = 0  # 0=İlkbahar, 1=Yaz, 2=Sonbahar, 3=Kış
        self.year = 1
        self.seasons = ["İlkbahar", "Yaz", "Sonbahar", "Kış"]
        self.day_length = 15 * 60  # Gerçek saniyeler (15 dakika = 1 oyun günü)
        self.time_scale = 1.0  # Zaman akış hızı çarpanı
        self.paused = False
    
    def update(self, dt):
        """Zamanı güncelle"""
        if self.paused:
            return
        
        # Gerçek-zaman ölçeği (15 dakikada 1 gün)
        real_dt = dt * self.time_scale
        
        # Bir günü (6:00-0:00 arası) 15 dakikada tamamla
        game_minute_per_second = (18 * 60) / (self.day_length)
        
        # Zamanı ilerlet
        self.minute += game_minute_per_second * real_dt * 60
        
        # Dakikalar saate dönüşür
        if self.minute >= 60:
            self.hour += int(self.minute / 60)
            self.minute %= 60
            
            # Saat gün değişimi
            if self.hour >= 24:
                self.day += 1
                self.hour %= 24
                
                # Yeni gün olayları
                self._on_new_day()
    
    def _on_new_day(self):
        """Yeni gün başladığında çağrılır"""
        # 28 gün sonra sezon değişimi
        if self.day > 28:
            self.day = 1
            self.season = (self.season + 1) % 4
            
            # Yeni sezon
            if self.season == 0:
                self.year += 1
    
    def get_time_of_day(self):
        """Günün zamanını insan tarafından okunabilir biçimde döndür"""
        return f"{self.hour:02d}:{self.minute:02d}"
    
    def get_date(self):
        """Tarihi insan tarafından okunabilir biçimde döndür"""
        return f"{self.seasons[self.season]} {self.day}, Yıl {self.year}"
    
    def is_day(self):
        """Gündüz mü?"""
        return 6 <= self.hour < 20
    
    def set_time_scale(self, scale):
        """Zaman akış hızını ayarla"""
        self.time_scale = min(max(0.1, scale), 10.0)  # 0.1x - 10x sınırla
    
    def pause(self):
        """Zamanı duraklat"""
        self.paused = True
    
    def resume(self):
        """Zamanı devam ettir"""
        self.paused = False