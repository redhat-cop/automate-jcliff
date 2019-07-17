#!/bin/bash
# A simple test suite, designed to be run by a ci-server
set -e

export ANSIBLE_NOCOLOR='True'
ansible-playbook -vvvv /work/wildfly-setup.yml
ansible-galaxy install redhat-cop.jcliff
ansible-playbook -vvvv /work/tune-wildfly-with-jcliff.yml --extra-vars "custom_rules_folder=/work/files/custom_rules"
rm -rf /work/*
