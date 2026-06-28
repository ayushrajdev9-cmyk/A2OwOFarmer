# A2 OWO FARMER - Combined OwO Bot Suite
# Made by Ayush Rajdev & Anzar Iqbal

import time

def format_seconds(seconds):
    if not seconds or seconds < 0:
        return "00:00:00"
        
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    
    return f"{h:02d}:{m:02d}:{s:02d}"
