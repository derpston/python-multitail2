import time
import glob
import os
import random

__version__ = "1.4.0"

class TailedFile:
   def __init__(self, path, skip_to_end = True, offset = None):
      self._path = path
      self._buf = ""
      self._offset = None
      self._open(path, skip_to_end, offset)
      self._bufoffset = 0
      # Read in blocks of 32kb and limit the buffer to 2x this.
      self._maxreadsize = 4096 * 8

   def _open(self, path, skip_to_end = True, offset = None):
      """Open `path`, optionally seeking to the end if `skip_to_end` is True."""
      fh = os.fdopen(os.open(path, os.O_RDONLY | os.O_NONBLOCK))

      # If the file is being opened for the first time, jump to the end.
      # Otherwise, it is being reopened after a rotation, and we want
      # content from the beginning.
      if offset is None:
         if skip_to_end:
            fh.seek(0, 2)

            self._offset = fh.tell()
         else:
            self._offset = 0
      else:
         fh.seek(offset)
         self._offset = fh.tell()
      
      self._fh = fh
      self._lastsize = fh.tell()
      self._inode = os.stat(self._path).st_ino

   def _read(self, limit = None):
      """Checks the file for new data and refills the buffer if it finds any."""
      # 64k ought to be enough for anybody
      limit = limit or 65535
      while True:
         data = os.read(self._fh.fileno(), limit)
         if data == '':
            break
         self._buf += data


   def hasBeenRotated(self):
      """Returns a boolean indicating whether the file has been removed and recreated during the time it has been open."""
      try:
         # If the inodes don't match, it means the file has been replaced.
         # The inode number cannot be recycled as long as we hold the
         # filehandle open, so this test can be trusted.
         return os.stat(self._path).st_ino != self._inode
      except OSError:
         # If the file doesn't exist, let's call it "rotated".
         return True

   def reopen(self):
      """Reopens the file. Usually used after it has been rotated."""
      # Read any remaining content in the file and store it in a buffer.
      self._read()
      
      # Reopen the file.
      try:
         self._open(self._path, skip_to_end = False)
         return True
      except OSError:
         # If opening fails, it was probably deleted.
         return False

   def readlines(self):
      """A generator producing lines from the file."""

      while True:
         # Clean the buffer sometimes.
         if self._bufoffset > (self._maxreadsize / 2):
            self._buf = self._buf[self._bufoffset:]
            self._bufoffset = 0

         # Fill up the buffer if necessary.
         if len(self._buf) < self._maxreadsize:
            self._read(self._maxreadsize)

         # Look for the next line.
         try:
            next_newline = self._buf.index("\n", self._bufoffset)
            line = self._buf[self._bufoffset:next_newline]
            self._bufoffset = next_newline + 1
            
            # Save the current file offset for yielding and advance the file offset.
            offset = self._offset
            self._offset += len(line) + 1
            yield line, offset

         except ValueError:
            # Reached the end of the buffer without finding any newlines.
            raise StopIteration

class MultiTail:
   """Provides an iterator for getting new lines from one or more files, with regard for adding new files automatically as they are created, not tracking files once they are deleted, and reopening rotated files."""

   def __init__(self, globspec, interval = 1.0, skip_to_end = True, offsets = None):
      """`globspec` is a path pattern like '/var/log/*.log' suitable for passing to the glob module, and `interval` is a float specifying how many seconds to sleep between checks for new files and new content. If `skip_to_end` is False (default True) all existing lines will be reported as new content immediately."""
      self._globspec = globspec
      self._interval = interval
      self._last_scan = 0
      self._tailedfiles = {}
      if offsets is None:
         self._offsets = {}
      else:
         self._offsets = offsets
    
      self._rescan(skip_to_end = skip_to_end)

   def _rescan(self, skip_to_end = True):
      """Check for new files, deleted files, and rotated files."""
      # Get listing of matching files.
      paths = glob.glob(self._globspec)

      # Remove files that don't appear in the new list.
      for path in self._tailedfiles.keys():
         if path not in paths:
            del self._tailedfiles[path]

      # Add any files we don't have open yet.
      for path in paths:
         try:
            # If the file has been rotated, reopen it.
            if self._tailedfiles[path].hasBeenRotated():
               # If it can't be reopened, close it.
               if not self._tailedfiles[path].reopen():
                  del self._tailedfiles[path]
         except KeyError:
            # Open a file that we haven't seen yet.
            self._tailedfiles[path] = TailedFile(path, skip_to_end = skip_to_end, offset = self._offsets.get(path, None))

   def poll(self, force_rescan = False):
      """A generator producing (path, line) tuples with lines seen since the last time poll() was called. Will not block. Checks for new/deleted/rotated files every `interval` seconds, but will check every time if `force_rescan` is True. (default False)"""
      # Check for new, deleted, and rotated files.
      if force_rescan or time.time() > self._last_scan + self._interval:
         self._rescan(skip_to_end = False)
         self._last_scan = time.time()

      filereaders = {}
      for path, tailedfile in self._tailedfiles.iteritems():
         filereaders[path] = tailedfile.readlines()

      # One line is read from each file in turn, in an attempt to read
      # from all files evenly. They'll be in an undefined order because
      # of using a dict for filereaders, but that's not a problem
      # because some entropy here is desirable for evenness.
      while len(filereaders) > 0:
         for path in filereaders.keys():
            lines = filereaders[path]
            try:
               line, offset = lines.next()
            except StopIteration:
               # Reached end the of this file.
               del filereaders[path]
               break
            
            yield (path, offset), line

   def __iter__(self):
      while True:
         for event in self.poll():
            yield event

         # TODO Replace this with FAM/inotify for watching filesystem events.
         time.sleep(self._interval)
 
   def offsets(self):
      """A generator producing a (path, offset) tuple for all tailed files."""
      for path, tailedfile in self._tailedfiles.iteritems():
         yield path, tailedfile._offset

