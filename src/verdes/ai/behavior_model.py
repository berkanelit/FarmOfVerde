"""
NPC davranışları için yapay zeka modeli.
"""
import os
import random
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path

class SimpleBehaviorNet(nn.Module):
    """Basit davranış sinir ağı"""
    
    def __init__(self, input_size, hidden_size, output_size):
        super(SimpleBehaviorNet, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

class BehaviorModel:
    """NPC'ler için AI davranış modeli"""
    
    def __init__(self, config):
        self.config = config
        self.model = None
        self.model_loaded = False
        
        # Model parametreleri (hafif)
        self.input_size = 8  # NPC durumu ve çevre bilgisi
        self.hidden_size = 16  # Küçük gizli katman
        self.output_size = 4  # Eylemler (yukarı, aşağı, sol, sağ)
        
        # Model yükleme
        self._load_model()
    
    def _load_model(self):
        """Davranış modelini yükle veya oluştur"""
        model_path = Path("data/ai_models/behavior_model.pt")
        
        try:
            if model_path.exists():
                # Önceden eğitilmiş model yükle
                self.model = SimpleBehaviorNet(self.input_size, self.hidden_size, self.output_size)
                self.model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
                self.model.eval()  # Değerlendirme modu
                self.model_loaded = True
                print("Davranış modeli yüklendi.")
            else:
                # Yeni model oluştur
                self._create_new_model(model_path)
        except Exception as e:
            print(f"Model yükleme hatası: {e}")
            self._create_new_model(model_path)
    
    def _create_new_model(self, model_path):
        """Yeni bir davranış modeli oluştur"""
        self.model = SimpleBehaviorNet(self.input_size, self.hidden_size, self.output_size)
        self.model.eval()  # Değerlendirme modu
        self.model_loaded = True
        
        # Dizin oluştur
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Modeli kaydet
        torch.save(self.model.state_dict(), model_path)
        print("Yeni davranış modeli oluşturuldu.")
    
    def get_action(self, npc, world, player):
        """NPC durumuna ve çevreye göre bir eylem seç"""
        # Basit AI aktif değilse veya model yüklü değilse
        if not self.model_loaded or self.config["ai"]["use_simple_ai"]:
            return self._get_rule_based_action(npc, world, player)
        
        try:
            # Durum vektörü oluştur
            state = self._create_state_vector(npc, world, player)
            
            # Tensor'a dönüştür
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            
            # Tahminde bulun
            with torch.no_grad():
                action_values = self.model(state_tensor)
            
            # En yüksek değerli eylemi seç
            action_idx = torch.argmax(action_values, dim=1).item()
            
            # Eylem indeksini eyleme dönüştür
            actions = ["up", "right", "down", "left"]
            return actions[action_idx]
        except Exception as e:
            print(f"AI eylem hatası: {e}")
            return self._get_rule_based_action(npc, world, player)
    
    def _create_state_vector(self, npc, world, player):
        """NPC durumunu ve çevresini vektörleştir"""
        # Normalize konumlar
        if world:
            norm_x = npc.x / (world.width * world.tile_size)
            norm_y = npc.y / (world.height * world.tile_size)
        else:
            norm_x = npc.x / 800  # Varsayılan ekran genişliği
            norm_y = npc.y / 600  # Varsayılan ekran yüksekliği
        
        # Oyuncuya olan mesafe ve yön
        dx = player.x - npc.x
        dy = player.y - npc.y
        distance = np.sqrt(dx*dx + dy*dy) / 1000  # Normalize et
        angle = np.arctan2(dy, dx) / np.pi  # -1 ile 1 arası normalize
        
        # Gün içindeki zaman (6-24 arasını 0-1 arasına normalize et)
        time_of_day = 0.5  # Varsayılan değer
        if hasattr(world, 'time_system') and world.time_system:
            hour = world.time_system.hour + world.time_system.minute / 60
            time_of_day = (hour - 6) / 18  # 6:00 - 24:00 arasını 0-1 arasına normalize et
        
        # Durum vektörü (toplam 8 öğe)
        state = [
            norm_x, norm_y,          # Konum (2)
            dx/1000, dy/1000,        # Oyuncuya göre yön (2)
            distance,                # Oyuncuya mesafe (1)
            angle,                   # Oyuncuya olan açı (1)
            time_of_day,             # Günün zamanı (1)
            float(npc.moving)        # Hareket durumu (1)
        ]
        
        return state
    
    def _get_rule_based_action(self, npc, world, player):
        """Basit kural tabanlı davranış"""
        # Oyuncuya yakınsa, rastgele hareket
        dx = player.x - npc.x
        dy = player.y - npc.y
        distance = np.sqrt(dx*dx + dy*dy)
        
        if distance < 100:
            # Oyuncuya yakınsa
            if random.random() < 0.7:
                # %70 oyuncuya doğru hareket
                if abs(dx) > abs(dy):
                    return "right" if dx > 0 else "left"
                else:
                    return "down" if dy > 0 else "up"
            else:
                # %30 rastgele hareket
                return random.choice(["up", "right", "down", "left"])
        else:
            # Oyuncudan uzaksa, rastgele dolaş
            if random.random() < 0.3:
                # %30 hareket değiştir
                return random.choice(["up", "right", "down", "left"])
            else:
                # %70 aynı yönde devam et
                if npc.direction == "up":
                    return "up"
                elif npc.direction == "right":
                    return "right"
                elif npc.direction == "down":
                    return "down"
                else:
                    return "left"
    
    def train(self, experiences, epochs=10, learning_rate=0.001):
        """Davranış modelini deneyimlerle eğit"""
        if not self.model_loaded or not experiences:
            return False
        
        # Eğitim moduna geç
        self.model.train()
        
        # Deneyimleri tensor'a dönüştür
        states = torch.FloatTensor([exp[0] for exp in experiences])
        actions = torch.LongTensor([exp[1] for exp in experiences])
        rewards = torch.FloatTensor([exp[2] for exp in experiences])
        
        # Optimizer
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # Eğitim döngüsü
        for epoch in range(epochs):
            # Tahminler
            predictions = self.model(states)
            
            # One-hot encoding
            action_one_hot = F.one_hot(actions, self.output_size).float()
            
            # MSE kaybı
            loss = F.mse_loss(predictions * action_one_hot, action_one_hot * rewards.unsqueeze(1))
            
            # Geriye yayılım
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 5 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")
        
        # Değerlendirme moduna geri dön
        self.model.eval()
        
        # Modeli kaydet
        model_path = Path("data/ai_models/behavior_model.pt")
        torch.save(self.model.state_dict(), model_path)
        
        return True