#!/usr/bin/python

##
## Ansible module to perform initial Jellyfin setup
##
## Copyright (C) 2024 Kian Kasad <kian@kasad.com>
## MIT License. See LICENSE file.
##

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
--- module: jellyfin_setup

short_description: Perform initial setup of a Jellyfin server

description: |-
    Performs initial setup of a Jellyfin server to meet my needs. This module is
    not designed to be extensible or configurable.

options:
    server_name:
        description:
            - Display name to set for the Jellyfin server.
            - Defaults to "Jellyfin Media Server"
        required: false type: str
    jellyfin_domain:
        description: Full domain name of the Jellyfin server. required: true
        type: str
    authentik_domain:
        description: Full domain name of the Authentik server. required: true
        type: str
    login_sso_only:
        description:
            - >-
                If enabled, the default login form will be hidden on the
                Jellyfin homepage and only the "Log in with Authentik" button
                will be displayed.
            - >-
                If disabled, the default login form persists and the "Log in
                with Authentik" button will be displayed below it.
            - Defaults to enabled.
        required: false
        type: bool
    oidc_client_id:
        description: OpenID Connect client ID. required: true type: str
    oidc_client_secret:
        description: OpenID Connect client ID. required: true type: str
    admin_username:
        description: Username for the initial admin user.
        required: true
        type: str
    admin_password:
        description: Password for the initial admin user.
        required: true
        type: str
    jellyfin_url:
        description:
            - URL to connect to the Jellyfin server with.
            - Defaults to "http://localhost:8096"
        required: false
        type: str

author:
    - Kian Kasad (@kdkasad)
'''

EXAMPLES = r'''
# Pass in a message
- name: Configure Jellyfin server
  jellyfin_setup:
    server_name: Jellyfin Media Server
    oidc_client_id: Ubaipha4ne3sienge1ua0aev  # gitleaks:allow
    oidc_client_secret: thaefoh5thee5iobaiqu9inguodoelah2fe5booMaiThe1paKuowaezee5oxee7U  # gitleaks:allow
    login_sso_only: true
    jellyfin_domain: jellyfin.example.org
    authentik_domain: authentik.example.org
    admin_username: admin
    admin_password: supersecurepassword
'''

RETURN = r'''
'''

from sys import stderr
from time import sleep
import uuid
import requests
from ansible.module_utils.basic import AnsibleModule


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        server_name=dict(type='str', required=False, default='Jellyfin Media Server'),
        oidc_client_id=dict(type='str', required=True),
        oidc_client_secret=dict(type='str', required=True, no_log=True),
        jellyfin_domain=dict(type='str', required=True),
        authentik_domain=dict(type='str', required=True),
        login_sso_only=dict(type='str', required=False, default=True),
        admin_username=dict(type='str', required=True),
        admin_password=dict(type='str', required=True, no_log=True),
        jellyfin_url=dict(type='str', required=False, default='http://localhost:8096'),
    )

    result = dict(changed=False)
    module = AnsibleModule(argument_spec=module_args)

    jellysetup(module, result)
    result['changed'] = True
    module.exit_json(**result)


def main():
    run_module()

# This function performs the actual setup
def jellysetup(module, result):
    # Version of this setup script
    VERSION = '1.0.0'

    # SSO plugin information
    PLUGIN_NAME = 'SSO Authentication'
    PLUGIN_GUID = '505ce9d1-d916-42fa-86ca-673ef241d7df'
    PLUGIN_MANIFEST_URL = 'https://raw.githubusercontent.com/9p4/jellyfin-plugin-sso/manifest-release/manifest.json'

    # Create HTTP session
    session = requests.Session()
    session.headers.update({
        'Accept': 'application/json',
        'Authorization': 'MediaBrowser ' + ', '.join([
            'Client="jellysetup.py"',
            'Device="jellysetup.py"',
            f'DeviceId="{uuid.uuid4()}"',
            f'Version="{VERSION}"',
        ]),
    })

    def fail(msg: str):
        module.fail_json(msg=msg, **result)

    # Wait until Jellyfin reports that it's ready. Times out after 2 minutes.
    def waitUntilHealthy():
        healthy = False
        for i in range(24): # 24 tries * 5 seconds = 2 minutes
            try:
                healthy = session.get(f"{module.params['jellyfin_url']}/health").ok
            except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
                pass # No error if connection fails
            if healthy:
                break
            sleep(5)
        if not healthy:
            fail('Error: Jellyfin did not start up in time')

    # Make a request to Jellyfin's API. Exits if the request fails, otherwise
    # decodes the JSON response and returns the data.
    def makeApiRequest(method: str, path: str, data: any = None):
        try:
            response = session.request(method, f"{module.params['jellyfin_url']}{path}", json=data)
        except e:
            fail(f'{method} {path} failed: {e}')
        if not response.ok:
            fail(f'{method} {path} failed: {response.status_code} {response.reason}')
        if response.text:
            try:
                return response.json()
            except requests.exceptions.JSONDecodeError:
                fail(f'{method} {path} failed: Error decoding JSON response')
        else:
            return response.text

    # Wait until Jellyfin is ready
    waitUntilHealthy()

    # Get the configuration. Jellyfin expects this to be called first, even if we
    # don't care what it returns.
    makeApiRequest('GET', '/Startup/Configuration')

    # Set the configuration
    makeApiRequest('POST', '/Startup/Configuration', {
        'UICulture': 'en-US',
        'MetadataCountryCode': 'US',
        'PreferredMetadataLanguage': 'en',
    })

    # Get the initial user. Jellyfin expects this to be called before setting the
    # user, even if we don't care what it returns.
    makeApiRequest('GET', '/Startup/User')

    # Set the initial (admin) user.
    makeApiRequest('POST', '/Startup/User', {
        'Name': module.params['admin_username'],
        'Password': module.params['admin_password'],
    })

    # Set remote access settings
    makeApiRequest('POST', '/Startup/RemoteAccess', {
        'EnableRemoteAccess': True,
        'EnableAutomaticPortMapping': False,
    })

    # Complete the initial setup
    makeApiRequest('POST', '/Startup/Complete')


    # Now that initial setup is done, we need to authenticate as the new admin user
    # to continue using the API.
    authResponse = makeApiRequest('POST', '/Users/AuthenticateByName', {
        'Username': module.params['admin_username'],
        'Pw': module.params['admin_password'],
    })
    accessToken = authResponse['AccessToken']

    # Add token to Authorization header
    session.headers['Authorization'] += f', Token="{accessToken}"'

    # Enable the Jellyfin-SSO plugin repository
    repositories = makeApiRequest('GET', '/Repositories')
    repositories.append({
        'Name': 'Jellyfin-SSO',
        'Url': PLUGIN_MANIFEST_URL,
        'Enabled': True,
    })
    makeApiRequest('POST', '/Repositories', repositories)

    # Install the Jellyfin-SSO plugin
    makeApiRequest('POST', f'/Packages/Installed/{PLUGIN_NAME}', {
        'assemblyGuid': PLUGIN_GUID
    })

    # Restart Jellyfin to apply plugin changes
    makeApiRequest('POST', '/System/Restart')
    sleep(5)

    # Wait until Jellyfin is ready again
    waitUntilHealthy()

    # Add Authentik OIDC provider
    makeApiRequest('POST', f'/sso/OID/Add/Authentik?api_key={accessToken}', {
        'oidEndpoint': f"https://{module.params['authentik_domain']}/application/o/jellyfin",
        'oidClientId': module.params['oidc_client_id'],
        'oidSecret': module.params['oidc_client_secret'],
        'oidScopes': ['openid', 'profile', 'email', 'groups'],
        'roleClaim': 'groups',
        'adminRoles': ['Administrators'],
        'enableAuthorization': True,
        'enableAllFolders': False,
        'enabledFolders': [],
        'enableFolderRoles': True,
        'enableLiveTv': False,
        # 'folderRoleMapping': {},
        'enabled': True,
    })

    # Configure branding to add SSO auth options to login page
    login_disclaimer_html = '''\
<form action="/sso/OID/start/Authentik">
<button class="raised block emby-button button-submit">
    Sign in with Authentik
</button>
</form>
'''
    custom_css = '''\
.loginDisclaimer {
width: 100%;
}
'''
    if module.params['login_sso_only']:
        custom_css += '''\
.manualLoginForm {
    display: none;
}
.readOnlyContent {
    display: flex;
    flex-direction: column-reverse;
}
button.btnForgotPassword {
    display: none;
}
'''
    makeApiRequest('POST', '/System/Configuration/Branding', {
        'LoginDisclaimer': login_disclaimer_html,
        'CustomCss': custom_css,
        'SplashscreenEnabled': False,
    })

    # Modify system configuration
    systemConfiguration = makeApiRequest('GET', '/System/Configuration')
    # Set server name
    systemConfiguration['ServerName'] = module.params['server_name']
    # Store metadata in a directory within the media library
    systemConfiguration['MetadataPath'] = '/media/metadata'
    makeApiRequest('POST', '/System/Configuration', systemConfiguration)

    # Restart the server to ensure all changes are applied
    makeApiRequest('POST', '/System/Restart')


if __name__ == '__main__':
    main()
