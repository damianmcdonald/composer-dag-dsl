from unittest import TestCase, mock, main
from composer.utils import auth_service


class AuthServiceTests(TestCase):

    @mock.patch('google.oauth2.service_account.Credentials.from_service_account_info')
    @mock.patch('google.auth.default')
    @mock.patch('google.oauth2.service_account.Credentials')
    def test_get_credentials(self, mock_credentials, mock_auth_default, mock_service_account):
        mock_service_account.return_value = mock_credentials
        mock_auth_default.return_value = mock_credentials, 'mock_tuple_value'
        credentials = auth_service.get_credentials()
        assert credentials is not None
        assert credentials.service_account_email is not None
        assert credentials.signer is not None
        assert credentials._token_uri is not None
        assert credentials.project_id is not None
        assert credentials.scopes is not None

    @mock.patch('google.oauth2.service_account.Credentials.from_service_account_info')
    @mock.patch('google.auth.default')
    @mock.patch('google.oauth2.service_account.Credentials')
    @mock.patch('google.auth.transport.requests.AuthorizedSession')
    def test_get_authenticated_session(self, mock_auth_session, mock_credentials, mock_auth_default, mock_service_account):
        mock_service_account.return_value = mock_credentials
        mock_auth_default.return_value = mock_credentials, 'mock_tuple_value'
        mock_auth_session.return_value = 'faked_auth_session'
        auth_session = auth_service.get_authenticated_session()
        assert auth_session is not None

    @mock.patch('google.oauth2.service_account.IDTokenCredentials.from_service_account_info')
    @mock.patch('os.environ')
    @mock.patch('google.oauth2.service_account.Credentials')
    @mock.patch('json.loads')
    @mock.patch('base64.b64decode')
    def test_get_id_token(self, mock_base64_decode, mock_json_loads, mock_id_credentials, mock_os_environ, mock_service_account):
        mock_os_environ['GOOGLE_APPLICATION_CREDENTIALS'].return_value = 'mock_creds_value'
        mock_service_account.return_value = mock_id_credentials
        mock_base64_decode.return_value = b'decoded_string'
        mock_json_loads.return_value = 'mock_json_string'
        mock_id_credentials.refresh.return_value = "refreshed"
        mock_id_credentials.token = 'fake_open_id_token'
        open_id_token = auth_service.get_id_token('fake_request', 'fake_audience')
        assert open_id_token is not None
        assert open_id_token == 'fake_open_id_token'


if __name__ == '__main__':
    main()
