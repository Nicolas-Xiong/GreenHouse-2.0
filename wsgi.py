# -*- coding: utf-8 -*-
"""
Created on Mon Jan 13 13:54:38 2020

@author: Nicolas Xiong
"""

import os

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env') 
if os.path.exists(dotenv_path):    
    load_dotenv(dotenv_path)
    
from application import app
