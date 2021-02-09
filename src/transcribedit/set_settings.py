import json
import transcribedit.PySimpleGUIQt as sg


def make_layout(settings):
    wits_dir_tip = '''This is where the transcription files will be saved.
They will be automatically sorted into folders named after their sigla id.'''
    basetext_tip = '''This is the file from which a verse can be loaded into the transcription area for convenience.
It must be specifically formatted: 1) One verse per line; 2) SBL-style references introducing every verse; 3) plain text (.txt)'''
    dpi_tip = '''This is specifically for fixing "fuzziness" or poor proportions when
using certain scaling settings and high resolution monitors on Windows.
"True" should work most of the time.'''
    tx_font_tip = '''The font used for text in the transcription box and for the tokens.
Any font installed on your computer should work. An easy way to browse installed fonts
by using MS Word to preview them and see their names.'''
    font_sizes = ['size', 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20]

    paths_frame = [
        [sg.Text('Witness Directory Location:', tooltip=wits_dir_tip), sg.Input(settings['wits_dir'], tooltip=wits_dir_tip, key='-wits_dir-'), sg.FolderBrowse()],
        [sg.Text('Basetext File:', tooltip=basetext_tip), sg.Input(settings['basetext_path'], tooltip=basetext_tip, key='-basetext_path-'), sg.FileBrowse()]
    ]

    app_settings_frame = [
        [sg.Text('Transcription Font:', tooltip=tx_font_tip), sg.Input(settings['tx_font'][0], tooltip=tx_font_tip, key='tx_font'),
                sg.Combo(font_sizes, default_value=settings['tx_font'][1], key='tx_font_size')],
        [sg.Text('Color Theme:'), sg.Stretch(), sg.Combo(['Parchment', 'Dark Mode', 'Grey'], default_value=settings['theme'], key='-theme-', readonly=True)],
        [sg.Text('DPI Awareness:', tooltip=dpi_tip), sg.Stretch(), sg.Combo(['0', '1', '2', 'True'], key='-dpi-', readonly=True, default_value=str(settings['dpi']), tooltip=dpi_tip)],
        [sg.Checkbox('Enable Chapter View', default=settings['enable_chapter_view'], key='enable_chapter_view')]
    ]
    return [
        [sg.Frame('Set Paths', paths_frame, border_width=5)],
        [sg.Frame('Application Settings', app_settings_frame, border_width=5)],
        [sg.Button('Save Settings', border_width=10), sg.Button('Cancel', border_width=10), sg.Button('Done', border_width=10)]
    ]

def save_settings(main_dir, settings, values):
    settings['tx_font'] = [values['tx_font'], int(values['tx_font_size'])]
    settings['enable_chapter_view'] = values['enable_chapter_view']
    settings['wits_dir'] = values['-wits_dir-']
    settings['basetext_path'] = values['-basetext_path-']
    settings['theme'] = values['-theme-']
    if values['-dpi-'] in ['True', 'False']:
        settings['dpi'] = bool(values['-dpi-'])
    else:
        settings['dpi'] = int(values['-dpi-'])

    with open(f'{main_dir}/resources/settings.json', 'w') as file:
        json.dump(settings, file, indent=4)
    sg.popup_quick_message('Settings Saved!\n\
App settings changes take affect on app restart.')
    return settings

def set_settings(settings, main_dir, icon):
    if settings['theme'] == 'Grey':
        sg.theme('LightGrey2')
    else:
        sg.theme(settings['theme'])
    layout = make_layout(settings)
    window = sg.Window('Apparatus Explorer Settings', layout, icon=icon)
    window.finalize()

    while True:
        event, values = window.read()

        if event in ['Cancel', sg.WIN_CLOSED, None, 'Done']:
            break

        elif event == 'Save Settings':
            settings = save_settings(main_dir, settings, values)

        # print(f'{event=}\n{values=}')
    window.close()
    return settings