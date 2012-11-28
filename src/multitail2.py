import resource
import time
import glob
import os

__version__ = "0.1.1"

class TailedFile:
   def __init__(self, path, pagesize = resource.getpagesize(), skip_to_end = True):
      self._path = path
      self._open(path, skip_to_end)
      self._buf = ""
      self._pagesize = pagesize

   def _open(self, path, skip_to_end = True):
      """Open `path`, optionally seeking to the end if `skip_to_end` is True."""
      fh = os.fdopen(os.open(path, os.O_RDONLY | os.O_NONBLOCK))

      # If the file is being opened for the first time, jump to the end.
      # Otherwise, it is being reopened after a rotation, and we want
      # content from the beginning.
      if skip_to_end:
         fh.seek(0, 2)

      self._fh = fh
      self._lastsize = fh.tell()
      self._inode = os.stat(self._path).st_ino

   def _read(self):
      """Checks the file for new data and refills the buffer if it finds any."""
      # XXX Reading only resource.getpagesize() bytes here limits the overall
      # read speed of any one file to that number of bytes per _read()/readlines()
      # call, which is done once per file per MultiTail interval. This might be as
      # low as 4k/sec by default.
      self._buf += self._fh.read(self._pagesize)

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
      """A generator producing any newline-delimited strings written to the file since the last time readlines() was called."""
      self._read()

      while "\n" in self._buf:
         line, self._buf = self._buf.split("\n", 1)
         yield line

class MultiTail:
   """Provides an iterator for getting new lines from one or more files, with regard for adding new files automatically as they are created, not tracking files once they are deleted, and reopening rotated files."""

   def __init__(self, globspec, interval = 1.0, skip_to_end = True):
      """`globspec` is a path pattern like '/var/log/*.log' suitable for passing to the glob module, and `interval` is a float specifying how many seconds to sleep between checks for new files and new content. If `skip_to_end` is False (default True) all existing lines will be reported as new content immediately."""
      self._globspec = globspec
      self._interval = interval
      self._last_scan = 0
      self._tailedfiles = {}
    
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
            self._tailedfiles[path] = TailedFile(path, skip_to_end = skip_to_end)

   def poll(self, force_rescan = False):
      """A generator producing (path, line) tuples with lines seen since the last time poll() was called. Will not block. Checks for new/deleted/rotated files every `interval` seconds, but will check every time if `force_rescan` is True. (default False)"""
      # Check for new, deleted, and rotated files.
      if force_rescan or time.time() > self._last_scan + self._interval:
         self._rescan(skip_to_end = False)
         self._last_scan = time.time()

      # Read new lines from all files and yield them.
      for path, tailedfile in self._tailedfiles.iteritems():
         for line in tailedfile.readlines():
            yield path, line

   def __iter__(self):
      while True:
         for event in self.poll():
            yield event

         time.sleep(self._interval)
   
