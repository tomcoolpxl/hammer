# Automation PE1

## Basic Assignment (50%)

### Demo Application

#### Goal

Deploy the python web application `app.py` on an AWS VM and ensure that it is accessible via the Internet.

#### Requirements

The python web application is written using the python3 framework Pyramid and uses the following python (pip) modules: `pyramid`, `waitress`.

In addition, the application also uses the python modules `psutil` and `distro`.

The web application can be started with the command `/usr/bin/python3 app.py`.

### Manual Preparation: AWS VM

* Create an AWS VM based on Amazon Linux in your AWS Academy Automation I lab.
* Do not forget to open the correct port in AWS for the python application. This may be done manually.

### Ansible Deployment

* Use the Ansible playbook `playbook.yaml` in the repository and complete this file and the associated Ansible inventory `aws_hosts.ini` to configure the AWS VM. Make sure that:

  * the python app `app.py` is deployed on the AWS VM described in your `aws_hosts.ini` inventory file.
  * the python app `app.py` on the VM is located in the directory `/opt/pyramid_app`.
  * the python app on the VM runs in the background after successfully applying the playbook. This does not have to be idempotent.
* After running the playbook, the python app must be HTTP accessible from your machine via the internet using a browser at the resource **[URI]/hostname**. Do not forget your port.
* Only built-in Ansible modules may be used: [Ansible Module Documentation](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/index.html)
* Then take a **screenshot** of your browser window, place it in the assignment directory, and do not forget to commit it.
* The entire deployment must work on a pristine machine. That means that if someone else runs the playbook, after adjusting the inventory file, on another newly deployed AWS VM, everything on the VM is configured correctly without manual intervention on the VM.

### Submission

* Make the necessary changes in the files `aws_hosts.ini` and `playbook.yaml` and commit these files.
* After running the playbook, the python app must be HTTP accessible from your machine via the internet using a browser at the resource **[URI]/hostname**. Then take a **screenshot** of the working solution in your browser window, place this file in the assignment directory, add this file to the repository, and commit it.
* Manual changes to the VM are not allowed, unless to manually test something. Do not forget to undo these manual actions.
* The use of the command and shell modules is not allowed, with 1 exception: starting the python web application.
* The use of scripts is not allowed.
* Only files that are committed **before** the deadline will be graded.

## Extras (50%)

The extras will be evaluated *only* if the Basic Assignment has been completed **fully** successfully.

Extend the playbook with the following extra features:

### Extra 1 - Ansible: iptables firewall (20%)

* Make sure that the iptables service is explicitly installed and running, also after reboots.
* Make sure that the correct port for the web application is opened in iptables. It is allowed that this Ansible task is not idempotent.
* The use of the command and shell modules is not allowed for this extra.

### Extra 2 - Ansible: app also runs after reboot (15%)

* Make sure that the application automatically starts and works after rebooting the VM, **without** Ansible intervention.
* The use of the command and shell modules is not allowed in this extra.

### Extra 3 - Ansible: new user `app_user` (15%)

* Make sure that a new user `app_user` is created during deployment. This does not have to be idempotent.
* Make sure that this user is the owner of the file(s) and directory for the python app deployment.
* The use of the command and shell modules is not allowed in this extra.

## Information for the PE

### Interesting Parameters

The ansible commands have the optional parameter `[--private-key PRIVATE_KEY_FILE]`.

### YUM Packages

Possibly useful yum packages are `python3`, `python3-pip` for python.
The yum package for iptables is called `iptables-services`, which installs the `iptables` service.

### Custom systemd Services

These are easy to create with a custom service file, for example `/etc/systemd/system/example.service`:

```
[Unit]
Description=Example service

[Service]
User=tomc
WorkingDirectory=/home/tomc
ExecStart=/usr/sbin/my-simple-daemon -d
Restart=always

[Install]
WantedBy=multi-user.target
```

### CLI

A useful command to start processes in the background is `nohup`.
For example `nohup ping google.com &` starts a ping background process that keeps running even after closing the shell (no hangup).
