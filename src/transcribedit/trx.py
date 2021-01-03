import ctypes
import json
import os
import pathlib
import re
# import PySimpleGUIWeb as sg
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
        [sg.Button('Okay', size=(10, 2), pad=(10, 10), border_width=10), sg.Button('Cancel', size=(10, 2), pad=(10, 10), border_width=10)]]
    popup = sg.Window(title, layout, icon=icon)
    response, _ = popup.read()
    popup.close()
    return response

def okay_popup(message: str, title: str, icon):
    layout = [[sg.Text(message, pad=(10, 10))],
        [sg.Button('Okay', pad=(10, 10), border_width=10)]]
    popup = sg.Window(title, layout, icon=icon)
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

def basetext_by_ref(main_dir: str, ref: str, window, settings: dict, icon):
    if ref in ['', None]:
        okay_popup('Type the reference for the unit to load into the "Reference" field.', 'Forget Something?', icon)
    else:
        basetext, index = get_basetext(ref.replace('.', ':'), settings)
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
       if verse.startswith(ref):
           return i, f'{settings["wits_dir"]}/{siglum}/{verse}'

def load_witness(filename, siglum: str, window):
    with open(filename, 'r', encoding='utf-8') as file:
        verse_dict = json.load(file)
    update_display_verse(verse_dict, window, siglum, '2')
    return verse_dict

def basetext_by_index(settings, index, direction, window):
    basetext = open_basetext(settings['basetext_path'])
    if direction == 'Next>':
        index += 1
    elif direction == '<Prev':
        index -= 1
    basetext = basetext[index]
    ref = re.search(r'[A-Za-z0-9]+ [0-9]+:[0-9]+', basetext).group(0).strip()
    window['-transcription-'].update(value=basetext.replace(ref, '').strip())
    window['-ref-'].update(value=ref)
    return index

def hide_unused(window, start: int):
    for i in range(start, 151, 2):
        window[f'word{i}'].update(visible=False)

def initial_verse_rows():
    row1 = []
    row2 = []
    row3 = []
    row4 = []
    key = 2
    for _ in range(20):
        row1.append(sg.Text('', visible=False, key=f'word{key}', justification='left', enable_events=True, pad=(2, 5)))
        row1.append(sg.Stretch())
        key += 2
    for _ in range(20):
        row2.append(sg.Text('', visible=False, key=f'word{key}', justification='left', enable_events=True, pad=(2, 5)))
        key += 2
        row2.append(sg.Stretch())
    for _ in range(20):
        row3.append(sg.Text('', visible=False, key=f'word{key}', justification='left', enable_events=True, pad=(2, 5)))
        key += 2
    for _ in range(20):
        row4.append(sg.Text('', visible=False, key=f'word{key}', justification='left', enable_events=True, pad=(2, 5)))
        key += 2
    return row1, row2, row3, row4

def update_display_verse(verse_dict: dict, window, siglum, index: str):
    verse_words, hands = tt.get_words_from_dict(verse_dict, siglum)
    if verse_words == []:
        sg.popup_quick_message('That witness hand does not seem to exist.')
        return
    for i, word in zip(range(2, 151, 2), verse_words):
        window[f'word{i}'].update(value=word, visible=True)
    hide_unused(window, i+2)
    mt.load_token(index, verse_dict, siglum, window)
    highlight_selected(window, f'word{index}')
    window['-hands-'].update(value=', '.join(hands))
    window['-transcription-'].update(value=verse_dict['text'])
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
    if values['-hand-'] != '*':
        siglum = f'{values["-siglum-"]}{values["-hand-"]}'
    else:
        siglum = values['-siglum-']
    return siglum

def guard_token_values(values, icon):
    for k in ['-original-', '-rule_match-', '-siglum-']:
        if values[k] == '':
            okay_popup('"Original", "Rule Match", and "Siglum" fields must be filled.', 'Forgetting something?', icon)
            return False
    if values['-no_gap-'] is False and values['-gap_details-'] == '':
        okay_popup('If "Gap After" or "Gap Before" are selected, then "Gap Details" must be filled.', 'One more thing...', icon)
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

def set_marg_radios(window, setting: bool):
    window['-l_marg-'].update(disabled=setting)
    window['-r_marg-'].update(disabled=setting)
    window['-marg_above-'].update(disabled=setting)
    window['-marg_after-'].update(disabled=setting)

def update_verse_and_marg(verse_dict: dict, values: dict):
    verse_dict['text'] = values['-transcription-']
    verse_dict['verse_note'] = values['verse_note']
    if values['verse_marg_type'] != '':
        verse_dict['verse_marginale'] = {
            'type': values['verse_marg_type'], 
            'loc': values['verse_marg_loc'], 
            'tx': values['verse_marg_tx']}
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

def get_layout():
    menu = [['File', ['!Check for Updates', 'Settings', '---', 'Exit']]]
    
    submitted1, submitted2, submitted3, submitted4 = initial_verse_rows()

    submitted_frame = [submitted1,
                       submitted2,
                       submitted3,
                       submitted4]

    note_col = [[sg.Text('Word Note')],
               [sg.Multiline(size=(None, 8), key='-note-')]]

    main_info_col = [[sg.Text('Index'), sg.Input('', key='-index-', disabled=True, size_px=(170, 40))],
                     [sg.Text('original'), sg.Input('', key='-original-')],
                     [sg.Radio('No Gap', 'gap', default=True, key='-no_gap-')],
                     [sg.Radio('Gap After', 'gap', key='-gap_after-'), sg.Radio('Gap Before', 'gap', key='-gap_before-')],
                     [sg.Text('Gap Details'), sg.Input('', key='-gap_details-')]]

    values_col = [[sg.Text('Image ID'), sg.Input('', size_px=(160, 40), key='-image_id-')],
                  [sg.Text('Page'), sg.Input('', size_px=(160, 40), key='-page-')],
                  [sg.Text('Break'), sg.Combo(['after', 'before', 'split', None], readonly=True, size_px=(100, 40), key='break_place', enable_events=True), sg.Combo(['line', 'column', 'page', None], size_px=(100, 40), key='break_type', readonly=True), sg.Input('', key='break_num', size_px=(70, 40))],
                  [sg.Text('Rule Match'), sg.Input('', key='-rule_match-')]]

    values_col2 = [[sg.Text('Correction', justification='center')],
                   [sg.Text('First Hand Reading'), sg.Input('', key='-first_hand_rdg-')],
                   [sg.Text('Type'), sg.Combo(['deletion', 'addition', 'substitution', None], readonly=True, size_px=(170, 40), key='-corr_type-')],
                   [sg.Text('Method'), sg.Combo(['above', 'left marg', 'right marg', 'overwritten', 'scraped', 'strikethrough', 'under', None], readonly=True, size_px=(170, 40), key='-corr_method-')],
                   [sg.Button('Submit Edits')]]
    
    values_col3 = [[sg.Text('Marginale Type'), sg.Input('', key='-marg_type-')],
                   [sg.Combo(['after word', 'above word', 'before word', 'below word', 'margin left', 'margin right', 'margin top', 'margin bottom', 'None'], default_value='None', size_px=(170, 40), readonly=True, key='marg_loc')],
                #    [sg.Radio('left margin', 'marg', disabled=True, key='-l_marg-'), sg.Radio('right margin', 'marg', disabled=True, key='-r_marg-')], 
                #    [sg.Radio('after word', 'marg', disabled=True, key='-marg_after-'), sg.Radio('above word', 'marg', disabled=True, key='-marg_above-')],
                   [sg.Button('ϛ'), sg.Button('Ϙ'), sg.Button('⁘ +')],
                   [sg.Multiline('', key='-marg_tx-')]]

    edit_kv_frame = [[sg.Column(note_col), sg.Column(main_info_col), sg.Column(values_col), sg.Column(values_col2), sg.Column(values_col3)]]

    transcription_frame = [[sg.Button('Load Basetext'), sg.Button('Load Witness'), sg.Button('Submit Verse'), sg.Button('Update Verse Text'), sg.Button('Show Editing Options'), sg.Button('Hide Editing Options'), sg.Button('Save'), sg.Combo(['Symbol', '·', '⁘ +', '※', 'ϗ', 'underdot'], size_px=(170, 40), key='-symbol-', enable_events=True, readonly=True)],
                            [sg.Multiline('', key='-transcription-', size_px=(1700, 400), font=('Cambria', 14))]]

    verse_note_frame = [[sg.Text('Verse Notes', justification='center')],
                        [sg.Multiline('', key='verse_note', size_px=(400, 150), font=('Cambria', 14))],
                        [sg.Text('Marginale Type', size_px=(180, 40)), sg.Input('', key='verse_marg_type', size_px=(220, 40))],
                        [sg.Combo(['above', 'below', 'margin left', 'margin right', 'margin top', 'margin bottom'], key='verse_marg_loc', size_px=(400, 40), readonly=True)],
                        [sg.Multiline('', size_px=(405, 150), key='verse_marg_tx')]]

    return [[sg.Menu(menu)],
            [sg.Frame('', submitted_frame, key='submitted_frame')],
            [sg.Frame('Edit Data', edit_kv_frame, visible=True, key='-edit_frame-', pad=(0,0))],
            [sg.Button('<Prev'), sg.Text('Reference'), sg.Input('', key='-ref-'), 
                sg.Button('Next>'), sg.Text('Witness Siglum'), 
                sg.Input('', key='-siglum-'), sg.Text('Hand'), 
                sg.Combo(['*', 'a', 'b', 'c', 'd', 'e', 'f'], readonly=True, size_px=(60, 40), key='-hand-', enable_events=True),
                sg.Text('Hands in Witness:'), sg.Input('', disabled=True, key='-hands-')],
            [sg.Frame('Transcription', transcription_frame, visible=True, pad=(0,0)), sg.Frame('', verse_note_frame, pad=(0,0))]]

def main():
    version = 0.1
    layout = get_layout()
    main_dir = pathlib.Path(__file__).parent.as_posix()
    icon = f'{main_dir}/resources/transcribedit.ico'
    settings = get_settings(main_dir)
    window = sg.Window(f'transcripEdIt   v{version}', layout, icon=icon)
    basetext_index = None
    verse_dict = None

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
            basetext_index = basetext_by_ref(main_dir, values['-ref-'], window, settings, icon)

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
            except:
                okay_popup('The file could not be loaded.', 'Bummer', icon)

        elif event in ['<Prev', 'Next>']:
            basetext_index = basetext_by_index(settings, basetext_index, event, window)

        elif event == 'Submit Verse':
            if values['-hand-'] == '*':
                verse_dict = submit_verse(values, window, icon)
            elif verse_dict is not None:
                submit_corrector_hand(verse_dict, values['-transcription-'], values['-ref-'], get_siglum_hand(values), window, icon)

        elif event.startswith('word'):
            highlight_selected(window, event)
            mt.load_token(event.replace('word', ''), verse_dict, get_siglum_hand(values), window)

        elif event == 'Submit Edits':
            if verse_dict is None or okay_or_cancel('Replace current token with new values?', 'Double-checking with you', icon) == 'Cancel':
                continue
            if guard_token_values(values, icon) is True:
                token = mt.make_new_token(values, get_siglum_hand(values))
                siglum = get_siglum_hand(values)
                verse_dict = tt.update_token(token, int(values['-index-']), verse_dict, siglum)
                update_display_verse(verse_dict, window, siglum, values['-index-'])

        # elif event == '-marg_type-':
        #     if values['-marg_type-'] != '':
        #         set_marg_radios(window, False)
        #     else:
        #         set_marg_radios(window, True)

        elif event == 'Save':
            if verse_dict is None:
                okay_popup('There is no submitted verse to save.', 'No Submitted Verse', icon)
                continue
            saved_path = save_tx(verse_dict, values['-siglum-'], settings, values['-ref-'])
            if saved_path is None:
                okay_popup('The witnesses directory has not been set.\n\
Please set your witnesses output folder in settings by navigating to File>Settings.', 'Witnesses Directory not Set', icon)
                continue
            okay_popup(f'JSON formatted transcription file was succesfully saved to\n\
{saved_path}', 'Saved!', icon)

        elif event == '-hand-':
            if verse_dict is not None:
                update_display_verse(verse_dict, window, get_siglum_hand(values), values['-index-'])

        elif event == 'Settings':
            settings = set_settings(settings, main_dir, icon)

        elif event == '-symbol-' and values['-symbol-'] != 'Symbol':
            if values['-symbol-'] == 'underdot':
                window['-transcription-'].update(value=f'\u0323', append=True)
                window['-symbol-'].update(set_to_index=0)
            else:
                window['-symbol-'].update(set_to_index=0)
                window['-transcription-'].update(value=f'{values["-symbol-"]}', append=True)
            window['-transcription-'].set_focus()

        elif event in ['⁘ +', 'ϛ', 'Ϙ']:
            window['-marg_tx-'].update(value=f'{event}', append=True)
            window['-marg_tx-'].set_focus()

        elif event == 'Update Verse Text':
            if verse_dict is not None:
                verse_dict = update_verse_and_marg(verse_dict, values)
            else:
                sg.popup_quick_message('First submit or load a verse')

        # print(event, values)
    window.close()
