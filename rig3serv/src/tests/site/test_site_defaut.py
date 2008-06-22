#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Site

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os
from datetime import datetime

from tests.rig_test_case import RigTestCase

from rig.site.site_default import SiteDefault
from rig.site_base import DEFAULT_THEME, SiteItem
from rig.sites_settings import SiteSettings
from rig.parser.dir_parser import DirParser, RelDir
from rig.source_reader import SourceDirReader
from rig.source_item import SourceDir
from rig.sites_settings import SiteSettings, SitesSettings

#------------------------
class MockSiteDefault(SiteDefault):
    """
    Behaves like a SiteDefault() but overrides the base template directory location
    to use testdata/templates instead.
    
    Also traps the last _Filltemplate parameters.
    """
    def __init__(self, test_case, log, dry_run, settings):
        self._test_case = test_case
        self._fill_template_params = {}
        self._write_file_params = []
        super(MockSiteDefault, self).__init__(log, dry_run, settings)

    def _TemplateDir(self):
        """"
        Uses testdata/templates/ instead of templates/
        """
        return os.path.join(self._test_case.getTestDataPath(), "templates")

    def _FillTemplate(self, template, **keywords):
        """
        Keeps a copy of the _FillTemplate parameters and then call the original.
        Trapped parameters are available in
          self._fill_template_params[template] => list(keyuword dict.)
        """
        if not template in self._fill_template_params:
            self._fill_template_params[template] = []
        self._fill_template_params[template].append(dict(keywords))
        return super(MockSiteDefault, self)._FillTemplate(template, **keywords)

    def _WriteFile(self, data, dest_dir, leafname):
        """
        Keeps a copy of all parameters given to _WriteFile.
        This implementation does NOT call the base class so that nothing gets
        written anywhere.
        
        Trapped parameters are available in
          self._write_file_params => list(data, dest_dir, leafname)
        See GetWriteFileData(n, m) below.
        """
        self._write_file_params.append((data, dest_dir, leafname))

    _DATA = 0
    _DEST_DIR = 1
    _LEAFNAME = 2
    
    def GetWriteFileData(self, tuple_index1, tuple_index2=None):
        """
        Returns a *copy* of the self._write_file_params list
        with items rearanged.
        - tuple_index1: _DATA, _DEST_DIR or _LEAFNAME, the first
          value to return.
        - tuple_index2: _DATA, _DEST_DIR, _LEAFNAME or None, the second value to return.
        
        This basically remaps (data, dest_dir, leafname) to whatever you like
        to test. If tuple_index2 is None, only one value is given directly
        in the list, otherwise it's a tuple (value1, value2).
        """
        # Hey kids, go write that in Java in less than a few dozen lines!
        if tuple_index2 is None:
            return [ p[tuple_index1] for p in self._write_file_params ]
        else:
            return [ ( p[tuple_index1], p[tuple_index2] ) for p in self._write_file_params ]


#------------------------
class SiteDefaultTest(RigTestCase):

    def setUp(self):
        self._tempdir = self.MakeTempDir()
        source = SourceDirReader(self.Log(), None,
                                 os.path.join(self.getTestDataPath(), "album"))
        self.s = SiteSettings(public_name="Test Album",
                              source_list=[ source ],
                              dest_dir=self._tempdir,
                              theme=DEFAULT_THEME,
                              base_url="http://www.example.com",
                              rig_base="http://example.com/photos/index.php")

    def tearDown(self):
        self.RemoveDir(self._tempdir)

    def testSimpleFileName(self):
        m = MockSiteDefault(self, self.Log(), False, self.s)
        self.assertEquals("filename_txt", m._SimpleFileName("filename.txt"))
        self.assertEquals("abc-de-f-g-h", m._SimpleFileName("abc---de   f-g h"))
        self.assertEquals("abc-de-f-g-h", m._SimpleFileName("abc///de\\\\f/g\\h"))
        self.assertEquals("a-ab_12_txt", m._SimpleFileName("a//\\ab!@#$12%^&@&*()_+.<>,txt"))
        self.assertEquals("long_3e3a06df", m._SimpleFileName("long_filename.txt", maxlen=13))
        self.assertEquals("someverylon_7eea09fa", m._SimpleFileName("someverylongfilename.txt", maxlen=20))
        self.assertEquals("the-unit-test-is-the-proof", m._SimpleFileName("the unit test is the proof", 50))
        self.assertEquals("the-unit-test-is_81bc09a5", m._SimpleFileName("the unit test is the proof", 25))

    def testFillTemplate(self):
        m = MockSiteDefault(self, self.Log(), False, self.s)

        keywords = self.s.AsDict()
        keywords["title"] = "MyTitle"
        keywords["entries"] = ["entry1", "entry2"]
        keywords["last_gen_ts"] = datetime(2007, 11, 12, 14, 15, 16)
        keywords["last_content_ts"] = datetime(2001, 3, 14, 15, 9, 2)
        keywords["rig3_version"] = "3.1.4.15"

        html = m._FillTemplate(SiteDefault._TEMPLATE_HTML_INDEX, **keywords)
        self.assertIsInstance(str, html)
        self.assertTrue(SiteDefault._TEMPLATE_HTML_INDEX in m._fill_template_params)
        self.assertTrue(1, len(m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX]))
        self.assertDictEquals(keywords, m._fill_template_params[SiteDefault._TEMPLATE_HTML_INDEX][0])
        self.assertListEquals([], m.GetWriteFileData(m._LEAFNAME))
        self.assertHtmlEquals(
            r"""<html lang="en-US">
                <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
                <title>Test Album - MyTitle</title>
                </head>
                <body>
                entry1
                entry2
                <p>
                Most recent entry: 2001-03-14 15:09:02 --
                Generated on 2007-11-12 14:15:16 by <a href="http://code.google.com/p/rig3/">Rig3 3.1.4.15</a> 
                </body>
                </html>""",
            html)

        keywords = self.s.AsDict()
        keywords["title"] = "MyTitle"
        keywords["sections"] = { "en": "Main <b>Text Content</b> as HTML",
                                 "images": "<a href='page_url'><img src='image_url'/></a>" }
        html = m._FillTemplate(SiteDefault._TEMPLATE_HTML_ENTRY, **keywords)
        self.assertIsInstance(str, html)
        self.assertTrue(SiteDefault._TEMPLATE_HTML_ENTRY in m._fill_template_params)
        self.assertTrue(1, len(m._fill_template_params[SiteDefault._TEMPLATE_HTML_ENTRY]))
        self.assertDictEquals(keywords, m._fill_template_params[SiteDefault._TEMPLATE_HTML_ENTRY][0])
        self.assertListEquals([], m.GetWriteFileData(m._LEAFNAME))
        self.assertHtmlEquals(
            r"""<div class="entry">
                <h2>MyTitle</h2>
                Main <b>Text Content</b> as HTML
                <br/>
                <a href='page_url'><img src='image_url'/></a>
                <br/>
                </div>
                """,
            html)

    def testDateAndTitleFromTitle(self):
        m = MockSiteDefault(self, self.Log(), False, self.s)

        self.assertEquals((None, "27"),        m._DateAndTitleFromTitle("27"))
        self.assertEquals((None, "2007"),      m._DateAndTitleFromTitle("2007"))
        self.assertEquals((None, "2007-1"),    m._DateAndTitleFromTitle("2007-1"))
        self.assertEquals((None, "2007-10"),   m._DateAndTitleFromTitle("2007-10"))
        self.assertEquals((None, "2007-10-2"), m._DateAndTitleFromTitle("2007-10-2"))
        self.assertEquals((None, "2007102"),   m._DateAndTitleFromTitle("2007102"))
        
        self.assertEquals((datetime(2007, 10, 27), ""),
                          m._DateAndTitleFromTitle("20071027"))
        self.assertEquals((datetime(2007, 10, 27), "rest"),
                          m._DateAndTitleFromTitle("2007-10-27 rest"))
        self.assertEquals((datetime(2007, 10, 27), "rest of the line.."),
                          m._DateAndTitleFromTitle("2007/10/27_rest of the line.."))
        self.assertEquals((datetime(2007, 10, 27), "whitespace"),
                          m._DateAndTitleFromTitle("2007-10/27    whitespace   "))
        self.assertEquals((datetime(2007, 10, 27, 12, 13, 14), ""), m._DateAndTitleFromTitle("20071027121314"))
        self.assertEquals((datetime(2007, 10, 27, 12, 13, 14), ""), m._DateAndTitleFromTitle("2007-10-27-12-13-14"))
        self.assertEquals((datetime(2007, 10, 27, 12, 13, 14), ""), m._DateAndTitleFromTitle("2007-10-27 12-13-14"))
        self.assertEquals((datetime(2007, 10, 27, 12, 13, 14), ""), m._DateAndTitleFromTitle("2007/10/27 12:13:14"))
        self.assertEquals((datetime(2007, 10, 27, 12, 13, 14), ""), m._DateAndTitleFromTitle("2007-10/27,12/13/14"))

    def testDateAndTitleFromTitle_ErrorCases(self):
        m = MockSiteDefault(self, self.Log(), False, self.s)

        # Hour is invalid: 44>23... log warning and ignore hour in this case
        self.assertEquals((datetime(2007, 10, 27), ""),
                          m._DateAndTitleFromTitle("20071027-4400"))

        # Day must be in 1..31
        self.assertRaises(ValueError, m._DateAndTitleFromTitle, "20071034")

        # Month must be in 1..12
        self.assertRaises(ValueError, m._DateAndTitleFromTitle, "20071527")

        # Year must be in range 1..9999
        self.assertRaises(ValueError, m._DateAndTitleFromTitle, "00001027")
        self.assertEquals((datetime(1, 10, 27), ""),
                          m._DateAndTitleFromTitle("00011027"))
        self.assertEquals((datetime(9999, 10, 27), ""),
                          m._DateAndTitleFromTitle("99991027"))

    def testGenerateItems_Izu(self):
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        source_dir = os.path.join(self.getTestDataPath(), "album")
        item = m.GenerateItem(SourceDir(datetime.today(),
                                        RelDir(source_dir, "2007-10-07_Folder 1"),
                                        [ "index.izu" ]))
        self.assertNotEquals(None, item)
        self.assertEquals(datetime(2007, 10, 07), item.date)
        self.assertHtmlMatches(r'<div class="entry">.+</div>', item.content_gen(SiteDefault._TEMPLATE_HTML_ENTRY))
        self.assertListEquals([ "foo", "bar", "other" ], item.categories, sort=True)
    
    def testGenerateItems_Html(self):
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        source_dir = os.path.join(self.getTestDataPath(), "album")
        item = m.GenerateItem(SourceDir(datetime.today(),
                                        RelDir(source_dir, "2006-05_Movies"),
                                        [ "index.html" ]))
        self.assertNotEquals(None, item)
        self.assertEquals(datetime(2006, 5, 28, 17, 18, 5), item.date)
        self.assertHtmlMatches(r'<div class="entry">.+<!-- \[izu:.+\] --> <table.+>.+</table>.+</div>',
                               item.content_gen(SiteDefault._TEMPLATE_HTML_ENTRY))
        self.assertListEquals([ "videos" ], item.categories, sort=True)

    def testImgPattern(self):
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        self.assertEquals(None, m._IMG_PATTERN.match("myimage.jpg"))
        self.assertEquals(None, m._IMG_PATTERN.match("PICT1200.jpg"))
        self.assertEquals(None, m._IMG_PATTERN.match("R12345-Some Name.bmp"))
        self.assertEquals(None, m._IMG_PATTERN.match("R12345-Some Name.gif"))
        self.assertDictEquals({ "index": "1000",
                                "rating": "_",
                                "name": " Old Index ",
                                "ext": ".jpg" }, 
                              m._IMG_PATTERN.match("1000_ Old Index .jpg").groupdict())
        self.assertDictEquals({ "index": "R12345",
                                "rating": "_",
                                "name": "Some Name",
                                "ext": ".jpg" }, 
                              m._IMG_PATTERN.match("R12345_Some Name.jpg").groupdict())
        self.assertDictEquals({ "index": "X12345",
                                "rating": "-",
                                "name": "Some Movie",
                                "ext": ".original.mov" }, 
                              m._IMG_PATTERN.match("X12345-Some Movie.original.mov").groupdict())
        self.assertDictEquals({ "index": "Y31415",
                                "rating": "+",
                                "name": "Web Version",
                                "ext": ".web.mov" }, 
                              m._IMG_PATTERN.match("Y31415+Web Version.web.mov").groupdict())
        self.assertDictEquals({ "index": "Z31415",
                                "rating": ".",
                                "name": "Web Version",
                                "ext": ".web.wmv" }, 
                              m._IMG_PATTERN.match("Z31415.Web Version.web.wmv").groupdict())

    def testGetRigLink(self):
        m = MockSiteDefault(self, self.Log(), False, self.s)

        expected = (
            '<a title="2007-11-08 Album Title" '
            'href="http://example.com/photos/index.php?album=My%20Albums/Year_2007/2007-11-08%20Album%20Title&img=Best%20of%202007.jpg">'
            '<img title="Best of 2007" alt="Best of 2007" src="http://example.com/photos/index.php?th=&album=My%20Albums/Year_2007/2007-11-08%20Album%20Title&img=Best%20of%202007.jpg&sz=400&q=75"/>'
            '</a>'
            )

        self.assertHtmlEquals(
            expected,
            m._GetRigLink(RelDir("base", "My Albums/Year_2007/2007-11-08 Album Title"),
                          "Best of 2007.jpg",
                          400))

        expected = (
            '<a title="2007-11-08 Album Title" '
            'href="http://example.com/photos/index.php?album=My%20Albums/Year_2007/2007-11-08%20Album%20Title&img=Best%20of%202007.jpg">'
            '<img title="Best of 2007" alt="Best of 2007" src="http://example.com/photos/index.php?th=&album=My%20Albums/Year_2007/2007-11-08%20Album%20Title&img=Best%20of%202007.jpg&sz=-1&q=75"/>'
            '</a>'
            )

        self.assertHtmlEquals(
            expected,
            m._GetRigLink(RelDir("base", "My Albums/Year_2007/2007-11-08 Album Title"),
                          "Best of 2007.jpg",
                          -1))

        expected = (
            '<a title="2007-11-08 Album &amp; Title" '
            'href="http://example.com/photos/index.php?album=My%20Albums/Year_2007/2007-11-08%20Album%20%26%20Title">'
            '2007-11-08 Album &amp; Title</a>'
            )

        self.assertHtmlEquals(
            expected,
            m._GetRigLink(RelDir("base", "My Albums/Year_2007/2007-11-08 Album & Title"),
                          None,
                          -1))

    def testGenerateImages(self):
        m = MockSiteDefault(self, self.Log(), False, self.s)

        self.assertEquals(
            None,
            m._GenerateImages(RelDir("base", ""), []))

        self.assertEquals(
            None,
            m._GenerateImages(RelDir("base", ""), [ "index.izu",
                                                    "index.html",
                                                    "image.jpeg" ]))

        self.assertEquals(
            None,
            m._GenerateImages(RelDir("base", ""), [ "J1234_sound.mp3" ]))
        
        self.assertHtmlEquals(
            m._GetRigLink(RelDir("base", ""), None, -1),
            m._GenerateImages(RelDir("base", ""), [ "J1234.image.jpg" ]))

        self.assertHtmlEquals(
            '<table class="image-table"><tr><td>\n' + m._GetRigLink(RelDir("base", ""), "J1234-image.jpg", -1) + '</td></tr></table>',
            m._GenerateImages(RelDir("base", ""), [ "J1234-image.jpg" ]))

    def testGenerateIndexPage(self):
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        
        m._GenerateIndexPage("", "", [], [], [], [])
        params = m._fill_template_params

        for key in [  "rig_img_url",
                      "rig_thumb_url",
                      "source_list",
                      "header_img_height",
                      "tracking_code",
                      "header_img_url", 
                      "rig_album_url",
                      "img_gen_script",
                      "entries",
                      "cat_include",
                      "last_content_ts",
                      "rig_img_size",
                      "month_pages",
                      "rig3_version",
                      "rig_base",
                      "title",
                      "rel_base_url",
                      "base_url",
                      "public_name",
                      "theme",
                      "all_categories",
                      "dest_dir",
                      "cat_exclude",
                      "last_gen_ts" ]:
            self.assertTrue(key in params[SiteDefault._TEMPLATE_HTML_INDEX][0], "Missing [%s] in %s" % (key, params))

    def testAcceptCategories(self):
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        y = SitesSettings(self.Log())

        # default is accept all
        s = SiteSettings()
        y._ProcessCatFilter(s, { "cat_filter": "" })
        self.assertTrue(m._AcceptCategories([], s))
        self.assertTrue(m._AcceptCategories([ "toto" ], s))
        self.assertTrue(m._AcceptCategories([ "foobar" ], s))
        self.assertTrue(m._AcceptCategories([ "foo" ], s))
        self.assertTrue(m._AcceptCategories([ "bar" ], s))
        self.assertTrue(m._AcceptCategories([ "foo", "bar" ], s))

        # exclude no-tags
        s = SiteSettings()
        y._ProcessCatFilter(s, { "cat_filter": "!$" })
        self.assertFalse(m._AcceptCategories([], s))
        self.assertTrue (m._AcceptCategories([ "toto" ], s))
        self.assertTrue (m._AcceptCategories([ "foobar" ], s))
        self.assertTrue (m._AcceptCategories([ "foo" ], s))
        self.assertTrue (m._AcceptCategories([ "bar" ], s))
        self.assertTrue (m._AcceptCategories([ "foo", "bar" ], s))

        # inclusion is an "OR" operation: at least one must match
        s = SiteSettings()
        y._ProcessCatFilter(s, { "cat_filter": "foo bar" })
        self.assertFalse(m._AcceptCategories([], s))
        self.assertFalse(m._AcceptCategories([ "toto" ], s))
        self.assertFalse(m._AcceptCategories([ "foobar" ], s))
        self.assertTrue (m._AcceptCategories([ "foo" ], s))
        self.assertTrue (m._AcceptCategories([ "bar" ], s))
        self.assertTrue (m._AcceptCategories([ "foo", "bar" ], s))
        self.assertTrue (m._AcceptCategories([ "toto", "bar" ], s))
        self.assertTrue (m._AcceptCategories([ "foo", "tata" ], s))

        # accept no-tags
        s = SiteSettings()
        y._ProcessCatFilter(s, { "cat_filter": "foo bar $" })
        self.assertTrue (m._AcceptCategories([], s))
        self.assertFalse(m._AcceptCategories([ "toto" ], s))
        self.assertFalse(m._AcceptCategories([ "foobar" ], s))
        self.assertTrue (m._AcceptCategories([ "foo" ], s))
        self.assertTrue (m._AcceptCategories([ "bar" ], s))
        self.assertTrue (m._AcceptCategories([ "foo", "bar" ], s))

        # exclude all
        s = SiteSettings()
        y._ProcessCatFilter(s, { "cat_filter": "foo bar !*" })
        self.assertFalse(m._AcceptCategories([], s))
        self.assertFalse(m._AcceptCategories([ "toto" ], s))
        self.assertFalse(m._AcceptCategories([ "foobar" ], s))
        self.assertFalse(m._AcceptCategories([ "foo" ], s))
        self.assertFalse(m._AcceptCategories([ "bar" ], s))
        self.assertFalse(m._AcceptCategories([ "foo", "bar" ], s))

        # exclusion takes precedence
        s = SiteSettings()
        y._ProcessCatFilter(s, { "cat_filter": "foo bar !foo" })
        self.assertFalse(m._AcceptCategories([], s))
        self.assertFalse(m._AcceptCategories([ "toto" ], s))
        self.assertFalse(m._AcceptCategories([ "foobar" ], s))
        self.assertFalse(m._AcceptCategories([ "foo" ], s))
        self.assertTrue (m._AcceptCategories([ "bar" ], s))
        self.assertFalse(m._AcceptCategories([ "foo", "bar" ], s))

        # only exclusion
        s = SiteSettings()
        y._ProcessCatFilter(s, { "cat_filter": "!foo !bar" })
        self.assertTrue (m._AcceptCategories([], s))
        self.assertTrue (m._AcceptCategories([ "toto" ], s))
        self.assertTrue (m._AcceptCategories([ "foobar" ], s))
        self.assertFalse(m._AcceptCategories([ "foo" ], s))
        self.assertFalse(m._AcceptCategories([ "toto", "foo" ], s))
        self.assertFalse(m._AcceptCategories([ "bar" ], s))
        self.assertFalse(m._AcceptCategories([ "foo", "bar" ], s))

    def testRigAlbumLink(self):
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        
        settings = SiteSettings()
        self.assertEquals("", m._RigAlbumLink(settings, "my album"))

        settings = SiteSettings(rig_base="http://my.rig/index.php")
        self.assertEquals("http://my.rig/index.php?album=my%20album",
                          m._RigAlbumLink(settings, "my album"))
        
    def testRigImgLink(self):
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()

        settings = SiteSettings()
        self.assertEquals("", m._RigImgLink(settings, "my album", "my image.jpg"))

        settings = SiteSettings(rig_base="http://my.rig/index.php")
        self.assertEquals("http://my.rig/index.php?album=my%20album&img=my%20image.jpg",
                          m._RigImgLink(settings, "my album", "my image.jpg"))

    def testRigThumbLink(self):
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        
        settings = SiteSettings()
        self.assertEquals("", m._RigThumbLink(settings, "my album", "my image.jpg", 640))

        settings = SiteSettings(rig_base="http://my.rig/index.php")
        self.assertEquals("http://my.rig/index.php?th=&album=my%20album&img=my%20image.jpg&sz=640&q=75",
                          m._RigThumbLink(settings, "my album", "my image.jpg", 640))

    def testGeneratePages(self):
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        self.assertListEquals([], m.GetWriteFileData(m._LEAFNAME))

        # printing an empty list of items only generates an index page
        m.GeneratePages(categories=[], items=[])
        self.assertListEquals([ "index.html", "atom.xml" ], m.GetWriteFileData(m._LEAFNAME))
        
        # printing 3 times + 1 the number of items per page generates 4 pages
        items = []
        cats = []
        for x in xrange(0, m._ITEMS_PER_PAGE * 3 + 1):
            # x % 12 => we'll generate 12 month pages
            si = SiteItem(datetime(2000, 1 + (x % 12), 1 + (x % 28), x % 24, x % 60, x % 60),
                          title="blah",
                          permalink="item",
                          content_gen=lambda t, x: "content",
                          categories=cats)
            items.append(si)
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        m.GeneratePages(cats, items)
        self.assertListEquals(
          [ "2000-12.html", "2000-11.html", "2000-10.html", "2000-09.html",
            "2000-08.html", "2000-07.html", "2000-06.html", "2000-05.html",
            "2000-04.html", "2000-03.html", "2000-02.html", "2000-01.html",
            "index.html", "atom.xml" ],
          m.GetWriteFileData(m._LEAFNAME))

        # print items with only one category, this does not generate
        # category indexes.
        items = []
        cats = [ "first" ]
        for x in xrange(0, m._ITEMS_PER_PAGE + 1):
            # x % 7 => we'll generate 7 month pages
            si = SiteItem(datetime(2000, 1 + (x % 7), 1 + (x % 28), x % 24, x % 60, x % 60),
                          title="blah",
                          permalink="item",
                          content_gen=lambda t, x: "content",
                          categories=cats)
            items.append(si)
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        m.GeneratePages(cats, items)
        self.assertListEquals(
          [ "2000-07.html", "2000-06.html", "2000-05.html",
            "2000-04.html", "2000-03.html", "2000-02.html", "2000-01.html",
            "index.html", "atom.xml" ],
          m.GetWriteFileData(m._LEAFNAME))

        # with two categories, we get category pages too
        items = []
        cats = [ "first", "second" ]
        for x in xrange(0, m._ITEMS_PER_PAGE + 1):
            # x % 5 => we'll generate 5 month pages
            si = SiteItem(datetime(2000, 1 + (x % 5), 1 + (x % 28), x % 24, x % 60, x % 60),
                          title="blah",
                          permalink="item",
                          content_gen=lambda t, x: "content",
                          categories=cats)
            items.append(si)
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        m.GeneratePages(cats, items)
        self.assertListEquals(
          [ "2000-05.html", "2000-04.html", "2000-03.html", "2000-02.html", "2000-01.html",
            "index.html", "atom.xml",
            os.path.join("cat", "first", "2000-05.html"),
            os.path.join("cat", "first", "2000-04.html"),
            os.path.join("cat", "first", "2000-03.html"),
            os.path.join("cat", "first", "2000-02.html"),
            os.path.join("cat", "first", "2000-01.html"),
            os.path.join("cat", "first", "index.html"),
            os.path.join("cat", "first", "atom.xml"),
            os.path.join("cat", "second", "2000-05.html"),
            os.path.join("cat", "second", "2000-04.html"),
            os.path.join("cat", "second", "2000-03.html"),
            os.path.join("cat", "second", "2000-02.html"),
            os.path.join("cat", "second", "2000-01.html"),
            os.path.join("cat", "second", "index.html"),
            os.path.join("cat", "second", "atom.xml") ],
          m.GetWriteFileData(m._LEAFNAME))

        # more categories: 4 main pages but each category has only 2 pages
        items = []
        cats = [ "first", "second", "three" ]
        for x in xrange(0, m._ITEMS_PER_PAGE * 3 + 3):
            # x % 3 => we'll generate 3 month pages and we have 3 categories
            # so each category ends up in the same month.
            si = SiteItem(datetime(2000, 1 + (x % 3), 1 + (x % 28), x % 24, x % 60, x % 60),
                          title="blah",
                          permalink="item",
                          content_gen=lambda t, x: "content",
                          categories=[ cats[x % 3] ])
            items.append(si)
        m = MockSiteDefault(self, self.Log(), False, self.s).MakeDestDirs()
        m.GeneratePages(cats, items)
        self.assertListEquals(
          [ "2000-03.html", "2000-02.html", "2000-01.html",
            "index.html", "atom.xml", 
            os.path.join("cat", "first", "2000-01.html"),
            os.path.join("cat", "first", "index.html"),
            os.path.join("cat", "first", "atom.xml"),
            os.path.join("cat", "second", "2000-02.html"),
            os.path.join("cat", "second", "index.html"),
            os.path.join("cat", "second", "atom.xml"),
            os.path.join("cat", "three", "2000-03.html"),
            os.path.join("cat", "three", "index.html"),
            os.path.join("cat", "three", "atom.xml") ],
          m.GetWriteFileData(m._LEAFNAME))


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
