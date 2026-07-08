import re

with open('presentation/master_deck.html', 'r') as f:
    content = f.read()

# 1. First, find all id="slide-X" from X=22 down to X=2 and replace with X+1
for x in range(22, 1, -1):
    # Use unique temporary place holders to avoid double shifting
    content = content.replace(f'id="slide-{x}"', f'id="slide-TEMP{x+1}"')

for x in range(22, 1, -1):
    content = content.replace(f'id="slide-TEMP{x+1}"', f'id="slide-{x+1}"')

# 2. Shift nav dots data-slide attributes from data-slide="22" down to "2"
for x in range(21, 1, -1):
    content = content.replace(f'data-slide="{x}"', f'data-slide="TEMP{x+1}"')

for x in range(21, 1, -1):
    content = content.replace(f'data-slide="TEMP{x+1}"', f'data-slide="{x+1}"')

with open('presentation/master_deck.html', 'w') as f:
    f.write(content)

print("Slide shifting complete!")
