from utils import *

class Chant():

    def __init__(self, team_id, file_id, afs_id):
        self.team_id = team_id
        self.file_id = file_id
        self.afs_id = afs_id

    @property
    def afs_name(self):
        return AFS_FILENAMES[self.afs_id]
