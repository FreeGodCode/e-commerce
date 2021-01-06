import os

from flask_migrate import MigrateCommand
from flask_script import Manager, Server

from app import create_app

env = os.environ.get('FLASK_ENV', 'develop')
app = create_app(env=env)
manager = Manager(app)
manager.add_command('runserver', Server())
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
