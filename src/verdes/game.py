"""
Verde oyunu ana modülü.
Pygame Zero entegrasyonu ve oyun durumu yönetimi.
"""
import os
import random
import yaml
from pathlib import Path

# Oyun bileşenlerini içe aktar
from verdes.world.map import World
from verdes.entities.player import Player
from verdes.entities.npc import NPC
from verdes.systems.time import TimeSystem
from verdes.systems.economy import EconomySystem
from verdes.systems.inventory import ItemDatabase
from verdes.ui.ui_manager import UIManager, Panel, Button, Label
from verdes.ai.dialogue_system import DialogueSystem
from verdes.ai.behavior_model import BehaviorModel

# Pygame Zero global değişkenleri
# Bunlar pgzrun tarafından otomatik olarak tanınır
WIDTH = 800
HEIGHT = 600
TITLE = "Verde - AI Farming Simulator"

# Oyun durumu ve nesneleri
game_state = "menu"  # "menu", "playing", "paused", "inventory", "shop", "dialogue"
world = None
player = None
npcs = []
time_system = None
economy_system = None
item_db = None
ui_manager = None
dialogue_system = None
behavior_model = None

# UI durumu
selected_menu_item = 0
show_fps = False
show_debug = False
last_fps = 0
fps_sum = 0
fps_count = 0

def setup_game():
    """Oyun öğelerini yükle ve ayarla"""
    global world, player, npcs, time_system, economy_system, item_db, ui_manager, dialogue_system, behavior_model
    
    # Gerekli dizinlerin varlığını kontrol et
    ensure_directories_exist()
    
    # Yapılandırmayı yükle
    config = load_config()
    
    # Veritabanı ve ekonomi sistemini yükle
    item_db = ItemDatabase()
    economy_system = EconomySystem()
    
    # Dünya oluştur
    world = World("farm", config)
    
    # Yapay zeka sistemleri
    dialogue_system = DialogueSystem(config)
    behavior_model = BehaviorModel(config)
    
    # Oyuncu oluştur
    player = Player(WIDTH // 2, HEIGHT // 2)
    
    # Zaman sistemi oluştur
    time_system = TimeSystem()
    
    # UI yöneticisi
    ui_manager = UIManager()
    setup_ui()
    
    # NPC'ler oluştur
    create_npcs()

def create_npcs():
    """NPC'leri oluştur"""
    global npcs
    
    # Örnek NPC'ler
    npc_data = [
        {"name": "farmer", "x": 200, "y": 200, "type": "villager"},
        {"name": "shopkeeper", "x": 500, "y": 300, "type": "shopkeeper"},
        {"name": "miner", "x": 350, "y": 250, "type": "villager"},
        {"name": "fisher", "x": 650, "y": 150, "type": "villager"}
    ]
    
    npcs = []
    for data in npc_data:
        npc = NPC(data["name"], data["x"], data["y"])
        npc.npc_type = data["type"]
        npcs.append(npc)

def setup_ui():
    """UI öğelerini oluştur"""
    global ui_manager
    
    if not ui_manager:
        return
    
    # Ana menü
    main_menu = Panel(0, 0, WIDTH, HEIGHT, bg_color=(0, 0, 0, 180))
    
    # Menü başlığı
    title_label = Label(WIDTH // 2, HEIGHT // 4, "VERDE", 
                      text_color=(255, 255, 255), font_size=60, align="center")
    title_label.x -= title_label.width // 2
    
    subtitle_label = Label(WIDTH // 2, HEIGHT // 4 + 60, "AI Destekli Çiftlik Simülatörü", 
                         text_color=(200, 255, 200), font_size=24, align="center")
    subtitle_label.x -= subtitle_label.width // 2
    
    # Menü butonları
    start_button = Button(WIDTH // 2 - 100, HEIGHT // 2, 200, 40, "Yeni Oyun", 
                        bg_color=(50, 150, 50), hover_color=(70, 170, 70),
                        on_click=lambda: start_new_game())
    
    load_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 50, 200, 40, "Oyun Yükle", 
                       bg_color=(50, 100, 150), hover_color=(70, 120, 170),
                       on_click=lambda: load_game())
    
    settings_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 40, "Ayarlar", 
                           bg_color=(150, 100, 50), hover_color=(170, 120, 70),
                           on_click=lambda: show_settings())
    
    exit_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 150, 200, 40, "Çıkış", 
                       bg_color=(150, 50, 50), hover_color=(170, 70, 70),
                       on_click=lambda: exit_game())
    
    # Menüye butonları ekle
    main_menu.add_child(title_label)
    main_menu.add_child(subtitle_label)
    main_menu.add_child(start_button)
    main_menu.add_child(load_button)
    main_menu.add_child(settings_button)
    main_menu.add_child(exit_button)
    
    # UI yöneticisine ekle
    ui_manager.add_element("main_menu", main_menu)
    
    # Duraklatma menüsü
    pause_menu = Panel(WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2, bg_color=(0, 0, 0, 200),
                      border_color=(100, 100, 100), border_width=2, border_radius=10)
    
    pause_title = Label(WIDTH // 2, HEIGHT // 4 + 30, "DURAKLATILDI", 
                       text_color=(255, 255, 255), font_size=30, align="center")
    pause_title.x -= pause_title.width // 2
    
    resume_button = Button(WIDTH // 2 - 80, HEIGHT // 2 - 30, 160, 40, "Devam Et", 
                         bg_color=(50, 150, 50), hover_color=(70, 170, 70),
                         on_click=lambda: resume_game())
    
    save_button = Button(WIDTH // 2 - 80, HEIGHT // 2 + 20, 160, 40, "Kaydet", 
                        bg_color=(50, 100, 150), hover_color=(70, 120, 170),
                        on_click=lambda: save_game())
    
    quit_button = Button(WIDTH // 2 - 80, HEIGHT // 2 + 70, 160, 40, "Menüye Dön", 
                        bg_color=(150, 50, 50), hover_color=(170, 70, 70),
                        on_click=lambda: return_to_menu())
    
    pause_menu.add_child(pause_title)
    pause_menu.add_child(resume_button)
    pause_menu.add_child(save_button)
    pause_menu.add_child(quit_button)
    
    ui_manager.add_element("pause_menu", pause_menu)
    
    # Envanter UI
    inventory_panel = Panel(WIDTH // 8, HEIGHT // 8, WIDTH * 3 // 4, HEIGHT * 3 // 4, 
                         bg_color=(30, 30, 30, 230), border_color=(100, 100, 100), 
                         border_width=2, border_radius=5)
    
    inventory_title = Label(WIDTH // 2, HEIGHT // 8 + 20, "ENVANTER", 
                          text_color=(255, 255, 255), font_size=24, align="center")
    inventory_title.x -= inventory_title.width // 2
    
    close_inv_button = Button(WIDTH * 7 // 8 - 30, HEIGHT // 8 + 10, 20, 20, "X", 
                            bg_color=(150, 50, 50), hover_color=(170, 70, 70),
                            on_click=lambda: close_inventory())
    
    inventory_panel.add_child(inventory_title)
    inventory_panel.add_child(close_inv_button)
    
    ui_manager.add_element("inventory", inventory_panel)
    
    # Diyalog UI
    dialogue_panel = Panel(50, HEIGHT - 180, WIDTH - 100, 160, 
                          bg_color=(20, 20, 20, 230), border_color=(100, 100, 100),
                          border_width=2, border_radius=10)
    
    npc_name_label = Label(70, HEIGHT - 170, "NPC", 
                          text_color=(200, 200, 255), font_size=18, align="left")
    
    dialogue_text = Label(70, HEIGHT - 140, "Diyalog metni burada görünecek...", 
                         text_color=(255, 255, 255), font_size=16, align="left")
    
    next_button = Button(WIDTH - 130, HEIGHT - 60, 80, 30, "Devam", 
                        bg_color=(70, 70, 120), hover_color=(90, 90, 140),
                        on_click=lambda: advance_dialogue())
    
    dialogue_panel.add_child(npc_name_label)
    dialogue_panel.add_child(dialogue_text)
    dialogue_panel.add_child(next_button)
    
    ui_manager.add_element("dialogue", dialogue_panel)
    
    # Başlangıçta gösterilecek ekranlar
    ui_manager.show_screen("main_menu")

# Oyun aksiyon fonksiyonları

def start_new_game():
    """Yeni oyun başlat"""
    global game_state
    game_state = "playing"
    ui_manager.hide_screen("main_menu")

def load_game():
    """Kaydedilmiş oyunu yükle"""
    # TODO: Oyun yükleme işlevi
    pass

def save_game():
    """Oyunu kaydet"""
    # TODO: Oyun kaydetme işlevi
    pass

def show_settings():
    """Ayarlar menüsünü göster"""
    # TODO: Ayarlar menüsü
    pass

def exit_game():
    """Oyundan çık"""
    exit()

def resume_game():
    """Oyuna devam et"""
    global game_state
    game_state = "playing"
    ui_manager.hide_screen("pause_menu")

def return_to_menu():
    """Ana menüye dön"""
    global game_state
    game_state = "menu"
    ui_manager.hide_screen("pause_menu")
    ui_manager.show_screen("main_menu")

def show_inventory():
    """Envanteri göster"""
    global game_state
    game_state = "inventory"
    ui_manager.show_screen("inventory")

def close_inventory():
    """Envanteri kapat"""
    global game_state
    game_state = "playing"
    ui_manager.hide_screen("inventory")

def show_dialogue(npc):
    """Diyalog ekranını göster"""
    global game_state
    
    if not dialogue_system:
        return
    
    game_state = "dialogue"
    ui_manager.show_screen("dialogue")
    
    # NPC adını ayarla
    name_label = ui_manager.get_element("dialogue").children[0]
    name_label.set_text(npc.name.capitalize())
    
    # İlk diyalog mesajını göster
    dialogue_text = ui_manager.get_element("dialogue").children[1]
    response = dialogue_system.get_response(npc.name, "greeting")
    dialogue_text.set_text(response)

def advance_dialogue():
    """Diyalogda ilerle"""
    global game_state
    
    # Diyaloğu bitir
    game_state = "playing"
    ui_manager.hide_screen("dialogue")

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
        "assets/images/objects",
        "assets/images/crops",
        "assets/images/ui",
        "assets/sounds/sfx",
        "assets/sounds/music",
        "assets/fonts",
        "data/config",
        "data/maps",
        "data/saves",
        "data/ai_models",
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

# Pygame Zero fonksiyonları

def draw():
    """Her karede çağrılır - ekran çizimi"""
    global fps_sum, fps_count, last_fps
    
    # Ekranı temizle
    screen.clear()
    
    if game_state == "menu":
        # Menü arka planı
        draw_menu_background()
        
        # UI yöneticisi ile ekranları çiz
        if ui_manager:
            ui_manager.draw(screen)
    
    elif game_state in ["playing", "inventory", "shop", "dialogue", "paused"]:
        # Oyun dünyasını çiz
        if world:
            world.draw()
        
        # NPC'leri çiz
        for npc in npcs:
            npc.draw()
        
        # Oyuncuyu çiz
        if player:
            player.draw()
        
        # Oyun HUD'unu çiz
        draw_hud()
        
        # UI yöneticisi ile ekranları çiz (envanteri, diyalogları vb.)
        if ui_manager:
            ui_manager.draw(screen)
        
        if game_state == "paused":
            # Yarı saydam karartma (dondurulmuş oyun üzerine)
            screen.draw.filled_rect(Rect(0, 0, WIDTH, HEIGHT), (0, 0, 0, 100))
    
    # FPS sayacı
    if show_fps:
        # Son 10 karenin ortalama FPS değerini hesapla
        fps = clock.get_fps()
        fps_sum += fps
        fps_count += 1
        
        if fps_count >= 10:
            last_fps = fps_sum / fps_count
            fps_sum = 0
            fps_count = 0
        
        # FPS değerini göster
        fps_text = f"FPS: {int(last_fps)}"
        screen.draw.text(fps_text, (10, 10), color=(255, 255, 0), fontsize=16)
    
    # Debug bilgileri
    if show_debug and player:
        debug_text = f"X: {int(player.x)}, Y: {int(player.y)}, Dir: {player.direction}"
        screen.draw.text(debug_text, (10, 30), color=(0, 255, 255), fontsize=16)

def update(dt):
    """Her karede çağrılır - oyun mantığı güncellemesi"""
    # Fare ve klavye durumunu güncelle
    mouse_x, mouse_y = pygame.mouse.get_pos() if 'pygame' in globals() else (0, 0)
    
    # Dünyayı güncelle
    if game_state == "playing":
        # Zaman sistemi güncelle
        if time_system:
            time_system.update(dt)
        
        # Dünyayı güncelle
        if world:
            # Kamera oyuncuyu takip etsin
            if player and world.camera:
                world.camera.follow(player)
            
            world.update(dt)
        
        # Oyuncu güncelle
        if player:
            player.update(dt)
        
        # NPC'leri güncelle
        for npc in npcs:
            # NPC davranışlarını yönet
            if behavior_model:
                # Dünya durumunu ve oyuncuyu davranış modeline gönder
                action = behavior_model.get_action(npc, world, player)
                
                # Eylem uygula
                if action == "up":
                    npc.move(0, -1, dt)
                elif action == "down":
                    npc.move(0, 1, dt)
                elif action == "left":
                    npc.move(-1, 0, dt)
                elif action == "right":
                    npc.move(1, 0, dt)
            
            npc.update(dt)
    
    # UI güncelle
    if ui_manager:
        ui_manager.update(dt)

def on_key_down(key):
    """Tuşa basıldığında çağrılır"""
    global game_state, show_fps, show_debug
    
    # UI yöneticisinin olayı işlemesine izin ver
    if ui_manager and ui_manager.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key)):
        return
    
    # Bazı tuşlar her zaman çalışır
    if key == keys.F3:
        show_fps = not show_fps
    elif key == keys.F4:
        show_debug = not show_debug
    
    # Menüdeyken
    if game_state == "menu":
        if key == keys.ESCAPE:
            exit()
    
    # Oyun sırasında
    elif game_state == "playing":
        if key == keys.ESCAPE:
            game_state = "paused"
            ui_manager.show_screen("pause_menu")
        elif key == keys.E or key == keys.I:
            show_inventory()
            
        # Etkileşim tuşu
        elif key == keys.SPACE:
            # Oyuncunun önündeki bir NPC ile etkileşim
            close_npc = find_closest_npc()
            if close_npc:
                show_dialogue(close_npc)
            else:
                # Eğer NPC yoksa, farming etkileşimi
                if player:
                    # Seçili öğeye göre eylem yap
                    selected_slot = player.inventory.slots[player.inventory.selected_slot]
                    if selected_slot.item:
                        if selected_slot.item.category == "seed":
                            player.plant_seed(selected_slot.item.id)
                        elif selected_slot.item.category == "tool":
                            player.use_tool(selected_slot.item.id)
                        else:
                            # Hasat denemesi
                            player.harvest()
        
        # Envanter yuva seçimi (1-9 tuşları)
        elif keys.K_1 <= key <= keys.K_9:
            slot_index = key - keys.K_1
            if player and slot_index < len(player.inventory.slots):
                player.inventory.selected_slot = slot_index
    
    # Envanter ekranında
    elif game_state == "inventory":
        if key == keys.ESCAPE or key == keys.E or key == keys.I:
            close_inventory()
    
    # Duraklatma ekranında
    elif game_state == "paused":
        if key == keys.ESCAPE:
            resume_game()
    
    # Diyalog ekranında
    elif game_state == "dialogue":
        if key == keys.ESCAPE or key == keys.SPACE or key == keys.RETURN:
            advance_dialogue()

def on_mouse_down(pos, button):
    """Fare tıklaması olayı"""
    # UI yöneticisinin olayı işlemesine izin ver
    if ui_manager and ui_manager.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button)):
        return
    
    # Oyun sırasında
    if game_state == "playing":
        # Sol tık - etkileşim veya alet kullan
        if button == mouse.LEFT:
            # Oyuncunun aktif aletini veya eğer tohum seçiliyse ekme işlemini yap
            if player:
                # Seçili öğeye göre eylem yap
                selected_slot = player.inventory.slots[player.inventory.selected_slot]
                if selected_slot.item:
                    if selected_slot.item.category == "seed":
                        player.plant_seed(selected_slot.item.id)
                    elif selected_slot.item.category == "tool":
                        player.use_tool(selected_slot.item.id)

def find_closest_npc():
    """Oyuncuya en yakın NPC'yi bul"""
    if not player:
        return None
    
    closest_npc = None
    min_distance = float('inf')
    
    for npc in npcs:
        dx = npc.x - player.x
        dy = npc.y - player.y
        distance = (dx * dx + dy * dy) ** 0.5
        
        # Etkileşim mesafesi içinde mi?
        if distance < player.interaction_range and distance < min_distance:
            min_distance = distance
            closest_npc = npc
    
    return closest_npc

def draw_menu_background():
    """Menü arka planını çiz"""
    # Basit bir gradient arka plan
    for y in range(0, HEIGHT, 2):
        # Üstten alta doğru renk geçişi
        color_value = int(180 * (1 - y / HEIGHT))
        color = (20, color_value, 20)
        screen.draw.line((0, y), (WIDTH, y), color)
    
    # Rastgele "yıldızlar" (çiftçilik teması için küçük bitkiler gibi)
    for _ in range(50):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.randint(1, 3)
        color = (100 + random.randint(0, 155), 200 + random.randint(0, 55), 100 + random.randint(0, 55))
        screen.draw.filled_circle((x, y), size, color)

def draw_hud():
    """Oyun içi HUD'u çiz"""
    if time_system:
        # Zaman bilgisi
        time_text = f"Gün {time_system.day}, {time_system.hour:02d}:{time_system.minute:02d}"
        screen.draw.text(time_text, topright=(WIDTH-10, 10), fontsize=20, color="white", shadow=(1, 1))
        
        # Mevsim
        season_text = f"Mevsim: {time_system.seasons[time_system.season]}"
        screen.draw.text(season_text, topright=(WIDTH-10, 35), fontsize=16, color="white", shadow=(1, 1))
    
    if player:
        # Enerji çubuğu
        energy_width = 150
        energy_height = 15
        energy_x = 10
        energy_y = 10
        
        # Arka plan
        screen.draw.filled_rect(Rect((energy_x, energy_y), (energy_width, energy_height)), (50, 50, 50))
        
        # Enerji seviyesi
        energy_level = int((player.energy / player.max_energy) * energy_width)
        screen.draw.filled_rect(Rect((energy_x, energy_y), (energy_level, energy_height)), (50, 200, 50))
        
        # Metin
        energy_text = f"Enerji: {int(player.energy)}/{player.max_energy}"
        screen.draw.text(energy_text, (energy_x + 5, energy_y + 2), fontsize=12, color="white")
        
        # Para
        money_text = f"Para: ${player.money}"
        screen.draw.text(money_text, (energy_x, energy_y + 25), fontsize=16, color="white", shadow=(1, 1))
        
        # Seçili envanter yuvası
        draw_inventory_bar()

def draw_inventory_bar():
    """Envanter çubuğunu çiz (hızlı erişim)"""
    if not player:
        return
    
    slot_size = 40
    slot_padding = 5
    total_width = (slot_size + slot_padding) * 9 - slot_padding
    start_x = (WIDTH - total_width) // 2
    start_y = HEIGHT - slot_size - 10
    
    # Arka plan panel
    screen.draw.filled_rect(
        Rect((start_x - 5, start_y - 5), (total_width + 10, slot_size + 10)),
        (30, 30, 30, 180)
    )
    
    # 9 envanter yuvası çiz
    for i in range(9):
        x = start_x + i * (slot_size + slot_padding)
        y = start_y
        
        # Yuva arka planı
        slot_color = (60, 60, 60) if i == player.inventory.selected_slot else (40, 40, 40)
        screen.draw.filled_rect(Rect((x, y), (slot_size, slot_size)), slot_color)
        
        # Yuva sınırı
        border_color = (200, 200, 100) if i == player.inventory.selected_slot else (100, 100, 100)
        screen.draw.rect(Rect((x, y), (slot_size, slot_size)), border_color)
        
        # Eğer yuvada eşya varsa, çiz
        slot = player.inventory.slots[i]
        if slot.item:
            # Eşya sprite'ı
            item_image = f"assets/images/items/{slot.item.icon}"
            try:
                item_actor = Actor(item_image)
                item_actor.x = x + slot_size // 2
                item_actor.y = y + slot_size // 2
                item_actor.draw()
            except:
                # Sprite yoksa, basit bir şekil çiz
                color = (200, 100, 100) if slot.item.category == "tool" else (100, 200, 100)
                screen.draw.filled_circle((x + slot_size // 2, y + slot_size // 2), slot_size // 3, color)
                
                # Eşya adının ilk harfi
                item_initial = slot.item.name[0].upper()
                screen.draw.text(item_initial, center=(x + slot_size // 2, y + slot_size // 2), 
                                fontsize=14, color="white")
            
            # Eğer yığınlanabilir bir eşyaysa ve birden fazla varsa, sayıyı göster
            if slot.item.stackable and slot.count > 1:
                count_text = str(slot.count)
                screen.draw.text(count_text, bottomright=(x + slot_size - 2, y + slot_size - 2), 
                               fontsize=12, color="white", shadow=(1, 1))
        
        # Kısayol numarası
        key_text = str(i + 1)
        screen.draw.text(key_text, topleft=(x + 2, y + 2), fontsize=10, color=(200, 200, 200))

# Ana modül ise oyunu başlat
if __name__ == "__main__":
    setup_game()