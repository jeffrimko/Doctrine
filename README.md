Doctrine
========

Utility for quickly viewing rendered [AsciiDoc](http://asciidoc.org/).

To view a document, simply open the text file in the application. The text will be rendered to a local `__doctrine__.html` file; please note that this file will deleted when the application is closed or a different document is opened. If the text file is modified, it can be reloaded to display the updated document. All local relative links should function properly.

Additionally, a document can be archived in a zip file. Asset files can be included in the archive and relative links should function. If the zip file contains an `__archive_info__.txt` (check out [Archiver](https://github.com/jeffrimko/Archiver)) it will rendered, otherwise the first found `.txt` file will be rendered.

Big thanks to [Stuart Rackham](http://www.methods.co.nz/stuart.html) for developing the excellent AsciiDoc format.

Additional details on this project are available at [jeffcomput.es/projects/doctrine](http://jeffcomput.es/projects/doctrine).
