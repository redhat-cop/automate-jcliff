#!/bin/bash
# A simple test suite, designed to be run by a ci-server
set -e

ansible-playbook -vvvv /work/wildfly-setup.yml
ansible-playbook -vvvv /work/tune-wildfly-with-jcliff.yml --extra-vars "custom_rules_folder=files/custom_rules"
