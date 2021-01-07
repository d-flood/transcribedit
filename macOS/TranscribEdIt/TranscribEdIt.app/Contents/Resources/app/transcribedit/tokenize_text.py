import re
 

def text_to_witness_dict(text: str, siglum: str):
    witness = {'id': siglum,
               'tokens': []}
    text = text.replace('-\n', '|')
    text = text.replace('\n', ' ')
    text = re.sub(r'<(.+)>', '', text)
    index = 2
    for word in text.split():
        if word in ['·', ',', '.', ':', '※', '⁘', '+', '...']:
            continue
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

def orig_to_dict(values: dict):
    return {
        '_id': f'{values["-siglum-"]}_{values["-ref-"]}',
        'transcription': values["-siglum-"],
        'transcription_siglum': values["-siglum-"],
        'siglum': values["-siglum-"],
        'context': values["-ref-"],
        'n': values["-ref-"],
        'text': values["-transcription-"],
        'verse_note': values["verse_note"],
        'verse_marginale': {'type': values['verse_marg_type'], 
                            'loc': values['verse_marg_loc'], 
                            'tx': values['verse_marg_tx']},
        'witnesses': [
            text_to_witness_dict(values["-transcription-"], values['-siglum-'])
            ]
            }

def add_hand_to_dict(verse_dict: dict, text: str, siglum_hand):
    hand_dict = text_to_witness_dict(text, siglum_hand)
    verse_dict['witnesses'].append(hand_dict)
    return verse_dict

def update_witness_dict(verse_dict: dict, text: str, siglum: str, values: dict):
    verse_dict['verse_marginale'] = {'type': values['verse_marg_type'], 
                                     'loc': values['verse_marg_loc'], 
                                     'tx': values['verse_marg_tx']}
    for i, wit in enumerate(verse_dict['witnesses']):
        if wit['id'] == siglum:
            verse_dict['witnesses'][i] = text_to_witness_dict(text, siglum)
            return verse_dict
    verse_dict['witnesses'].append(text_to_witness_dict(text, siglum))
    return verse_dict

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
            verse_words = wit['tokens']
        #     for token in wit['tokens']:
        #         verse_words.append(token['original'])
        hands.append(wit['id'])
    return verse_words, hands