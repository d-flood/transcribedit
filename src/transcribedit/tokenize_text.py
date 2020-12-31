
 

def text_to_witness_dict(text: str, siglum: str):
    witness = {'id': siglum,
               'tokens': []}
    text = text.replace('-\n', '|')
    text = text.replace('\n', ' ')
    index = 2
    for word in text.split():
        orig_word = word
        if '|' in word:
            word = word.replace('|', '')
        witness['tokens'].append({"index": f"{index}",
                                 "siglum": siglum,
                                 "reading": siglum,
                                 "original": orig_word,
                                 "rule_match": [word],
                                 "t": word})
        index += 2
    return witness

def orig_to_dict(text: str, siglum: str, ref: str):
    return {
        '_id': f'{siglum}_{ref}',
        'transcription': siglum,
        'transcription_siglum': siglum,
        'siglum': siglum,
        'context': ref,
        'n': ref,
        'text': text,
        'witnesses': [text_to_witness_dict(text, siglum)]
            }

def add_hand_to_dict(verse_dict: dict, text: str, siglum_hand):
    hand_dict = text_to_witness_dict(text, siglum_hand)
    verse_dict['witnesses'].append(hand_dict)
    return verse_dict

def update_witness_dict(orig: dict, text: str, siglum: str):
    for i, wit in enumerate(orig['witnesses']):
        if wit['id'] == siglum:
            orig['witnesses'][i] = text_to_witness_dict(text, siglum)
            return orig
    orig['witnesses'].append(text_to_witness_dict(text, siglum))
    return orig

def update_token(token: dict, index: int, verse: dict, siglum: str):
    loc_index = (index / 2) - 1
    loc_index = int(loc_index)
    for i, wit in enumerate(verse['witnesses']):
        if wit['id'] == siglum:
            verse['witnesses'][i]['tokens'][loc_index] = token
            return verse

def get_token(index: int, verse: dict, siglum: str):
    loc_index = (index / 2) - 1
    loc_index = int(loc_index)
    for i, wit in enumerate(verse['witnesses']):
        if wit['id'] == siglum:
            return verse['witnesses'][i]['tokens'][loc_index]

def get_words_from_dict(verse: dict, siglum: str):
    hands = []
    verse_words = []
    for wit in verse['witnesses']:
        if wit['id'] == siglum:
            for token in wit['tokens']:
                verse_words.append(token['original'])
        hands.append(wit['id'])
    return verse_words, hands