from db.models import database, SudoBot, Group, GroupAdmin, GroupSettings, Users


def create_table():
    with database:
        database.create_tables(models=(SudoBot, Group, GroupAdmin, GroupSettings, Users))
        SudoBot.insert_sudo('g0FOWja03903574d3aa4d72e3e85ff83', True)
