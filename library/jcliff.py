#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from jinja2 import Template, Environment, FileSystemLoader
import json
import subprocess
import os
import tempfile
import shutil

def formatOutput(output):
  result = ""
  i = 0
  for line in output.split(os.linesep):
      i += 1
      result += { i : line }
  return result

def renderFromTemplate(rulesdir, template_name, output_file,values):
  # FIXME: can't load that everytime
  file_loader = FileSystemLoader('/etc/ansible/jcliff/')
  env = Environment(loader=file_loader)
  template = env.get_template(template_name)
  with open( os.path.join(rulesdir,output_file), 'w') as template_file:
    template_file.write(template.render(values=values))

def generateRuleFromTemplate(data,rulesdir):
  if data['subsystems'] is not None:
    subsystems = data['subsystems']
    for subsys in subsystems:
      if subsys['datasources'] is not None:
        datasources = subsys["datasources"]
        for ds in datasources:
          renderFromTemplate(rulesdir, 'datasource.j2', "datasource-" + ds['name'] + ".yml", ds)
      if subsys['system_props'] is not None:
        renderFromTemplate(rulesdir,'system-properties.j2', 'system-properties.yml', subsys['system_props'])
      if subsys['deployments'] is not None:
        renderFromTemplate(rulesdir,'deployments.j2', 'deployments.yml', subsys['deployments'])
      if subsys['drivers'] is not None:
        for driver in subsys['drivers']:
          renderFromTemplate(rulesdir,'drivers.j2', "drivers-" + driver['driver_name'] + ".yml", driver)

def listRuleFiles(rulesdir):
  rules_filename = os.listdir(rulesdir)
  rule_files = []
  for filename in rules_filename:
      rule_files.append(rulesdir + "/" + filename)
  return rule_files

def addToEnv(name, value):
  if value is not None:
    os.environ[name] = value

def executeRulesWithJCliff(data,rulesdir):

  jcliff_command_line = ["bash", "-x", data["jcliff"], "--cli=" + data['wfly_home'] + "/bin/jboss-cli.sh", "--ruledir=" + data['rules_dir'], "--controller=" + data['management_host'] + ":" + data['management_port'], "-v"]

  if data["management_username"] is not None:
    jcliff_command_line.extend(["--user=" + data["management_username"]])
  if data["management_password"] is not None:
    jcliff_command_line.extend(["--password=" + data["management_password"]])

  jcliff_command_line.extend(listRuleFiles(rulesdir))
  output = None
  status = "undefined"
  addToEnv('JAVA_HOME', data['jcliff_jvm'])
  addToEnv('JBOSS_HOME', data['wfly_home'])
  addToEnv('JCLIFF_HOME', data['jcliff_home'])

  try:
    output = subprocess.check_output(jcliff_command_line,stderr=subprocess.STDOUT, shell=False, env=os.environ)
    status = 0
  except subprocess.CalledProcessError as jcliffexc:
    error = jcliffexc.output.decode()
    if (jcliffexc.returncode != 2) and (jcliffexc.returncode != 0):
        return { "failed": True, "report": { "status" : jcliffexc.returncode, "output": output, "rulesdir": rulesdir , "jcliff_cli": jcliff_command_line , "JAVA_HOME": os.getenv("JAVA_HOME","Not defined"), "JCLIFF_HOME": os.getenv("JCLIFF_HOME", "Not defined"), "JBOSS_HOME": os.getenv("JBOSS_HOME", "Not defined"), "error": error } }, jcliffexc.returncode
    else:
        return {"present:": error },2
  except Exception as e:
     output = e
     status = 1
  if status == 0:
    return {"present" : output, "rc": status, "ruledir" : rulesdir, "jcliff_cli": jcliff_command_line }, status
  else:
      return {"failed" : True, "report": output, "rc": status, "ruledir" : rulesdir, "jcliff_cli": jcliff_command_line }, status

def copyRulesToRulesdir(rulefiles, rulesdir):
  try:
    for rulefile in rulefiles.split(" "):
      shutil.copy2(rulefile, rulesdir)
  except shutil.Error as e:
    print('Directory not copied. Error: %s' % e)
  except OSError as e:
    print('Directory not copied. Error: %s' % e)

def ansibleResultFromStatus(status):
  has_changed = False
  has_failed = False
  if status == 2:
    has_changed = True
  if status != 0 and status != 2:
    has_failed = True
  return (has_changed, has_failed)

def jcliff_present(data):
  rulesdir = tempfile.mkdtemp()
  generateRuleFromTemplate(data, rulesdir)
  if data['rule_file'] is not None:
    copyRulesToRulesdir(data['rule_file'], rulesdir)
  print("Executing JCliff:")
  meta, status = executeRulesWithJCliff(data, rulesdir)
  #shutil.rmtree(rulesdir)
  has_changed, has_failed = ansibleResultFromStatus(status)
  return (has_changed, has_failed, meta)

def jcliff_absent(data=None):
   has_changed = False
   #subprocess.run(["ls", "-l"])
   meta = {"absent": "not yet implemented"}

def main():
    default_jcliff_home = "/usr/share/jcliff"
    fields = dict(
         jcliff_home=dict(type='str', default=default_jcliff_home),
         jcliff=dict(default='/usr/bin/jcliff', type='str'),
         management_username=dict(required=False, type='str'),
         management_password=dict(required=False, type='str'),
         rules_dir=dict(type='str', default=default_jcliff_home + "/rules"),
         wfly_home=dict(required=True, type='str'),
         management_host=dict(default='localhost', type='str'),
         management_port=dict(default='9990', type='str'),
         jcliff_jvm=dict(default=os.getenv("JAVA_HOME",None), type='str', required=False),
         rule_file=dict(required=False, type='str'),
         subsystems=dict(type='list', required=False, elements='dict',
            options=dict(
                drivers=dict(type='list', required=False, elements='dict', options=dict(
                    driver_name=dict(type='str', required=True),
                    driver_module_name=dict(type='str', required=True),
                    driver_xa_datasource_class_name=dict(type='str', default='undefined'),
                    driver_class_name=dict(type='str', default='undefined'),
                    driver_datasource_class_name=dict(type='str', default='undefined'),
                    module_slot=dict(type='str', default='undefined'),
                    )
                ),
                datasources=dict(type='list', required=False, elements='dict', options=dict(
                    name=dict(type='str', required=True),
                    jndi_name=dict(type='str', required=True),
                    use_java_context=dict(type='str', default='true'),
                    connection_url=dict(type='str', required=True),
                    driver_name=dict(type='str', required=True),
                    enabled=dict(type='str', default='true'),
                    password=dict(type='str', required=False),
                    user_name=dict(type='str', required=False),
		    max_pool_size=dict(type='str', default='undefined'),
            	    min_pool_size=dict(type='str', default='undefined'),
	            idle_timeout_minutes=dict(type='str', default='undefined'),
                    query_timeout=dict(type='str', default='undefined'),
                    check_valid_connection_sql=dict(type='str', default='undefined'),
                    validate_on_match=dict(type='str', default='undefined')
                    )
                ),
                system_props=dict(type='list', required=False, elements='dict', options=dict(
                    name=dict(type='str', required=False),
                    value=dict(type='str', required=False)
                    )
                ),
                deployments=dict(type='list', required=False, elements='dict', options=dict(
                    artifact_id=dict(type='str', required=True),
                    name=dict(type='str', required=False),
                    path=dict(type='str', required=True)
                    )
                )
            )
         ),
         state=dict(default="present", choices=['present', 'absent'], type='str')
    )

    module = AnsibleModule(argument_spec=fields)
    if os.environ.get("JCLIFF_HOME"):
        fields["jcliff_home"] = os.environ.get("JCLIFF_HOME")
    # TODO validation that jcliff_home exits + dir

    choice_map = {
        "present": jcliff_present,
        "absent": jcliff_absent,
    }
    has_changed, has_failed, result = choice_map.get(module.params['state'])(data=module.params)
    module.exit_json(changed=has_changed, failed=has_failed, meta=result)
if __name__ == '__main__':
    main()
