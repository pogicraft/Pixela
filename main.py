import PySimpleGUI as sg
import requests
from data_helpers import DataHelper

    
def show_profile(the_user):
    requests.get(f'https://pixe.la/@{the_user}')


def get_user():
    return DataHelper()


def main_layout():
    layout = [
        [sg.Button("New Entry", k='-add-')],
        [sg.Button("Edit Entry", k='-edit-')],
        [sg.Button("Delete Entry", k='-delete-')],
        [sg.Combo([], "    ---User Graphs---", expand_x=True, enable_events=True, readonly=True, k='-graph_list-')],
        [sg.Button("New Graph", k='-create-'), sg.Button("View Graph", k='-see-')],
        [sg.Button("Change User", k='-cycle-'), sg.Button("Delete User", k='-kill_profile-')],
        [sg.Button("Exit")],
    ]
    return layout


main_win = sg.Window('Pixela Project', [[sg.Frame("", main_layout(), expand_x=True, expand_y=True)]], finalize=True)
user = get_user()
existing_data = {'selection': user.data_variables}
# This was for an optional point which saved the variables locally so the
# program doesn't have to use the network as much
main_win['-graph_list-'].update(user.combo_label, values=[each for each in user.get_graphlist()])

while True:
    window, event, values = sg.read_all_windows(timeout=100)
    if not event == '__TIMEOUT__':
        print(window, event, values)
        if event == sg.WINDOW_CLOSED or event == 'Exit':
            break
        elif event == '-cycle-':
            user = get_user()
            main_win['-graph_list-'].update(user.combo_label, values=[each for each in user.get_graphlist()])
        elif event == '-add-' or event == '-edit-' or event == '-delete-':
            user.input_window(event)
        elif event == '-create-':
            user.input_window(event)
            main_win['-graph_list-'].update(user.combo_label, values=[each for each in user.get_graphlist()])
        elif event == '-kill_profile-':
            user.delete_profile()
        elif event == '-graph_list-':
            if values['-graph_list-'] != user.combo_label:
                user.selected_graph(values['-graph_list-'])
        elif event == '-see-':
            user.get_image()
        else:
            print(window, event, values)

main_win.close()
