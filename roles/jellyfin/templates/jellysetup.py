#!/usr/bin/env python3

#
# Automated Jellyfin initial setup script
#
# Copyright (C) 2024 Kian Kasad
#

from sys import stderr
from time import sleep
import requests

# Version of this setup script
VERSION = '0.0.0'

# Plugin information
PLUGIN_NAME = 'SSO Authentication'
PLUGIN_GUID = '505ce9d1-d916-42fa-86ca-673ef241d7df'
PLUGIN_MANIFEST_URL = 'https://raw.githubusercontent.com/9p4/jellyfin-plugin-sso/manifest-release/manifest.json'

BASEURL = 'http://127.0.0.1:8096'

# Create HTTP session
session = requests.Session()
session.headers.update({
    'Accept': 'application/json',
    'Authorization': 'MediaBrowser ' + ', '.join([
        'Client="jellysetup.py"',
        'Device="jellysetup.py"',
        'DeviceId="{{ ansible_machine_id }}"',
        f'Version="{VERSION}"',
    ]),
})

# Function to print to stderr
def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)

# Wait until Jellyfin reports that it's ready. Times out after 2 minutes.
def waitUntilHealthy():
    healthy = False
    for i in range(24): # 24 tries * 5 seconds = 2 minutes
        healthy = session.get(f'{BASEURL}/health').ok
        if healthy:
            break
        sleep(5)
    if not healthy:
        eprint('Error: Jellyfin did not start up in time')
        exit(1)

# Make a request to Jellyfin's API. Exits if the request fails, otherwise
# decodes the JSON response and returns the data.
def makeApiRequest(method: str, path: str, data: any = None):
    try:
        response = session.request(method, f'{BASEURL}{path}', json=data)
    except e:
        eprint(f'{method} {path} failed: {e}')
        exit(1)
    if not response.ok:
        eprint(f'{method} {path} failed: {response.status_code} {response.reason}')
        exit(1)
    if response.text:
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            eprint(f'{method} {path} failed: Error decoding JSON response')
            exit(1)
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
    'Name': "{{ jellyfin_admin_username | mandatory }}",
    'Password': "{{ jellyfin_admin_password | mandatory }}",
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
    'Username': "{{ jellyfin_admin_username | mandatory }}",
    'Pw': "{{ jellyfin_admin_password | mandatory }}",
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
    'oidEndpoint': f"https://{{ authentik_routing.subdomain | default('authentik') }}.{{ general.domain }}/application/o/jellyfin",
    'oidClientId': "{{ jellyfin_sso_client_id | mandatory }}",
    'oidSecret': "{{ jellyfin_sso_client_secret | mandatory }}",
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
LOGIN_DISCLAIMER_HTML = '''
<form action="/sso/OID/start/Authentik">
  <button class="raised block emby-button button-submit">
    Sign in with Authentik
  </button>
</form>
'''
CUSTOM_CSS = '''
.loginDisclaimer {
  width: 100%;
}
{% if jellyfin_sso_only is true %}
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
{% endif %}
'''
makeApiRequest('POST', '/System/Configuration/Branding', {
    'LoginDisclaimer': LOGIN_DISCLAIMER_HTML,
    'CustomCss': CUSTOM_CSS,
    'SplashscreenEnabled': False,
})

# Modify system configuration
systemConfiguration = makeApiRequest('GET', '/System/Configuration')
# Set server name
systemConfiguration['ServerName'] = "{{ jellyfin_server_name }}"
# Store metadata in a directory within the media library
systemConfiguration['MetadataPath'] = '/media/metadata'
makeApiRequest('POST', '/System/Configuration', systemConfiguration)

# Restart the server to ensure all changes are applied
makeApiRequest('POST', '/System/Restart')
