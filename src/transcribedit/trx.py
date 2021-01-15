import ctypes
import json
import os
import pathlib
import re
import transcribedit.PySimpleGUIQt as sg
import transcribedit.manage_token as mt
from transcribedit.set_settings import set_settings
import transcribedit.tokenize_text as tt


def get_settings(main_dir: str):
    try:
        with open(f'{main_dir}/resources/settings.json', 'r') as file:
            return json.load(file)
    except:
        settings = {"wits_dir": "",
                    "basetext_path": "",
                    "theme": "Parchment",
                    "font": "Cambria 12",
                    "dpi": True}
        with open(f'{main_dir}/resources/settings.json', 'w') as file:
            json.dump(settings, file, indent=4)
        return settings

main_dir = pathlib.Path(__file__).parent.as_posix()
settings = get_settings(main_dir)
sg.set_options(font=settings['font'])
if settings['theme'] == 'Grey':
    sg.theme('LightGrey2')
else:
    sg.LOOK_AND_FEEL_TABLE['Parchment'] = {'BACKGROUND': '#FFE9C6', 'TEXT': '#533516', 'INPUT': '#EAC8A3', 'TEXT_INPUT': '#2F1B0A', 'SCROLL': '#B39B73', 'BUTTON': ('white', '#C55741'), 'PROGRESS': ('#01826B', '#D0D0D0'), 'BORDER': 3, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0}
    sg.LOOK_AND_FEEL_TABLE['DarkMode'] = {'BACKGROUND': '#161D20', 'TEXT': '#039386', 'INPUT': '#32434B', 'TEXT_INPUT': '#89DDFF', 'SCROLL': '#B39B73', 'BUTTON': ('white', '#2E3437'), 'PROGRESS': ('#01826B', '#D0D0D0'), 'BORDER': 3, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0}
    sg.theme(settings['theme'])
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(settings['dpi']) # for Windows users with high resolution (greater than 1080x1920) monitors.
except:
    pass

def okay_or_cancel(message: str, title: str, icon):
    layout = [[sg.Text(message, pad=(10, 10))],
        [sg.Button('Okay', pad=(10, 10)), sg.Stretch(), sg.Button('Cancel', pad=(10, 10))]]
    popup = sg.Window(title, layout, icon=icon, return_keyboard_events=True)
    while True:
        response, _ = popup.read()
        if response in [sg.WINDOW_CLOSED, 'Cancel', 'special 16777216']: # special = Esc
            response = 'Cancel'
            break
        elif response in ['Okay', 'special 16777220']: # special = Enter
            response = 'Okay'
            break
    popup.close()
    return response

def okay_popup(message: str, title: str, icon):
    layout = [[sg.Text(message, pad=(10, 10))],
        [sg.Stretch(), sg.Button('Okay', pad=(10, 10)), sg.Stretch()]]
    popup = sg.Window(title, layout, icon=icon, return_keyboard_events=True)
    popup.read()
    popup.close()

def open_basetext(basetext_path: str):
    with open(basetext_path, 'r', encoding='utf-8') as file:
        return file.readlines()

def get_basetext(ref, settings):
    basetext = open_basetext(settings['basetext_path'])
    for i, verse in enumerate(basetext):
        if verse.startswith(ref):
            return verse.replace(ref, '').strip(), i
    return None, None

def basetext_by_ref(main_dir: str, ref: str, window, settings: dict, icon):
    if ref in ['', None]:
        okay_popup('Type the reference for the unit to load into the "Reference" field.', 'Forget Something?', icon)
    else:
        basetext, index = get_basetext(ref.replace('.', ':'), settings)
        if basetext is None:
            sg.popup_quick_message(f'{ref} is not present in the basetext file.')
        window['-transcription-'].update(value=basetext)
        return index

def witness_by_ref(ref: str, siglum: str, main_dir, settings: dict, icon):
    try:
        all_verses = os.listdir(f"{settings['wits_dir']}/{siglum}")
    except:
        okay_popup(f'Could not find {settings["wits_dir"]}/{siglum}/', 'Could not find folder', icon)
        return None
    ref = ref.replace(' ', '')
    ref = ref.replace(':', '.')
    for i, verse in enumerate(all_verses):
        verse_ref = verse.replace('.json', '')
        if verse_ref == ref:
           return i, f'{settings["wits_dir"]}/{siglum}/{verse}'

def load_witness(filename, siglum: str, window):
    with open(filename, 'r', encoding='utf-8') as file:
        verse_dict = json.load(file)
    update_display_verse(verse_dict, window, siglum, '2')
    return verse_dict

def basetext_by_index(settings, index, direction, window, icon):
    if index is None:
        sg.popup_quick_message('Basetext must be loaded before moving to adjacent verses.')
        return
    basetext = open_basetext(settings['basetext_path'])
    if direction == 'Next>':
        index += 1
    elif direction == '<Prev':
        index -= 1
    basetext = basetext[index]
    ref = re.search(r'[A-Za-z0-9 ]+:[0-9]+', basetext)
    try:
        ref = ref.group(0).strip()
    except AttributeError:
        okay_popup(f'The following line in the basetext file is not introduced with an SBL style reference:\n\
"{basetext.strip()}"\nThis is probably a book title. Ideally, the basetext file\n\
should contain only verses preceded by SBL references, e.g. "Rom 3:23"', 'Cannot Load Basetext', icon)
        return index
    window['-transcription-'].update(value=basetext.replace(ref, '').strip())
    window['-ref-'].update(value=ref)
    return index

def hide_unused(window, start: int):
    for i in range(start, 151, 2):
        window[f'word{i}'].update(visible=False)

def display_words_from_dict(tokens, window):
    for i, token in zip(range(2, 151, 2), tokens):
        word = token['original']
        marg_sigla = []
        if 'marginale' in token:
            marg_sigla.append('^')
        if 'note' in token:
            marg_sigla.append('*')
        if 'corr_type' in token:
            marg_sigla.append('`')
        if 'break_after' in token:
            marg_sigla.append('|')
        elif 'break_before' in token:
            word = f'|{word}'
        if marg_sigla != []:
            word = f'{word}{"".join(marg_sigla)}'
        window[f'word{i}'].update(value=word, visible=True)
    return i # type: ignore

def update_display_verse(verse_dict: dict, window, siglum, index: str):
    verse_words, hands = tt.get_words_from_dict(verse_dict, siglum)
    if verse_words == [] or verse_words is None:
        print(verse_words)
        sg.popup_quick_message('That witness hand does not seem to exist.')
        return
    i = display_words_from_dict(verse_words, window)
    hide_unused(window, i+2)
    mt.load_token(index, verse_dict, siglum, window)
    highlight_selected(window, f'word{index}')
    window['-hands-'].update(value=', '.join(hands))
    try:
        window['-transcription-'].update(value=verse_dict['text'])
    except KeyError:
        window['-transcription-'].update(value='')
    try:
        window['verse_note'].update(value=verse_dict['verse_note'])
    except KeyError:
        window['verse_note'].update(value='')
    if 'verse_marginale' in verse_dict:
        window['verse_marg_type'].update(value=verse_dict['verse_marginale']['type'])
        window['verse_marg_loc'].update(values=['above', 'below', 'margin left', 'margin right', 'margin top', 'margin bottom'], value=verse_dict['verse_marginale']['loc'])
        window['verse_marg_tx'].update(value=verse_dict['verse_marginale']['tx'])
    else:
        window['verse_marg_type'].update(value='')
        window['verse_marg_tx'].update(value='')
        window['verse_marg_loc'].update(set_to_index=0)

def submit_verse(values: dict, window, icon):
    response = okay_or_cancel('Confirm transcription submission. This will overwrite all previously saved verse data.', 'Confirm Submission', icon)
    if response == 'Cancel':
        return
    if '' in [values['-transcription-'], values['-ref-'], values['-siglum-']]:
        okay_popup('Transcription, Reference, and Siglum fields must be filled.', 'Forgetting something?', icon)
        return
    tokenized_verse = tt.orig_to_dict(values)
    update_display_verse(tokenized_verse, window, values['-siglum-'], '2')
    return tokenized_verse

def submit_corrector_hand(verse_dict: dict, text: str, ref: str, siglum: str, window, icon):
    response = okay_or_cancel('Confirm transcription submission. This will overwrite all previously saved data for this hand.', 'Confirm Submission', icon)
    if response == 'Cancel':
        return
    if '' in [text, ref, siglum]:
        okay_popup('Transcription, Reference, and Siglum fields must be filled.', 'Forgetting something?', icon)
        return
    verse_dict = tt.add_hand_to_dict(verse_dict, text, siglum)
    update_display_verse(verse_dict, window, siglum, '2')
    return verse_dict

def get_siglum_hand(values):
    if values['-hand-'].strip() != '*':
        siglum = f'{values["-siglum-"]}{values["-hand-"]}'
    else:
        siglum = values['-siglum-']
    return siglum

def guard_token_values(values, icon):
    for k in ['-original-', '-rule_match-', '-siglum-']:
        if values[k] == '':
            okay_popup('"Original", "Rule Match", and "Siglum" fields must be filled.', 'Forgetting something?', icon)
            return False
    if values['gap'] not in ['no gap', ''] and values['gap_details'] in ['', '(gap details)']:
        okay_popup('If "gap after" or "gap before" are selected, then "Gap Details" must be filled.', 'One more thing...', icon)
        return False
    return True

def highlight_selected(window, event):
    window[event].update(background_color='#C7EAA3')
    key = 2
    for _ in range(75):
        if str(key) == event.replace('word', ''):
            key += 2
            continue
        window[f'word{key}'].update(background_color=sg.DEFAULT_BACKGROUND_COLOR)
        key += 2

def update_verse_and_marg(verse_dict: dict, values: dict):
    verse_dict['text'] = values['-transcription-']
    verse_dict['verse_note'] = values['verse_note']
    if values['verse_marg_type'] != '':
        verse_dict['verse_marginale'] = {
            'type': values['verse_marg_type'], 
            'loc': values['verse_marg_loc'], 
            'tx': values['verse_marg_tx']}
    elif values['verse_marg_type'] == '' and 'verse_marginale' in verse_dict:
        verse_dict.pop('verse_marginale')
    sg.popup_quick_message('Verse text and/or verse note updated')
    return verse_dict

def get_metadata(siglum):
    return {'_id': siglum, 'siglum': siglum}

def save_tx(verse_dict: dict, siglum: str, settings: dict, ref: str):
    ref = ref.replace(':', '.')
    ref = ref.replace(' ', '')
    wits_dir = settings['wits_dir']
    if wits_dir == '':
        return None
    wit_folder = f'{wits_dir}/{siglum}'
    if not os.path.exists(wit_folder):
        os.makedirs(wit_folder, exist_ok=True)
    with open(f'{wit_folder}/{ref}.json', 'w', encoding='utf-8') as file:
        json.dump(verse_dict, file, ensure_ascii=False)
    if not os.path.exists(f'{wit_folder}/metadata.json'):
        with open(f'{wit_folder}/metadata.json', 'w') as file:
            json.dump(get_metadata(siglum), file, indent=4)
    return f'{wit_folder}/{ref}.json'

def save(verse_dict: dict, values, icon):
    if verse_dict is None:
        okay_popup('There is no submitted verse to save.', 'No Submitted Verse', icon)
        return
    verse_dict = update_verse_and_marg(verse_dict, values)
    saved_path = save_tx(verse_dict, values['-siglum-'], settings, values['-ref-'])
    if saved_path is None:
        okay_popup('The witnesses directory has not been set.\n\
Please set your witnesses output folder in settings by navigating to File>Settings.', 'Witnesses Directory not Set', icon)
        return verse_dict
    okay_popup(f'JSON formatted transcription file was succesfully saved to\n\
{saved_path}', 'Saved!', icon)
    return verse_dict

def initial_verse_rows():
    row1 = []
    row2 = []
    row3 = []
    row4 = []
    key = 2
    for _ in range(20):
        row1.append(sg.Text('', visible=False, key=f'word{key}', justification='left', enable_events=True, pad=(2, 3)))
        row1.append(sg.Stretch())
        key += 2
    for _ in range(20):
        row2.append(sg.Text('', visible=False, key=f'word{key}', justification='left', enable_events=True, pad=(2, 3)))
        key += 2
        row2.append(sg.Stretch())
    for _ in range(20):
        row3.append(sg.Text('', visible=False, key=f'word{key}', justification='left', enable_events=True, pad=(2, 3)))
        row3.append(sg.Stretch())
        key += 2
    for _ in range(20):
        row4.append(sg.Text('', visible=False, key=f'word{key}', justification='left', enable_events=True, pad=(2, 3)))
        row4.append(sg.Stretch())
        key += 2
    return row1, row2, row3, row4

def get_layout():
    s = sg.Stretch()
    menu = [['File', ['!Check for Updates', 'Settings', '---', 'Exit']]]
    
    submitted1, submitted2, submitted3, submitted4 = initial_verse_rows()

    submitted_frame = [submitted1,
                       submitted2,
                       submitted3,
                       submitted4]

    note_col = [[s, sg.Text('Word Note'), s],
               [sg.Multiline('', key='-note-')]]

    main_info_col = [[sg.Text('Index'), s, sg.Input('', key='-index-', disabled=True)],
                     [sg.Text('Original'), s, sg.Input('', key='-original-')],
                     [sg.Text('Rule Match'), s, sg.Input('', key='-rule_match-')],
                     [sg.Text('Collate'), s, sg.Input('', key='to_collate')]]

    values_col = [[sg.Text('Image ID'), s, sg.Input('', key='-image_id-')],
                  [sg.Text('Page'), s, sg.Input('', key='-page-')],
                  [sg.Text('Break'), sg.Combo(['', 'after', 'before', 'split'], readonly=True, key='break_place', default_value='no break'), sg.Combo(['line', 'column', 'page', None], key='break_type', readonly=True), sg.Input('', key='break_num', size_px=(120, 40))],
                  [sg.Combo(['', 'gap after', 'gap before'], default_value='no gap', key='gap', readonly=True), sg.Input('(gap details)', key='gap_details')]]

    corr_tip = 'For when the currently selected hand is NOT the first (*) hand'

    values_col2 = [[sg.Text('Correction', justification='center', tooltip=corr_tip)],
                   [sg.Text('First Hand Reading'), s, sg.Input('', key='-first_hand_rdg-', tooltip=corr_tip)],
                   [sg.Text('Type'), s, sg.Combo(['', 'deletion', 'addition', 'substitution'], readonly=True, key='-corr_type-')],
                   [sg.Text('Method'), s, sg.Combo(['', 'above', 'left marg', 'right marg', 'overwritten', 'scraped', 'strikethrough', 'under'], readonly=True, key='-corr_method-')],
                   [sg.Button('Submit Edits')]]
    
    values_col3 = [[sg.Text('Marginale Type'), s, sg.Input('', key='-marg_type-')],
                   [sg.Combo(['', 'after word', 'above word', 'before word', 'below word', 'margin left', 'margin right', 'margin top', 'margin bottom'], default_value='', readonly=True, key='marg_loc'),
                              s, sg.Combo(['Symbol         ', 'ϛ', 'Ϙ', '·', '⁘', '※', 'ϗ', 'underdot', 'overline', '\u2627', '\u2ce8', '\u2020', '–'], key='marg_word_symbol', enable_events=True, readonly=True)],
                #    [sg.Button('ϛ'), sg.Button('Ϙ'), sg.Button('⁘ +')],
                   [sg.Multiline('', key='-marg_tx-')]]

    edit_kv_frame = [[sg.Column(note_col), sg.VerticalSeparator(), 
                      sg.Column(main_info_col), sg.VerticalSeparator(), 
                      sg.Column(values_col), sg.VerticalSeparator(), 
                      sg.Column(values_col2), sg.VerticalSeparator(), 
                      sg.Column(values_col3)]]

    transcription_frame = [
                           [sg.Button('  Load Basetext  ', key='Load Basetext'), s, 
                            sg.Button('  Load Witness  ', key='Load Witness'), s, 
                            sg.Button('  Submit Verse  ', key='Submit Verse'), s, 
                            sg.Button('  Update Verse Text  ', key='Update Verse Text'), s,
                            sg.Button('  Show Editing Options ', key='Show Editing Options'), s, 
                            sg.Button('  Hide Editing Options  ', key='Hide Editing Options'), s,
                            sg.Button('  Save  ', key='Save'), s,
                            sg.Combo([' Symbol ', '·', '⁘', 'ϛ', 'Ϙ', '※', 'ϗ', 'underdot', 'overline', '\u2627', '\u2ce8', '\u2020', '\u0345'], 
                                      key='-symbol-', enable_events=True, readonly=True)
                                      ],
                            [sg.Multiline('', key='-transcription-', font=('Cambria', 14))]]

    verse_note_frame = [
                        [sg.Multiline('', key='verse_note', font=('Cambria', 14))],
                        [sg.Text('Marginale Type'), s, sg.Input('', key='verse_marg_type')],
                        [sg.Combo(['', 'above', 'below', 'margin left', 'margin right', 'margin top', 'margin bottom'], key='verse_marg_loc', readonly=True), s,
                            sg.Combo(['Symbol         ', 'ϛ', 'Ϙ', '·', '⁘', '※', 'ϗ', 'underdot', 'overline', '\u2627', '\u2ce8', '\u2020', '–'], key='marg_verse_symbol', enable_events=True, readonly=True)],
                        [sg.Multiline('', key='verse_marg_tx')]]

    layout = [[sg.Menu(menu)],
            [sg.Frame('', submitted_frame, key='submitted_frame')],
            [sg.Frame('Edit Data', edit_kv_frame, visible=True, key='-edit_frame-')],
            [sg.HorizontalSeparator()],
            [sg.Text('Reference'), sg.Input('', key='-ref-'),
                sg.VerticalSeparator(), sg.Text('Witness Siglum'),
                sg.Input('', key='-siglum-'), sg.VerticalSeparator(), sg.Text('Hand'),
                sg.Combo(['*    ', 'a', 'b', 'c', 'd', 'e', 'f'], readonly=True, key='-hand-', enable_events=True),
                sg.Text('Hands in Witness:'), sg.Input('', disabled=True, key='-hands-'), sg.Stretch()],
            [sg.Frame('Transcription', transcription_frame, visible=True), sg.Frame('Verse Notes', verse_note_frame)]]

    return layout

def main():
    version = 0.1
    layout = get_layout()
    main_dir = pathlib.Path(__file__).parent.as_posix()
    icon = f'{main_dir}/resources/transcribedit.ico'
    settings = get_settings(main_dir)
    window = sg.Window(f'transcribEdIt   v{version}', layout, icon=icon, return_keyboard_events=True)
    basetext_index = None
    verse_dict = None
    word_index = None

    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, None, 'Exit'):
            break
        
        elif event == 'Show Editing Options':
            window['-edit_frame-'].update(visible=True)
            window['submitted_frame'].update(visible=True)

        elif event == 'Hide Editing Options':
            window['-edit_frame-'].update(visible=False)
            window['submitted_frame'].update(visible=False)
            window.visibility_changed()

        elif event == 'Load Basetext':
            if values['-ref-'] == '':
                okay_popup('In order to know which verse from the basetext to load,\n\
the "Reference" field must be filled.', 'Silly Goose', icon)
                continue
            new_vt_index = basetext_by_ref(main_dir, values['-ref-'], window, settings, icon)
            if new_vt_index is not None:
                basetext_index = new_vt_index

        elif event == 'Load Witness':
            if '' in [values['-ref-'], values['-siglum-']]:
                okay_popup('Which verse? Which witness? The "Reference" and "Siglum" fields must be filled.', 'Silly Goose', icon)
                continue
            try:
                _, wit_file = witness_by_ref(values['-ref-'], values['-siglum-'], main_dir, settings, icon) # wit_index is for getting the next or previous verse
            except:
                sg.popup_quick_message('No file found')
                continue
            try:
                verse_dict = load_witness(wit_file, get_siglum_hand(values), window)
                word_index = '2'
            except:
                okay_popup('The file could not be loaded.', 'Bummer', icon)

        elif event == 'special 16777272':
            basetext_index = basetext_by_index(settings, basetext_index, '<Prev', window, icon)

        elif event == 'special 16777273':
            basetext_index = basetext_by_index(settings, basetext_index, 'Next>', window, icon)

        elif event == 'Submit Verse':
            if values['-hand-'].strip() == '*':
                verse_dict = submit_verse(values, window, icon)
                word_index = '2'
            elif verse_dict is not None:
                submit_corrector_hand(verse_dict, values['-transcription-'], values['-ref-'], get_siglum_hand(values), window, icon)
                word_index = '2'
            # verse_dict = save(verse_dict, values, icon)

        elif event.startswith('word'):
            word_index = event.replace('word', '')
            highlight_selected(window, event)
            mt.load_token(event.replace('word', ''), verse_dict, get_siglum_hand(values), window)

        elif event in ['Submit Edits', 'special 16777266']:
            if verse_dict is None or okay_or_cancel('Replace current token with new values?', 'Double-checking with you', icon) == 'Cancel':
                continue
            if guard_token_values(values, icon) is True:
                token = mt.make_new_token(values, get_siglum_hand(values))
                siglum = get_siglum_hand(values)
                verse_dict = tt.update_token(token, int(values['-index-']), verse_dict, siglum)
                
                update_display_verse(verse_dict, window, siglum, values['-index-'])

        elif event in ['Save', 'special 16777264']:
            verse_dict = save(verse_dict, values, icon)

        elif event == 'Settings':
            settings = set_settings(settings, main_dir, icon)

        elif event == 'special 16777267': # F4
            window['-transcription-'].update(value='·', append=True)

        elif event == 'special 16777268': # F5
            window['-transcription-'].update(value='\u0305', append=True)

        elif event == '-symbol-' and values['-symbol-'] != ' Symbol ':
            if values['-symbol-'] == 'underdot':
                window['-transcription-'].update(value='\u0323', append=True)
                window['-symbol-'].update(set_to_index=0)
            elif values['-symbol-'] == 'overline':
                window['-transcription-'].update(value='\u0305', append=True)
                window['-symbol-'].update(set_to_index=0)
            else:
                window['-symbol-'].update(set_to_index=0)
                window['-transcription-'].update(value=f'{values["-symbol-"]}', append=True)
            window['-transcription-'].set_focus() # pylint: disable=no-member

        elif event == 'marg_word_symbol' and values['marg_word_symbol'] != 'Symbol         ':
            if values['marg_word_symbol'] == 'underdot':
                window['-marg_tx-'].update(value='\u0323', append=True)
                window['marg_word_symbol'].update(set_to_index=0)
            elif values['marg_word_symbol'] == 'overline':
                window['-marg_tx-'].update(value='\u0305', append=True)
                window['marg_word_symbol'].update(set_to_index=0)
            else:
                window['-marg_tx-'].update(value=values['marg_word_symbol'], append=True)
                window['marg_word_symbol'].update(set_to_index=0)
            window['-marg_tx-'].set_focus() # pylint: disable=no-member

        elif event == 'marg_verse_symbol' and not values['marg_verse_symbol'].startswith('Symbol'):
            if values['marg_verse_symbol'] == 'underdot':
                window['verse_marg_tx'].update(value='\u0323', append=True)
                window['marg_verse_symbol'].update(set_to_index=0)
            elif values['marg_verse_symbol'] == 'overline':
                window['verse_marg_tx'].update(value='\u0305', append=True)
                window['marg_verse_symbol'].update(set_to_index=0)
            else:
                window['verse_marg_tx'].update(value=values['marg_verse_symbol'], append=True)
                window['marg_verse_symbol'].update(set_to_index=0)
            window['verse_marg_tx'].set_focus() # pylint: disable=no-member

        elif event in ['Update Verse Text', 'special 16777265']:
            if verse_dict is not None:
                verse_dict = update_verse_and_marg(verse_dict, values)
            else:
                sg.popup_quick_message('First submit or load a verse')

        elif event == 'special 16777274':
            if word_index not in [None, '2']:
                i = int(word_index)-2
                word_index = str(i)
                word = f'word{word_index}'
                highlight_selected(window, word)
                mt.load_token(word_index, verse_dict, get_siglum_hand(values), window)

        elif event == 'special 16777275':
            if word_index is not None:
                i = int(word_index)+2
                word = f'word{i}'
                try:
                    mt.load_token(word.replace('word', ''), verse_dict, get_siglum_hand(values), window)
                    highlight_selected(window, word)
                    word_index = word.replace('word', '')
                except IndexError:
                    pass

        elif event == 'special 16777269': # F6
            window['-marg_type-'].update(value='section number')
            window['-marg_type-'].set_focus() # pylint: disable=no-member

        # print(event)
    window.close()

# special 16777216 = Esc
# special 16777264 = F1
# special 16777265 = F2
# special 16777266 = F3
# special 16777267 = F4
# special 16777268 = F5
# special 16777269 = F6
# special 16777270 = F7
# special 16777271 = F8
# special 16777223 = Delete
# special 16777220 = Enter