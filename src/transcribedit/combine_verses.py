import json
import re
import os

from natsort import natsorted


def get_chapter_tx(siglum: str, ref: str, wit_dir: str, verse_per_line: bool, remove_markup: bool):
    sep = ''
    t = None
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
                    t = wit['text']
                    break
                else:
                    t = tx['text']
                    break
            if verse_per_line:
                t = t.replace(' \n', ' ')
                t = t.replace('-\n', '')
                t = t.replace('\n', ' ')
                sep = '\n'
            if remove_markup:
                t = re.sub(r'<[^>]+>', '', t)
                t = re.sub(r' +', ' ', t)
            text.append(f"<{v.replace('.json', '')}> {t}{sep}")
    text = ''.join(text)
    return text

# with open('test.txt', 'w', encoding='utf-8') as file:
#     file.write(text)
