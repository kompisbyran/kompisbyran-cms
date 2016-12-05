# -*- coding: utf-8 -*-

import sys
import os
from flask import request, session, Flask, escape
from mock import MagicMock
from flask_testing import TestCase
from bs4 import BeautifulSoup
from werkzeug.datastructures import ImmutableMultiDict

from features import FEATURES
from app import app
from cadapter import CAdapter

if not os.path.exists('src/static/css'):
    os.makedirs('src/static/css')
reload(sys)

ContentfulAdapter = CAdapter()


class FlaskTest(TestCase):
    def create_app(self):
        app.config.update(TESTING=True, PRESERVE_CONTEXT_ON_EXCEPTION=False)
        app.secret_key = 'temporary'
        for key in FEATURES.keys():
            FEATURES[key] = True
        return app

    def test_index_route_return_200_status(self):
        response = self.client.get('/')
        self.assert200(response, 'Index route does not return 200 status')

    # Example test on how to use the mock object
    def test_index_route_return_content(self):
        ContentfulAdapter.get_entries = MagicMock(side_effect=contentful_mock)
        ContentfulAdapter.get_text = MagicMock(return_value={'text': 'text',
                                                             'title': 'title'})
        response = self.client.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')
        self.assertEquals(soup.title.string, 'Kompisbyrån')

    def test_if_footer_exist_on_start_page(self):
        ContentfulAdapter.get_entries = MagicMock(side_effect=contentful_mock)
        ContentfulAdapter.get_text = MagicMock(return_value={'text': 'text',
                                                             'title': 'title'})
        response = self.client.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')
        self.assertNotEqual(soup.find('footer', class_='footer'), None)

    def test_if_menu_exist_on_start_page(self):
        ContentfulAdapter.get_entries = MagicMock(side_effect=contentful_mock)
        ContentfulAdapter.get_text = MagicMock(return_value={'text': 'text',
                                                             'title': 'title'})
        response = self.client.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')
        self.assertNotEqual(soup.find('div', class_='navbar-header'), None)

    def test_if_secondary_friends_are_on_start_page(self):
        ContentfulAdapter.get_entries = MagicMock(side_effect=contentful_mock)
        ContentfulAdapter.get_text = MagicMock(return_value={'text': 'text',
                                                             'title': 'title'})
        response = self.client.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')
        div = soup.find('div', class_='secondary-campaign')
        self.assertNotEqual(div, None)

    def test_if_faq_questions_are_on_start_page(self):
        ContentfulAdapter.get_entries = MagicMock(side_effect=contentful_mock)
        ContentfulAdapter.get_text = MagicMock(return_value={'text': 'text',
                                                             'title': 'title'})
        response = self.client.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')
        div = soup.find_all('div', class_='faq__element')
        self.assertTrue(len(div) > 1 and len(div) < 5)

    def test_route_to_short_non_existant_page_gives_404(self):
        response = self.client.get('/invalid_url_adress')
        self.assert404(response, 'Should return 404 status.')

    def test_route_to_long_non_existant_page_gives_404(self):
        response = self.client.get('/long/invalid/url')
        self.assert404(response, 'Should return 404 status.')

    # Could not append files to the post and therefor this test could not test the whole mail chain.
    def test_mail_notifier_return_correct_status(self):
        data = ImmutableMultiDict([('body-plain', 'test')])
        response = self.client.post(
            '/mail-notifier', data=data, follow_redirects=True)
        self.assertEquals(response.data, 'OK')


def contentful_mock(*args, **kwargs):
    if args == ():
        arg = kwargs
    else:
        arg = args[0]

    if arg['content_type'] == 'about_page':
        return AboutPage()  # Not done
    elif arg['content_type'] == 'campaign':
        campaign = Campaign()
        campaign.mainFriend = get_friend_mock()
        campaign.secondaryFriends = [get_friend_mock(), get_friend_mock()]
        return [campaign]
    elif arg['content_type'] == 'friendPage':
        friendPage = get_friend_mock()
        return [friendPage]
    elif arg['content_type'] == 'newsItem':
        picture = type('picture', (), {})()
        picture.fields = {'file': 'www.dummy-url-to-the-picture.com/image'}
        news_item = NewsItem()
        news_item.title = 'news item'
        news_item.text = 'News text! This is text that describes the news item'
        news_item.picture = picture
        news_item.link = 'www.example-url-to-news-item.com/news_item'
        news_item.linkText = 'Go to news page'
        return [news_item]
    elif arg['content_type'] == 'meetup':
        picture = type('picture', (), {})()
        picture.fields = {'file': 'www.dummy-url-to-the-picture.com/image'}
        meetup = Meetup()
        meetup.date = "2016-12-28"
        meetup.picture = picture
        meetup.meetup = "Vi hade en trevlig fika"
        return [meetup]
    elif arg['content_type'] == 'sponsor':
        logo = type('logo', (), {})()
        logo.fields = {'file': 'www.dummy-url-to-the-logo.com/logo'}
        sponsor = Sponsor()
        sponsor.name = "Sponsor"
        sponsor.logo = logo
        return [sponsor]
    elif arg['content_type'] == 'menu':
        menu = Menu()
        menu.menuTitle = 'test title'
        menu.entries = []
        return [menu]
    elif arg['content_type'] == 'question':
        question = Question()
        question.question = 'The question'
        question.answer = 'The answer'
        return [question, question, question]
    elif arg['content_type'] == 'text':
        text = Text()
        text.title = 'Text title'
        text.text = 'Text snippet'
        return [text]
    else:
        return ['not existing']


def get_friend_mock():
    mainImage = type('mainImage', (), {})()
    mainImage.fields = {'file': 'www.url-to-the-picture.com/image'}
    friend = FriendPage()
    friend.title = 'Type title'
    friend.url = 'type'
    friend.mainImage = mainImage
    friend.introductionText = "Short text with introduction"
    friend.text = "The real text about this friend type"
    friend.promotionPage = None
    friend.sidePanel = 'Nothing'
    friend.image = None
    friend.meetup = None
    friend.video = None
    friend.youtubeVideo = None
    return friend
