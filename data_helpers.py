import PySimpleGUI as sg
import json
import datetime
import requests


def time_convert(t_input):
    temp = datetime.datetime.strptime(t_input, '%a, %B %d, %Y')
    return datetime.datetime.strftime(temp, "%Y%m%d")


def input_frame(layout, spf_text=""):
    layout.append([sg.Button("Send Request", k='-ok-'), sg.Button("Cancel", k='-cancel-')])
    input_frame = sg.Window(spf_text, layout, finalize=True)
    while True:
        event, values = input_frame.read()
        print(event, values)
        if event in (sg.WIN_CLOSED, '-cancel-'):
            input_frame.close()
            return 'cancel'
        elif event == '-ok-':
            input_frame.close()
            return values


def pick_date(target):
    return sg.CalendarButton('Choose Date', close_when_date_chosen=True, locale='en_US', no_titlebar=True,
                             target=target, format='%a, %B %d, %Y')


def post_http(url, data, headers=None):
    if headers is None:
        req = requests.post(url, json=data)
    else:
        req = requests.post(url, json=data, headers=headers)
    return req


def get_http(url, config=None, headers=None):
    req = requests.get(url, json=config, headers=headers)
    return req


def check(response):
    if response.status_code == 200:
        return True
    else:
        try:
            temp = response.json()
        except json.decoder.JSONDecodeError:
            print("json decode error, response below:")
            print(response)
            sg.Popup(response.text, title='ERROR')
            return False
        else:
            if temp['isSuccess']:
                return True


def edit_config(graph_id='', name='', unit=''):
    return {'id': graph_id, 'name': name, 'unit': unit, 'type': 'float', 'color': 'ichou'}


ROOT = 'https://pixe.la/'
TOKEN = 'C8VVVBUDTRIO'
USERNAME = 'kernelhermit'


class DataHelper:
    def __init__(self):
        self.data_variables = []
        self.graph_config = edit_config()
        self.chosen = None
        
        try:
            with open('./users.json', 'r') as f_users:
                u_dict = json.load(f_users)
        except ValueError:
            self.users = {}
            added_user = self.new_user()
            if added_user is not None:
                added_key = list(added_user)[0]
                self.users[added_key] = added_user[added_key]
                self.resave_json()
                self.selected_user = self.users[added_key]
        else:
            self.users = u_dict
            self.selected_user = self.cycle_users()
            # print(self.selected_user)
            self.token = self.selected_user['token']
            self.headers = {'X-USER-TOKEN': self.token}
            self.user_name = self.selected_user['username']
        
        self.graphs_list = self.get_graphlist()
        self.combo_label = "    ---User Graphs---"
        self.c_graph = self.combo_label
    
    def cycle_users(self):
        reply = 'No'
        for each in self.users:
            reply = sg.PopupYesNo(f"Found username {self.users[each]['username']} \n Is this correct?")
            if reply == 'Yes':
                response = get_http(f"{ROOT}/@{self.users[each]['username']}")
                if check(response):
                    return self.users[each]
                else:
                    sg.Popup("Profile not found on server")
        if reply == 'No':
            sg.Popup("That was the last user")
            added_user = self.new_user()
            if added_user is not None:
                added_key = list(added_user)[0]
                self.users[added_key] = added_user[added_key]
                self.resave_json()
                return added_user[added_key]
    
    def new_user(self):
        num_names = len(self.users)
        layout = [
            [sg.Frame("Create New User?", layout=[
                [sg.Text("Username:"), sg.Input(k='-username-')],
                [sg.Text("Unique Key:"), sg.Input(k='-token-')]
            ])]
        ]
        new_user = input_frame(layout)
        token = new_user['-token-']
        username = new_user['-username-']
        response = post_http(f'{ROOT}v1/users',
                             {'token': token, 'username': username, 'agreeTermsOfService': 'yes',
                              'notMinor': 'yes'})
        if check(response):
            return {f'user_{num_names}': {'username': username, 'token': token}}
        else:
            sg.Popup("Error in creating user")
            return None
    
    def resave_json(self):
        with open('./users.json', 'w') as f_users:
            json.dump(self.users, f_users, indent=4)
    
    def delete_profile(self):
        headers = {'X-USER-TOKEN': self.selected_user['token']}
        username = self.selected_user['username']
        
        reply = sg.PopupYesNo(f"Are you sure you want to delete {username}'s profile?", line_width=35)
        if reply == 'Yes':
            response = requests.delete(url=f'{ROOT}v1/users/{username}', headers=headers)
            if check(response):
                sg.Popup(f"Successfully deleted user - {username}", line_width=35)
    
    def input_window(self, input_type):
        layout = []
        spf_text = ""
        values = {}
        if input_type == "-add-":
            layout = [
                [sg.Frame("Add New Data Point:", layout=[
                    [sg.Text("Value:  "), sg.Input(k="-datapoint-", size=(18, 0))],
                    [sg.Text("Date:"), sg.Input(k='-date-', size=(20, 0)), pick_date('-date-')]])]
            ]
            spf_text = "Add Data"
            values = input_frame(layout, spf_text)
            if not values == 'cancel':
                data_value, v_date, button = values
                date = time_convert(values[v_date])
                response = post_http(f"{ROOT}/v1/users/{self.user_name}/graphs/{self.c_graph}",
                                     data={'date': date, 'quantity': values[data_value]}, headers=self.headers)
                if check(response):
                    sg.Popup("Successfully Added")
        elif input_type == "-edit-":
            spf_text = "Edit data point"
            layout = [
                [sg.Text("New Value:"), sg.Input(k='i_v')],
                [sg.Input(k='date'), pick_date('date')]
            ]
            values = input_frame(layout, spf_text)
            date = values['date']
            get_http(f"{ROOT}/v1/users/{self.user_name}/graphs/{self.c_graph}/{date}")
        elif input_type == "-delete-":
            layout = [[sg.CalendarButton('Choose Date', close_when_date_chosen=True, locale='en_US', no_titlebar=True,
                                         format='%a, %B %d, %Y')]]
            values = input_frame(layout)
            if not values == 'cancel':
                v_date = time_convert(values['Choose Date'])
                a = sg.PopupYesNo(f"Are you sure you want to delete pixel at {values['Choose Date']}?", line_width=35)
                if a == 'Yes':
                    response = requests.delete(f"{ROOT}/v1/users/{self.user_name}/graphs/{self.c_graph}/{v_date}",
                                               headers=self.headers)
                    if check(response):
                        sg.Popup(f"Successfully deleted pixel data point at: {values['Choose Date']}.", line_width=35)
                    else:
                        sg.Popup(f"{self.user_name} path to item {self.c_graph} at {values['Choose Date']} not found.", line_width=35)
        elif input_type == "-create-":
            spf_text = "New Chart"
            layout = [
                [sg.Frame("Create a new graph", layout=[
                    [sg.Text("Graph ID:"), sg.Input(k='-id-', size=(15, 0), expand_x=True)],
                    [sg.Text("Title:"), sg.Input(k='-name-', size=(18, 0), expand_x=True)],
                    [sg.Text("Units:"), sg.Text("", expand_x=True), sg.Input(k='-units-', size=(15, 0))]])]
            ]
            values = input_frame(layout, spf_text)
            if not values == 'cancel':
                unique_id, name, units = values
                self.graph_config = edit_config(values[unique_id], values[name], values[units])
                response = post_http(f"{ROOT}/v1/users/{self.user_name}/graphs", data=self.graph_config,
                                     headers=self.headers)
                print(response.json())
    
    def get_graphlist(self):
        response = get_http(f"{ROOT}/v1/users/{self.user_name}/graphs",
                            headers=self.headers)
        if check(response):
            graphlist = response.json()
            names = {each['name']: each['id'] for each in graphlist['graphs']}
            return names
            # return [f"{each['name']}" for each in graphlist['graphs']]
        else:
            return "-NONE-"
    
    def selected_graph(self, value):
        self.c_graph = self.graphs_list[value]
        print(self.c_graph)

    def get_image(self):
        response = get_http(f"{ROOT}/v1/users/{self.user_name}/graphs/{self.c_graph}")
        if check(response):
            print(response.json())
        #TODO still need to change this code to get the pixels from site and redraw them using colour or pillow or sg