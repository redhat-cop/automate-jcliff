# from ansible import utils
# import ansible.constants as C
# import ansible.utils.template as template
# from ansible import errors
# from ansible.runner.return_data import ReturnData

from ansible.errors import AnsibleError, AnsibleAction, _AnsibleActionDone

import os
import tempfile

from ansible.plugins.action import ActionBase
from ansible.template import Templar

class ActionModule(ActionBase):

  TRANSFERS_FILES = True
  TARGET_FILENAME_SUFFIX = ".jcliff.yml"

  def _writeTemplateResultToFile(self,content):
    tmp = tempfile.NamedTemporaryFile('w',delete=False)
    tmp.writelines(content)
    tmp.close()
    return tmp.name

  # this is temporary workaround, until we figured out a proper way
  # of doing this
  def _get_role_home(self):
    return os.environ['HOME'] + '/.ansible/roles/redhat-cop.jcliff'

  def _templateFromJinjaToYml(self, templateName, subsystem_values):
    templates = self._loader.path_dwim_relative(self._loader.get_basedir(), 'templates/rules', templateName)
    if ( not os.path.isfile(templates) ):
      templates = self._get_role_home() + '/templates/rules/' + templateName

    with open(templates, 'r') as file:
      data = file.read()
    self._templar.set_available_variables(subsystem_values)
    return self._writeTemplateResultToFile(self._templar.template(data))

  def _deployCustomRulesIfAny(self, tmp_remote_src):
    if 'rule_file' in self._task.args:
      custom_rulesdir = self._task.args['rule_file']
      if custom_rulesdir is not None:
        for custom_rule_file in os.listdir(custom_rulesdir):
          self._transfer_file(custom_rulesdir + "/" + custom_rule_file, tmp_remote_src + custom_rule_file + "-custom" + self.TARGET_FILENAME_SUFFIX)

  def _buildAndDeployJCliffRulefiles(self, tmp_remote_src):
    templateNameBySubsys = {
      'drivers': 'drivers.j2',
      'datasources': 'datasource.j2',
      'system_props': 'system-properties.j2',
      'deployments': 'deployments.j2'
    }
    subsystems = self._task.args['subsystems']
    if subsystems is not None:
      for subsys in subsystems:
        for key in subsys.keys():
          if key == 'drivers' or key == 'datasources':
            for index, subsystem_values in enumerate(subsys[key]):
              self._transfer_file(self._templateFromJinjaToYml(templateNameBySubsys[key], { "values": subsystem_values }), tmp_remote_src + key + "-" + str(index) + self.TARGET_FILENAME_SUFFIX)
          if key == 'system_props' or key == 'deployments':
            self._transfer_file(self._templateFromJinjaToYml(templateNameBySubsys[key], { "values": subsys[key]}), tmp_remote_src + key + self.TARGET_FILENAME_SUFFIX)

  def run(self, tmp=None, task_vars=None):
    tmp_remote_src = self._make_tmp_path()
    self._buildAndDeployJCliffRulefiles(tmp_remote_src)
    self._deployCustomRulesIfAny(tmp_remote_src)
    result = super(ActionModule, self).run(tmp, task_vars)
    new_module_args = self._task.args.copy()
    new_module_args.update(dict(remote_rulesdir=tmp_remote_src,))
    result.update(self._execute_module(module_name='jcliff', module_args=new_module_args, task_vars=task_vars))
    self._remove_tmp_path(self._connection._shell.tmpdir)
    return result

