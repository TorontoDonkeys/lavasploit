from app.utility.base_world import BaseWorld
from plugins.lavasploit.app.lavasploit_gui import LavasploitGUI
from plugins.lavasploit.app.lavasploit_api import LavasploitAPI

name = 'Lavasploit'
description = 'Auto Privilege Escalation Plugin for Caldera Framework. Powered by Zhicheng Song, National University of Singaporem and supported by DSTA.'
address = '/plugin/lavasploit/gui'
access = BaseWorld.Access.RED


async def enable(services):
    app = services.get('app_svc').application
    lavasploit_gui = LavasploitGUI(services, name=name, description=description)
    app.router.add_static('/lavasploit', 'plugins/lavasploit/static/', append_version=True)
    app.router.add_route('GET', '/plugin/lavasploit/gui', lavasploit_gui.splash)

    lavasploit_api = LavasploitAPI(services)
    # Add API routes here
    app.router.add_route('POST', '/plugin/lavasploit/exploit', lavasploit_api.exploit)
    app.router.add_route('POST', '/plugin/lavasploit/autope', lavasploit_api.run_auto_priv_esc)
    app.router.add_route('GET', '/plugin/lavasploit/status', lavasploit_api.retrieve_status)
