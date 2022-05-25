import os
import shutil
import re
import random
import csv 
import subprocess
import time

# -----------------------------------------------------------------------------
# TEXT COLOURING CLASS AND SUBROUTINES
# -----------------------------------------------------------------------------
class text_colours: 
    RED = '\033[31m'
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    PURPLE = '\033[34m'

    ENDC = '\033[m' # returns terminal to default

class lists:
    legal = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~:/?#[]@!$&'()*+,;=") # legal chars in urls
    illegal = list(",.<>?!/\\\"'|;:[]{}=+)(*&^%$£@`~§§#€ ")
    reserve = list(":/#?&@%+~") # reserved chars inside urls
    suffix1 = ["jpeg","jpg","png","tif","gif","tiff", "pdf", "aspx", ":80", ".app", ".xx", ".xxx", ".php"]
    prefix1 = ["-"]
    filesuf = [".py", ".pdf", ".txt", ".csv", ".config"]    # files that won't be deleted on cleanup

class open_write:
    def error_files(string):
        error_files = open("error_files.txt", "a")
        error_files.write(string + "\n")
        error_files.close()
        return

    def metadata_record(identifier, title, file_name):
        file = open("metadata_record", "a")
        file.write("\"" + identifier + "\",\"" + title + "\",\"" + file_name + "\n")
        file.close()
        return

class cmd:
    ia_bulk = 'ia upload --spreadsheet="ia_upload.csv" --sleep=30 --retries 10'
   
    def pdftk(input_file, output_file, count, timeout=60):
        # This calls PDFtk program to run over a PDF and modify (compress, flaten, fix syntax, etc)
        # input cannot equal output, thus the requirement for both. Switched back in main script.
        if os.path.exists(input_file) is False:
            return
        pdftk_command = 'pdftk "' + input_file + '" output "' + output_file + '" flatten drop_xfa compress dont_ask'
        ptt.command("\n[--  Process --] File #" + str(count).rjust(5) + "  " + pdftk_command)
        pdftk = subprocess.Popen(pdftk_command, shell=True)        
        n = 0
        while n <= timeout:                     # timeout after 60 seconds
            if pdftk.poll() is None:            # if pdftk subprocess is alive
                time.sleep(1)                   # sleep and provide feedback
                print(text_colours.YELLOW + "[--  -------  --] " + "Processing... " + str(60 - n) + text_colours.ENDC, end="\r")
            else:
                return                          # if subpro ends within 60sc, end as usual 
            n += 1
        try:                                    # if timeout occurs:
            pdftk.kill()                        #   try to kill
            try:    # tidy up by removing any partial/error output files, leaving the original input
                cmd.remove_file(output_file)
            except:                             # ignore errors in cleanup
                pass
        except:                                 # ignore errors in killing
            pass
        finally:                                # feedback and return
            ptt.error("PDFtk Aborted after" + str(timeout_sc) + " seconds. Continuing.")
            return 

    def pdftk_meta(input_file):
        try:
            return str(subprocess.check_output(["pdftk " + input_file + " dump_data"], shell=True)).split("\\n")
        except:
            return ""
    
    def metadata_format(metalist):
        n, tick, author, created_on = 0, 0, "", ""
        if len(metalist) != 0:
            for item in metalist:
                if tick == 2:
                    break

                if item.startswith("InfoKey: Author"):
                    try:
                        author = metalist[n + 1].lstrip("InfoValue: ")
                    except:
                        pass
                    tick += 1

                if item.startswith("InfoKey: CreationDate"):
                    try:
                        raw_co = metalist[n + 1].lstrip("InfoValue: D:")[0:8]
                        created_on = raw_co[0:4] + "-" + raw_co[4:6] + "-" + raw_co[6:8]
                    except:
                        pass
                    if cmd.validate(created_on) is False:   # if invalid date, set to empty/i.e. ignore
                        date = ""
                    tick += 1

                n += 1
        return author, created_on

    def wget(url, log_file, quotastring, user_agent, filetype):
        return "wget " + url + " -o " + log_file + " -nv --tries=2 --retry-connrefused --timeout=10 --wait=0.5 --random-wait --quota=" + quotastring + " --user-agent=" + user_agent + " -r -l 0 -A " + filetype + " " + filetype.upper() + " -H -e --robots=off"
    
    def wget2(url, log_file, quotastring, user_agent, filetype):
        return "wget2 " + url + " -r -l 0 --max-threads=20 -A ." + filetype + " ." + filetype.upper() + " --restrict-file-names=ascii --timeout=10 --wait=0.5 --random-wait --tries=2 --waitretry=5 --quota=" + quotastring + " --user-agent=" + user_agent + " --max-threads=20 --span-hosts=on --robots=off --retry-connrefused -o " + log_file
    

    def raw_subprocess(command):
        subprocess.run(command, shell=True)
        return

    def pause():
        input("Pause [Press any key to continue] ")
        return

    def remove_file(file):
        try:                            # removes old URL file
            os.remove(file)
        except:
            pass
        return

    def check_and_remove(file):
        if os.path.exists(file) is True:      # checks if a ia file already exists
            os.remove(file)           #   if so.. deletes it to prevent conflict
        return

    def get_size_KB(file, path=os.getcwd()):
        return (os.path.getsize(os.path.join(path, file)))/1024 

    def retrieve_uprecord(upload_record, uploaded_list=[], write_record=True):
        count = 0
        if write_record is True:
            if os.path.exists(upload_record) is True:
                for line in open(upload_record, "r"):
                    if line.strip("\n") not in uploaded_list:
                        uploaded_list.append(line.strip("\n"))
                    elif line.strip("\n") in uploaded_list: 
                        count += 1    
        return uploaded_list

    def write_uprecord(ia_file, upload_record_txtfile):
        try:
            open(upload_record_txtfile, "a").write(ia_file.split("/")[-1] + "\n")   # split long path and use filename only
        except:
            pass    # ignore errors (no real loss in the odd file not being recorded)
        finally:  
            return

    def log_cleanup(last_log, n=0, mypath=os.getcwd()):
        # deletes old wget logs by cycling through from 0 upwards
        while n < last_log: 
            if n > 0:
                try:
                    os.remove(os.path.join(mypath, "/wget-log." + str(n)))
                    ptt.warning("/wget-log." + str(n) + " deleted")
                except:
                    pass
            else:
                try:
                    os.remove(os.path.join(mypath, "/wget-log"))
                    ptt.warning("/wget-log deleted")
                except:
                    pass
            n += 1
        return

    def validate(date_text):
        # https://stackoverflow.com/a/16870699
        try:
            datetime.datetime.strptime(date_text, '%Y-%m-%d')
            return True
        except:
            return False

    def write_master_record(line):
        try:
            with open("master_metadata.csv", "a", encoding="utf8") as record:
                record.write(line)
        except:
            pass
        finally:
            return


class ptt:   #"  Print To Terminal"
    def warning(text):                                          # Warnings in Yellow
        print(text_colours.YELLOW + "[!?  Warning  ?!] " + text + text_colours.ENDC)

    def alert(text):                                            # Alerts in Yellow
        print(text_colours.YELLOW + "[-?   Alert   ?-] " + text + text_colours.ENDC)
        return

    def error(text):                                            # Errors in Red
        print(text_colours.RED + "[!!   Error   !!] " + text + text_colours.ENDC)
        return

    def command(text):                  # Commands passed to System (via  OS) in Cyan
        print(text_colours.CYAN + text + text_colours.ENDC)
        return

    def yellow(text):
        print(text_colours.YELLOW + text + text_colours.ENDC)
        return

    def input(text):
        print(text_colours.PURPLE + text + text_colours.ENDC)
        return

    def wget_wait(time, log_file):
        try:
            filesize = cmd.get_size_KB(log_file)
            if filesize/1024 >= 1:
                if (filesize/1024)/1024 >= 1:
                    print(" Seconds remaining until timeout: " + time.rjust(7) + "     " + log_file + " size: " + strcv.dp3((filesize/1024)/1024).rjust(9) + "GB", end="\r")
                else:

                    print(" Seconds remaining until timeout: " + time.rjust(7) + "     " + log_file + " size: " + strcv.dp3(filesize/1024).rjust(9) + "MB", end="\r")
            else:
                print(" Seconds remaining until timeout: " + time.rjust(7) + "     " + log_file + " size: " + strcv.dp3(filesize).rjust(9) + "KB", end="\r")
        except:
            pass
        finally:
            return

    def nl():  # newline
        print("\n")
        return

    def sums(sum_vals):
        if sum_vals[0] == 0:
            return
        print("\n")
        sum_percent = (100/sum_vals[0])*sum_vals[2]
        if sum_vals[2] > 0:
            ptt.error("Total PDFtk cycle compression GAIN: +" + strcv.dp3(sum_vals[2]) + "KB (+" + strcv.dp2(sum_percent) + "%)")
            ptt.error("[Sum start size: " + strcv.dp3(sum_vals[0]) + "KB --- Sum end size: " + strcv.dp3(sum_vals[1]) + "KB")
        elif sum_vals[2]/1024 <= -1:
            if (sum_vals[2]/1024)/1024 <= -1:
                ptt.alert("Total PDFtk cycle compression savings: " + strcv.dp3((sum_vals[2]/1024)/1024) + "GB (" + strcv.dp2(sum_percent) + "%)")
                ptt.alert("[Sum start size: " + strcv.dp3(sum_vals[0]) + "GB --- Sum end size: " + strcv.dp3(sum_vals[1]) + "GB")
            else:
                ptt.alert("Total PDFtk cycle compression savings: " + strcv.dp3(sum_vals[2]/1024) + "MB (" + strcv.dp2(sum_percent) + "%)")
                ptt.alert("[Sum start size: " + strcv.dp3(sum_vals[0]) + "MB --- Sum end size: " + strcv.dp3(sum_vals[1]) + "MB")
        elif sum_vals[2] == 0:
            ptt.alert("Total PDFtk cycle compression savings: " + strcv.dp3(sum_vals[2]) + "KB (" + strcv.dp2(sum_percent) + "%)")
            ptt.alert("[Sum start size: " + strcv.dp3(sum_vals[0]) + "KB --- Sum end size: " + strcv.dp3(sum_vals[1]) + "KB")
        else:
            ptt.alert("Total PDFtk cycle compression savings: " + strcv.dp3(sum_vals[2]) + "KB (" + strcv.dp2(sum_percent) + "%)")
            ptt.alert("[Sum start size: " + strcv.dp3(sum_vals[0]) + "KB --- Sum end size: " + strcv.dp3(sum_vals[1]) + "KB")
        return

class strcv:                                # string convert
    def dp2(text): # 2 dp
        return "{:.2f}".format(text)
    def dp3(text): # 3 dp
        return "{:.3f}".format(text)

    def get_domain(url):    # strips prefix and splits at / to find the domain in pos 0 (i.e. www.pdf.com/a becomes pdf.com )
        return strcv.general((url.lstrip("http://").lstrip("https://").lstrip("www.")).split("/")[0]) 

    def general(string):
        return string.strip("\n").strip().replace('"',"")

    def general_quote(string):
        if string.startswith('"') is False:
            string = '"' + string
        if string.endswith('"') is False: 
            string = string + '"'
        return string

class create:
    def ia_upload_command(line, metadata_name):
        if len(line) != 0:
            ia_upload_command = "ia upload " + line[0] + " \"" + line[-1] + "\"" # minimum infomation required for ia
            n = 1
            while n < (len(line) - 1):    # Runs through each csv line and adds metadata where avaliable. 
                try:
                    if line[n] != "":
                        ia_upload_command += " --metadata=\"" + metadata_name[n] + ":" + line[n] + "\""
                except:
                    pass
                finally:
                    n += 1
            ia_upload_command += " --sleep=30 --retries 10"     # ia settings

            return ia_upload_command
        else:
            ptt.error("Unable to create IA upload command from csv line: " + str(line))
            return

    def wget_log_file():    #   Creates a sequentially numbered log file for wget
        log_n = 0
        while True:               # while break flag is false
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
            if log_n > 10000:
                ptt.error("Error in subroutine create.wget_log_file()")
                return

class calculate:
    def total_bandwith(input):
        return



# -----------------------------------------------------------------------------
# INITIAL LOADING FEEDBACK
# Used to provide basic feedback after loading settings from a config file
# -----------------------------------------------------------------------------
def loading_feedback(quotastring, contributor, clean_up, confirm_uploads, filetype, mediatype, write_record, upload_record_txtfile, uploaded_pdfs_folder, wget2, user_agent, reject_urls, reject_list, url_list, bulk_uploads, timeout_sc, defaulted=False):
    print("------------------------------------------------------------------------------\n"*3)

    if defaulted is True:
        print("!! Using default values (config file not found or has errors!) \n")
        cmd.pause()

    print("Traffic Quota:                   " + quotastring)
    print("Contributor(s):                  " + contributor)
    print("Filetype to find:                " + filetype + " " + filetype.upper())
    print("Archive.org mediatype:           " + mediatype )
    
    if wget2 is True:
        print("Wget agent:                      wget2")
    else:
        print("Wget agent:                      wget (not using wget2)")

    print("Wget time limit (timeout; sc):   " + str(timeout_sc))
    print("Wget user-agent:                 " + user_agent)
    print("Uploaded PDF moved to folder:    " + uploaded_pdfs_folder)
    if bulk_uploads is True:
        print("Bulk uploads:                    True")
    else:
        print("Bulk uploads:                    False")
    if write_record is True:
        print("Writing local upload record to:  " + upload_record_txtfile)
    else:
        print("Not writing local upload record")

    if clean_up == True:
        print("Automatically cleaning up")
    elif clean_up == False:
        print("Not cleaning up")
    else:
        pass

    if confirm_uploads == True:
        print("Confirming uploads")
    elif confirm_uploads == False:
        print("Not confirming uploads")

    if reject_urls is True:
        print("Rejecting URLs based on list: " + reject_list)
        
    print("\n")
    print("------------------------------------------------------------------------------\n"*3)
    return      

# -----------------------------------------------------------------------------
# REMOVE ("DROP") EMPTY DIRECTORIES
#   Remove any empty folders that have been created to keep things tidy
#   ---->   https://stackoverflow.com/a/23488980
#   ---->   https://stackoverflow.com/a/61925392
# -----------------------------------------------------------------------------
def remove_empty_folders(directory):  
    # Work topdown to delete needless files (generally tmp and html)
    for dirpath, dirnames, filenames in os.walk(directory):
        for file in filenames:
            allowed = False                                 # allowed file flag (default:)
            if file.startswith("wget-log") is True:         # keeps wget-log files
                allowed = True
            else:
                for suffix in lists.filesuf:                # keeps permitted files, inc config and .py
                    if file.endswith(suffix) is True:       
                        allowed = True
            if allowed is False:                            # if disallowed, deletes
                try:
                    os.remove(os.path.join(dirpath, file))  # [ Tries to remove,
                except:                                     #   just ignore if it kicks an error]
                    pass
    # Then work backwards to delete empty folders
    for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
      if not dirnames and not filenames:    
            try:
                os.rmdir(dirpath)           # [ Tries to remove said folders, 
            except:                         #       but just ignore any errors]
                pass
    return

# -----------------------------------------------------------------------------
# IDENTIFIER FORMATTING
#   Each archive upload requires an alphanumeric identifier of a len < 100 char
#       This section takes the standard identifier generated when creating
#   the bulk upload csv and formats it by removing illegal characters.
# -----------------------------------------------------------------------------
def identifier_formatting(identifier): # Remove non-alphanumeric characters
        if identifier.isidentifier() is True:            # Basic check/shortcut
            new_identifier = identifier
        else:
            count, new_identifier = 0, ""       
            # Loops through every character, and only accepts legal chars.
            while count < len(identifier) and count < 80: 
                if identifier[count] not in lists.illegal:
                    new_identifier += identifier[count]  
                count += 1
        # Lastly checks that it is of a sufficient len (here: 10 - arbitrary!)
        if len(new_identifier) <= 10:                 
            return "MRS_PDFbot-" + new_identifier     # add arbitary prefix as here
        else:
            return new_identifier
        # there is no minimimum id len, but shorter ones are more likely to
        #   conflict with existing uploads - so this is an easy 

# -----------------------------------------------------------------------------
# FIX PDF
#   Uses PDFtk as suggested by ia to fix potential errors and reduce size.
# -----------------------------------------------------------------------------
def fix_pdf(ia_file, count, filetype=".pdf", my_path=os.getcwd()):
    if filetype == ".pdf":
        sum_vals = [0, 0, 0]                                        # start, end, absolute size values
        start_size = cmd.get_size_KB(ia_file)                       # calculate "before" size
        sum_vals[0] += start_size                                   
        new_file = ia_file.rstrip(filetype) + "-tmp" + filetype     # creates temp file for PDFtk b/c in != out
        try:                        # tries. If exception occurs it still returns the original, unchanged file
            cmd.pdftk(ia_file, new_file, count)                     # Runs the PDFtk command and outputs to file-tmp.pdf (input != output)
            if os.path.exists(new_file) is True: # only if new file exists, go ahead and delete the old
                end_size = cmd.get_size_KB(ia_file)                 # calculates end size (i.e. new file size)
                absolute_change = -(start_size - end_size)          # calculates change in size
                sum_vals[1] += end_size
                sum_vals[2] += absolute_change
                percent_change = (100/start_size)*absolute_change   # calculates percentage change
                start_size, end_size, percent_change = strcv.dp3(start_size), strcv.dp3(end_size), strcv.dp2(percent_change) # convert to 2 decimal places
                if absolute_change > 0:
                    ptt.error(start_size.rjust(10) + "KB --> " + end_size.rjust(10) + "KB (+" + strcv.dp3(absolute_change).rjust(6) + "KB, +" + percent_change.rjust(6) + "%)")
                    cmd.remove_file(new_file)           # if file got larger, use the origignal by deleting new version
                elif absolute_change < 0:
                    ptt.alert(start_size.rjust(10) + "KB --> " + end_size.rjust(10) + "KB (" + strcv.dp3(absolute_change).rjust(6) + "KB, " + percent_change.rjust(6) + "%)")
                    cmd.remove_file(ia_file)            # if file got smaller, deletes the old (input) file         
                    os.rename(new_file, ia_file)        #  and renames the new (output) file to the original name (swaps them)
                elif absolute_change == 0:
                    ptt.yellow("[--  -------  --] " + start_size.rjust(10) + "KB --> " + end_size.rjust(10) + "KB (± 0.000KB, +  0.00%) [NO CHANGE]")
                    cmd.remove_file(ia_file)            # if the file size did not change, delete the old file (may have still fixed syntax errors, etc.)        
                    os.rename(new_file, ia_file)        #  and renames the new (output) file to the original name (swaps them)
        except:                                            
            pass  
    return ia_file, sum_vals

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
#  WGET COMMAND
#   Using the inputs calls either wget or wget2 depending on config
# -----------------------------------------------------------------------------
def call_wget(wget2, url, filetype, user_agent, quotastring, reject_list, log_file="", timeout_sc=1800):
    timeouted = False
    if wget2 is True:
        command = cmd.wget2(url, log_file, quotastring, user_agent, filetype)
    else:
        command = cmd.wget(url, log_file, quotastring, user_agent, filetype)


    ptt.command("\n[--  Downl'd  --] (Timeout after: " + str(timeout_sc) + " sc): " + command + "\n")    # user feedback
    wget_call = subprocess.Popen([command], shell=True)    # creates a subroutine, and then essentially waits   
    
    n = 0
    while n <= timeout_sc:
        if wget_call.poll() is None:
            # p.subprocess is alive
            time.sleep(1)
            ptt.wget_wait(str(timeout_sc-n), log_file)

        else:
            ptt.warning("\nWget finished (data quota reached, or error)")
            return   
        n += 1
    
    try:
        wget_call.kill()                                # so kill the subroutine, and then pass args to dummy vars
    except:
        pass
    finally:
        ptt.error("Search Process Timeout after " + str(timeout_sc) + " seconds. Continuing.")
  
        return


# -----------------------------------------------------------------------------
#  CREATE IA CSV
#   One of many ways to use the ia command is by using a csv/spreadsheet
#   to use for bulk uploads. This section creates said file, and forms the
#   basis for many of the other modules
# -----------------------------------------------------------------------------
def create_ia_csv(contributor, mediatype, files, write_record, filetype, upload_record_txtfile, uploaded_files_list=[], ia_csv="ia_upload.csv", mypath=os.getcwd()):
    filetype = "." + strcv.general(filetype).lower()
    cmd.check_and_remove(ia_csv)
    # create new csv; encode to utf8 to help stop identifier errors
    output_csv = open(ia_csv, "x", encoding="utf8")


    archive_setup = output_csv.write("identifier,title,contributor,mediatype,source,creator,date,file")
    uploaded_files_list = cmd.retrieve_uprecord(upload_record_txtfile, uploaded_files_list)
    sum_vals = [0, 0, 0]
    count = 1
    # Transfer "files" list to the csv with some mild formatting
    for item in files:
        new_name = item.replace(" ", "_")   # replaces spaces with underscores, as spaces cause problems with PDFtk
        try:
            os.rename(item, new_name)
        except:
            pass
        # Only accept the wanted filetype files, in case any others have crept in!
        item = strcv.general(item).lower()
        if item.endswith(".pdf") is True:
            ia_file = item.replace(mypath +"/", "") # ia_file is the FULL path - relative to script dir - to file needed for the uploader
        
            if os.path.exists(ia_file) is True and item != str("." + filetype):        # if the file exists (i.e. passes basic checks as above)
                if ia_file not in uploaded_files_list:     # i.e. if it hasn;t already been uploaded
                 
                    title = item.split("/")[-1].replace("_", " ").replace(filetype, "").replace("-", " ") # removes underscores, hyphens and extention for easy readability
                    identifier = identifier_formatting(item.split("/")[-1].replace(filetype, "")) # generated from the file name, per requirements
                    
                    
                    source_website = item.split("/")[len(mypath.split("/"))]
                    
                    author, created_on = cmd.metadata_format(cmd.pdftk_meta(ia_file))

                    ia_file, sum_vals_out  = fix_pdf(ia_file, count, filetype)  # "fixes" the pdf with brief compression and syntax corrections
                    try:    # in case of errors, tries to remove any residual tmp files created by fix_pdf()
                        cmd.remove_file(ia_file.rstrip(".pdf") + "-tmp.pdf")
                    except:
                        pass

                    sum_vals += sum_vals_out
                    uploaded_files_list.append(ia_file)     # add the file to the uploaded file list
                   
                    output_csv.write("\n" + identifier + "," + '"' + title + '",' + contributor + "," + mediatype + ',' + source_website + ',' + author + ',' + created_on + ',"' + ia_file +'"') # writes all the above to the csv (if the file existsn and hasn't already been uploaded)

                    count += 1
                    if write_record is True:                                    # if config asks to create a upload record
                        cmd.write_uprecord(ia_file, upload_record_txtfile)      #   add to the record
                    elif write_record is False:
                        pass
                    else:
                        ptt.error("[!!   Error   !!] Write Record Error.")          # Feedback for unkown errors
                        break                                                   # Exit script due to said unkown behaviour
                elif ia_file in uploaded_files_list:                                    # if it has already been uploaded then....
                    ptt.warning("File already uploaded, skipping: " + ia_file)
                else:                                                           # if something strange has happened....
                    ptt.error("File already uploaded? Skipping: " + ia_file)

    output_csv.close()
    ptt.sums(sum_vals)
    ptt.nl()
    return count

# ------------------------------------------------------------------------------
#  CALLS THE INTERNET ARCHIVE SCRIPT   
#   Once the csv is created, we ask for confirmation of the uploads to archive.org
#   (qeury disabled by default in config). Then we call the basic ia command for
#   bulk uploads. 
# ------------------------------------------------------------------------------
def call_ia_cli(confirm_uploads=False, bulk_uploads=False, count=0, continue_with_ia=False):
    if bulk_uploads is True:
        if confirm_uploads == False:          # if confirmation isn't required
            print('\n\n[--  -------  --] ' + cmd.ia_bulk)     # printed for user feedback
            subprocess.run(cmd.ia_bulk,  shell=True)                            # call the command
        elif confirm_uploads != False:    # if confirmation is required, asks for it, checks the first letter to be Y for yes
            if input("[--   Input   --] Upload to IA? [Y/N]: ").lower()[0] == "y":
                print('\n\n[--  -------  --] ' + cmd.ia_bulk)     # printed for user feedback
                subprocess.run(cmd.ia_bulk,  shell=True)                            # call the command
            else:
                ptt.warning("File upload to ia skipped")    # skips if input isn't correct, print for feedback
        else:
            ptt.error("call_ia_cli Error. File upload to ia skipped") # catches any other errors
        return
    elif bulk_uploads is False:
        b_count = 0
        if confirm_uploads != False:    # if confirmation is required, asks for it, checks the first letter to be Y for yes
            if input("[--   Input   --] Upload to IA? [Y/N]: ").lower()[0] == "y":
                continue_with_ia = True          # call the command
            else:
                ptt.warning("File upload to ia skipped")    # skips if input isn't correct, print for feedback
                return
        if continue_with_ia is True or confirm_uploads == False:
            with open("ia_upload.csv", "r") as spreadsheet:
                read_ia_csv = csv.reader(spreadsheet, delimiter=",")
                header_line = True
                for line in read_ia_csv:
                    if header_line is True:
                        metadata_name, header_line = line, False
                    else:
                        ia_upload = create.ia_upload_command(line, metadata_name)
                        ptt.command('\n[--   Upload  --] (File ' + str(b_count) + " of " + str(count) + ") " + ia_upload + "\n")     # printed for user feedback
                        try:
                            subprocess.run(ia_upload, shell=True)
                            cmd.write_master_record(line) # if upload worked without problems, write to record
                        except:
                            ptt.warning("Error with upload of: " + line[-1] + " writing to record")
                            open_write.error_files(line[-1])
                    b_count += 1
        elif continue_with_ia is False:
            ptt.warning("File upload to ia skipped")    # skips if input isn't correct, print for feedback
        else:
            pass
        
    return

# ------------------------------------------------------------------------------
# POST-RUN FILE CLEANUP
#   Cleans up the files by deleting empty directories and moving PDFs to
#   a seperate "uploaded" folder in the source dir for offline backups.
#   If ia_upload has thrown an error and stoped the uploading process, and this
#   module is on by default, then it will still run and move PDFs to a seperate
#   folder even if they've not been uploaded.
# ------------------------------------------------------------------------------
def cleanup_def(total_moved, total_delete, clean_up=False, filetype=".pdf", upload_dir="uploaded_PDFs", ia_file="ia_upload.csv", mypath=os.getcwd()):
    all_files = find_files()        # finds all the files in the same directory as this script
    pdf_files, problem_files = [], []

    # Create a list of problem files to ignore, so they can be tried again
    try:
        for line in open("error_files.txt", "a"):
            problem_files.apend(strcv.general(line))
    except:
        ptt.warning("Ignoring problem files (error_files.txt does not exist)")

    for item in all_files:           
        if item.endswith(filetype) is True:
            pdf_files.append(item)

    if clean_up is True:             # if the config states that the script should clean-up post-upload...
        print("\n[--  -------  --] Moving PDFs to seperate file for personal archiving.")   # user feedback
        # Sees if a file already exists, otherwise tries to create on ein the script directory
        if os.path.isdir("uploaded_PDFs") is False:        # checks to see if a directory exists into which PDFs can be moved to
            try:
                os.mkdir("uploaded_PDFs")                  # if it doesn't exist, create
                print("[--  -------  --] Created directory at /uploaded_PDFs")  # feedback
            except:
                pass
        moved_count, delete_count, ignore_count = 0, 0, 0    # temporary counters
        for line in pdf_files:              # for every PDF file
            if line in problem_files:
                ptt.warning("FileNotFoundError | File in Problem List. Ignoring: " + line)
                ignore_count += 1
            else:
                try:
                    shutil.move(line, "./uploaded_PDFs/")
                    moved_count += 1
                    ptt.warning("File moved to ./uploaded_PDFs/: " + line)
                except FileNotFoundError:
                    ptt.error("(Ignoring) FileNotFoundError in Cleanup Process: " + line)
                    try:
                        error_files = open("error_files.txt", "a")
                        error_files.write(line + "\n")
                        error_files.close()
                    except:
                        pass
                    ignore_count += 1
                except:
                    try:
                        os.remove(line)
                        ptt.error("Unable to move file. Deleting: " + line)
                        delete_count += 1
                    except:
                        error_files = open("error_files.txt", "a")
                        error_files.write(line + "\n")
                        error_files.close()
                        ignore_count += 1
              
        # Deletes empty folders
        remove_empty_folders(mypath)
        # User feedback
        total_moved += moved_count
        total_delete += delete_count
        print("\n[--  -------  --] File move complete. Files moved: " + str(moved_count) + "    [Running Total: " + str(total_moved) + "]")
        print("[--  -------  --] File deletion complete. Files deleted: " + str(delete_count) + "    [Running Total: " + str(total_delete) + "]")
        print("[--  -------  --] Files ignored: " + str(ignore_count))
        print("[--  -------  --] Empty files deleted")     
    
    elif clean_up is False:
        ptt.warning("No post-archiving clean up performed.\n")

    return total_moved, total_delete

#------------------------------------------------------------------------------
# URL FILTER (FOR CREATING NEW URL LIST)
#   Simple sub-routine to reduce the number of URLs by (attempting) to remove
#   obvious duplicates
#------------------------------------------------------------------------------
def url_filter(url_string, reject_urls=False, reject_list="reject-list.txt", domain_list=[], reject_domains=[], mypath=os.getcwd()):
    if reject_urls is True:
        for line in open(os.path.join(mypath, reject_list), "r"):
            if line.startswith("#") is False:
                reject_domains.append(line.strip("\n"))

    for url in url_string:           # For every URL past to the routine
        invalid  = False              # "Invalid URL" flag
        domain = strcv.get_domain(url) 
        if domain in domain_list or domain in reject_domains:               # if it is already in our list, reject
            pass
        elif domain not in domain_list and domain not in reject_domains:         # if it is new to us, add to our list
            for suffix in lists.suffix1:
                for prefix in lists.prefix1:
                    if domain.endswith(suffix) is True or domain.startswith(prefix) is True:
                        invalid = True
            if "." in domain and invalid is False:                               # check that it's a URL, not just a plain string
                domain_list.append(domain)

    return domain_list                          # return the list for further processing

#------------------------------------------------------------------------------
# QUOTASTRING FORMATTER
#   Converts all possible config file imputs for the quotastring into two
#   seperate parts (a base and value) not currently used as seperate (bar a
#   few feedback lines), and are converted back to a string within main() for
#   use elsewhere. Mainly used for error catching.
#------------------------------------------------------------------------------
def quotastring_formatter(quotastring):           
    catch_int = False   # flag for while loops, when looking for a valid int value
    numeral = "0123456789"
    quotastring = quotastring.lower()
    if quotastring[-1] not in numeral:              # if the last char is NOT a number (i.e. a letter)
        if quotastring.endswith(tuple(["k", "m", "g"])) is True: # if it is a valid letter...
            quota_base = quotastring[-1]                                # use that letter as the base
            try:                
                quota_num = int(quotastring[0:-1])      # try to use the rest of the string as the int
            except ValueError:                          # if invalid (i.e. other letters therein?)
                n = len(quotastring) - 2
                while catch_int is False:
                    try:                                # ignore the next last, and see if thats an int
                        quota_num = int(quotastring[0:n])
                        ptt.warning("Quota value determined; Quota base determined | Input: " + quotastring + " | Output: " + str(quota_num) + quota_base)  # if no error (i.e. valid int), use as value
                        catch_int = True                # and trigger flag to exscape while loop
                    except ValueError:                  # if still an error, pass and reduce n to
                        pass                            # see if removing another char produces a valid int
                    finally:
                        if n == 0:                      # if n = 0 (i.e we've tried all the string)
                            catch_int = True            # trigger escape
                            quota_num = 10              # set to default, and warn. Use valid base still
                            ptt.warning("Quota value error, defaulting to 10; Quota base determined | Input: " + quotastring + " | Output: " + str(quota_num) + quota_base)
                        else:                           # otherwise, carry on and reduce n
                            pass
                    n = n - 1
        elif quotastring.endswith(tuple(["k", "m", "g"])) is False: # if it doesn't end with a valid char
            if quotastring[-2] == "k" or quotastring[-2] == "m" or quotastring[-2] == "g": #assume "mb', "gb" or "kb"
                quota_base = quotastring[-2]        # if the 2nd to last char is valid, set as base
                try:                                # see if the rest of the string is a valid int
                    quota_num = int(quotastring[0:-2])  #... if so, set as quota
                except ValueError:                  # otherwise, run another loop (as above) to catch a valid value
                    n = len(quotastring) - 2
                    while catch_int is False:
                        try:
                            quota_num = int(quotastring[0:n])
                            catch_int = True
                        except ValueError:
                            pass
                        finally:
                            if n == 0:
                                catch_int = True
                                quota_num = 10
                                ptt.warning("Quota value error, defaulting to 10; Quota base determined | Input: " + quotastring +  "| Output: " + str(quota_num) + quota_base)
                        n = n - 1
            else:                                   # else if the 2nd to last char is also invalid, ignore
                try:                                # and just look for a valid value/int
                    quota_num = int(quotastring[0:-1]) # try all but the last chart
                    quota_base = "m"                # default base to m
                    ptt.warning("Quota value found; Quota base defaulting to \"m\" | Input: " + quotastring + " | Output: " + qstr(uota_num) + quota_base)
                except ValueError:                  # if an error, run a loop as above to try and catch
                    n = len(quotastring) - 1.       #   a valid int value
                    while catch_int is False:
                        print(n)
                        try:
                            quota_num = int(quotastring[0:n])
                            quota_base = "m" # default
                            ptt.warning("Quota value found; Quota base defaulting to \"m\" | Input: " + quotastring + " | Output: " + str(quota_num) + quota_base)
                            catch_int = True
                        except ValueError:
                            pass
                        finally:
                            print("--")
                            if n == 0:    # if nothign can be found, default to 10m
                                quota_num, quota_base = 10, "m"    
                                ptt.error("Quota value or base not found. Defaulting to 10m | Input: " + quotastring)
                                catch_int = True
                        n = n - 1

    elif quotastring[-1] in numeral:    # if the last char IS a number, assume no base provided
        quota_base = "m"                # set to default
        try:                            # try and see if the whole string is just a value
            quota_num = int(quotastring)
            ptt.warning("Quota value found; Quota base defaulting to \"m\" | Input: " + quotastring + " | Output: " + str(quota_num) + quota_base)
        except ValueError:      # if not, there's a random char contained therein, so rather then trying to catch a value
            quota_num = 10      # just set to default and provide feedback
            ptt.error("Quota value or base not found. Defaulting to 10m | Input: " + quotastring)
    else:                               # for any other errors, default to 10m
        quota_num, quota_base = 10, "m"
        ptt.error("Quota value or base not found. Defaulting to 10m | Input: " + quotastring)

    if quota_base == "g":    # i.e. GB, not accepted by wget/2 so convert to m by multiplying by 1000
        ptt.warning("Quotabase not permitted (\"g\" for GB?), converting to \"m\" (MB) by value*1000")
        quota_num, quota_base = quota_num*1000, "m" 

    quotastring = str(quota_num) + str(quota_base) # we convert back knowing that the final char is the size
    return quotastring   # and all others are the value. If needed as seperate vallues, it can now be split.

#------------------------------------------------------------------------------
# NEW URL LIST CREATOR
#   Poor mans way to create a new URL list. Used the wget-log's as a base, to 
#   continue where the program may have left off.
#------------------------------------------------------------------------------
def new_url_list(reject_urls, reject_list, mypath=os.getcwd()):
    log_count, url_total = 0, 0
    cmd.remove_file("url_file.txt")       # removes old URL file
    more_logs = True
    while more_logs is True:
        log_file_name = "wget-log"  # Normal log file name. Might be different if wget above edited
        if log_count > 0:           # log files other than the first are appended with a numeral
            log_file_name += "." + str(log_count)   # wget is set to appends additional logfiles as ".n"
        if os.path.exists(mypath + "/" + log_file_name) is True:        # checks that log file exists in current directory
            ptt.warning("Reading " + log_file_name)        # user feedback
            try: 
                log_file = open(log_file_name).read()                    # opens and reads logfile to log_file str       
                # regex to convert the entire log file to just a list of URLS as found from: https://stackoverflow.com/a/50790119
                log_file_urls = re.findall(r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b",log_file)

                with open("url_file.txt", "a") as url_file:                     # append new urls to url list
                    for url in url_filter(log_file_urls, reject_urls, reject_list): # filter to use only valid urls
                        if random.randint(0, 9999) > 9995 and url_total < 256:   # accept 0.05% of urls, and a max of 256
                            url_total += 1                         
                            url_file.write(url + "\n")          # write url too the new url list file, with a newline delimiter
                            ptt.yellow("[--  -------  --] URL injected: " + url) 
                        elif url_total >= 256:
                            more_logs = False       # exit loop(s) when URL file is full, to prevent wasting time. Skips all the rest and deletes later
                            break
            except UnicodeDecodeError:
                ptt.error("UnicodeDecodeError reading: " + log_file_name + " (Skipping)")
            except:
                ptt.error("Error reading: " + log_file_name + " (Skipping)")
            finally:
                try:
                    log_file.close()
                except:
                    pass
        else:       # Once the final numbered log has been used, break loop
            break    
        log_count += 1
    ptt.alert("[--  -------  --] Total URLs injected: " + str(url_total))
    cmd.log_cleanup(log_count)  # clean up by deleting all the currnet logs
    return

# ------------------------------------------------------------------------------
# CHECK URL LIST FOR VALIDITY
#   Some basic checks to see if the URL in the list are (possibly) valid. 
#   wget rejects invalid URLs without crashing the program, so not strictly 
#   neccesary but does save some time.
# ------------------------------------------------------------------------------
def check_url_list(reject_urls, reject_list, url_list=[], valid=True, feedback=True):
    checked_list = []                       # list of checked URLs to reference
    if len(url_list) != 0:             # i.e. if it IS a list at all
        for entry in url_list:              # For every URL to check...
            valid = True                    # general flag
            for character in list(entry):   # for every character list entry
                if character not in lists.legal:                # if char is NOT in the legal char list...
                    if character in lists.reserve:             # if char IS a reserved char, warn but accept
                        ptt.warning("Possible reserved characters in input URL: " + entry)
                    elif character not in lists.reserve:       # if char IS NOT a reserved, reject char
                        ptt.error("[!! Rejecting !!] Illegal characters in input URL: " + entry)
                        valid = False   # set flag
                    else:
                        ptt.warning("check_url_list error (unable to validate): " + entry)
                elif character in lists.legal:                  # if char IS legal
                    pass                                            # accept character
                else:
                     ptt.warning("check_url_list error (unable to validate): " + entry) # unkown error, but accept char
            if valid is True:            # if valid flag is NOT False (i.e. True/Valid)
                checked_list.append(entry)                     # if valid flag is NOT False (i.e. True/Valid) (otherwise ignore/continue.)
           
    checked_list = url_filter(checked_list, reject_urls, reject_list)
    for entry in checked_list:
        if feedback is True:        # if feedback is required, then print
            print("[--  -------  --] URL accepted: " + entry)    

    return checked_list, len(url_list) + 1

# ------------------------------------------------------------------------------
# READ CONFIG FILE
#   Simply reads the configuration file and assigns values
#   Loads no_config_defaults first, and then overwrights with values that are
#   present
# ------------------------------------------------------------------------------
def read_config(file="MRS-PDFbot.config", url_file="", mypath=os.getcwd()):
    # defaults
    single_url = ""
    url_file = "url_file.txt"
    contributor = '"Marley R. Sexton, MRS.PDFbot"'
    confirm_uploads = False
    clean_up = False
    uploaded_pdfs_folder = "uploaded_PDFs"
    filetype = "pdf"
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
    bulk_uploads = False
    timeout_sc = 1800

    if os.path.exists(os.path.join(mypath, "MRS-PDFbot.config")) is True:
        ptt.warning("Reading MRS-PDFbot.config")
        for line in open(file, "r"):
            if line.startswith("#") is False:        #  Ignore commentted lines, (in config file:)   key_name    =   key_value 
                key_name, key_value = strcv.general(line.split("=")[0]).lower(), strcv.general(line.split("=")[-1]).lower()


                if key_name.startswith("startpage"):
                    if single_url != "":    # if a single_url is specified, adds it to the url_list (regardless of url_list file)
                        
                        url_list.append(single_url)

                elif key_name.startswith("url_list"):
                    url_file = key_value
                    try:        
                        for line in open(os.path.join(mypath, url_file), "r"):                           # try to read file and extract every url (one per line)
                            url_list.append(strcv.general(line))          # add to the to-do list
                    except:
                        ptt.error("URL File invalid. Defaulting")     
                        url_file = "url_file.txt"                           # if none exists, searches for default
                        try:
                            print("+")
                            for line in open(os.path.join(mypath, "url_file.txt") , "r"):
                                print("+")
                                url_list.append(strcv.general(line))
                        except:
                            pass

                elif key_name.startswith("quotastring"):
                    quotastring = quotastring_formatter(key_value)   

                elif key_name.startswith("contributor"):
                    contributor = strcv.general_quote(key_value).title().replace("Mrs.Pdfbot", "MRS.PDFbot")
                    
                elif key_name.startswith("confirm_uploads"):
                    if key_value[0] not in "yn":                            # If not y or n, just default to y 
                        ptt.error("Confirming uploads line error. Defaulting to True (Y)")
                    if key_value[0]  == "y":
                        confirm_uploads = True

                elif key_name.startswith("clean_up"): 
                    if key_value[0] not in "yn":                                    # If not y or n, just default to n
                        ptt.error("[!!   Error   !!] Confirming clean upline error. Defaulting to False (N)")
                    if key_value[0] == "y":
                        clean_up = True

                elif key_name.startswith("uploaded_pdfs_folder"):
                    uploaded_pdfs_folder = strcv.general_quote(key_value)

                elif key_name.startswith("filetype "):
                    filetype  = "." + key_value.strip(".")

                elif key_name.startswith("mediatype"):
                    mediatype = key_value

                elif key_name.startswith("wget2"):
                    if key_value.startswith("true") is True:
                        wget2 = True

                elif key_name.startswith("user-agent"):
                    user_agent = strcv.general_quote(strcv.general(line.split("=")[-1]))

                elif key_name.startswith("local upload record"):
                    if key_value.startswith("true") is True:
                        write_record = True
                    
                elif key_name.startswith("upload record file)"):
                    if write_record is True:
                        if key_value.endswith(".txt") is True:
                            upload_record_txtfile = key_value
                        else:
                            ptt.warning("Defined upload record file is not of required type (.txt). Defaulting to upload_record.txt")

                elif key_name.startswith("use reject list"):
                    if key_value.startswith("true") is True:
                        reject_urls = True

                elif key_name.startswith("reject file"):
                    reject_list = key_value

                elif key_name.startswith("bulk_uploads"):
                    if key_value.startswith("true"):
                        bulk_uploads = True 

                elif key_name.startswith("wget timeout"):
                    try:
                        timeout_sc = int(key_value)
                    except:
                        pass

    else:
        ptt.error("No config file found; using defaults")

    if single_url == "" and len(url_list) == 0:
        url_list.append(input("!!! ---> Input start URL: "))

    return single_url, url_file, quotastring, contributor, confirm_uploads, clean_up, uploaded_pdfs_folder, filetype, mediatype, wget2, user_agent, write_record, upload_record_txtfile, reject_urls, reject_list, url_list, bulk_uploads, timeout_sc



if __name__ == "__main__": 
        total_moved, total_delete = 0, 0
        single_url, url_file, quotastring, contributor, confirm_uploads, clean_up, uploaded_pdfs_folder, filetype, mediatype, wget2, user_agent, write_record, upload_record_txtfile, reject_urls, reject_list, url_list, bulk_uploads, timeout_sc = read_config()
        loading_feedback(quotastring, contributor, clean_up, confirm_uploads, filetype, mediatype, write_record, upload_record_txtfile, uploaded_pdfs_folder, wget2, user_agent, reject_urls, reject_list, url_list, bulk_uploads, timeout_sc)

        while True: 
            url_list, total_urls = check_url_list(reject_urls, reject_list, url_list)
           
            total_bandwidth = str(len(url_list)*int(quotastring[:-1])) # estimated MINIMUM bandwith used. total urls times quota
            ptt.warning("\n[--  -------  --] Total URLs to process: " + str(total_urls) + " | Max Estimated Bandwith = " + total_bandwidth + quotastring[-1].upper() + "B (+10%)")
            
            processed = 0     # count restarted every time a new URL list is used (once per large cycle)

            for url in url_list:
                call_wget(wget2, url, filetype, user_agent, quotastring, reject_list, create.wget_log_file(), timeout_sc)          # Call wget/2 web search
                count = create_ia_csv(contributor, mediatype, find_files(), write_record, filetype, upload_record_txtfile)
                call_ia_cli(confirm_uploads, bulk_uploads, count)                                                # call ia cli to upload
                processed += 1.                   # Tick up the total processed number
                print("\n[--  -------  --] URLs processed: " + str(processed) + " | To-do: " + str(total_urls))
                print("\n[--  -------  --] Estimated bandwidth still needed: " + str((total_urls - 1)*int(quotastring[:-1])) + quotastring[-1].upper() + "B")
                
                total_moved, total_delete = cleanup_def(total_moved, total_delete, clean_up, filetype)
            
            new_url_list(reject_urls, reject_list)



    
