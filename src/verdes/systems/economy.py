"""
Ekonomi sistemi - alışveriş ve ticaret.
"""
from typing import List, Dict, Optional, Tuple
import random
from pathlib import Path
import yaml
from verdes.systems.inventory import Item, ItemDatabase, Inventory

class Shop:
    """Mağaza sınıfı"""
    
    def __init__(self, name: str, owner: str = "Satıcı"):
        self.name = name
        self.owner = owner
        self.stock: Dict[str, Tuple[int, float]] = {}  # item_id: (miktar, fiyat_çarpanı)
        self.inventory = Inventory(size=40)  # Mağaza envanteri
        self.item_db = ItemDatabase()
        self.buy_multiplier = 0.5  # Satın alma fiyatı = değer * buy_multiplier
        self.sell_multiplier = 1.0  # Satış fiyatı = değer * sell_multiplier
        self._load_stock()
    
    def _load_stock(self) -> None:
        """Mağaza stoğunu dosyadan yükler"""
        shop_path = Path(f"data/config/shops/{self.name}.yaml")
        
        if shop_path.exists():
            with open(shop_path, "r", encoding="utf-8") as f:
                shop_data = yaml.safe_load(f)
                
                if "items" in shop_data:
                    for item_data in shop_data["items"]:
                        item_id = item_data.get("id")
                        quantity = item_data.get("quantity", 1)
                        price_multiplier = item_data.get("price_multiplier", 1.0)
                        
                        if item_id and self.item_db.get_item(item_id):
                            self.stock[item_id] = (quantity, price_multiplier)
                            
                            # Envantere ekleme
                            item = self.item_db.get_item(item_id)
                            if item:
                                self.inventory.add_item(item, quantity)
                
                # Mağaza ayarları
                self.buy_multiplier = shop_data.get("buy_multiplier", 0.5)
                self.sell_multiplier = shop_data.get("sell_multiplier", 1.0)
        else:
            # Varsayılan mağaza stoğu oluştur
            self._create_default_stock(shop_path)
    
    def _create_default_stock(self, shop_path: Path) -> None:
        """Varsayılan mağaza stoğu oluşturup dosyaya kaydeder"""
        # Mağaza türüne göre farklı varsayılan stock
        default_items = []
        
        if self.name == "general_store":
            default_items = [
                {"id": "turnip_seed", "quantity": 20, "price_multiplier": 1.0},
                {"id": "potato_seed", "quantity": 15, "price_multiplier": 1.0},
                {"id": "tomato_seed", "quantity": 10, "price_multiplier": 1.0},
                {"id": "hoe", "quantity": 1, "price_multiplier": 1.0},
                {"id": "watering_can", "quantity": 1, "price_multiplier": 1.0},
                {"id": "axe", "quantity": 1, "price_multiplier": 1.0}
            ]
        
        default_shop = {
            "name": self.name,
            "owner": self.owner,
            "buy_multiplier": self.buy_multiplier,
            "sell_multiplier": self.sell_multiplier,
            "items": default_items
        }
        
        # Dizini oluştur
        Path("data/config/shops").mkdir(parents=True, exist_ok=True)
        
        # Dosyaya yaz
        with open(shop_path, "w", encoding="utf-8") as f:
            yaml.dump(default_shop, f, default_flow_style=False)
        
        # Envantere ekle
        for item_data in default_items:
            item_id = item_data.get("id")
            quantity = item_data.get("quantity", 1)
            price_multiplier = item_data.get("price_multiplier", 1.0)
            
            if item_id:
                self.stock[item_id] = (quantity, price_multiplier)
                
                # Envantere ekleme
                item = self.item_db.get_item(item_id)
                if item:
                    self.inventory.add_item(item, quantity)
    
    def get_buy_price(self, item_id: str) -> int:
        """Belirtilen eşyanın satın alma fiyatını döndürür (oyuncu -> mağaza)"""
        item = self.item_db.get_item(item_id)
        if not item:
            return 0
        
        return max(1, int(item.value * self.buy_multiplier))
    
    def get_sell_price(self, item_id: str) -> int:
        """Belirtilen eşyanın satış fiyatını döndürür (mağaza -> oyuncu)"""
        item = self.item_db.get_item(item_id)
        if not item:
            return 0
        
        # Stokta varsa, fiyat çarpanını uygula
        price_multiplier = 1.0
        if item_id in self.stock:
            _, price_multiplier = self.stock[item_id]
        
        return max(1, int(item.value * self.sell_multiplier * price_multiplier))
    
    def buy_from_player(self, player_inventory: Inventory, item_id: str, quantity: int = 1) -> bool:
        """Oyuncudan eşya satın alır"""
        if quantity <= 0:
            return False
        
        # Eşyayı kontrol et
        item = self.item_db.get_item(item_id)
        if not item:
            return False
        
        # Oyuncunun yeterli miktarda eşyası var mı?
        if not player_inventory.has_item(item_id, quantity):
            return False
        
        # Toplam fiyatı hesapla
        price_per_item = self.get_buy_price(item_id)
        total_price = price_per_item * quantity
        
        # Eşyayı oyuncudan kaldırıp, parayı ekle
        player_inventory.remove_item(item_id, quantity)
        
        # Bu çağrıda player.add_money(total_price) olarak kullanılacak
        return True
    
    def sell_to_player(self, player_inventory: Inventory, player_money: int, item_id: str, quantity: int = 1) -> bool:
        """Oyuncuya eşya satar"""
        if quantity <= 0:
            return False
        
        # Eşyayı kontrol et
        item = self.item_db.get_item(item_id)
        if not item:
            return False
        
        # Mağazada yeterli miktar var mı?
        if not self.inventory.has_item(item_id, quantity):
            return False
        
        # Toplam fiyatı hesapla
        price_per_item = self.get_sell_price(item_id)
        total_price = price_per_item * quantity
        
        # Oyuncunun yeterli parası var mı?
        if player_money < total_price:
            return False
        
        # Eşyayı mağazadan kaldırıp, oyuncuya ekle
        self.inventory.remove_item(item_id, quantity)
        remaining = player_inventory.add_item(item, quantity)
        
        # Eğer oyuncunun envanteri doluysa, işlemi iptal et
        if remaining > 0:
            # Eşyayı geri mağazaya ekle
            self.inventory.add_item(item, quantity)
            return False
        
        # Bu çağrıda player.spend_money(total_price) olarak kullanılacak
        return True
    
    def restock(self) -> None:
        """Mağaza stoğunu yeniler"""
        for item_id, (quantity, price_multiplier) in self.stock.items():
            item = self.item_db.get_item(item_id)
            if item:
                # Şu andaki miktarı kontrol et
                current_quantity = self.inventory.get_item_count(item_id)
                max_quantity = quantity
                
                # Eğer mağaza stoğu azsa, yenile
                if current_quantity < max_quantity:
                    restock_amount = max_quantity - current_quantity
                    self.inventory.add_item(item, restock_amount)

class EconomySystem:
    """Ekonomi sistemini yönetir"""
    
    def __init__(self):
        self.shops: Dict[str, Shop] = {}
        self.item_db = ItemDatabase()
        self._load_shops()
    
    def _load_shops(self) -> None:
        """Tüm mağazaları yükle"""
        shops_dir = Path("data/config/shops")
        
        if not shops_dir.exists():
            # Varsayılan mağazalar oluştur
            shops_dir.mkdir(parents=True, exist_ok=True)
            
            # Genel mağaza
            general_store = Shop("general_store", "Pierre")
            self.shops["general_store"] = general_store
        else:
            # Mevcut mağazaları yükle
            for shop_file in shops_dir.glob("*.yaml"):
                shop_name = shop_file.stem
                
                with open(shop_file, "r", encoding="utf-8") as f:
                    shop_data = yaml.safe_load(f)
                    owner = shop_data.get("owner", "Satıcı")
                    
                    shop = Shop(shop_name, owner)
                    self.shops[shop_name] = shop
    
    def get_shop(self, shop_name: str) -> Optional[Shop]:
        """Belirtilen adlı mağazayı döndürür"""
        return self.shops.get(shop_name)
    
    def update_all_shops(self) -> None:
        """Tüm mağazaları günceller (günlük yenileme)"""
        for shop in self.shops.values():
            shop.restock()