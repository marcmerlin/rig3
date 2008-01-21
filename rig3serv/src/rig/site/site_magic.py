#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Site generator for "magic" theme 

Site generators are instantiated by rig.site.__init__.py.CreateSite()

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from rig.site.site_default import SiteDefault

#------------------------
class SiteMagic(SiteDefault):
    """
    Describes and how to generate the content of a site using the "magic" theme.
    
    Right now the "magic" theme is identicaly to the "default" theme
    so the implementation is empty. This is expected to change later.
    """

    def _TemplatePath(self, path, **keywords):
        """
        Returns the relative path to "path" under the default theme's template
        directory.        
        """
        return super(SiteMagic, self)._TemplatePath(path, theme="default")

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End: