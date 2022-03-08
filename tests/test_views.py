"""
dj-stripe Views Tests.
"""

import pytest
import stripe
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory
from django.urls import reverse
from pytest_django.asserts import assertContains

from djstripe import models, utils
from djstripe.views import ConfirmCustomAction

from .fields.models import TestCustomActionModel

pytestmark = pytest.mark.django_db


class TestConfirmCustomActionView:
    kwargs_called_with = {}

    # to get around Session/MessageMiddleware Deprecation Warnings
    def dummy_get_response(self, request):
        return None

    @pytest.mark.parametrize(
        "action_name", ["_resync_instances", "_sync_all_instances", "_cancel"]
    )
    def test_get_form_kwargs(self, action_name, admin_user, monkeypatch):

        model = TestCustomActionModel

        # monkeypatch utils.get_model
        def mock_get_model(*args, **kwargs):
            return model

        monkeypatch.setattr(utils, "get_model", mock_get_model)

        kwargs = {
            "action_name": action_name,
            "model_name": model.__name__.lower(),
        }

        # get the custom action POST url
        change_url = reverse("djstripe:djstripe_custom_action", kwargs=kwargs)

        request = RequestFactory().get(change_url)
        # add the admin user to the mocked request
        request.user = admin_user

        # Add the session/message middleware to the request
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)

        view = ConfirmCustomAction()
        view.setup(request, **kwargs)

        # Invoke the get_form_kwargs method
        form_kwargs = view.get_form_kwargs()
        assert form_kwargs.get("model_name") == model.__name__.lower()
        assert form_kwargs.get("action_name") == action_name

    @pytest.mark.parametrize(
        "action_name", ["_resync_instances", "_sync_all_instances", "_cancel"]
    )
    @pytest.mark.parametrize("is_admin_user", [True, False])
    def test_dispatch(self, is_admin_user, action_name, admin_user, monkeypatch):

        model = TestCustomActionModel

        # monkeypatch utils.get_model
        def mock_get_model(*args, **kwargs):
            return model

        monkeypatch.setattr(utils, "get_model", mock_get_model)

        kwargs = {
            "action_name": action_name,
            "model_name": model.__name__.lower(),
        }

        # get the custom action POST url
        change_url = reverse("djstripe:djstripe_custom_action", kwargs=kwargs)

        request = RequestFactory().get(change_url)

        if is_admin_user:
            # add the admin user to the mocked request
            request.user = admin_user
        else:
            # add the AnonymousUser to the mocked request
            request.user = AnonymousUser()

        # Add the session/message middleware to the request
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)

        view = ConfirmCustomAction()
        view.setup(request, **kwargs)

        # Invoke the dispatch method
        response = view.dispatch(request)

        if is_admin_user:
            assert response.status_code == 200
        else:
            assert response.status_code == 302
            assert (
                response.url
                == f"/admin/login/?next=/djstripe/action/{action_name}/testcustomactionmodel/"
            )

    @pytest.mark.parametrize(
        "action_name", ["_resync_instances", "_sync_all_instances", "_cancel"]
    )
    @pytest.mark.parametrize("djstripe_owner_account_exists", [False, True])
    def test_form_valid(self, djstripe_owner_account_exists, action_name, monkeypatch):
        model = TestCustomActionModel

        # create instance to be used in the Django Admin Action
        instance = model.objects.create(id="test")

        if djstripe_owner_account_exists:
            account_instance = models.Account.objects.first()
            instance.djstripe_owner_account = account_instance
            instance.save()

        data = {
            "action": action_name,
            helpers.ACTION_CHECKBOX_NAME: [instance.pk],
        }

        if action_name == "_sync_all_instances":
            data[helpers.ACTION_CHECKBOX_NAME] = ["_sync_all_instances"]

        # monkeypatch utils.get_model and
        def mock_get_model(*args, **kwargs):
            return model

        monkeypatch.setattr(utils, "get_model", mock_get_model)

        kwargs = {
            "action_name": action_name,
            "model_name": model.__name__.lower(),
        }

        # get the custom action POST url
        change_url = reverse("djstripe:djstripe_custom_action", kwargs=kwargs)

        request = RequestFactory().post(change_url, data=data, follow=True)

        # Add the session/message middleware to the request
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)

        view = ConfirmCustomAction()
        view.setup(request, **kwargs)

        # monkeypatch Request Handler
        def mock_request_handler(*args, **kwargs):
            return None

        monkeypatch.setattr(view, action_name, mock_request_handler)

        # get the form
        form = view.get_form()

        # Ensure form is valid
        assert form.is_valid()

        # Invoke form_valid()
        response = view.form_valid(form)

        # assert user redirected to the correct url
        assert response.status_code == 302
        assert response.url == "/admin/fields/testcustomactionmodel/"

    @pytest.mark.parametrize(
        "action_name", ["_resync_instances", "_sync_all_instances", "_cancel"]
    )
    @pytest.mark.parametrize("djstripe_owner_account_exists", [False, True])
    def test_form_invalid(
        self, djstripe_owner_account_exists, action_name, monkeypatch
    ):
        model = TestCustomActionModel

        # create instance to be used in the Django Admin Action
        instance = model.objects.create(id="test")

        if djstripe_owner_account_exists:
            account_instance = models.Account.objects.first()
            instance.djstripe_owner_account = account_instance
            instance.save()

        data = {
            "action": action_name,
        }

        # monkeypatch utils.get_model and
        def mock_get_model(*args, **kwargs):
            return model

        monkeypatch.setattr(utils, "get_model", mock_get_model)

        kwargs = {
            "action_name": action_name,
            "model_name": model.__name__.lower(),
        }

        # get the custom action POST url
        change_url = reverse("djstripe:djstripe_custom_action", kwargs=kwargs)

        request = RequestFactory().post(change_url, data=data, follow=True)

        # Add the session/message middleware to the request
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)

        view = ConfirmCustomAction()
        view.setup(request, **kwargs)

        # get the form
        form = view.get_form()

        # Ensure form is not valid
        assert not form.is_valid()

        # Invoke form_invalid()
        response = view.form_invalid(form)

        # assert user got redirected to the action page with the error rendered
        assertContains(
            response,
            '<ul class="messagelist">\n              <li class="error">* This field is required.</li>\n            </ul>',
            html=True,
        )

    @pytest.mark.parametrize("djstripe_owner_account_exists", [False, True])
    def test__resync_instances(self, djstripe_owner_account_exists, monkeypatch):
        model = TestCustomActionModel

        # create instance to be used in the Django Admin Action
        instance = model.objects.create(id="test")

        if djstripe_owner_account_exists:
            account_instance = models.Account.objects.first()
            instance.djstripe_owner_account = account_instance
            instance.save()

        data = {
            "action": "_resync_instances",
            helpers.ACTION_CHECKBOX_NAME: [instance.pk],
        }

        # monkeypatch instance.api_retrieve, instance.__class__.sync_from_stripe_data, and app_config.get_model
        def mock_instance_api_retrieve(*args, **keywargs):
            self.kwargs_called_with = keywargs

        def mock_instance_sync_from_stripe_data(*args, **kwargs):
            pass

        def mock_get_model(*args, **kwargs):
            return model

        monkeypatch.setattr(model, "api_retrieve", mock_instance_api_retrieve)

        monkeypatch.setattr(
            model,
            "sync_from_stripe_data",
            mock_instance_sync_from_stripe_data,
        )

        monkeypatch.setattr(utils, "get_model", mock_get_model)

        kwargs = {
            "action_name": "_resync_instances",
            "model_name": model.__name__.lower(),
        }

        # get the custom action POST url
        change_url = reverse("djstripe:djstripe_custom_action", kwargs=kwargs)

        request = RequestFactory().post(change_url, data=data, follow=True)

        # Add the session/message middleware to the request
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)

        view = ConfirmCustomAction()
        view.setup(request, **kwargs)

        # Invoke the Custom Actions
        view._resync_instances(request, [instance])

        # assert correct Success messages are emmitted
        messages_sent_dictionary = {
            m.message: m.level_tag for m in messages.get_messages(request)
        }

        # assert correct success message was emmitted
        assert (
            messages_sent_dictionary.get(f"Successfully Synced: {instance}")
            == "success"
        )

        if djstripe_owner_account_exists:
            # assert in case djstripe_owner_account exists that kwargs are not empty
            assert self.kwargs_called_with == {
                "stripe_account": instance.djstripe_owner_account.id,
                "api_key": instance.default_api_key,
            }
        else:
            # assert in case djstripe_owner_account does not exist that kwargs are empty
            assert self.kwargs_called_with == {}

    def test__resync_instances_stripe_permission_error(self, monkeypatch):

        model = TestCustomActionModel

        # create instance to be used in the Django Admin Action
        instance = model.objects.create(id="test")

        data = {
            "action": "_resync_instances",
            helpers.ACTION_CHECKBOX_NAME: [instance.pk],
        }

        # monkeypatch instance.api_retrieve and app_config.get_model
        def mock_instance_api_retrieve(*args, **kwargs):
            raise stripe.error.PermissionError("some random error message")

        def mock_get_model(*args, **kwargs):
            return model

        monkeypatch.setattr(instance, "api_retrieve", mock_instance_api_retrieve)
        monkeypatch.setattr(utils, "get_model", mock_get_model)

        kwargs = {
            "action_name": "_resync_instances",
            "model_name": model.__name__.lower(),
        }

        # get the custom action POST url
        change_url = reverse("djstripe:djstripe_custom_action", kwargs=kwargs)

        request = RequestFactory().post(change_url, data=data, follow=True)

        # Add the session/message middleware to the request
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)

        view = ConfirmCustomAction()
        view.setup(request, **kwargs)

        # Invoke the Custom Actions
        view._resync_instances(request, [instance])

        # assert correct Success messages are emmitted
        messages_sent_dictionary = {
            m.message.user_message: m.level_tag for m in messages.get_messages(request)
        }

        # assert correct success message was emmitted
        assert messages_sent_dictionary.get("some random error message") == "warning"

    def test__resync_instances_stripe_invalid_request_error(self, monkeypatch):
        model = TestCustomActionModel

        # create instance to be used in the Django Admin Action
        instance = model.objects.create(id="test")

        data = {
            "action": "_resync_instances",
            helpers.ACTION_CHECKBOX_NAME: [instance.pk],
        }

        # monkeypatch instance.api_retrieve and app_config.get_model
        def mock_instance_api_retrieve(*args, **kwargs):
            raise stripe.error.InvalidRequestError({}, "some random error message")

        def mock_get_model(*args, **kwargs):
            return model

        monkeypatch.setattr(instance, "api_retrieve", mock_instance_api_retrieve)
        monkeypatch.setattr(utils, "get_model", mock_get_model)

        kwargs = {
            "action_name": "_resync_instances",
            "model_name": model.__name__.lower(),
        }

        # get the custom action POST url
        change_url = reverse("djstripe:djstripe_custom_action", kwargs=kwargs)

        request = RequestFactory().post(change_url, data=data, follow=True)

        # Add the session/message middleware to the request
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)

        view = ConfirmCustomAction()
        view.setup(request, **kwargs)

        with pytest.raises(stripe.error.InvalidRequestError) as exc_info:
            # Invoke the Custom Actions
            view._resync_instances(request, [instance])

        assert str(exc_info.value.param) == "some random error message"
