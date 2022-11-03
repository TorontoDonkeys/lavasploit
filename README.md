# Lavasploit


## Experiment Environment Configuration

### System: Ubuntu 18.04.6 AMD64 Image


further setup

## Enable root account
1. set root password
```bash
sudo passwd root
```

2. modify user profile
```bash
sudo vim /usr/share/lightdm/lightdm.conf.d/50-ubuntu.conf
```
Add the following two lines to the end of the file aforementioned.
```bash
greeter-show-manual-login=true
all-guest=false
```
Save and exit.

3. modify pam configuration

comment out the following line:
```bash
auth required pam_succeed_if.so user!=root quiet_success
```

in both two files:
```bash
/etc/pam.d/gdm-autologin
/etc/pam.d/gdm-password
```


4. modify root profile

Open the profile file:
```bash
sudo vim /root/.profile
```
and modify the last line as:
```bash
tty -s && mesg n || true
```



5. Reboot to enable 


## Add mis-configured sudo privileges
modify the sudo configuration file:
```bash
sudo vim /etc/sudoers
```

Add the following configuration to the last of the file aforementioned:
```bash
kali    ALL=(ALL:ALL) NOPASSWD:ALL
```
Please note "kali" is the current username on local virtual machine.




## Add mis-configured crontab
switch to root user

Then create a bash script file in /tmp/test.sh with following content:

```bash
#!/bin/bash
ls
```

Grant the misconfigured write privilege to all users of other group:
```bash
chmod 772 /tmp/test.sh
```

Then add the following line to /etc/crontab
```bash
* * * * * 	root	/tmp/test.sh
```



