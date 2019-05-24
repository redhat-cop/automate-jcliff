# jcliff Ansible Support

[![Ansible Galaxy](https://img.shields.io/badge/galaxy-redhatcop.jcliff-blue.svg)](https://galaxy.ansible.com/redhat-cop/jcliff)

This repository contains tooling to support utilizing [Ansible](https://www.ansible.com/) with the [jcliff](https://github.com/bserdar/jcliff) utility to manage [Red Hat Enterprise Application Platform (EAP)](https://www.redhat.com/en/technologies/jboss-middleware/application-platform) / [Wildfly](https://wildfly.org/) configuration.

## Ansible Galaxy

Content from this repository is available in [Ansible Galaxy](https://galaxy.ansible.com/redhat-cop/jcliff). Installation can be facilitated by the executing the following command:

```
ansible-galaxy install redhat-cop.jcliff
```

## Installing Wildfly using Ansible

With the role install, you can directly install Widlfy using the provided playbook:

```
# cd ~/.ansible/role/...
# ansible-playbook ~/.ansible/roles/redhat-cop.jcliff/wildfly-setup.yml
```
Note that this installation is PLAIN Ansible, the role provided here is not (yet) being used. This installation also download the require artefact for setting up a Postgresql driver later on.

## Tweak your Wildfly configuration with JCliff

Once Wildfly is successfully installed and is running, you can see how to use the JCliff module, provided by this role, to fine tune the setup of your Wildfly:

```
# ansible-playbook ~/.ansible/roles/redhat-cop.jcliff/tune-wildfly-with-jcliff.yml
```


