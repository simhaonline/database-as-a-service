from logging import getLogger
from util import exec_remote_command_host

LOG = getLogger(__name__)

script_mongodb_rotate = """cat <<EOT >> /opt/dbaas/scripts/mongodb_rotate_script.sh
#!/bin/bash
source /root/.profile

HOST_ADDRESS=\`/bin/hostname -i\`

if [ \$? -ne 0 ]
then
    echo "Host Address not found!"
    exit 3
fi

IS_MASTER=\$(/usr/local/mongodb/bin/mongo \${HOST_ADDRESS}:27017/admin --quiet << EOF
db.isMaster()['ismaster']
exit
EOF
)
IS_SECONDARY=\$(/usr/local/mongodb/bin/mongo \${HOST_ADDRESS}:27017/admin --quiet << EOF
db.isMaster()['secondary']
exit
EOF
)

# Checking whether node is primary/sencondary or arbiter
if [ "\${IS_MASTER}" = "true" ] || [ "\${IS_SECONDARY}" = "true" ]
then
    /usr/local/mongodb/bin/mongo \$HOST_ADDRESS:27017/admin -u \${MONGODB_ADMIN_USER} -p \${MONGODB_ADMIN_PASSWORD} << EOF
    db.runCommand("logRotate");
    exit
EOF
else
    /sbin/pidof mongod | xargs kill -SIGUSR1
fi

# Compress log files already rotated
counter=0
has_compressed_files=0

while [ \$counter -le 5 ] && [ \$has_compressed_files -eq 0 ]
do
  if [[ \$(find /data/logs/ -name 'mongodb.log.*[[:digit:]]' -type f)  ]]
  then
      find /data/logs/ -name 'mongodb.log.*[[:digit:]]' -type f | xargs /usr/bin/gzip -f
      has_compressed_files=1
  else
     (( counter++ ))
     sleep 5
  fi
done

# Remove log backups onder than 7 days
find /data/logs/ -name 'mongodb.log.*.gz' -mtime +7 -type f | xargs rm -f
EOT
"""

script_mongodb_log_params = """cat <<EOT >> /opt/dbaas/scripts/log_rotate_params.sh
#!/bin/bash
(cat <<EOF
export MONGODB_ADMIN_USER=\${MONGODB_ADMIN_USER}
export MONGODB_ADMIN_PASSWORD=\${MONGODB_ADMIN_PASSWORD}
EOF
) >  /root/.profile
"""

script_is_syslog = 'grep syslog /data/mongodb.conf'
script_is_datalog_empty = '[ ! -s /data/logs/mongodb.log ]'
script_rotate_already_executed = '[[ -f /opt/dbaas/scripts/mongodb_rotate_script.sh ]] && [[ -f /opt/dbaas/scripts/log_rotate_params.sh ]]'
remove_log_rotate_file = 'rm -f /etc/logrotate.d/mongodb_rotate'

create_mongodb_rotate_script = 'install -m 755 /dev/null /opt/dbaas/scripts/mongodb_rotate_script.sh'
create_log_params_script = 'install -m 755 /dev/null /opt/dbaas/scripts/log_rotate_params.sh'

create_profile_file = 'export MONGODB_ADMIN_USER=admindbaas;export MONGODB_ADMIN_PASSWORD=Rt2va8Mc;source /opt/dbaas/scripts/log_rotate_params.sh'
add_cron_job = '! (crontab -l | grep -q "/opt/dbaas/scripts/mongodb_rotate_script.sh") && (crontab -l; echo "0 0 * * * /opt/dbaas/scripts/mongodb_rotate_script.sh") | crontab -'

def execute(task, mongodb_restarted_instances):
    for i, instance in enumerate(mongodb_restarted_instances):
        task.update_details(
            "Checking restarted instances and executing script...", persist=True
        )

        host = instance.hostname
        log = '\n{} of {} - Host '.format(
            i+1, len(mongodb_restarted_instances), host
        )
        LOG.info(log)
        task.update_details(log, persist=True)

        output = {}
        return_code = exec_remote_command_host(host, script_is_syslog, output)
        if return_code == 0:
            msg = 'Host {}: SYSLOG'.format(host)
            LOG.info(msg)
            task.update_details(msg, persist=True)
        else:
            return_code = exec_remote_command_host(
                host, script_is_datalog_empty, output
            )
            if return_code == 0:
                msg = 'Host {}: Writing to filer, but it needs restart.'.format(host)
                LOG.info(msg)
                task.update_details(msg, persist=True)
            else:
                return_code = exec_remote_command_host(
                    host, script_rotate_already_executed, output
                )
                if return_code == 0:
                    msg = 'Host {}: Rotate Already updated.'.format(host)
                    LOG.info(msg)
                    task.update_details(msg, persist=True)
                else:
                    exec_remote_command_host(host, remove_log_rotate_file, output)
                    exec_remote_command_host(
                        host, create_mongodb_rotate_script, output
                    )
                    exec_remote_command_host(host, create_log_params_script, output)
                    exec_remote_command_host(host, script_mongodb_rotate, output)
                    exec_remote_command_host(host, script_mongodb_log_params, output)
                    exec_remote_command_host(host, create_profile_file, output)
                    exec_remote_command_host(host, add_cron_job, output)
                    msg = 'Host {}: Rotate script updated.'.format(host)
                    LOG.info(msg)
                    task.update_details(msg, persist=True)
