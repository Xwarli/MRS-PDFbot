import os
import shutil
import re
import random


# Used to provide basic feedback after loading settings from a config file
def loading_feedback(quotastring, contributor, clean_up, confirm_uploads, filetype, filetype_upper, mediatype, uploaded_pdfs_folder):

        three_line_break()
        
        if defaulted is True:
            print("!! Using default values (config file not found or has errors!) \n")
        
        print("Traffic Quota: " + quotastring)
        print("Contributor(s): " + contributor)
        print("Filetype to find: " + filetype + filetype_upper)
        print("Archive.org mediatype: " + mediatype )
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

        three_line_break()
                

# https://stackoverflow.com/a/23488980
def remove_empty_dirs(path):
    for root, dirnames, filenames in os.walk(path, topdown=False):
        for dirname in dirnames:
            remove_empty_dir(os.path.realpath(os.path.join(root, dirname)))

##def check_quota_format(quota, default=False):
##    # Basic way to check the quota format is correct.
##    #   Just checks it starts with a number, and ends with k, b or m.
##    #   and also whether other characters are in - a basic check only
##    numstring = "1234567890"
##    quota = multi_str_strip(quota)
##    if quota[0] in numstring:
##        default = True
##    elif quota[-1] in numstring:
##        default = True
##    else:
##        size = "bkm"
##        # should_notbe = "acdefghijlnopqrstuvwxyz,./;'\[]<>?:\\!@£$%^&*()_+-=~`±§\"||{}"
##        if quota[-1] not in size:
##            default = True
##
##    if default is True:
##        print("Quota value ERROR: defaulting to 10m")
##        quota = "1m"
##    elif default is False:
##        pass
##    else:
##        pass
##    
##    return quota
        
def three_line_break():
    print("------------------------------------------------------------------------------\n"*3)
        

def multi_str_strip(string):
    return string.strip(' ,"').strip("'").strip("\n")

def no_config_defaults():
    print("[!?  Warning  ?!] No configuration file found. Defaulting...")
    confirm_uploads = "y"
    clean_up = "n"
    contributor = '"Marley R. Sexton, MRS.PDFbot"'
    quotastring = "2m"
    startpage = "https://www.rspb.org.uk/"
    uploaded_pdfs_folder = "uploaded_PDFs"
    defaulted = True
    return confirm_uploads, clean_up, contributor, quotastring, startpage, uploaded_pdfs_folder, defaulted

def drop_empty_folders(directory):
    #https://stackoverflow.com/a/61925392
    """Verify that every empty folder removed in local storage."""
    for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
        if not dirnames and not filenames:
            try:
                os.rmdir(dirpath)
            except:
                pass

def identifier_formatting(identifier):
        # Remove non-alphanumeric characters
        if identifier.isidentifier() is True:
            pass
        else:
            up_count, new_identifier, illegal_chars = 0, "", ",.<>?!/\\\"'|;:[]{}=+)(*&^%$£@`~§§#€ "
            max_count = len(identifier)
            if max_count > 255:
                max_count = 255
            while up_count < max_count:
                if identifier[up_count] in illegal_chars:
                    pass
                else:
                    new_identifier += identifier[up_count]
                up_count += 1
            identifier = new_identifier
        # Check that it is of a sufficient len (here: 10, randomly chosen!)
        #   if not, append botname at the start to lenghthen it.
        if len(identifier) <= 10:
            identifier = "MRS_PDFbot-" + identifier
        else:
            pass

        return identifier


# Used PDFtk to try and preemtivly fix PDFs with syntax errors as sujested by IA
def fix_pdf(ia_file):
    new_ia_file = ia_file.rstrip(".pdf") + "-tmp.pdf"
    pdftk_command = 'pdftk "' + ia_file + '" output "' + new_ia_file + '" flatten drop_xfa compress verbose dont_ask'
    try:
        print(pdftk_command)
        os.system(pdftk_command)            # Runs the PDFtk command and outputs to file-tmp.pdf (input != output)
        os.remove(ia_file)                  # Deletes the old (input) file
        os.rename(new_ia_file, ia_file)     # Renames the new (output) file to the original name
    except:
        pass
    finally:
        return ia_file
    
# Some basic checks to see if the URL in the list are (possibly) valid. wget rejects invalid URLs without crashing
#   the program, so not strictly neccesary but does save some time.
def check_url_list(url_list, valid=True, feedback=True):

    legal_url_chars = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~:/?#[]@!$&'()*+,;=")
    reserved_url_chars = list(":/#?&@%+~")
    checked_list = []
    
    if bool(url_list) is False:             # i.e. if it isn't a list at all
        valid = False
        url_list = []
    else:
        for entry in url_list:
            valid = True
            for character in list(entry):
                if character not in legal_url_chars:
                    if character in reserved_url_chars:
                        print("[!?  Warning  ?!] Possible reservec characters in input URL: " + entry)
                    elif character not in reserved_url_chars:
                        print("[!! Rejecting !!] Illegal characters in input URL: " + entry)
                        valid = False
                    else:
                        print("[!?  Warning  ?!] check_url_list error (unable to validate): " + entry)
                elif character in legal_url_chars:
                    pass
                else:
                     print("[!?  Warning  ?!] check_url_list error (unable to validate): " + entry)
            if valid is False:
                pass
            else:
                checked_list.append(entry)
                if feedback is True:
                    print("[--  -------  --] URL accepted: " + entry)



    return url_list, valid
                    
        



# Initialize vars
total_moved, total_delete = 0, 0

# Infinite loop!          
while True:
# ------------------------------------------------------------------------------
# Find the relative path (directory this script is is)
# ------------------------------------------------------------------------------
    mypath = os.getcwd()

# ------------------------------------------------------------------------------
# Parses the config file (if it does not exist, sets defults inline)
# ------------------------------------------------------------------------------
    
    url_list = []
    defaulted = False
    if os.path.exists("MRS-PDFbot.config") is True:
        config_file = open("MRS-PDFbot.config")
        for line in config_file:
            if line.startswith("#"):
                pass
            else:
                
                config_line = line.split("=")
                key_name, key_value = config_line[0].lower(), config_line[-1].lower()
                #   (in config file:)   key_name    =   key_value 

                if key_name.startswith("startpage"):
                    single_url = multi_str_strip(key_value)
                    if single_url != "":
                        url_list.append(single_url)

                elif key_name.startswith("url_list"):
                    url_file = multi_str_strip(key_value)
                    try:
                        url_file = open(url_file, "r")
                        for line in url_file:
                            url_list.append(multi_str_strip(line))
                        url_file.close()
                    except:
                        print("[!!   Error   !!] URL File invalid. Defaulting")
                    
                elif key_name.startswith("quotastring"):
                    #quotastring = check_quota_format(multi_str_strip(key_value).lower())
                    quotastring = multi_str_strip(key_value).lower()                 
                   
                elif key_name.startswith("contributor"):
                    contributor = multi_str_strip(key_value)
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

        config_file.close()

    # If there is no config file, or default flag is set, sets the defults as in the subroutine.
    elif os.path.exists("MRS-PDFbot.config") is False or  defaulted is True:
        confirm_uploads, clean_up, contributor, quotastring, startpage, uploaded_pdfs_folder, defaulted = no_config_defaults()

    # User feedback, seperated into subroutine for readability      
    loading_feedback(quotastring, contributor, clean_up, confirm_uploads, filetype, filetype_upper, mediatype, uploaded_pdfs_folder)

    # ------------------------------------------------------------------------------
    # URL checking.
    #   Runs some basic checks on input URLs and get user input if none found.
    #   get_url is flagged as false, and once a URL of suitable quality is entered
    #   it is flagged as true and allows the program to continue.
    # ------------------------------------------------------------------------------


    url_list, valid_check = check_url_list(url_list)
    get_url = False
    while get_url is False:
        if len(url_list) == 0 or valid_check is False:
            url_list = []                                                   # Overwrites
            url_list.append(input("No valid URL provided. Enter URL: "))    # Catches input and adds to list
            url_list, valid_check = check_url_list(url_list)                # Recheckes list
            if len(url_list) != 0 and valid_check is True:                  # Double check (valid_check is really only needed)
                get_url is True                                             # If acceptable, switches flag and allows escape
            else:                                       
                print("[!!   Error   !!] Error with entry. Please try again.")                # Else feedsback and sends the loop around again.
        else:
            break                                                           # Allows escape if something strange happens
        
    # ------------------------------------------------------------------------------
    # Create wget string from variables, before printing (in case of errors) and
    #   then run via os
    # ------------------------------------------------------------------------------
    for url in url_list:
        
        # https://unix.stackexchange.com/a/128476
        wget_command = "wget " + url + " -r -l --level=inf -p -A " + filetype + " -H -nc -nv --user-agent=\"\" -e --robots=off --restrict-file-names=ascii --quota=" + quotastring + " --wait=1 --random-wait --tries=2 --timeout=10 2>&1 | tee -a wget-log"
        print("\n[--  -------  --] " + wget_command + "\n")
        os.system(wget_command)



# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# CREATING FILE FOR BULK UPLOAD TO ARCHIVE.ORG VIA ia upload COMMAND
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

        # Create empty csv file to create metadata and file list. Deletes any existing
        #   file to overwrite
        if os.path.exists("ia_upload.csv"):
          os.remove("ia_upload.csv")
        output_csv = open("ia_upload.csv", "x")


        # Add the basic headers required by ia
        archive_setup = output_csv.write("identifier,title,contributor,mediatype,file")



        # Find each pdf file, and create a list of file paths with os.walk
        files, ignore_list = [], ["uploaded_PDFs"]
        for (dirpath, dirnames, filenames_list) in os.walk(mypath):
            
            if "uploaded_PDFs" in dirpath:
                pass
            else:
                for individual_file in filenames_list:
                    files.append(os.path.join(dirpath, individual_file))
            # break

        # Transfer "files" list to the csv with some mild formatting
        lines = 0 
        for item in files:
            # Only accept the wated filetype files, in case any others have crept in!
            if item.endswith(filetype):
                exists = True
                ia_file = item.replace(mypath +"/", "")
                # ia_file is the path to file needed for the uploader
                # Title simply removes underscores and extention for easy readability
                # Identifier is generated from the file name, just removing the extension and disallowed characters per def
                if os.path.exists(item) is False:
                    exists = False
                
                if ia_file == ".pdf":
                    exists = False
            
                if os.path.exists(item) is True:
                    title = item.split("/")[-1].replace("_", " ").replace(".pdf", "").replace("-", " ") 
                    
                    identifier = identifier_formatting(item.split("/")[-1].replace(".pdf", ""))

                    ia_file = fix_pdf(ia_file)
                    # writes all the above to the csv (if the file exists)
                    output_csv.write("\n")
                    output_csv.write(identifier + "," + title + "," + contributor + "," + mediatype + "," + ia_file)
                else:
                    pass

        output_csv.close()


        # ------------------------------------------------------------------------------
        # Once the csv is created, we ask for confirmation of the uploads to archive.org
        #   (qeury disabled by default in config). Then we call the basic ia command for
        #   bulk uploads. Inter-upload sleep set from default (30sc) to 0sc.
        # ------------------------------------------------------------------------------

        if confirm_uploads == "n":
            # calls the ia upload file, referencing the csv
            ia_upload_command = '[--  -------  --] ia upload --spreadsheet="ia_upload.csv" --sleep=1 --retries 10'
            print('\n\n' + ia_upload_command) # printed for user feedback
            os.system(ia_upload_command)
        elif confirm_uploads != "n":
            if input("[--   Input   --] Upload to IA? [Y/N]: ").lower()[0] == "y":
                print('\n\n' + ia_upload_command) # printed for user feedback
                os.system(ia_upload_command)
            else:
                print("[!?  Warning  ?!] File upload to ia skipped")
        else:
            print("[!?  Warning  ?!] File upload to ia skipped")


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# POST-RUN FILE CLEANUP
# ------------------------------------------------------------------------------
#   Cleans up the files by deleting empty directories and moving PDFs to
#   a seperate "uploaded" folder in the source dir for offline backups.
#   If ia_upload has thrown an error and stoped the uploading process, and this
#   module is on by default, then it will still run and move PDFs to a seperate
#   folder even if they've not been uploaded.
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

        skipped_header = False
        if clean_up == "y":
            print("\n[--  -------  --] Moving PDFs to seperate file for personal archiving.")

            # Sees if a file already exists, otherwise tries to create on in the script directory
            if os.path.isdir("uploaded_PDFs") is False:
                try:
                    os.mkdir("uploaded_PDFs")
                except:
                    pass
                finally:
                    print("[--  -------  --] Created directory at /uploaded_PDFs")
            
            ia_file = open("ia_upload.csv", "r")
            ia_file_list = []
            moved_count, delete_count = 0, 0
            
            for line in ia_file:
                if skipped_header is True:
                    ia_filename = multi_str_strip(line.split(",")[-1])
                    try:
                        # Tries to move a file to the new directory. If it can't (probably because
                        #       it already exists, then simply deletes it when it throws an error.
                        shutil.move(ia_filename, "./uploaded_PDFs/")
                        moved_count += 1
                    except FileNotFoundError:
                        try:
                            print("[!!   Error   !!] FileNotFoundError in Cleanup Process: " + ia_filename)
                            os.remove(ia_filename)
                            delete_count += 1
                        except:
                            pass
                    except:     # Quick fix for a broad range of possible errors..
                        try:
                            os.remove(ia_filename)
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
            print("[--  -------  --] File move complete. Files moved: " + str(moved_count) + "    [Running Total: " + str(total_moved) + "]")
            print("[--  -------  --] File deletion complete. Files deleted: " + str(delete_count) + "    [Running Total: " + str(total_delete) + "]")
            print("[--  -------  --] Empty files deleted")
                  
        elif clean_up == "n":
            print("[!?  Warning  ?!] No post-archiving clean up performed.\n")
        else:
            print("\n[!!   Error   !!] Cleaning up error. !!")

        ia_file.close()                 # Finishes cleaning up by closing the csv file and then deleting it
        try:
            os.rmdir(ia_upload.csv)         # (same command occurs earlier in an 'if', but it here makes certain it's gone)
        except NameError:                   # essentially "it already exists (as predicted)
            pass
        except:                             # any other error that might occur unexpectedly
            print("[!?  Warning  ?!] Possible error deleting ia_upload.csv).")
            pass
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# CREATES A NEW URL LIST FROM PREVIOUSLY CHECKED URLS LISTED IN THE LOGFILES
# ------------------------------------------------------------------------------
#   Essentially a cheap/poor-mans way to start again without physically
#   looking for new pages.
#
#   The obvious downside is that when wget starts from the new links it might
#   (or WILL) duplicate work and rexplore URLs already visited. Perhaps far
#   more likey when deep searches have already occured and it starts again from
#   an earlier link.
#
#   TO DO: Exclude early links!
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
   
   
    log_count, url_total = 0, 0
    more_logs, first_overwrite = True, True
    
    while more_logs is True:
        log_file_name = "wget-log"  # Normal log file name. Might be different if wget above edited
        if log_count > 0:
            log_file_name += "." + str(log_count)   # wget appends additional logfiles as ".n"
        else:
            pass

        if os.path.exists(mypath + "/" + log_file_name) is True:    # checks file exists in current directory
            print("[!?  Warning  ?!] Reading " + log_file_name )                  # user feedback
            log_file = open(log_file_name).read()                   # opens and reads logfile to log_file str       
           # log_file = log_file.read()
            # https://stackoverflow.com/a/50790119
            urls_from_log_file = re.findall(r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b",log_file)


            # Only overwrite an old file (the first one it calls.)
            #   If it has already been overwritte, then append
            if first_overwrite is True:
                new_url_list = open("url_file.txt", "w")
                first_overwrite = False
            else:
                new_url_list = open("url_file.txt", "a")
                

            # Injects URLs to search based on a random selection from the
            #   log files (to try and incrasse variety)
            #   URL total limits the total number of URLs per file to
            #   whatever the user chooses. URLs are checked to ensure they are
            #   not index pages or temp files, as the regex above likes to
            #   spit these out as geniune URLS. Once excluded, add to the total
            #   count and then write the file on a new line. Print for user.
            for url in urls_from_log_file:
                random_num = random.randint(0, 99)
                if random_num > 97 and url_total < 256:
                    if url.endswith(".tmp") is False and url != "index.html":
                        url_total += 1
                        new_url_list.write(url + "\n")
                        print("URL injected: " + url + "\\n")
                else:
                    pass

            new_url_list.close()
            
        else:
            # Once the final numbered log has been used, set flag to False to prevent
            #   it kicking up an error about it not exisiting.
            more_logs = False
            
        log_count += 1

    # At this point, the file starts again with the new url list!

        
    



