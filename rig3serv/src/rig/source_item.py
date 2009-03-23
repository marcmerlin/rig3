#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: One-line module description

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide at gmail com"

from datetime import datetime
from rig.parser.dir_parser import RelDir, RelFile

#------------------------
def _rig_hash(obj):
    h = 0
    if isinstance(obj, list):
        for v in obj:
            h = h ^ _rig_hash(v)
    elif isinstance(obj, dict):
        for k, v in obj.iteritems():
            h = h ^ _rig_hash(k) ^ _rig_hash(v)
    else:
        h = hash(obj)
    return h


#------------------------
class SourceSettings(object):
    """
    Settings attached to a specific source.
    """
    def __init__(self, rig_base=None):
        self.rig_base = rig_base

    def AsDict(self):
        """
        Returns a copy of the settings' dictionary.
        It's safe for caller to modify this dictionary.
        """
        return dict(self.__dict__)

    def KnownKeys(self):
        """
        List the variables declared by this SourceSettings
        """
        keys = self.__dict__.keys()
        keys.sort()
        return keys

    def __eq__(self, rhs):
        return (isinstance(rhs, SourceSettings) and self.__dict__ == rhs.__dict__)

    def __hash__(self):
        return _rig_hash(self.__dict__)

    def __repr__(self):
        try:
            return "[%s: %s]" % (self.__class__.__name__, self.__dict__)
        except:
            return super(RelPath, self).__repr__()


#------------------------
class SourceItem(object):
    """
    Abstract base class to represents an item:
    - list of categories (list of string)
    - date (datetime)
    - source_settings (not optional)

    The class is conceptually abstract, meaning it has no data.
    In real usage, clients will process derived classes (e.g. SourceDir)
    which have members with actual data to process.
    """
    def __init__(self, date, source_settings, categories=None):
        self.date = date
        self.source_settings = source_settings
        self.categories = categories or []

    def __eq__(self, rhs):
        return (isinstance(rhs, SourceItem) and
                self.date == rhs.date and
                self.source_settings == rhs.source_settings and
                self.categories == rhs.categories)

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def __hash__(self):
        h = (hash(self.date) ^
             hash(self.source_settings) ^
             _rig_hash(self.categories))
        return h


#------------------------
class SourceDir(SourceItem):
    """
    Represents a directory item from a SourceDirReader.

    Such a directory generally contains an index.izu or index.html
    and a bunch of image files.

    Parameters:
    - date (datetime): Date of the directory (i.e. most recent item)
    - rel_dir (RelDir): absolute+relative source directory
    - all_files (list [string]): All interesting files in this directory
    """
    def __init__(self, date, rel_dir, all_files, source_settings):
        super(SourceDir, self).__init__(date, source_settings)
        self.rel_dir = rel_dir
        self.all_files = all_files

    def __eq__(self, rhs):
        if not super(SourceDir, self).__eq__(rhs):
            return False
        return (isinstance(rhs, SourceDir) and
                self.rel_dir == rhs.rel_dir and
                self.all_files == rhs.all_files)

    def __hash__(self):
        h = super(SourceDir, self).__hash__() ^ hash(self.rel_dir.realpath())
        for f in self.all_files:
            h = h ^ hash(f)
        return h

    def __repr__(self):
        return "<%s (%s) %s, %s, %s, %s>" % (self.__class__.__name__,
                                             self.date,
                                             self.rel_dir,
                                             self.all_files,
                                             self.categories,
                                             self.source_settings)

#------------------------
class SourceFile(SourceItem):
    """
    Represents a file item from a SourceFileReader.

    Paremeters:
    - date (datetime): Date of the file
    - rel_file (RelFile): absolute+relative source file
    - source_settings (not optional)
    """
    def __init__(self, date, rel_file, source_settings):
        super(SourceFile, self).__init__(date, source_settings)
        self.rel_file = rel_file

    def __eq__(self, rhs):
        if not super(SourceFile, self).__eq__(rhs):
            return False
        return (isinstance(rhs, SourceFile) and
                self.rel_file == rhs.rel_file)

    def __hash__(self):
        h = super(SourceFile, self).__hash__() ^ hash(self.rel_file.realpath())
        return h

    def __repr__(self):
        return "<%s (%s) %s, %s, %s>" % (self.__class__.__name__,
                                         self.date,
                                         self.rel_file,
                                         self.categories,
                                         self.source_settings)


# TODO:  SourceBlog
#    - content: the data of the file
#    - rel_filename: filename of the generated file relative to the site's
#                    dest_dir.



#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
