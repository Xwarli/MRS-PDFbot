
# MRS-PDFbot

(Very ugly) script to scrape websites for PDFs (with wget) and upload to archive.org

Using wget, this script can start with either a single website or a url_list (as defined in the config files) to run an endless search for PDFs.

Wget is limited per starting line via a tranfer quota, and once finished it then creates a spreadsheet for use with the IA bulk uploader.

Once uploaded, it then cleans up by moving PDFs to a seperate local folder, and deletes any empty directories. It then works with the next URL in the provided list.

Finally, using the wget log MRS-PDFbot finds a list of previously visited URLs, and writes a random number to a new URL_list file.
The program then loops back to the beginning, and starts working through the new url list.

Prerequesites:
-- Python 3.x
-- Internet Archive CLI (https://github.com/jjjake/internetarchive)
-- wget (https://www.gnu.org/software/wget/)


Code is open source and free to use (although contributions or credits would be appritiated!)
Shoutout to the Archive Team at https://wiki.archiveteam.org/index.php/Main_Page
