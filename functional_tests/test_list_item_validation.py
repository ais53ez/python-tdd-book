from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from .base import FunctionalTest


class ItemValidationTest(FunctionalTest):
    def test_cannot_add_empty_list_items(self):
        # Edith goes to the home page and accidendally tries to submit
        # an empty list item. She hits Enter on the empty input box

        # The home pge refreshes, and there is an error message saying
        # that list items cannot be blank

        # She tries again with some text for the item, which now works

        # Perversely, she now decides to submit a second blank list item

        # She receives a similar warning on the list page

        # And she can correct it by filling some text in
        self.fail('write me!')
        self.browser.get(self.live_server_url)
        inputbox = self.browser.find_element_by_id('id_new_item')
        inputbos.send_keys(Keys.ENTER)
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertNotIn('1: ', page_text)
        self.assertIn('List items cannot be blank', page_text)

