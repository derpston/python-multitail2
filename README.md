python-multitail2
================

Python module to follow new lines from multiple files at once, taking account of new files, deleted files, and rotated files.

Suitable for following sets of logs where you don't necessarily know how many files there are, what their names are, and don't want to have to keep track of changes yourself.

Doesn't (yet) support inotify for detecting file change events because of portability concerns and the lack of an inotify module in the Python standard library.

Another one?
------------
Yeah, another one. Other multitail implementations I found didn't support automatically following new files.

Features
--------
* Accepts globbing syntax, like /var/log/*.log
* Opens new files
* Closes deleted files
* Reopens rotated files

Example
-------
Emits (path, line) tuples representing the path to the file that each line comes from.

```python
>>> import multitail2
>>> mt = multitail2.MultiTail("/home/user/test/*")
>>> for line in mt:
...  print line
... 
('/home/user/test/foo', 'bar')
('/home/user/test/foo', 'bar')
```

TODO
----
* Use inotify, where available. Should not be a hard dependency.

Bugs
----
* Should probably be able to read files faster than resource.getpagesize() bytes per interval. With the defaults, this is 4k per second per open file.
* Does not handle truncated files - new content will be ignored until the file size exceeds what it was previously.

Contributing
------------
Contributions welcome!
