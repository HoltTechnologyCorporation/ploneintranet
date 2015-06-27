# -*- coding: utf-8 -*-
from zExceptions import NotFound
from AccessControl import Unauthorized
from plone import api

from ploneintranet.userprofile.tests.base import BaseTestCase
from ploneintranet.userprofile.browser.userprofile import UserProfileView
from ploneintranet.userprofile.browser.userprofile import AuthorView
from ploneintranet.userprofile.browser.userprofile import MyProfileView


class TestUserProfileBase(BaseTestCase):

    def setUp(self):
        super(TestUserProfileBase, self).setUp()
        self.login_as_portal_owner()
        self.profile1 = api.content.create(
            container=self.profiles,
            type='ploneintranet.userprofile.userprofile',
            id='johndoe',
            username='johndoe',
            first_name='John',
            last_name='Doe',
        )
        api.content.transition(self.profile1, 'approve')
        self.profile1.reindexObject()

        self.profile2 = api.content.create(
            container=self.profiles,
            type='ploneintranet.userprofile.userprofile',
            id='janedoe',
            username='janedoe',
            first_name='Jane',
            last_name='Doe',
        )
        api.content.transition(self.profile2, 'approve')
        self.profile2.reindexObject()

        self.logout()


class TestUserProfileView(TestUserProfileBase):

    def test_is_me(self):
        profile_view = UserProfileView(self.profile1, self.request)

        self.login(self.profile1.username)
        self.assertTrue(profile_view.is_me())
        self.logout()

        self.login(self.profile2.username)
        self.assertFalse(profile_view.is_me())
        self.logout()

    def test_avatar_url(self):
        self.login(self.profile1.username)
        profile_view = UserProfileView(self.profile1, self.request)
        url = profile_view.avatar_url()
        # No profile data by default
        # Avatar lookup is properly tested in ploneintranet.api
        self.assertIsNone(url)

    def test__user_details(self):
        self.login(self.profile1.username)
        profile_view = UserProfileView(self.profile1, self.request)
        details = profile_view._user_details([
            self.profile1.username,
            self.profile2.username,
        ])
        self.assertEqual(len(details), 2)
        self.assertEqual(
            details[0]['title'], self.profile1.fullname,
        )
        self.assertEqual(
            details[1]['title'], self.profile2.fullname,
        )


class TestAuthorView(TestUserProfileBase):

    def test_call(self):
        self.login(self.profile2.username)
        author_view = AuthorView(self.portal, self.request)

        author_view.publishTraverse(self.request,
                                    self.profile1.username)
        redirect_url = author_view()
        self.assertEqual(
            redirect_url,
            self.profile1.absolute_url(),
        )

        author_view.publishTraverse(self.request,
                                    'not-a-username')
        with self.assertRaises(NotFound):
            author_view()


class TestMyProfileView(TestUserProfileBase):

    def test_call(self):
        self.login(self.profile2.username)
        myprofile_view = MyProfileView(self.portal, self.request)

        redirect_url = myprofile_view()
        self.assertEqual(
            redirect_url,
            self.profile2.absolute_url(),
        )

        self.logout()

        with self.assertRaises(Unauthorized):
            myprofile_view()