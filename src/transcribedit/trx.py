import ctypes
import json
import os
import pathlib
import re
# import PySimpleGUIWeb as sg
import transcribedit.manage_token as mt
from transcribedit.set_settings import set_settings
import transcribedit.tokenize_text as tt
import transcribedit.PySimpleGUIQt as sg


sg.LOOK_AND_FEEL_TABLE['Parchment'] = {'BACKGROUND': '#FFE9C6',
                                        'TEXT': '#533516',
                                        'INPUT': '#EAC8A3',
                                        'TEXT_INPUT': '#2F1B0A',
                                        'SCROLL': '#B39B73',
                                        'BUTTON': ('white', '#C55741'),
                                        'PROGRESS': ('#01826B', '#D0D0D0'),
                                        'BORDER': 3, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0,
                                        }
sg.LOOK_AND_FEEL_TABLE['DarkMode'] = {'BACKGROUND': '#161D20',
                                        'TEXT': '#039386',
                                        'INPUT': '#32434B',
                                        'TEXT_INPUT': '#89DDFF',
                                        'SCROLL': '#B39B73',
                                        'BUTTON': ('white', '#2E3437'),
                                        'PROGRESS': ('#01826B', '#D0D0D0'),
                                        'BORDER': 3, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0,
                                        }

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

def submit_verse(verse: str, ref: str, siglum: str, window, icon):
    response = okay_or_cancel('Confirm transcription submission. This will overwrite all previously saved verse data.', 'Confirm Submission', icon)
    if response == 'Cancel':
        return
    if '' in [verse, ref, siglum]:
        okay_popup('Transcription, Reference, and Siglum fields must be filled.', 'Forgetting something?', icon)
        return
    tokenized_verse = tt.orig_to_dict(verse, siglum, ref)
    update_display_verse(tokenized_verse, window, siglum, '2')
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
    if values['-hand-'] != 'First':
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

def get_metadata(siglum):
    return {'_id': siglum, 'siglum': siglum}

def save_tx(verse_dict: dict, siglum: str, settings: dict, ref: str):
    ref = ref.replace(':', '.')
    ref = ref.replace(' ', '')
    wits_dir = settings['wits_dir']
    wit_folder = f'{wits_dir}/{siglum}'
    if not os.path.exists(wit_folder):
        os.makedirs(wit_folder, exist_ok=True)
    with open(f'{wit_folder}/{ref}.json', 'w', encoding='utf-8') as file:
        json.dump(verse_dict, file)
    if not os.path.exists(f'{wit_folder}/metadata.json'):
        with open(f'{wit_folder}/metadata.json', 'w') as file:
            json.dump(get_metadata(siglum), file, indent=4)
    return f'{wit_folder}/{ref}.json'

def get_layout():
    menu = [['File', ['Settings', '---', 'Exit']]]
    
    submitted1, submitted2, submitted3, submitted4 = initial_verse_rows()

    submitted_frame = [submitted1,
                       submitted2,
                       submitted3,
                       submitted4]

    note_col = [[sg.Text('Note')],
               [sg.Multiline(size=(None, 8), key='-note-')]]

    main_info_col = [[sg.Text('Index'), sg.Input('', key='-index-', disabled=True, size_px=(170, 40))],
                     [sg.Text('original'), sg.Input('', key='-original-')],
                     [sg.Radio('No Gap', 'gap', default=True, key='-no_gap-')],
                     [sg.Radio('Gap After', 'gap', key='-gap_after-'), sg.Radio('Gap Before', 'gap', key='-gap_before-')],
                     [sg.Text('Gap Details'), sg.Input('', key='-gap_details-')]]

    values_col = [[sg.Text('Page'), sg.Input('', size_px=(160, 40), key='-page-')],
                  [sg.Text('Break After'), sg.Combo(['line break', 'page break', 'column break', None], readonly=True, size_px=(160, 40), key='-break_after-'), sg.Spin([i for i in range(41)], key='-break_after_num-', size_px=(60, 40), initial_value=0)],
                  [sg.Text('Break Before'), sg.Combo(['line break', 'page break', 'column break', None], readonly=True, size_px=(160, 40), key='-break_before-'), sg.Spin([i for i in range(41)], key='-break_before_num-', size_px=(60, 40), initial_value=0)],
                  [sg.Text('Split'), sg.Combo(['line break', 'page break', 'column break', None], readonly=True, size_px=(160, 40), key='-split-'), sg.Spin([i for i in range(41)], key='-split_num-', size_px=(60, 40), initial_value=0)],
                  [sg.Text('Rule Match'), sg.Input('', key='-rule_match-')]]

    values_col2 = [[sg.Text('Image ID'), sg.Input('', size_px=(160, 40), key='-image_id-')],
                  [sg.Text('Correction', justification='center')],
                  [sg.Text('First Hand Reading'), sg.Input('', key='-first_hand_rdg-')],
                  [sg.Text('Type'), sg.Combo(['deletion', 'addition', 'substitution', None], readonly=True, size_px=(170, 40), key='-corr_type-')],
                  [sg.Text('Method'), sg.Combo(['above', 'left marg', 'right marg', 'overwritten', 'scraped', 'strikethrough', 'under', None], readonly=True, size_px=(170, 40), key='-corr_method-')]]
    
    values_col3 = [[sg.Text('Marginale Type'), sg.Input('', key='-marg_type-', enable_events=True)],
                   [sg.Radio('left margin', 'marg', disabled=True, key='-l_marg-'), sg.Radio('right margin', 'marg', disabled=True, key='-r_marg-')], 
                   [sg.Radio('after word', 'marg', disabled=True, key='-marg_after-'), sg.Radio('above word', 'marg', disabled=True, key='-marg_above-')],
                   [sg.Multiline('', key='-marg_tx-')],
                   [sg.Button('Submit Edits')]]

    edit_kv_frame = [[sg.Column(note_col), sg.Column(main_info_col), sg.Column(values_col), sg.Column(values_col2), sg.Column(values_col3)]]

    transcription_frame = [[sg.Button('Load Basetext'), sg.Button('Load Witness'), sg.Button('Submit Verse'), sg.Button('Show Editing Options'), sg.Button('Hide Editing Options'), sg.Button('Save')],
                            [sg.Multiline(size=(None, 3), key='-transcription-')]]

    return [[sg.Menu(menu)],
            [sg.Frame('Select Word to Edit', submitted_frame)],
            [sg.Frame('Edit Data', edit_kv_frame, visible=True, key='-edit_frame-')],
            [sg.Button('<Prev'), sg.Text('Reference'), sg.Input('', key='-ref-'), 
                sg.Button('Next>'), sg.Text('Witness Siglum'), 
                sg.Input('', key='-siglum-'), sg.Text('Hand'), 
                sg.Combo(['First', 'a', 'b', 'c', 'd', 'e', 'f'], readonly=True, size_px=(160, 40), key='-hand-', enable_events=True),
                sg.Text('Hands in Witness:'), sg.Input('', disabled=True, key='-hands-')],
            [sg.Frame('Transcription', transcription_frame, visible=True)]]

def main():
    layout = get_layout()
    main_dir = pathlib.Path(__file__).parent.as_posix()
    icon = f'{main_dir}/resources/transcribedit.ico'
    settings = get_settings(main_dir)
    window = sg.Window('Testing', layout, icon=icon)
    basetext_index = None
    verse_dict = None

    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, None, 'Exit'):
            break
        
        elif event == 'Show Editing Options':
            window['-edit_frame-'].update(visible=True)

        elif event == 'Hide Editing Options':
            window['-edit_frame-'].update(visible=False)
            # window.visibility_changed()

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
            if values['-hand-'] == 'First':
                verse_dict = submit_verse(values['-transcription-'], values['-ref-'], values['-siglum-'], window, icon)
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

        elif event == '-marg_type-':
            if values['-marg_type-'] != '':
                set_marg_radios(window, False)
            else:
                set_marg_radios(window, True)

        elif event == 'Save':
            if verse_dict is None:
                okay_popup('There is no submitted verse to save.', 'No Submitted Verse', icon)
                continue
            saved_path = save_tx(verse_dict, values['-siglum-'], settings, values['-ref-'])
            okay_popup(f'JSON formatted transcription file was succesfully saved to\n\
{saved_path}', 'Saved!', icon)

        elif event == '-hand-':
            if verse_dict is not None:
                update_display_verse(verse_dict, window, get_siglum_hand(values), values['-index-'])

        elif event == 'Settings':
            settings = set_settings(settings, main_dir, icon)

        # print(event, values)
    window.close()
