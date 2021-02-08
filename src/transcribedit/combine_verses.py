import json
import re
import os

from natsort import natsorted


def get_chapter_tx(siglum: str, ref: str, wit_dir: str):
    ref = ref.replace(':', '.')
    ref = ref.replace(' ', '')
    chap = re.sub(r'\..+', '', ref)
    verse_files = os.listdir(f'{wit_dir}/{siglum}')
    text = []
    for v in natsorted(verse_files):
        if v.startswith(chap):
            with open(f'{wit_dir}/{siglum}/{v}', 'r', encoding='utf=8') as file:
                tx = json.load(file)
            for wit in tx['witnesses']:
                if 'text' in wit and 'c' not in wit:
                    text.append(f" <{v.replace('.json', '')}> {wit['text']}")
                    break
                else:
                    text.append(f" <{v.replace('.json', '')}> {tx['text']}")
                    break
    text = ''.join(text)
    return text

# with open('test.txt', 'w', encoding='utf-8') as file:
#     file.write(text)
