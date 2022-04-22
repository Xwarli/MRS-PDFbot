# MRS-PDFbot

(Very ugly) script to scrape websites for PDFs (with wget) and upload to archive.org. Whilst designed with PDFs in mind, it can easily be adapted in the config file to hunt for any file type.

Written by Marley Sexton – a very amateur programmer (so forgive obvious errors or quirks!)


--- OVERVIEW ---
Using wget, this script can start with either a single website or a url_list (as defined in the config files) to run an endless search for PDFs.

Wget is limited per starting line via a transfer quota, and once finished it then creates a spreadsheet for use with the IA bulk uploader.

Once uploaded, it then cleans up by moving PDFs to a separate local folder and deletes any empty directories. It then works with the next URL in the provided list.

Finally, using the wget log MRS-PDFbot finds a list of previously visited URLs, and writes a random number to a new URL_list file.
The program then loops back to the beginning and starts working through the new url list.


--- PREREQUISITES --
-- Python 3.x
-- Internet Archive CLI (https://github.com/jjjake/internetarchive)
-- wget (https://www.gnu.org/software/wget/)
-- PDFtk (https://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/ -- use this later version not easily found on their webpage: https://gist.github.com/seignovert/45b5dbcb14335f1b94d221aa9b98cbab )


--- LICENSE --
Code is open source and free to use without restrictions (although contributions or credits would be appreciated!)

Shoutout to the Archive Team at https://wiki.archiveteam.org/index.php/Main_Page
