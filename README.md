# Home server playbook

[![CI](https://github.com/kdkasad/home-server/actions/workflows/ci.yml/badge.svg)](https://github.com/kdkasad/home-server/actions/workflows/ci.yml)

An Ansible playbook to manage my home server,
a mini-PC running Debian.

This playbook is heavily inspired by David Stephens'
[Ansible NAS](https://ansible-nas.io) project.
Much of the structure and some of the roles are taken from there.

Any roles which were adapted from Ansible NAS have their own license files
in their respective directories to retain the original copyright and license.

## What's included?

This playbook installs and configures the following services
(when enabled in `config.yml`):

### User-facing services

These are services hosted on the server that end users can interact with
directly.

#### Organization
- [Homarr](https://homarr.dev) web dashboard.

#### Observability & monitoring
- [Grafana](https://grafana.com), a data dashboarding tool.
  Used to display metrics from Prometheus and send alerts based on data.
- [Prometheus](https://prometheus.io), a monitoring and alerting toolkit.
  Collects metrics from various sources, and provides them to Grafana for display.
- [Loki](https://grafana.com/loki), a log aggregation system.
  Collects logs from various sources, and provides them to Grafana for display.

#### Storage & file sharing
- LAN file sharing (for NAS use), using [Samba](https://www.samba.org/)
  - Zero-configuration network discovery for MacOS, Windows, and Linux clients
    using [Avahi](https://github.com/avahi/avahi) (mDNS, DNS-SD)
    and [wsdd2](https://github.com/Netgear/wsdd2) (WS-Discovery, LLMNR).
- [Jellyfin](https://jellyfin.org) media server. Streams movies, TV shows,
  music, and more over the web.
- [MinIO](https://min.io), an S3-compatible object storage server.

#### Infrastructure & security
- [Authentik](https://goauthentik.io), a self-hosted identity provider.
  Acts as a central authentication system for other services.
- [Tailscale](https://tailscale.com), a VPN service.
  Allows secure access to the server from anywhere.
- [Bitwarden](https://bitwarden.com) password manager,
  using [Vaultwarden](https://github.com/dani-garcia/vaultwarden).

#### Games
- [Minecraft](https://www.minecraft.net/en-us) server
  (Java Edition), using [itzg/docker-minecraft-server](https://github.com/itzg/docker-minecraft-server).

### System services

The server also runs several services that are not directly user-facing, but are
necessary nonetheless.

- [Docker](https://docker.io), a containerization platform.
  Used to run most of the other services as containers.
- [Traefik](https://traefik.io/traefik/) reverse proxy, for routing traffic to
  services and managing TLS certificates.
- [ddclient](https://github.com/ddclient/ddclient), a dynamic DNS client.
  Updates the server's DNS record with the current public IP address.
- Local DNS server using [dnsmasq](https://dnsmasq.org/doc.html).
  Allows for custom DNS records, making the server accessible by the same name
  from the local network and the rest of the internet.
- Cron job to ping Healthchecks.io service.
- Metric/log exporters:
  - [Prometheus node exporter](https://github.com/prometheus/node_exporter)
    to export system metrics.
  - [cAdvisor](https://github.com/google/cadvisor)
    to export Docker container performance metrics.
  - [Promtail](https://grafana.com/docs/loki/latest/send-data/promtail/),
    to export system & Docker container logs to Loki.
- [Fail2ban](https://github.com/fail2ban/fail2ban), a log-based intrusion
  prevention system. Monitors logs for authentication failures and blocks
  IPs that have too many failures.

### Planned

These are some of the services/features I'd like to add in the near future:

- Automated data backups
- Automated configuration for using Authentik to provide authentication for services

## Installation

If you're looking to use this playbook to deploy your own home server, you may
want to take a look at [Ansible NAS](https://ansible-nas.io) instead.
It's a more complete and polished project, designed for you to customize.
This playbook is just for my personal server,
and while it is designed to be customizable,
it's not as polished or well-tested as Ansible NAS.

That being said, follow these steps to deploy a home server with this playbook:

#### 1. Install the latest version of Debian on your server.

I am running Debian 12 (Bookworm), but I plan to keep this playbook up-to-date
when new versions of Debian are released.

##### LVM

This playbook expects an LVM volume group to be set up.
Because that depends on the specific disk configuration of your server,
you will need to set that up manually before running this playbook.
The playbook uses the name `pool` for the VG, but that can be changed in `config.yml`.

> [!NOTE]
> If you are using the Debian installer, you can simply select the _Guided - use entire disk and set up LVM_ option.
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

```
$ cp inventory.sample inventory
```

Then edit `inventory`, replacing the `<placeholders>` with the proper values for your environment.

I also specify the SSH key to use in the inventory file,
and I store that key in the `keys/` directory of this repository.
You can remove this setting, and Ansible will use the default SSH key search path instead.

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
>
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
