import urllib

from logging import getLogger
from Products.Five import BrowserView
from plone import api
from plone.memoize import view
from zope.component import getUtility

from ploneintranet.library import _
from ploneintranet.library.browser import utils
from ploneintranet.search.interfaces import ISiteSearch

log = getLogger(__name__)


class LibraryHomeView(BrowserView):
    """
    The '/library' link in the portal tabs is coded as a CMF action
    and not derived from the actual library app URL.
    This view redirects to the, or a, actual LibraryApp/view.
    """
    def __call__(self):
        catalog = api.portal.get_tool('portal_catalog')
        results = catalog(portal_type='ploneintranet.library.app')
        if not results:
            msg = "Somebody removed the last library app and broke the site."
            log.error(msg)
            return msg
        target = results[0].getURL()

        if len(results) > 1:
            # pick the first one, unless there is one actually called 'libary'
            for brain in results:
                if brain.id == 'library':
                    target = brain.getURL()

        # get us to an actual LibraryAppView
        self.request.response.redirect(target)


class LibraryBaseView(BrowserView):

    groupby = 'section'

    def selected(self, value):
        if value == self.groupby:
            return dict(selected=1)
        return {}

    def __call__(self):
        groupby = self.request.get('groupby', None)
        if not groupby:
            return super(LibraryBaseView, self).__call__()

        if groupby == 'section':
            self.request.response.redirect(self.context.absolute_url())
        elif groupby == 'tag':
            self.request.response.redirect('{}/tag'.format(
                self.context.absolute_url()))

    def app(self):
        return self.chain(getapp=True)

    @view.memoize
    def chain(self, getapp=False):
        _chain = []
        obj = self.context
        while (obj.portal_type != 'ploneintranet.library.app' and
               obj.portal_type != 'Plone Site'):
            _chain.insert(0, dict(title=obj.Title,
                                  absolute_url=obj.absolute_url()))
            obj = obj.aq_inner.aq_parent

        if obj.portal_type == 'Plone Site':
            raise AttributeError("Cannot find parent Library app!")

        if getapp:
            return obj
        return _chain

    @view.memoize
    def sections(self):
        """Return toplevel section navigation"""
        app = self.app()
        sections = app.objectValues()
        current_url = self.request['ACTUAL_URL']
        current_nav = app
        for s in sections:
            if current_url.startswith(s.absolute_url()):
                current_nav = s
                break

        app_current = (app == current_nav) and 'current' or ''
        menu = [dict(title=_("All topics"),
                     absolute_url=app.absolute_url(),
                     current=app_current)]

        for s in sections:
            s_current = (s == current_nav) and 'current' or ''
            menu.append(dict(title=s.Title,
                             absolute_url=s.absolute_url(),
                             current=s_current))
        return menu

    @view.memoize
    def children(self):
        """Return children and grandchildren of current context"""
        return utils.sections_of(self.context)

    def can_edit(self):
        return api.user.has_permission('Add portal content',
                                       obj=self.context)


class LibraryAppView(LibraryBaseView):

    def info(self):
        return {}


class LibrarySectionView(LibraryBaseView):

    def info(self):
        return dict(title=self.context.Title,
                    description=self.context.Description)


class LibraryFolderView(LibraryBaseView):

    def info(self):
        return dict(
            chain=self.chain(),
            description=self.context.Description)


class LibraryTagView(LibraryBaseView):

    groupby = 'tag'

    def info(self):
        return {}

    def sections(self):
        """Toplevel section navigation, targets tag facet"""
        menu = super(LibraryTagView, self).sections()
        for section in menu:
            section['absolute_url'] += '/@@tag'
        return menu

    def children(self):
        """Expose tag facet for library or section"""
        path = '/'.join(self.context.getPhysicalPath())
        sitesearch = getUtility(ISiteSearch)
        response = sitesearch.query(filters=dict(path=path))
        struct = []
        for tag in response.facets.get('tags'):
            url = "%s/@@tag/%s" % (self.context.absolute_url(),
                                   urllib.quote(tag))
            section = dict(title=tag,
                           absolute_url=url,
                           type='tag',
                           subtags=[],
                           content=[])
            sub_response = sitesearch.query(filters=dict(path=path,
                                                         tags=tag))
            for sub_tag in sub_response.facets.get('tags'):
                sub_url = "%s/@@tag/%s" % (self.context.absolute_url(),
                                           urllib.quote(sub_tag))
                section['subtags'].append(dict(title=sub_tag,
                                               absolute_url=sub_url))
            struct.append(section)
        return struct
