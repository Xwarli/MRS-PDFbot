import os
import shutil
import re
import random

## wget https://gnuwget.gitlab.io/wget2/wget2-latest.tar.gz
##	tar xf wget2-latest.tar.gz
##	cd wget2-*
##	./configure
##	make
##	make check
##	sudo make install

# -----------------------------------------------------------------------------
# PROGRAM PAUSE
# -----------------------------------------------------------------------------
def pause_input():
    input("Pause [Press any key to continue] ")
    return
# -----------------------------------------------------------------------------
# INITIAL LOADING FEEDBACK
# Used to provide basic feedback after loading settings from a config file
# -----------------------------------------------------------------------------
def loading_feedback(quotastring, contributor, clean_up, confirm_uploads, filetype, filetype_upper, mediatype, write_record, upload_record_txtfile, uploaded_pdfs_folder, wget2, user_agent, reject_urls, reject_list, url_list, defaulted=False):
    print("------------------------------------------------------------------------------\n"*3)

    if defaulted is True:
        print("!! Using default values (config file not found or has errors!) \n")
        pause_input()

    print("Traffic Quota: " + quotastring)
    print("Contributor(s): " + contributor)
    print("Filetype to find: " + filetype + filetype_upper)
    print("Archive.org mediatype: " + mediatype )
    print("Wget user-agent: " + user_agent)
    print("Uploaded PDF Folder: " + uploaded_pdfs_folder)

    if clean_up == "Y":
        print("Automatically cleaning up")
    elif clean_up == "N":
        print("Not cleaning up")
    else:
        pass

    if confirm_uploads == "Y":
        print("Confirming uploads")
    elif confirm_uploads == "N":
        print("Not confirming uploads")
    else:
        pass

    if write_record is True:
        print("Writing local upload record to: " + upload_record_txtfile)
    else:
        print("Not writing local upload record")

    if wget2 is True:
        print("Using wget2 protocol")
    else:
        print("UNot using wget2 protocol (using wget)")

    if reject_urls is True:
        print("\nRejecting URLs based on list: " + reject_list)
        

    print("------------------------------------------------------------------------------\n"*3)

    return      
# -----------------------------------------------------------------------------
# MULTIPLE STRING STRIPPER
#   Strips a couple of common characters from an input string (shortcut)
# -----------------------------------------------------------------------------
def multi_str_strip(string):
    return string.strip(' ,"').strip("'").strip("\n")

# -----------------------------------------------------------------------------
# DEFAULT VALUES WHEN NO CONFIG
#   Assignes default config values
# -----------------------------------------------------------------------------
def no_config_defaults():
    single_url = "https://www.twitter.co.uk/"
    url_file = "url_file.txt"
    contributor = '"Marley R. Sexton, MRS.PDFbot"'
    confirm_uploads = "y"
    clean_up = "n"
    uploaded_pdfs_folder = "uploaded_PDFs"
    filetype, filetype_upper = "pdf", "PDF"
    quotastring = "2m"
    mediatype = "texts"
    wget2 = False
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
    write_record = False
    upload_record_txtfile = "upload_record.txt"
    defaulted = True
    reject_urls = False 
    reject_list = "reject-list.txt"
    url_list = []
    return single_url, url_file, quotastring, contributor, confirm_uploads, clean_up, uploaded_pdfs_folder, filetype, filetype_upper, mediatype, wget2, user_agent, write_record, upload_record_txtfile, reject_urls, reject_list, url_list

# -----------------------------------------------------------------------------
# REMOVE ("DROP") EMPTY DIRECTORIES
#   Remove any empty folders that have been created to keep things tidy
#   ---->   https://stackoverflow.com/a/23488980
#   ---->   https://stackoverflow.com/a/61925392
# -----------------------------------------------------------------------------
def drop_empty_folders(directory):  
    # first, work topdown to delete needless files (generally tmp and html)
    for dirpath, dirnames, filenames in os.walk(directory):
        for file in filenames:
            if file.endswith(".html") is True or file.endswith(".tmp") is True:
                try:
                    os.remove(os.path.join(dirpath, file))  # tries to remove
                except:                                     # just ignore if it kicks an error
                    pass
    # Then work backwards to delete empty folders
    for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
      if not dirnames and not filenames:    # if not dirnames or files
            try:
                os.rmdir(dirpath)           # try to remove said path, but just ignore
            except:                         # any errors
                pass

# -----------------------------------------------------------------------------
# IDENTIFIER FORMATTING
#   Each archive upload requires an alphanumeric identifier of a reasonable
#   length. This section takes the standard identifier generated when creating
#   the bulk upload csv and formats it by removing illegal characters, keeping
#   it below 256 characters, and adding extra to very short versions.
# -----------------------------------------------------------------------------
def identifier_formatting(identifier): # Remove non-alphanumeric characters
        if identifier.isidentifier() is True:       # Basic check
            pass
        else:
            up_count, new_identifier, illegal_chars = 0, "", ",.<>?!/\\\"'|;:[]{}=+)(*&^%$£@`~§§#€ "
            max_count = len(identifier)     # ensures loop doesn't kick up an error by looking for a char that doesn't exsit
            if max_count > 255:             
                max_count = 255
            while up_count < max_count:     # while the counter is below the unformatted identifer length
                if identifier[up_count] in illegal_chars:
                    pass                    # ignore character
                else:
                    new_identifier += identifier[up_count]  # if legal character, add it to a new identifier string
                up_count += 1
            identifier = new_identifier     #   once the loop completes, switches the strings back round
        # Check that it is of a sufficient len (here: 10, randomly chosen!)
        #   if not, append botname at the start to lenghthen it.
        if len(identifier) <= 10:           # if it is too short (10 is an arbitary number)
            identifier = "MRS_PDFbot-" + identifier     # add arbitary prefix
        else:
            pass            
        return identifier

# -----------------------------------------------------------------------------
# FIX PDF
#   Uses PDFtk as suggested by ia to fix potential errors. Limited sucess, but
#   very little is lost by trying. Some compression helps long-term.
# -----------------------------------------------------------------------------
def fix_pdf(ia_file):
    new_ia_file = ia_file.rstrip(".pdf") + "-tmp.pdf"       # creates a new temp tile (PDFtk input != output)
    pdftk_command = 'pdftk "' + ia_file + '" output "' + new_ia_file + '" flatten drop_xfa compress dont_ask'
    try:        # tries. If exception occurs it still returns the original, unchanged file
        print(pdftk_command)    # print's for user feedback
        os.system(pdftk_command)            # Runs the PDFtk command and outputs to file-tmp.pdf (input != output)
        os.remove(ia_file)                  # Deletes the old (input) file
        os.rename(new_ia_file, ia_file)     # Renames the new (output) file to the original name (swaps them)
    except:
        pass       # ignore errors
    finally:
        return ia_file
  
# -----------------------------------------------------------------------------
# RETRIEVE FROM THE UPLOAD RECORD
# -----------------------------------------------------------------------------
def retrieve_from_upload_record(upload_record_txtfile, uploaded_files_list=[], write_record=True):
    count = 0
    uploaded_files_list=[] 
    if write_record is True:
        if os.path.exists(upload_record_txtfile) is True:
            local_upload_record = open(upload_record_txtfile, "r")
            for line in local_upload_record:
                if line.strip("\n") not in uploaded_files_list:
                    uploaded_files_list.append(line.strip("\n"))
                elif line.strip("\n") in uploaded_files_list: 
                    count += 1
                    pass
                else:
                    pass
            local_upload_record.close()
        elif os.path.exists(upload_record_txtfile) is False:
            pass
        else:
            pass
    else:
        pass
        
    return uploaded_files_list

# -----------------------------------------------------------------------------
#  WRITE TO UPLOAD RECORD
#   Opens and writes the uploaded ia_file to the txt record of uploads
# -----------------------------------------------------------------------------
def write_to_upload_record(ia_file, upload_record_txtfile):
    openfile = open(upload_record_txtfile, "a")     # append file only
    try:
        openfile.write(ia_file.split("/")[-1] + "\n")   # split long path and use filename only
    except:
        pass    # ignore errors (no real loss in the odd file not being recorded)
    finally:
        openfile.close()    
        return

# -----------------------------------------------------------------------------
# CREATE LOG FILE
#   Creates a sequentially numbered log file
# -----------------------------------------------------------------------------
def log_file_create():
    log_n, log_break = 0, False
    while log_break is False:               # while break flag is false
        if log_n == 0:                      # ignore zero value (assume no suffix)
            if os.path.exists("wget-log"):  # check for default, unnumbered file
                pass                        
            else:
                return "wget-log"            # if default doesn't exist, break to let script know
        else:                               # otherwise check for the next numbered file
            if os.path.exists("wget-log." + str(log_n)):
                pass
            else:                           # if wget-log.n doesn't exist, break and use current log_n
                return "wget-log." + str(log_n)
        log_n += 1                          # tick up until loop breaks
    return

# ------------------------------------------------------------------------------
#  CALLS THE INTERNET ARCHIVE SCRIPT   
#   Once the csv is created, we ask for confirmation of the uploads to archive.org
#   (qeury disabled by default in config). Then we call the basic ia command for
#   bulk uploads. 
# ------------------------------------------------------------------------------
def call_ia_cli(confirm_uploads="n"):
    if confirm_uploads == "n":          # if confirmation isn't required
        ia_upload_command = 'ia upload --spreadsheet="ia_upload.csv" --sleep=30 --retries 10' # calls the ia upload file, referencing the csv
        print('\n\n[--  -------  --] ' + ia_upload_command)     # printed for user feedback
        os.system(ia_upload_command)                            # call the command
    elif confirm_uploads != "n":    # if confirmation is required, asks for it, checks the first letter to be Y for yes
        if input("[--   Input   --] Upload to IA? [Y/N]: ").lower()[0] == "y":
            print('\n\n' + ia_upload_command)                   # printed for user feedback
            os.system(ia_upload_command)                        # call the command
        else:
            print("[!?  Warning  ?!] File upload to ia skipped")    # skips if input isn't correct, print for feedback
    else:
        print("[!!  Warning  !!] call_ia_cli Error. File upload to ia skipped") # catches any other errors
    return

# -----------------------------------------------------------------------------
#  WGET COMMAND
#   Using the inputs calls either wget or wget2 depending on config
# -----------------------------------------------------------------------------
def call_wget(wget2, url, filetype, user_agent, quotastring, log_file=""):
    if wget2 is False:
        # https://unix.stackexchange.com/a/128476
        wget_command = "wget " + url + " -r -l --level=inf -p -A " + filetype + " -H -nc -nv --user-agent=\"" + user_agent + "\" -e --robots=off --restrict-file-names=ascii --quota=" + quotastring + " --wait=1 --random-wait --tries=2 --timeout=10 2>&1 | tee -a wget-log"
        print("\n[--  -------  --] " + wget_command + "\n")     # user feedback
        os.system(wget_command)
    elif wget2 is True:
        wget2_command = "wget2 " + url + " -A " + filetype + " --quota=" + quotastring + " --user-agent=\"" + user_agent + "\" --max-threads=20 -r -l 0 --span-hosts=on --restrict-file-names=ascii --robots=off --wait=0.5 --random-wait --tries=2 --timeout=10 --retry-connrefused -o " + log_file
        print("\n[--  -------  --] " + wget2_command + "\n")    # user feedback
        os.system(wget2_command)
    else:
        pass
    return

# -----------------------------------------------------------------------------
# FIND FILES (RELATIVE TO SCRIPT)
#   Finds a list of ALL files and returns files for further processing
# -----------------------------------------------------------------------------
def find_files(files=[], ignore_folder="uploaded_PDFs", mypath=os.getcwd()):
    for (dirpath, dirnames, filenames_list) in os.walk(mypath):     
        if ignore_folder in dirpath:        # ignore the folder where PDFs are moved to
            pass
        else:                               # otherwise:
            for individual_file in filenames_list:  # for every file found:
                files.append(os.path.join(dirpath, individual_file))    # add the full path to the files list
    return files

# -----------------------------------------------------------------------------
#  CREATE IA CSV
#   One of many ways to use the ia command is by using a csv/spreadsheet
#   to use for bulk uploads. This section creates said file, and forms the
#   basis for many of the other modules
# -----------------------------------------------------------------------------
def create_ia_csv(files, write_record, filetype, filetype_upper, uploaded_files_list, ia_csv="ia_upload.csv"):
    if os.path.exists(ia_csv):      # checks if a ia file already exists
        os.remove(ia_csv)           #   if so.. deletes it to prevent conflict
    output_csv = open(ia_csv, "x", encoding="utf8")     # create new csv; encode to utf8 to help stop identifier errors
    
    # Add the basic headers required by ia
    archive_setup = output_csv.write("identifier,title,contributor,mediatype,file")

    # Transfer "files" list to the csv with some mild formatting
    lines = 0   # counter
    for item in files:
        # Only accept the wanted filetype files, in case any others have crept in!
        if item.endswith(filetype):
            exists = True   # assume the file does exist (although we will check!)
            ia_file = item.replace(mypath +"/", "") # ia_file is the FULL path - relative to script dir - to file needed for the uploader
            if os.path.exists(item) is False:       # if the item DOES NOT EXIST
                exists = False                      #   mark exists flag as false
            
            if ia_file == ".pdf":                   # sometimes a file is included just called ".pdf" - this weeds them out
                exists = False                      #   mark exists flag as false
        
            if os.path.exists(item) is True:        # if the file exists (i.e. passes basic checks as above)
                # reads the uploaded files record and adds missing records to the list
                uploaded_files_list = retrieve_from_upload_record(upload_record_txtfile, uploaded_files_list)

                if ia_file not in uploaded_files_list:     # i.e. if it hasn;t already been uploaded
                    title = item.split("/")[-1].replace("_", " ").replace(".pdf", "").replace("-", " ") # removes underscores, hyphens and extention for easy readability
                    identifier = identifier_formatting(item.split("/")[-1].replace(".pdf", "")) # generated from the file name, per requirements
                    ia_file = fix_pdf(ia_file)  # "fixes" the pdf with brief compression and syntax corrections
                    uploaded_files_list.append(ia_file)     # add the file to the uploaded file list
                    output_csv.write("\n" + identifier + "," + '"' + title + '"' + "," + contributor + "," + mediatype +  "," + '"' + ia_file + '"') # writes all the above to the csv (if the file existsn and hasn't already been uploaded)

                    if write_record is True:                                    # if config asks to create a upload record
                        write_to_upload_record(ia_file, upload_record_txtfile)  #   add to the record
                    elif write_record is False:
                        pass
                    else:
                        print("[!!   Error   !!] Write Record Error.")          # Feedback for unkown errors
                        break                                                   # Exit script due to said unkown behaviour
                elif item in uploaded_files:                                    # if it has already been uploaded then....
                    print("[!?  Warning  ?!] File already uploaded, skipping: " + ia_file)
                else:                                                           # if something strange has happened....
                    print("[!!   Error   !!] File already uploaded? Skipping: " + ia_file)
            else:   # passes the file if the exists flag is False
                pass
    output_csv.close()
    return

# ------------------------------------------------------------------------------
# POST-RUN FILE CLEANUP
#   Cleans up the files by deleting empty directories and moving PDFs to
#   a seperate "uploaded" folder in the source dir for offline backups.
#   If ia_upload has thrown an error and stoped the uploading process, and this
#   module is on by default, then it will still run and move PDFs to a seperate
#   folder even if they've not been uploaded.
# ------------------------------------------------------------------------------
def cleanup_def(total_moved, total_delete, clean_up="n", upload_dir="uploaded_PDFs", ia_file="ia_upload.csv", mypath=os.getcwd()):
    all_files = find_files()        # finds all the files in the same directory as this script
    pdf_files = []
    for item in all_files:           
        if item.endswith(".pdf") is True:
            pdf_files.append(item)
        else:
            pass
    skipped_header = False
    if clean_up == "y":             # if the config states that the script should clean-up post-upload...
        print("\n[--  -------  --] Moving PDFs to seperate file for personal archiving.")   # user feedback
        # Sees if a file already exists, otherwise tries to create on in the script directory
        if os.path.isdir("uploaded_PDFs") is False:        # checks to see if a directory exists into which PDFs can be moved to
            try:
                os.mkdir("uploaded_PDFs")                  # if it doesn't exist, create
                print("[--  -------  --] Created directory at /uploaded_PDFs")  # feedback
            except:
                pass
        moved_count, delete_count = 0, 0    # temporary counters
        for line in pdf_files:              # for every PDF file
            if skipped_header is True:
                try:
                    # Tries to move a file to the new directory. If it can't (probably because
                    #       it already exists, then simply deletes it when it throws an error.
                    shutil.move(line, "./uploaded_PDFs/")
                    moved_count += 1
                except FileNotFoundError:
                    try:
                        print("[!!   Error   !!] FileNotFoundError in Cleanup Process: " + line)
                        os.remove(line)
                        delete_count += 1
                    except:
                        pass
                except:     # Quick fix for a broad range of possible errors..
                    try:
                        os.remove(line)
                        delete_count += 1
                    except:
                        pass
                else:
                    pass
            else:
                # Once the first csv line has processed, set skipped_header to True to
                #   permit the rest to process as normal. Otherwise an error is thrown
                #   when the file column returns "file" and not a file path!
                skipped_header = True       

        # Deletes empty folders
        drop_empty_folders(mypath)

        # User feedback
        total_moved += moved_count
        total_delete += delete_count
        print("\n[--  -------  --] File move complete. Files moved: " + str(moved_count) + "    [Running Total: " + str(total_moved) + "]")
        print("[--  -------  --] File deletion complete. Files deleted: " + str(delete_count) + "    [Running Total: " + str(total_delete) + "]")
        print("[--  -------  --] Empty files deleted")     
    elif clean_up == "n":
        print("[!?  Warning  ?!] No post-archiving clean up performed.\n")
    else:
        print("\n[!!   Error   !!] Cleaning up error. !!")

    return total_moved, total_delete

#------------------------------------------------------------------------------
# URL FILTER (FOR CREATING NEW URL LIST)
#   Simple sub-routine to reduce the number of URLs by (attempting) to remove
#   obvious duplicates
#------------------------------------------------------------------------------
def url_filter(url_string, reject_urls=False, reject_list="reject-list.txt", domain_list=[], reject_domains=[], mypath=os.getcwd()):
    if reject_urls is True:
        load_file = open(os.path.join(mypath, reject_list), "r")
        for line in load_file:
            if line.startswith("#") is False:
                reject_domains.append(line.strip("\n"))
        load_file.close()
    else:
        pass

    for url in url_string:                      # For every URL pass to the routine
        url = url.lstrip("http://").lstrip("https://").lstrip("www.") # strip prefixes
        domain = url.split("/")[0]              # split at / and read the domain name
        if domain in domain_list or domain in reject_domains:               # if it is already in our list, reject
            pass
        elif domain not in domain_list and domain not in reject_domains:         # if it is new to us, add to our list
            domain_list.append(domain)
        else:
            pass
    return domain_list                          # return the list for further processing

#------------------------------------------------------------------------------
# LOG-FILE CLEANUP
#   Works through a count and removes all the wget log files
#------------------------------------------------------------------------------
def log_cleanup(last_log, n=0):
    while n < last_log:
        if n > 0:
            try:
                os.remove("wget-log." + str(n))
            except:
                pass
        else:
            try:
                os.remove("wget-log")
            except:
                pass
        n += 1
    return

#------------------------------------------------------------------------------
# NEW URL LIST CREATOR
#   Poor mans way to create a new URL list. Used the wget-log's as a base, to 
#   continue where the program may have left off.
#------------------------------------------------------------------------------
def new_url_list(mypath, reject_urls, reject_list):
    log_count, url_total = 0, 0
    more_logs = True
    while more_logs is True:
        log_file_name = "wget-log"  # Normal log file name. Might be different if wget above edited
        if log_count > 0:           # log files other than the first are appended with a numeral
            log_file_name += "." + str(log_count)   # wget is set to appends additional logfiles as ".n"
        else:
            pass

        if os.path.exists(mypath + "/" + log_file_name) is True:        # checks that log file exists in current directory
            print("[!?  Warning  ?!] Reading " + log_file_name )        # user feedback
            log_file = open(log_file_name).read()                       # opens and reads logfile to log_file str       
            # regex to convert the entire log file to just a list of URLS
            # as found from: https://stackoverflow.com/a/50790119
            urls_from_log_file = re.findall(r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b",log_file)

            
            new_url_list = open("url_file.txt", "a")
            
            url_list = url_filter(urls_from_log_file, reject_urls, reject_list)
            for url in url_list:
                random_num = random.randint(0, 9999)
                if random_num > 9750 and url_total < 256:   # accept 2.5% of urls, and a max of 256
                    url_total += 1                         
                    new_url_list.write(url + "\n")          # write url too the new url list file, with a newline delimiter
                    print("[--  -------  --] URL injected: " + url) # user feedback

                else:
                    pass
            new_url_list.close()
        else:                       # Once the final numbered log has been used, set flag to False to prevent
            more_logs = False       # it kicking up an error about a log not existing
            log_cleanup(log_count)  # clean up by deleting all the currnet logs
        log_count += 1
    return

# ------------------------------------------------------------------------------
# URL CHECKING
#   Runs some basic checks on input URLs (from file?) and get user input if none found.
#   get_url is flagged as false, and once a URL of suitable quality is entered
#   it is flagged as true and allows the program to continue.
# ------------------------------------------------------------------------------
def check_url_list_major(url_list):
    url_list, valid_check = check_url_list_minor(url_list)  # creates a list of URLS
    get_url = False
    while get_url is False:
        if len(url_list) == 0 or valid_check is False:
            url_list = []                                                   # Overwrites
            url_list.append(input("No valid URL provided. Enter URL: "))    # Catches input and adds to list
            url_list, valid_check = check_url_list_minor(url_list)          # Recheckes list
            if len(url_list) != 0 and valid_check is True:                  # Double check (valid_check is really only needed)
                get_url is True                                             # If acceptable, switches flag and allows escape
            else:                                       
                print("[!!   Error   !!] Error with entry. Please try again.")  # Else feedsback and sends the loop around again.
        else:
            break                                                           # Allows escape if something strange happens
    return url_list

# ------------------------------------------------------------------------------
# CHECK URL LIST FOR VALIDITY
#   Some basic checks to see if the URL in the list are (possibly) valid. 
#   wget rejects invalid URLs without crashing the program, so not strictly 
#   neccesary but does save some time.
# ------------------------------------------------------------------------------
def check_url_list(reject_urls, reject_list, url_list=[], valid=True, feedback=True):
    legal_url_chars = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~:/?#[]@!$&'()*+,;=")
    reserved_url_chars = list(":/#?&@%+~")  # not permitted in general
    checked_list = []                       # list of checked URLs to reference
    if bool(url_list) is False:             # i.e. if it isn't a list at all
        valid, url_list = False, []
    else:
        for entry in url_list:              # For every URL to check...
            valid = True                    # general flag
            for character in list(entry):   # for every character list entry
                if character not in legal_url_chars:                # if char is NOT in the legal char list...
                    if character in reserved_url_chars:             # if char IS a reserved char, warn but accept
                        print("[!?  Warning  ?!] Possible reserved characters in input URL: " + entry)
                    elif character not in reserved_url_chars:       # if char IS NOT a reserved, reject char
                        print("[!! Rejecting !!] Illegal characters in input URL: " + entry)
                        valid = False   # set flag
                    else:
                        print("[!?  Warning  ?!] check_url_list error (unable to validate): " + entry)
                elif character in legal_url_chars:                  # if char IS legal
                    pass                                            # accept character
                else:
                     print("[!?  Warning  ?!] check_url_list error (unable to validate): " + entry) # unkown error, but accept char
            if valid is False:              # Then... if valid flag is False (invalid)
                pass                        #   pass on said URL (i.e. don't add it to the list)
            else:                           # if valid flag is NOT False (i.e. True/Valid)
                checked_list.append(entry)  #   add the URL to the list of chcked URLs
                if feedback is True:        # if feedback is required, then print
                    print("[--  -------  --] URL accepted: " + entry)    
    checked_list = url_filter(checked_list, reject_urls, reject_list)
    return checked_list, len(url_list) + 1

# ------------------------------------------------------------------------------
# READ CONFIG FILE
#   Simply reads the configuration file and assigns values
#   Loads no_config_defaults first, and then overwrights with values that are
#   present
# ------------------------------------------------------------------------------
def read_config(file="MRS-PDFbot.config", url_file="",mypath=os.getcwd()):
    single_url, url_file, quotastring, contributor, confirm_uploads, clean_up, uploaded_pdfs_folder, filetype, filetype_upper, mediatype, wget2, user_agent, write_record, upload_record_txtfile, reject_urls, reject_list, url_list = no_config_defaults()
    file = open(file)
    for line in file:
        if line.startswith("#"):    # Ignore commentted lines
            pass
        else:        #   (in config file:)   key_name    =   key_value 
            key_name, key_value, key_value_raw = line.split("=")[0].lower(), line.split("=")[-1].lower(), line.split("=")[-1]         
            if key_name.startswith("startpage"):
                single_url = multi_str_strip(key_value)
                if single_url != "":    # if a single_url is specified, adds it to the url_list (regardless of url_list file)
                    url_list.append(single_url)
            elif key_name.startswith("url_list"):
                url_file = multi_str_strip(key_value)
                try:        
                    url_file = open(os.path.join(mypath, url_file), "r") # try to read file
                    for line in url_file:                               # extract every url (one per line)
                        url_list.append(multi_str_strip(line))          # add to the to-do list
                    url_file.close()
                except:
                    print("[!!   Error   !!] URL File invalid. Defaulting")     
                    url_file = "url_file.txt"                           # if none exists, searches for default
                    try:
                        url_file = open(os.path.join(mypath, url_file), "r")
                        for line in url_file:
                            url_list.append(multi_str_strip(line))
                        url_file.close()
                    except:
                        pass
            elif key_name.startswith("quotastring"):
                #quotastring = check_quota_format(multi_str_strip(key_value).lower())
                quotastring = multi_str_strip(key_value).lower()                 
            elif key_name.startswith("contributor"):
                contributor = multi_str_strip(key_value).title().replace("Mrs.Pdfbot", "MRS.PDFbot")
                if contributor.startswith('"') is False:                    # Ensures whole string is within quotes since
                    contributor = '"' + contributor                         #   comma seperated values cause issues later and
                if contributor.endswith('"') is False:                      #   when trying to upload - since archive thinks
                    contributor = contributor + '"'                         #   the commas are seperating imputs
            elif key_name.startswith("confirm_uploads"):
                confirm_uploads = (multi_str_strip(key_value))[0]           # First char only (i.e. y in Yes, n in No)
                if confirm_uploads not in "yn":                            # If not y or n, just default to y 
                    print("[!!   Error   !!] Confirming uploads line error. Defaulting to True (Y)")
                    confirm_uploads = "y"  
            elif key_name.startswith("clean_up"):       
                clean_up = (multi_str_strip(key_value))[0]                  # First char only (i.e. y in Yes, n in No)
                if clean_up not in "yn":                                    # If not y or n, just default to n
                    print("[!!   Error   !!] Confirming clean upline error. Defaulting to True (Y)")
                    clean_up = "n"
            elif key_name.startswith("uploaded_pdfs_folder"):
                uploaded_pdfs_folder = '"' + multi_str_strip(key_value) + '"'
            elif key_name.startswith("filetype "):
                filetype  = ("." + multi_str_strip(key_value).strip(".")).lower()
                filetype_upper = " " + filetype.upper()     # file extension in both lower and upper case covers most examples
            elif key_name.startswith("mediatype"):
                mediatype = multi_str_strip(key_value)
            elif key_name.startswith("wget2"):
                if multi_str_strip(key_value.lower()).startswith("true") is True:
                    wget2 = True
                else:
                    wget2 = False
            elif key_name.startswith("user-agent"):
                user_agent = multi_str_strip(key_value_raw).lstrip('"').rstrip('"')
            elif key_name.startswith("local upload record"):
                if multi_str_strip(key_value.lower()).startswith("true") is True:
                    write_record = True
                else:
                    write_record = False
            elif key_name.startswith("upload record file)"):
                if write_record is False:
                    pass
                else:
                    if multi_str_strip(key_value.lower()).endswith(".txt") is True:
                        upload_record_txtfile = multi_str_strip(key_value)
                    else:
                        print("Defined upload record file is not of required type (.txt). Defaulting to upload_record.txt")
                        upload_record_txtfile = "upload_record.txt"
            elif key_name.startswith("use reject list"):
                if multi_str_strip(key_value.lower()).startswith("true") is True:
                    reject_urls = True
                else:
                    reject_urls = False
            elif key_name.startswith("reject file"):
                reject_list = multi_str_strip(key_value)
    file.close()
    return single_url, url_file, quotastring, contributor, confirm_uploads, clean_up, uploaded_pdfs_folder, filetype, filetype_upper, mediatype, wget2, user_agent, write_record, upload_record_txtfile, reject_urls, reject_list, url_list

# ------------------------------------------------------------------------------
# MAIN SCRIPT
# -----------------------------------------------------------------------------
def main():  
        total_moved = 0
        total_delete = 0
        processed = 1
        mypath=os.getcwd()
        if os.path.exists(os.path.join(mypath, "MRS-PDFbot.config")) is True:
            defaulted = False
            print("Reading MRS-PDFbot.config")
            single_url, url_file, quotastring, contributor, confirm_uploads, clean_up, uploaded_pdfs_folder, filetype, filetype_upper, mediatype, wget2, user_agent, write_record, upload_record_txtfile, reject_urls, reject_list, url_list = read_config()
        else:
            defaulted = True
            single_url, url_file, quotastring, contributor, confirm_uploads, clean_up, uploaded_pdfs_folder, filetype, filetype_upper, mediatype, wget2, user_agent, write_record, upload_record_txtfile, reject_urls, reject_list, url_list = no_config_defaults()
        # User feedback, seperated into subroutine for readability      
        loading_feedback(quotastring, contributor, clean_up, confirm_uploads, filetype, filetype_upper, mediatype, write_record, upload_record_txtfile, uploaded_pdfs_folder, wget2, user_agent, reject_urls, reject_list, url_list, defaulted)
        
        while True: 
            url_list, total_urls = check_url_list(reject_urls, reject_list, url_list)
            total_urls = len(url_list) + 1
            print("[--  -------  --] Total URLs to process: " + str(total_urls))
            processed = 1
            for url in url_list:
                log_file = log_file_create()                                                # create log file
                call_wget(wget2, url, filetype, user_agent, quotastring, log_file)          # Call wget/2 web search
                files = find_files()                                                        # find all the files downloaded
                create_ia_csv(files, filetype, filetype_upper, write_record, upload_record_txtfile)                   # create spreadsheet for ia
                call_ia_cli(confirm_uploads)                                                # call ia cli to upload
                print("\n[--  -------  --] URLs processed: " + str(processed) + " | To-do: " + str(total_urls - processed) )
                
                processed += 1
                total_moved, total_delete = cleanup_def(total_moved, total_delete, clean_up)
            new_url_list(mypath, reject_urls, reject_list)

main()


        
