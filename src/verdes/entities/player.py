"""
Oyuncu varlık sınıfı.
"""
from verdes.entities.actor import Actor

class Player(Actor):
    """Oyuncu sınıfı"""
    
    def __init__(self, x, y):
        super().__init__("player", x, y)
        self.speed = 150  # Biraz daha hızlı
        self.max_energy = 100
        self.energy = self.max_energy
        self.money = 500
        self.inventory = []
        self.active_tool = None
        self.interaction_range = 50  # Piksel
    
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
            self.move(dx, dy, dt)
            
            # Hareket için enerji tüket (çok az)
            self.use_energy(0.05 * dt)
    
    def use_energy(self, amount):
        """Enerji tüket"""
        self.energy = max(0, self.energy - amount)
    
    def restore_energy(self, amount):
        """Enerji yenile"""
        self.energy = min(self.max_energy, self.energy + amount)
    
    def use_tool(self, tool_name):
        """Alet kullan"""
        # Farklı aletler için farklı enerji tüketimi
        energy_costs = {
            "hoe": 2.0,      # Çapa
            "watering_can": 1.0,  # Sulama kabı
            "axe": 3.0,      # Balta
            "pickaxe": 4.0,  # Kazma
            "scythe": 2.0,   # Tırpan
        }
        
        # Alet için enerji maliyeti
        energy_cost = energy_costs.get(tool_name, 1.0)
        
        # Yeterli enerji var mı?
        if self.energy >= energy_cost:
            # Enerji tüket
            self.use_energy(energy_cost)
            return True
        
        return False
    
    def add_to_inventory(self, item):
        """Envantere öğe ekle"""
        self.inventory.append(item)
    
    def add_money(self, amount):
        """Para ekle"""
        self.money += amount
    
    def spend_money(self, amount):
        """Para harca"""
        if self.money >= amount:
            self.money -= amount
            return True
        return False