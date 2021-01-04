import transcribedit.tokenize_text as tt

def load_token(index: str, verse: dict, siglum: str, window):
    index = int(index.replace('word', ''))
    token = tt.get_token(index, verse, siglum)
    # necessary data
    window['-rule_match-'].update(value=', '.join(token['rule_match']))
    window['-index-'].update(value=index)
    window['-original-'].update(value=token['original'])
    window['to_collate'].update(value=token['t'])
    
    # optional data
    if 'note' in token:
        window['-note-'].update(value=token['note'])
    else:
        window['-note-'].update(value='')
    for i, brk in enumerate(['break_after', 'break_before', 'break_split']):
        if brk in token:
            window['break_place'].update(set_to_index=i+1)
            window['break_num'].update(value=token[brk][1])
            if token[brk][0] == 'line':
                window['break_type'].update(set_to_index=0)
            elif token[brk][0] == 'column':
                window['break_type'].update(set_to_index=1)
            elif token[brk][0] == 'page':
                window['break_type'].update(set_to_index=2)
            break
        else:
            window['break_place'].update(set_to_index=0)
            window['break_type'].update(set_to_index=3)
            window['break_num'].update(value='')
      
    if 'first_hand_rdg' in token:
        window['-first_hand_rdg-'].update(value=token['first_hand_rdg'])
    else:
        window['-first_hand_rdg-'].update(value='')
    if 'corr_type' in token:
        for i, item in enumerate(['deletion', 'addition', 'substitution']):
            if token['corr_type'] == item:
                window['-corr_type-'].update(set_to_index=i)
    else:
        window['-corr_type-'].update(set_to_index=3)
    if 'corr_method' in token:
        for i, item in enumerate(['above', 'left marg', 'right marg', 'overwritten', 'scraped', 'strikethrough', 'under']):
            if token['corr_method'] == item:
                window['-corr_method-'].update(set_to_index=i)
    else:
        window['-corr_method-'].update(set_to_index=7)
    if 'gap_after' in token:
        window['gap'].update(set_to_index=1)
        window['gap_details'].update(value=token['gap_details'])
    elif 'gap_before' in token:
        window['gap'].update(set_to_index=2)
        window['gap_details'].update(value=token['gap_details'])
    else:
        window['gap'].update(set_to_index=0)
        window['gap_details'].update(value='gap details')
    if 'page' in token:
        window['-page-'].update(value=token['page'])
    else:
        window['-page-'].update(value='')
    if 'image_id' in token:
        window['-image_id-'].update(value=token['image_id'])
    else:
        window['-image_id-'].update(value='')
    if 'marginale' in token:
        window['marg_loc'].update(values=['after word', 'above word', 'before word', 'below word', 'margin left', 'margin right', 'margin top', 'margin bottom'], value=token['marginale']['loc'].replace('_', ' '))
        window['-marg_type-'].update(value=token['marginale']['marg_type'])
        window['-marg_tx-'].update(value=token['marginale']['marg_tx'])
    else:
        window['-marg_type-'].update(value='')
        window['-marg_tx-'].update(value='')
        window['marg_loc'].update(set_to_index=8)

def make_new_token(values, siglum_hand):
    rule_match = values['-rule_match-'].replace(' ', '').split(',')
    siglum = siglum_hand

    token = {"index": values['-index-'],
             "siglum": siglum,
             "reading": siglum,
             "original": values['-original-'],
             "rule_match": rule_match,
             "t": values['to_collate']}

    if values['break_place'] != 'no break':
        token[f'break_{values["break_place"]}'] = (values['break_type'], values['break_num'])
    if values['-corr_type-'] != None:
        token['corr_type'] = values['-corr_type-']
    if values['-corr_method-'] != None:
        token['corr_method'] = values['-corr_method-']
    if values['gap'] != 'no gap':
        token[f'{values["gap"].replace(" ", "_")}'] = True
        # if values['-gap_after-'] is True:
        #     token['gap_after'] = True
        # elif values['-gap_before-'] is True:
        #     token['gap_before'] = True
        token['gap_details'] = values['gap_details']
    for v in ['page', 'image_id', 'note', 'first_hand_rdg']:
        if values[f'-{v}-'] != '':
            token[v] = values[f'-{v}-']
    if values['-marg_type-'] != '':
        token['marginale'] = {'marg_type': values['-marg_type-'],
                              'loc': values['marg_loc'].replace(' ', '_'),
                              'marg_tx': values['-marg_tx-']}
        
    return token