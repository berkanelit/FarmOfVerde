#!/usr/bin/env python
"""
Verde - Stardew Valley benzeri yapay zeka destekli çiftlik oyunu
Ana Başlatıcı Dosyası
"""
import os
import sys

# Modül yolunu ayarla
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

# Oyunu başlat
from verdes.game import setup_game
import pgzrun

# Oyun ayarlarını yapılandır
WIDTH, HEIGHT = 800, 600
TITLE = "Verde - AI Farming Simulator"

# Ana oyun öğelerini yükle
setup_game()

# Sadece ana script olarak çalıştırılıyorsa
if __name__ == "__main__":
    # Pygame Zero'yu başlat
    pgzrun.go()