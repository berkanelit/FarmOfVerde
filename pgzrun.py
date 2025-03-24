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
import pgzrun
from verdes.game import setup_game

# Oyun ayarlarını yapılandır
WIDTH, HEIGHT = 800, 600
TITLE = "Verde - AI Farming Simulator"

# Ana oyun öğelerini yükle
setup_game()

# Pygame Zero'yu başlat
pgzrun.go()