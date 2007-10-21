#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Template generator

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os
import sys

#------------------------
_WS = " \t\f"
_EOL = "\r\n"

#------------------------
class Buffer(object):
    """
    A buffer wraps a data string with a "current position" offset.
    All operations advance the offset.
    """
    def __init__(self, filename, data, offset):
        self.filename = filename
        self.data = data
        self.offset = offset
        self.lineno = 1

    def EndReached(self):
        """
        Returns true if the end of the buffer has been reached
        """
        return self.offset >= len(self.data)

    #def SetOffset(self, offset):
    #    self.offset = offset

    def StartsWith(self, word, whitespace=False, consume=False):
        """
        Returns true if the given word is present at the current position
        in the buffer.
        If whitespace is true, some whitespace must be present after the word
        or the end of the buffer must have been reached.
        If consume is True, the content is 'consumed' (i.e. offset is moved to end)
        if found. If whitespace is requested, it also consumes the whitespace.
        
        Returns false if the end of the buffer has been reached or if the
        given word is empty.
        """
        if not word or self.EndReached():
            return False
        end = self.offset + len(word)
        if self.data[self.offset:end] == word:
            found = True
            if whitespace and end < len(self.data):
                found = self.data[end] in _WS
                if consume:
                    consume = False
                    while found and self.data[end] in _WS:
                        end += 1
                        self.offset = end
            if consume:
                self.offset = end
            return found
        return False

    def NextWord(self):
        """
        Returns None or tuple (string: word, int: initial position)
        Side effect: advances current offset.
        """
        data = self.data
        initial = offset = self.offset
        if self.EndReached():
            return None
        if data[offset:offset + 2] == "[[":
            return ("[[", offset + 2)
        if data[offset:offset + 2] == "]]":
            return ("]]", offset + 2)
        s = ""
        while True:
            if data[offset:offset + 2] in ["[[", "]]"]:
                break
            c = data[offset]
            if c in " \t\f":
                if not s:
                    offset += 1
                    continue
                else:
                    break
            if c in "\r\n":
                self.lineno += 1
            s += c
            offset += 1
        self.offset = offset
        return (s, initial)
        

#------------------------
class Node(object): pass

class NodeList(Node):
    def __init__(self, list=[]):
        self.list = list

    def Append(self, node):
        self.list.append(node)

class NodeLiteral(Node):
    def __init__(self, literal):
        self.literal = literal

class NodeTag(Node):
    def __init__(self, tag, parameters=[], content=None):
        self.tag = tag
        self.parameters = parameters
        self.content = content

class NodeVariable(Node):
    def __init__(self, names=[], filters=[]):
        self.names = names
        self.filters = filters

#------------------------
class Template(object):
    """
    Parses a template, either from a file or from a string:
    - if file is present, it must be a filename or a file object to be read from.
    - otherwise, source must be defined and it must be a string with the content
      of the template to parse.
    If there's a parsing error, a SyntaxError exception is thrown. 
    If neither file nor source is defined, TypeError is thrown.
    """
    def __init__(self, log, file=None, source=None):
        _file = file
        self._log = log
        if _file is not None:
            if isinstance(_file, str):
                return self._ParseFile(filename=_file)
            elif _file.read:  # does _file.read() exists?
                def _file_name(f):
                    "Returns the filename for a real file() object"
                    try:
                        return f.name
                    except AttributeError:
                        return "file"
                return self._Parse(_file_name(_file), _file.read())
        elif source is not None:
            return self._Parse("source", source)
        raise TypeError("Template: missing file or source parameters")

    def _ParseFile(self, filename):
        """
        Helper to parse a file given by its filename.
        """
        f = None
        try:
            f = file(filename)
            self._Parse(filename, f.read())
        finally:
            if f: f.close()

    def _Parse(self, filename, source):
        """
        Parses a source string for the given filename.
        """
        buffer = Buffer(os.path.basename(filename), source, 0)
        nodes = NodeList()
        #while not buffer.EndReached():
        #    n = self._GetNextNode(buffer)
        #    if n:
        #        nodes.Append(n)
        self._nodes = nodes

    def _GetNextNode(self, buffer):
        """
        Returns the next node in the buffer.
        """
        if buffer.StartsWith("[[", consume=True):
            # get tag
            pass
        else:
            literal = buffer.SkipTo("[[")
            return NodeLiteral(literal)
        

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
