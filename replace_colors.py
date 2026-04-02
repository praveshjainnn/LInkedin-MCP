import re
import os

path = 'static/style.css'
with open(path, 'r', encoding='utf-8') as f:
    css = f.read()

# Protect root variables we just changed from being scrambled
css_parts = css.split("/* ── Reset ── */")
if len(css_parts) > 1:
    root_part = css_parts[0]
    rest_part = "/* ── Reset ── */" + css_parts[1]
else:
    root_part = ""
    rest_part = css

# Mapping old colors to new colors
replacements = {
    # Amethyst/Blue solid colors -> Coral/Terracotta/Cream
    '#8CA9FF': '#DA7756',  # Bright blue -> Coral
    '#AAC4F5': '#E8967A',  # Light blue -> Light Coral
    '#FFF8DE': '#F5F0EB',  # Warm white/cream -> Claude Cream
    '#FFF2C6': '#E8B89A',  # Yellowish cream -> Amber cream
    '#5870cc': '#C96442',  # Mid blue -> Terracotta
    '#2a1e56': '#323230',  # Purple-blue dark -> Surface high
    '#06080f': '#1C1C1B',  # Very dark blue -> Claude Charcoal
    '#181f38': '#2A2A28',  # Dark blue -> Surface container
    '#0d1120': '#212120',  # Dark background -> Surface low
    '#090c16': '#1C1C1B',  # Email shell dark -> Charcoal
    '#4a5580': '#7A7570',  # Email label blue -> Muted text
    '#d0cbb8': '#F5F0EB',
    '#e8e0cc': '#E0DCD6',
    
    # SVG gradients or related
    '#810CA8': '#DA7756',
    '#C147E9': '#C96442',

    # rgba replacements for borders, hover states, glows
    # rgba(140,169,255,X) -> main blue/purple accent -> rgba(218,119,86,X) (Coral)
    r'rgba\(140,169,255,': 'rgba(218,119,86,',
    
    # rgba(88,112,204,X) -> mid blue -> rgba(201,100,66,X) (Terracotta)
    r'rgba\(88,112,204,': 'rgba(201,100,66,',
    
    # rgba(170,196,245,X) -> light blue -> rgba(232,150,122,X) (Light coral)
    r'rgba\(170,196,245,': 'rgba(232,150,122,',
    
    # rgba(255,248,222,X) -> cream/warm -> rgba(245,240,235,X)
    r'rgba\(255,248,222,': 'rgba(245,240,235,',
    
    # rgba(255,242,198,X) -> yellow cream -> rgba(232,184,154,X)
    r'rgba\(255,242,198,': 'rgba(232,184,154,',
    
    # rgba(6,8,15,X) -> dark base -> rgba(28,28,27,X) (from #1C1C1B)
    r'rgba\(6,8,15,': 'rgba(28,28,27,',
    
    # rgba(0,0,0,0.4) ... keep as is
}

for old, new in replacements.items():
    if old.startswith('rgba'):
        rest_part = re.sub(old, new, rest_part)
    elif old.startswith('r'):
        # Just in case it's regex string
        rest_part = re.sub(old, new, rest_part)
    else:
        rest_part = rest_part.replace(old, new)
        rest_part = rest_part.replace(old.lower(), new)

new_css = root_part + rest_part

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_css)

print("Replaced colors successfully.")
