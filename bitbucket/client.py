import requests

from bitbucket.exceptions import UnknownError, InvalidError, NotFoundError, NotAuthenticatedError, PermissionError


class Client(object):
    BASE_URL = 'https://api.bitbucket.org/'

    def __init__(self, user, password, owner=None):
        """Initial session with user/password, and setup repository owner

        Args:
            params:

        Returns:

        """

        self.user = user
        self.password = password

        user_data = self.get_user()

        # for shared repo, set baseURL to owner
        if owner is None:
            owner = user_data.get('username')
        self.username = owner

    def get_user(self, params=None):
        """Returns user data.

        Args:
            params:

        Returns:

        """
        return self._get('2.0/user')

    def get_workspaces(self, params=None):
        endpoint = '2.0/workspaces/'
        return self._get(endpoint, params=params)

    def get_repositories(self, next_url=None, workspace=None, params=None):
        """Returns first page of the repositories this user has access, a workspace can be given
        to narrow down the result

        Args:
            workspace:
            params:

        Returns:

        """
        if next_url:
            return self._get_url(next_url)
        else:
            workspace = workspace if workspace else self.username
            endpoint = '2.0/repositories/{}'.format(workspace)
            return self._get(endpoint, params=params)

    def get_repository(self, repository_slug, params=None):
        """Returns the object describing this repository.

        Args:
            repository_slug:
            params:

        Returns:

        """
        return self._get('2.0/repositories/{}/{}'.format(self.username, repository_slug), params=params)

    def _get(self, endpoint, params=None):
        response = requests.get(self.BASE_URL + endpoint, params=params, auth=(self.user, self.password))
        return self._parse(response)

    def _get_url(self, url):
        response = requests.get(url, auth=(self.user, self.password))
        return self._parse(response)

    def _parse(self, response):
        status_code = response.status_code
        if 'application/json' in response.headers['Content-Type']:
            r = response.json()
        else:
            r = response.text
        if status_code in (200, 201):
            return r
        if status_code == 204:
            return None
        message = None
        try:
            if 'errorMessages' in r:
                message = r['errorMessages']
        except Exception:
            message = 'No error message.'
        if status_code == 400:
            raise InvalidError(message)
        if status_code == 401:
            raise NotAuthenticatedError(message)
        if status_code == 403:
            raise PermissionError(message)
        if status_code == 404:
            raise NotFoundError(message)
        raise UnknownError(message)