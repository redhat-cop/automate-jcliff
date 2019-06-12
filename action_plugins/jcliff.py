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

  def _create_remote_copy_args(module_args):
    """remove action plugin only keys"""
    return dict((k, v) for k, v in module_args.items() if k not in ('content', 'decrypt'))


  def run(self, tmp=None, task_vars=None):
    #if not tmp is None: print("tmp:" + tmp)
    #print("tasks_vars:" + task_vars)
    print("hello")
    wp = self._loader.get_basedir()
    #tmp_remote_src = self._make_tmp_path()
    #print(str(tmp_remote_src))
    #new_module_args = self._create_remote_copy_args(self._task.args)
    #new_module_args.update(
    #              dict(
    #                  jcliff_rule_folder=tmp_remote_src,
    #              )
    #          )
    #print(new_module_args)
    subsystems = self._task.args['subsystems']
    for subsys in subsystems:
      for key in subsys.keys():
        if key == 'drivers':
          for driver in subsys[key]:
            values= { "values": driver }
            print(values)
            templates = self._loader.path_dwim_relative(wp, 'templates/rules','drivers.j2')
            with open(templates, 'r') as file:
              data = file.read()
            print("templating...")
            self._templar.set_available_variables(values)
            res = self._templar.template(data)
            print(res)
            temp = tempfile.TemporaryFile()
            f = open("drivers.j2","w+")
            f.write(res)
            f.close()
            #self._connection._shell.join_path(self._connection._shell.tmpdir, os.path.basename(src))
            print("send file over")
            self._transfer_file("drivers.j2", "/etc/ansible/jcliff/drivers.j2")

    print("execute module")
    result = super(ActionModule, self).run(tmp, task_vars)
    result.update(self._execute_module(module_name='jcliff', task_vars=task_vars))
    print("back from module")
    #self._remove_tmp_path(self._connection._shell.tmpdir)
    return result

