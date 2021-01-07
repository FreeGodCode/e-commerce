import os

from flask_migrate import MigrateCommand
from flask_script import Manager, Server
from flask_script.commands import ShowUrls

from app import create_app

env = os.environ.get('FLASK_ENV', 'develop')
app = create_app(env=env)
manager = Manager(app)
manager.add_command('runserver', Server())
manager.add_command('db', MigrateCommand())
manager.add_command('showurls', ShowUrls())
manager.add_option('-c', '--config', dest='config', required=False, choices=E)
manager.add_option('-n', '--name', dest='app_name', required=False, choices=APP_NAME)


if __name__ == '__main__':
    manager.run()
