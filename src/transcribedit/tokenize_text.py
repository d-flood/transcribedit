import re


def initial_token(word: str, siglum: str, index):
    return {"index": f"{index}",
            "siglum": siglum,
            "reading": siglum,
            "original": word,
            "rule_match": [word],
            "t": word}

def prepare_text(text: str):
    text = text.replace('\n<cb> ', 'C|') #break_before columng
    text = text.replace('\n<pb> ', 'P|') #break_before page
    text = text.replace('-\n<cb>', '-C-') #break_split column
    text = text.replace('-\n<pb>', '-P-') #break_split page
    text = text.replace('\nC|', ' C|')
    text = text.replace('\nP|', ' P|')
    text = text.replace('-\n', '|') #break_split line
    text = text.replace(' \n', ' |') #break before
    text = re.sub(r'<[^>]+>', '', text) #removes anything enclosed in angle brackets
    text = re.sub(r'{[^}]+}', '', text) #removes anything enclosed in braces
    # this replaces words entirely enclosed in square brackets with a gap marker '...'
    # but leaves brackets in partially reconstructed words
    text = re.sub(r' \[[^}]+\] ', ' ... ', text)
    text = text.replace(' ...', '_[...]') #gap after
    text = text.replace('... ', '[...]_') #gap before
    return text

def regularize_word(word: str):
    word = word.replace('|', '')
    word = word.replace('\u0305', '')
    word = word.replace('\u0345', '')
    word = word.replace('\u0308', '')
    word = word.replace('(', '')
    word = word.replace(')', '')
    word = word.replace('[...]', '')
    word = word.replace('_', '')
    word = word.replace('-', '')
    word = word.replace('<cb>', '')
    word = word.replace('<pb>', '')
    word = word.replace('P', '')
    word = word.replace('C', '')
    word = word.lower()
    # word = word.replace('[', '')
    # word = word.replace(']', '')
    # word = word.replace('\u0323', '')
    return word

def encode_word(raw_word: str, token: dict):
    if raw_word.startswith('P|'):
        token.update({'break_before': ['page', '?']})
    elif '-P-' in raw_word:
        token.update({'break_split': ['page', '?']})
    elif raw_word.startswith('C|'):
        token.update({'break_before': ['column', '2']})
    elif '-C-' in raw_word:
        token.update({'break_split': ['column', '2']})
    elif raw_word.startswith('|'):
        token.update({'break_before': ['line', '?']})
    elif '|' in raw_word:
        token.update({'break_split': ['line', '?']})
    if raw_word.startswith('[...]_'):
        token.update({'gap_before': True,
                      'gap_details': 'lac'})
    elif raw_word.endswith('_[...]'):
        token.update({'gap_after': True,
                      'gap_details': 'lac'})
    token.update({'raw_word': raw_word})
    return token

def text_to_witness_dict(text: str, siglum: str):
    witness = {'id': siglum,
               'text': text,
               'tokens': []}
    text = prepare_text(text)
    index = 2
    for word in text.split():
        if word in ['·', ',', '.', ':', '※', '⁘', '+', '~', '-']:
            continue
        raw_word = word
        word = regularize_word(word)
        token = initial_token(word, siglum, index)
        token = encode_word(raw_word, token)
        witness['tokens'].append(token)
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

def delete_hand(verse_dict: dict, siglum):
    for i, wit in enumerate(verse_dict['witnesses']):
        if wit['id'] == siglum:
            verse_dict['witnesses'].pop(i)
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