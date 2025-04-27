import os

def database_path():
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'memoria_jarvis.db')
