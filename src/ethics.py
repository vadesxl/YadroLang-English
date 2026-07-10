# -*- coding: utf-8 -*-
"""Compatibility facade for the YadroLang Ethical Analyzer v2.1."""
from src.ethics_v21 import *  # noqa: F401,F403
from src.ethics_flow import SoundEthicalAnalyzer

EthicalAnalyzer = SoundEthicalAnalyzer
