#!/bin/bash
# A simple test suite, designed to be run by a ci-server
set -e

export ANSIBLE_NOCOLOR='True'

readonly JCLIFF_ROLE_NAME='redhat-cop.jcliff'
readonly JCLIFF_PLAYBOOK='/work/tune-wildfly-with-jcliff.yml'

ansible-playbook -vvvv /work/wildfly-setup.yml
ansible-galaxy install "${JCLIFF_ROLE_NAME}"
ansible-playbook -vvvv "${JCLIFF_PLAYBOOK}" --extra-vars "custom_rules_folder=/work/files/custom_rules ansible_distribution=CentOS"
rm -rf /work/*
