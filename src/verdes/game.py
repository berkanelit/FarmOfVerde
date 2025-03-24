"""
Verde oyunu ana modülü.
Pygame Zero entegrasyonu ve oyun durumu yönetimi.
"""
import os
import random
import yaml
from pathlib import Path

# Pygame Zero global değişkenleri
# Bunlar pgzrun tarafından otomatik olarak tanınır
WIDTH = 800
HEIGHT = 600
TITLE = "Verde - AI Farming Simulator"

# Oyun durumu
game_state = "menu"  # "menu", "playing", "paused"
world = None
player = None
npcs = []
time_system = None

def setup_game():
    """Oyun öğelerini yükle ve ayarla"""
    global world, player, npcs, time_system
    
    # Gerekli dizinlerin varlığını kontrol et
    ensure_directories_exist()
    
    # Yapılandırmayı yükle
    config = load_config()
    
    # Oyun bileşenlerini içe aktar
    from verdes.world.map import World
    from verdes.entities.player import Player
    from verdes.entities.npc import NPC
    from verdes.systems.time import TimeSystem
    
    # Dünya oluştur
    world = World("farm", config)
    
    # Oyuncu oluştur
    player = Player(WIDTH // 2, HEIGHT // 2)
    
    # Zaman sistemi oluştur
    time_system = TimeSystem()
    
    # NPC'ler oluştur
    npcs = [
        NPC("farmer", 200, 200),
        NPC("villager", 500, 300),
    ]

def load_config():
    """Oyun yapılandırmasını yükle veya varsayılanlara dön"""
    config_path = Path("data/config/game_config.yaml")
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    # Varsayılan yapılandırma
    default_config = {
        "display": {
            "width": WIDTH,
            "height": HEIGHT,
            "fullscreen": False,
        },
        "audio": {
            "music_volume": 0.5,
            "sfx_volume": 0.7,
        },
        "gameplay": {
            "day_length_minutes": 15,  # Gerçek dakika cinsinden 
            "season_days": 28,
        },
        "ai": {
            "use_simple_ai": True,  # Basit AI kullan (daha hafif)
            "dialogue_model": "small",  # 'small', 'medium', 'none'
        }
    }
    
    # Dizini oluştur ve varsayılan yapılandırmayı kaydet
    os.makedirs(config_path.parent, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(default_config, f, default_flow_style=False)
    
    return default_config

def ensure_directories_exist():
    """Gerekli dizin yapısının varlığını kontrol et ve oluştur"""
    dirs = [
        "assets/images/characters",
        "assets/images/tiles",
        "assets/images/items",
        "assets/images/ui",
        "assets/sounds",
        "assets/fonts",
        "data/config",
        "data/maps",
        "data/ai_models",
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

# Pygame Zero fonksiyonları

def draw():
    """Her karede çağrılır - ekran çizimi"""
    screen.clear()
    
    if game_state == "menu":
        draw_menu()
    elif game_state == "playing":
        draw_game()
    elif game_state == "paused":
        draw_game()
        draw_pause()

def update(dt):
    """Her karede çağrılır - oyun mantığı güncellemesi"""
    if game_state == "playing":
        # Zaman sistemi güncelle
        if time_system:
            time_system.update(dt)
        
        # Oyuncu güncelle
        if player:
            player.update(dt)
        
        # NPC'leri güncelle
        for npc in npcs:
            npc.update(dt)

def on_key_down(key):
    """Tuşa basıldığında çağrılır"""
    global game_state
    
    if game_state == "menu":
        if key == keys.SPACE:
            game_state = "playing"
        elif key == keys.ESCAPE:
            exit()
    
    elif game_state == "playing":
        if key == keys.ESCAPE:
            game_state = "paused"
    
    elif game_state == "paused":
        if key == keys.ESCAPE:
            game_state = "menu"
        elif key == keys.SPACE:
            game_state = "playing"

def draw_menu():
    """Ana menüyü çiz"""
    screen.fill((50, 100, 50))  # Yeşilimsi arka plan
    
    screen.draw.text("VERDE", center=(WIDTH/2, HEIGHT/3), fontsize=60, color="white")
    screen.draw.text("AI Destekli Çiftlik Simülasyonu", center=(WIDTH/2, HEIGHT/3 + 50), fontsize=30, color="white")
    
    screen.draw.text("SPACE tuşuna basarak başlayın", center=(WIDTH/2, HEIGHT/3 + 150), fontsize=20, color="white")
    screen.draw.text("ESC tuşuna basarak çıkın", center=(WIDTH/2, HEIGHT/3 + 180), fontsize=20, color="white")

def draw_game():
    """Oyun ekranını çiz"""
    # Dünyayı çiz
    if world:
        world.draw()
    
    # NPC'leri çiz
    for npc in npcs:
        npc.draw()
    
    # Oyuncuyu çiz
    if player:
        player.draw()
    
    # HUD'u çiz
    draw_hud()

def draw_pause():
    """Duraklatma menüsünü çiz"""
    # Yarı saydam örtü
    screen.draw.filled_rect(Rect(0, 0, WIDTH, HEIGHT), (0, 0, 0, 128))
    
    screen.draw.text("DURAKLATILDI", center=(WIDTH/2, HEIGHT/2 - 30), fontsize=40, color="white")
    screen.draw.text("SPACE tuşuna basarak devam edin", center=(WIDTH/2, HEIGHT/2 + 20), fontsize=20, color="white")
    screen.draw.text("ESC tuşuna basarak menüye dönün", center=(WIDTH/2, HEIGHT/2 + 50), fontsize=20, color="white")

def draw_hud():
    """Oyun içi HUD'u çiz"""
    if time_system:
        # Zaman bilgisi
        time_text = f"Gün {time_system.day}, {time_system.hour:02d}:{time_system.minute:02d}"
        screen.draw.text(time_text, topright=(WIDTH-10, 10), fontsize=20, color="white")
    
    if player:
        # Enerji bilgisi
        energy_text = f"Enerji: {player.energy}/{player.max_energy}"
        screen.draw.text(energy_text, topleft=(10, 10), fontsize=20, color="white")
        
        # Para bilgisi
        money_text = f"Para: ${player.money}"
        screen.draw.text(money_text, topleft=(10, 40), fontsize=20, color="white")

# Ana modül ise oyunu başlat
if __name__ == "__main__":
    setup_game()