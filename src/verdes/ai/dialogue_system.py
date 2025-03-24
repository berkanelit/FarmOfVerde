"""
Hafif NLP tabanlı diyalog sistemi.
"""
import os
import random
import yaml
import torch
from pathlib import Path

class DialogueSystem:
    """AI tabanlı diyalog sistemi"""
    
    def __init__(self, config):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self.dialogue_data = self._load_dialogue_data()
        
        # Model yükleme (eğer yapılandırmada etkinse)
        if config["ai"]["dialogue_model"] != "none":
            self._load_model()
    
    def _load_model(self):
        """NLP modelini yükle"""
        try:
            print("Model yükleniyor...")
        except Exception as e:
            print(f"Model yükleme hatası: {e}")
            print("Basit diyalog sistemi kullanılacak.")
    
    def _load_dialogue_data(self):
        """Basit diyalog verisini yükle"""
        dialogue_path = Path("data/config/dialogue_data.yaml")
        
        if dialogue_path.exists():
            with open(dialogue_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        
        # Varsayılan diyaloglar
        default_dialogues = {
            "greetings": [
                "Merhaba!",
                "Selam, nasılsın?",
                "Güzel bir gün, değil mi?",
                "Bugün nasılsın?"
            ],
            "weather": [
                "Hava bugün çok güzel.",
                "Yağmur yağacak gibi görünüyor.",
                "Bu mevsim için oldukça sıcak.",
                "Hava çok güzel, değil mi?"
            ],
            "farming": [
                "Mahsulün iyi görünüyor!",
                "Çiftçilik nasıl gidiyor?",
                "Bu sezon için iyi bir hasat olacak.",
                "Ne ekmeyi planlıyorsun?"
            ],
            "shop": [
                "Bir şeyler satın almak ister misin?",
                "Bugün özel indirimlerim var.",
                "En kaliteli ürünleri satıyorum.",
                "Neye ihtiyacın var?"
            ],
            "generic": [
                "Hmm, ilginç.",
                "Anlıyorum.",
                "Devam et.",
                "Başka?",
                "Bu konuda daha fazla şey duymak isterim."
            ]
        }
        
        # Dizini oluştur ve varsayılan veriyi kaydet
        os.makedirs(dialogue_path.parent, exist_ok=True)
        with open(dialogue_path, "w", encoding="utf-8") as f:
            yaml.dump(default_dialogues, f, default_flow_style=False)
        
        return default_dialogues
    
    def get_response(self, npc_name, player_input, context=None):
        """Oyuncu girdisine yanıt oluştur"""
        # AI model yüklüyse ve etkinse kullan
        if self.model_loaded:
            try:
                # Bağlam ile birlikte prompt oluştur
                if context:
                    prompt = f"{npc_name}: {context}\nPlayer: {player_input}\n{npc_name}:"
                else:
                    prompt = f"Player: {player_input}\n{npc_name}:"
                
                # Tokenize
                inputs = self.tokenizer(prompt, return_tensors="pt")
                
                # Yanıt oluştur
                with torch.no_grad():  # Bellek tasarrufu
                    outputs = self.model.generate(
                        inputs["input_ids"],
                        max_length=50,  # Kısa tutuyoruz (hafif)
                        num_return_sequences=1,
                        temperature=0.7,
                        top_p=0.9,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                
                # Decode
                response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Yanıtı ayıkla
                if f"{npc_name}:" in response:
                    response = response.split(f"{npc_name}:")[-1].strip()
                else:
                    response = response.replace("Player: " + player_input, "").strip()
                
                return response
            except Exception as e:
                print(f"AI yanıt hatası: {e}")
                return self._get_rule_based_response(player_input)
        
        # Model yoksa veya aktif değilse, kural tabanlı yanıt kullan
        return self._get_rule_based_response(player_input)
    
    def _get_rule_based_response(self, player_input):
        """Basit kural tabanlı yanıt seçimi"""
        player_input = player_input.lower()
        
        # Anahtar kelime tabanlı yanıt kategorisi seçimi
        if any(word in player_input for word in ["merhaba", "selam", "sa", "hey"]):
            category = "greetings"
        elif any(word in player_input for word in ["hava", "yağmur", "güneş", "kar"]):
            category = "weather"
        elif any(word in player_input for word in ["çiftlik", "ekin", "mahsul", "hasat"]):
            category = "farming"
        elif any(word in player_input for word in ["sat", "al", "fiyat", "kaç"]):
            category = "shop"
        else:
            category = "generic"
        
        # Seçilen kategoriden rastgele yanıt
        responses = self.dialogue_data.get(category, self.dialogue_data["generic"])
        return random.choice(responses)
    
    def train_model(self, dialogue_samples):
        """Modeli yeni diyaloglarla eğit (çok basit örnek)"""
        # Not: Gerçek bir uygulamada daha karmaşık eğitim kodu olmalı
        # Bu sadece yapıyı göstermek için
        if self.model_loaded:
            print("Model eğitimi başlatılıyor...")
            # Eğitim kodu buraya gelecek
            print("Eğitim tamamlandı!")
            return True
        
        return False