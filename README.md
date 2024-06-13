# Home server playbook

An Ansible playbook to manage my home server,
a mini-PC running Debian.

This playbook is heavily inspired by David Stephens'
[Ansible NAS](https://ansible-nas.io) project.
Much of the structure and some of the roles are taken from there.

Any roles which were adapted from Ansible NAS have their own license files
in their respective directories to retain the original copyright and license.

# How to use

If you're looking to use this playbook to deploy your own home server, you may
want to take a look at [Ansible NAS](https://ansible-nas.io) instead.
It's a more complete and polished project, designed for you to customize.
This playbook is just for my personal server,
and while it is designed to be customizable,
it's not as polished or well-tested as Ansible NAS.


That being said, follow these steps to deploy a home server with this playbook:

#### 1.  Install the latest version of Debian on your server.
I am running Debian 12 (Bookworm), but I plan to keep this playbook up-to-date
when new versions of Debian are released.

##### LVM
This playbook expects an LVM volume group to be set up.
Because that depends on the specific disk configuration of your server,
you will need to set that up manually before running this playbook.
The playbook uses the name `pool` for the VG, but that can be changed in `config.yml`.

> [!NOTE]
> If you are using the Debian installer, you can simply select the *Guided - use entire disk and set up LVM* option.
> Note the name of the volume group that is created.
> This can be found by running the `vgs` command in the new system.

##### SSH
Set up **key-based** SSH access for a user with sudo or su privileges.
The playbook disables password authentication for SSH.

> [!CAUTION]
> If you don't have an SSH keypair set up, you will lose SSH access to your server.

#### 2. Install Ansible on your local machine.

#### 3. Clone this repository.
```
$ git clone https://github.com/kdkasad/home-server.git
```

#### 4. Install the required dependencies from Ansible Galaxy.
```
$ ansible-galaxy install -r requirements.yml
```

#### 5. Configure the `inventory` file to match your server's network address.

I also specify the SSH key to use in the inventory file,
and I store that key in the `keys/` directory of this repository.
You can omit this, and Ansible will use the default SSH key search path.

#### 6. Use the sample configuration file to create your own configuration file.
```
$ cp config.yml.sample config.yml
```
Then edit `config.yml` to meet your needs.

 > [!NOTE]
 > This will overwrite the existing `config.yml` file,
 > which contains my personal settings for my server.
 >
 > If you want to keep that file for reference,
 > rename it first:
 > ```
 > $ mv config.yml config-kdkasad.yml
 > ```

#### 7. Simply run the `main.yml` playbook using Ansible.
```
$ ansible-playbook -K main.yml
```

#### 8. You're done!
You can reboot your server to be extra sure all changes are applied,
but it shouldn't be necesary.
