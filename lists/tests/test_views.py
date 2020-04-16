import unittest
from django.http import HttpRequest
from django.test import TestCase
from django.utils.html import escape
from django.contrib.auth import get_user_model

from lists.models import Item, List
from lists.forms import (
    ERROR_DUPLICATE_ITEM, ERROR_EMPTY_ITEM,
    ExistingListItemForm, ItemForm
)
from lists.views import new_list


User = get_user_model()


class HomePageTest(TestCase):
    def test_uses_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')

    def test_home_page_uses_item_form(self):
        response = self.client.get('/')
        self.assertIsInstance(response.context['form'], ItemForm)


@unittest.mock.patch('lists.views.NewListForm')
class NewListViewUnitTest(unittest.TestCase):
    def setUp(self):
        self.request = HttpRequest()
        self.request.POST['text'] = 'new list item'
        self.request.user = unittest.mock.Mock()

    def test_passes_POST_data_to_NewListForm(self, mockNewListForm):
        new_list(self.request)
        mockNewListForm.assert_called_once_with(data=self.request.POST)

    def test_saves_form_with_owner_if_form_valid(self, mockNewListForm):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = True
        new_list(self.request)
        mock_form.save.assert_called_once_with(owner=self.request.user)

    @unittest.mock.patch('lists.views.redirect')
    def test_redirects_to_form_returned_object_if_form_valid(
            self, mock_redirect, mockNewListForm
    ):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = True

        response = new_list(self.request)

        self.assertEqual(response, mock_redirect.return_value)
        mock_redirect.assert_called_once_with(mock_form.save.return_value)

    @unittest.mock.patch('lists.views.render')
    def test_renders_home_template_with_form_if_form_invalid(
            self, mock_render, mockNewListForm
    ):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = False

        response = new_list(self.request)

        self.assertEqual(response, mock_render.return_value)
        mock_render.asssert_called_once_with(
            self.request, 'home.html', {'form': mock_form}
        )

    def test_does_not_save_if_form_invalid(self, mockNewListForm):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = False
        new_list(self.request)
        self.assertFalse(mock_form.save.called)


class NewListViewIntegratedTest(TestCase):
    def post_invalid_input(self):
        return self.client.post('/lists/new', data={'text': ''})
    
    def test_can_save_a_POST_request(self):
        response = self.client.post('/lists/new', data={'text': 'A new list item'})
        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new list item')

    def test_redirects_after_POST(self):
        response = self.client.post('/lists/new', data={'text': 'A new list item'})
        new_list = List.objects.first()
        self.assertRedirects(response, f'/lists/{new_list.id}/')

    def test_for_invalid_input_renders_home_templat(self):
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_validation_errors_are_shown_on_home_page(self):
        response = self.post_invalid_input()
        self.assertContains(response, ERROR_EMPTY_ITEM)

    def test_for_invalid_input_passes_form_to_template(self):
        response = self.post_invalid_input()
        self.assertIsInstance(response.context['form'], ItemForm)

    def test_invalid_list_items_arent_saved(self):
        self.post_invalid_input()
        self.assertEqual(List.objects.count(), 0)
        self.assertEqual(Item.objects.count(), 0)

    def test_for_invalid_input_doesnt_save_but_shows_errors(self):
        response = self.post_invalid_input()
        self.assertEqual(List.objects.count(), 0)
        self.assertContains(response, ERROR_EMPTY_ITEM)

    def test_list_owner_is_saved_if_user_is_authenticated(self):
        user = User.objects.create(email='a@b.com')
        self.client.force_login(user)
        self.client.post('/lists/new', data={'text':'new item'})
        list_ = List.objects.first()
        self.assertEqual(list_.owner, user)


class ListViewTest(TestCase):
    def post_invalid_input(self):
        list_ = List.objects.create()
        return self.client.post(f'/lists/{list_.id}/', data={'text': ''})
    
    def test_uses_list_template(self):
        list_ = List.objects.create()
        response = self.client.get(f'/lists/{list_.id}/')
        self.assertTemplateUsed(response, 'list.html')
    
    def test_passes_correct_list_to_template(self):
        other_list = List.objects.create()
        correct_list = List.objects.create()
        response = self.client.get(f'/lists/{correct_list.id}/')
        self.assertEqual(response.context['list'], correct_list)
    
    def test_displays_item_form(self):
        list_ = List.objects.create()
        response = self.client.get(f'/lists/{list_.id}/')
        self.assertIsInstance(response.context['form'], ExistingListItemForm)
        self.assertContains(response, 'name="text"')
    
    def test_displays_only_items_for_that_list(self):
        correct_list = List.objects.create()
        Item.objects.create(text='itemey 1', list=correct_list)
        Item.objects.create(text='itemey 2', list=correct_list)
        other_list = List.objects.create()
        Item.objects.create(text='other list item 1', list=other_list)
        Item.objects.create(text='other list item 2', list=other_list)

        response = self.client.get(f'/lists/{correct_list.id}/')
        
        self.assertContains(response, 'itemey 1')
        self.assertContains(response, 'itemey 2')
        self.assertNotContains(response, 'other list item 1')
        self.assertNotContains(response, 'other list item 1')

    def test_can_save_a_POST_request_to_an_existing_list(self):
        other_list = List.objects.create()
        correct_list = List.objects.create()

        self.client.post(
                f'/lists/{correct_list.id}/',
                data={'text': 'A new item for an existing list'}
        )

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new item for an existing list')
        self.assertEqual(new_item.list, correct_list)

    def test_POST_redirects_to_list_view(self):
        other_list = List.objects.create()
        correct_list = List.objects.create()

        response = self.client.post(
            f'/lists/{correct_list.id}/',
            data={'text': 'A new item for an existing list'}
        )
        self.assertRedirects(response, f'/lists/{correct_list.id}/')

    def test_for_invalid_input_nothing_saved_to_db(self):
        self.post_invalid_input()
        self.assertEqual(Item.objects.count(), 0)

    def test_for_invalid_input_renders_list_template(self):
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'list.html')

    def test_for_invalid_input_passes_form_to_template(self):
        response = self.post_invalid_input()
        self.assertIsInstance(response.context['form'], ExistingListItemForm)

    def test_for_invalid_input_shows_error_on_page(self):
        response = self.post_invalid_input()
        self.assertContains(response, ERROR_EMPTY_ITEM)

    def test_duplicate_item_validation_errors_end_up_on_lists_page(self):
        list_ = List.objects.create()
        item = Item.objects.create(list=list_, text='textey')
        response = self.client.post(
            f'/lists/{list_.id}/',
            data={'text': 'textey'}
        )
        self.assertContains(response, ERROR_DUPLICATE_ITEM)
        self.assertTemplateUsed(response, 'list.html')
        self.assertEqual(Item.objects.count(), 1)

class MyListsTest(TestCase):
    def test_my_lists_url_renders_my_lists_template(self):
        user = User.objects.create(email='a@b.com')
        response = self.client.get('/lists/users/a@b.com/')
        self.assertTemplateUsed(response, 'my_lists.html')

    def test_passes_correct_owner_to_template(self):
        User.objects.create(email='wrong@owner.com')
        correct_user = User.objects.create(email='a@b.com')
        response = self.client.get('/lists/users/a@b.com/')
        self.assertEqual(response.context['owner'], correct_user)

    def test_show_shared_lists(self):
        user = User.objects.create(email='user@1.com')
        list_ = List.objects.create()
        item_ = Item.objects.create(list=list_, text='share this')
        list_.shared_with.add(user)
        response = self.client.get(f'/lists/users/{user.email}/')
        self.assertContains(response, 'share this')


class ShareListTest(TestCase):
    def test_post_redirects_to_lists_page(self):
        list_ = List.objects.create()
        item = Item.objects.create(list=list_, text='new item')
        response = self.client.post(
            f'/lists/{list_.id}/share'
        )
        self.assertRedirects(response, list_.get_absolute_url())

    def test_same_user_part_of_shared_when_requested(self):
        email = 'a@b.com'
        user = User.objects.create(email=email)
        list_ = List.objects.create()
        response = self.client.post(
            f'/lists/{list_.id}/share',
            data={'share_with_email': email}
        )
        self.assertEqual([email], [u.email for u in list_.shared_with.all()])

    def test_unknown_user_will_not_be_shared(self):
        email = 'un@known.com'
        list_ = List.objects.create()
        response = self.client.post(
            f'/lists/{list_.id}/share',
            data={'share_with_email': email}
        )
        self.assertEqual([], [u.email for u in list_.shared_with.all()])

    def test_user_shows_up_in_list_sharee(self):
        list_ = List.objects.create()
        email = 'to_share@with.com'
        user = User.objects.create(email=email)
        self.client.post(
            f'/lists/{list_.id}/share',
            data={'share_with_email': email}
        )
        response = self.client.get(f'/lists/{list_.id}/')
        self.assertContains(response, 'List shared with')
        self.assertContains(response, email)

