# -*- coding: utf-8 -*-
import logging
from dbaas_credentials.models import CredentialType
from dbaas_cloudstack.provider import CloudStackProvider
from dbaas_nfsaas.models import HostAttr
from dbaas_cloudstack.models import PlanAttr
from dbaas_cloudstack.models import HostAttr as CsHostAttr
from itertools import permutations
from util import check_ssh
from util import get_credentials_for
from util import exec_remote_command
from util import full_stack
from util import build_context_script
from workflow.steps.util.base import BaseStep
from workflow.exceptions.error_codes import DBAAS_0013

LOG = logging.getLogger(__name__)


class InitDatabase(BaseStep):
    def __unicode__(self):
        return "Initializing database..."

    def do(self, workflow_dict):
        try:
            statsd_credentials = get_credentials_for(
                environment=workflow_dict['environment'],
                credential_type=CredentialType.STATSD)

            statsd_host, statsd_port = statsd_credentials.endpoint.split(':')

            for index, hosts in enumerate(permutations(workflow_dict['hosts'])):

                LOG.info("Getting vm credentials...")
                host_csattr = CsHostAttr.objects.get(host=hosts[0])

                LOG.info("Cheking host ssh...")
                host_ready = check_ssh(
                    server=hosts[0].address, username=host_csattr.vm_user, password=host_csattr.vm_password, wait=5,
                    interval=10)

                if not host_ready:
                    LOG.warn("Host %s is not ready..." % hosts[0])
                    return False

                host_nfsattr = HostAttr.objects.get(host=hosts[0])

                planattr = PlanAttr.objects.get(plan=workflow_dict['plan'])

                contextdict = {
                    'EXPORTPATH': host_nfsattr.nfsaas_path,
                    'DATABASENAME': workflow_dict['name'],
                    'DBPASSWORD': get_credentials_for(environment=workflow_dict['environment'],
                                                      credential_type=CredentialType.MYSQL).password,
                    'HOST': workflow_dict['hosts'][index].hostname.split('.')[0],
                    'ENGINE': 'mysql',
                    'STATSD_HOST': statsd_host,
                    'STATSD_PORT': statsd_port,
                }

                if len(workflow_dict['hosts']) > 1:
                    LOG.info("Updating contexdict for %s" % hosts[0])

                    contextdict.update({
                        'SERVERID': index + 1,
                        'IPMASTER': hosts[1].address,
                        'IPWRITE': workflow_dict['databaseinfraattr'][0].ip,
                        'IPREAD': workflow_dict['databaseinfraattr'][1].ip,
                        'MASTERPAIRNAME': workflow_dict['databaseinfra'].name,
                        'HOST01': workflow_dict['hosts'][0],
                        'HOST02': workflow_dict['hosts'][1],
                        'INSTANCE01': workflow_dict['instances'][0],
                        'INSTANCE02': workflow_dict['instances'][1],
                        'SECOND_SCRIPT_FILE': '/opt/dbaas/scripts/dbaas_second_script.sh'
                    })

                scripts = (planattr.initialization_script,
                           planattr.configuration_script,
                           planattr.start_database_script)

                host = hosts[0]
                for script in scripts:
                    LOG.info("Executing script on %s" % host)

                    script = build_context_script(contextdict, script)
                    return_code = exec_remote_command(server=host.address,
                                                      username=host_csattr.vm_user,
                                                      password=host_csattr.vm_password,
                                                      command=script)

                    if return_code != 0:
                        return False

            if len(workflow_dict['hosts']) > 1:
                script = planattr.start_replication_script
                script = build_context_script(contextdict, script)

                for host in workflow_dict['hosts']:
                    host_csattr = CsHostAttr.objects.get(host=host)

                    LOG.info("Executing script on %s" % host)
                    return_code = exec_remote_command(server=host.address,
                                                      username=host_csattr.vm_user,
                                                      password=host_csattr.vm_password,
                                                      command=script)

                    if return_code != 0:
                        return False

            return True
        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0013)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False

    def undo(self, workflow_dict):
        try:
            LOG.info("Remove all database files")

            for host in workflow_dict['hosts']:
                LOG.info("Removing database files on host %s" % host)
                host_csattr = CsHostAttr.objects.get(host=host)

                exec_remote_command(server=host.address,
                                    username=host_csattr.vm_user,
                                    password=host_csattr.vm_password,
                                    command="/opt/dbaas/scripts/dbaas_deletedatabasefiles.sh")

            return True

        except Exception:
            traceback = full_stack()

            workflow_dict['exceptions']['error_codes'].append(DBAAS_0013)
            workflow_dict['exceptions']['traceback'].append(traceback)

            return False
