import os

import testinfra.utils.ansible_runner
import pytest

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


@pytest.mark.parametrize('service', [
  'wfly',
])
def test_systemd(host, service):
    systemd_service = host.service(service)

    assert systemd_service.is_enabled
    assert systemd_service.is_running
