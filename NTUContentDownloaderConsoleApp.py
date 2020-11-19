import getpass
import os
import pathlib
import re
import ssl
import sys
import time
import urllib

import requests
from bs4 import BeautifulSoup
from selenium import webdriver  # 
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm

#Enter Credentials information here

username = "WTENG002@student.main.ntu.edu.sg"
password = ""
CHUNK_SIZE = 1024 * 1024 # 1MB

NEWLY_DOWNLOADED_FILES = []

options = Options()
options.add_argument("--headless")
options.add_argument('user-agent="Mozilla/5.0 (iPod; U; CPU iPhone OS 2_1 like Mac OS X; ja-jp) AppleWebKit/525.18.1 (KHTML, like Gecko) Version/3.1.1 Mobile/5F137 Safari/525.20"')
driver = webdriver.Chrome(r'C:\Users\wilso\\Documents\chromedriver.exe', options=options)
driver.set_window_size(3000, 3000)

CWD = os.getcwd()
MOTHER_LINK = r'https://ntulearn.ntu.edu.sg'
global requests_session, response # requests session
requests_session = requests.Session() # requests session

def check_url(url):
    if MOTHER_LINK not in url:
        url = MOTHER_LINK + url
    return url

def print_level(level):
    if level >= 1:
        print("|_", end="")
        for _ in range(level-1):
            print("._", end="")
        print(" ", end="")

def download_file(url, save_dir):
    save_dir = save_dir.replace(":", "")
    if pathlib.Path(save_dir).is_file():
        print("[!file-exist]")
        return (False, save_dir)
    if not os.path.exists(os.path.dirname(save_dir)):
        os.makedirs(os.path.dirname(save_dir))
    with requests_session.get(url, stream=True) as response:
        with open(save_dir, 'wb') as handle:
            for data in tqdm(response.iter_content(chunk_size=CHUNK_SIZE)): # 1MB
                handle.write(data)
    return (True, save_dir)

def navigate_folder(href, folder_name, path_name, level=1):
    curr_url = driver.current_url
    driver.get(href)

    soup = BeautifulSoup(driver.page_source,features="lxml")
    containerHTML = soup.findAll("ul", {"class": "contentList"})[0]
    anonymous_elements = re.findall("anonymous_element_\d+",str(containerHTML))
    ContentNames = BeautifulSoup(str(containerHTML),features="lxml").find("ul").findAll("li", recursive=False)
    print("Parent Length : ", len(ContentNames))

    ContentNamesList = []
    for (index, contentName) in enumerate(ContentNames):
        children = BeautifulSoup(str(contentName),features="lxml").findAll("a", href=True)
        # print(f"Children len : {len(children)}")
        for child in children:
            name = child.get_text()
            if name == "":
                print("[!EMPTY CHILD]")
                continue
            ContentNamesList.append(name)
            url = check_url(child['href'])
            if "/webapps/blackboard/content/listContent.jsp" in child['href']:
                # is folder
                navigate_folder(url, name, os.path.join(path_name, folder_name), level=level+1)
            elif "/bbcswebdav/" in child['href']:
                # is file
                print_level(level)
                print(f"{index + 1}) {name} ")
                success = download_file(url, os.path.join(path_name, folder_name, name))
                if (success[0]): NEWLY_DOWNLOADED_FILES.append(success[1])
    driver.get(curr_url)


while True:
    # if (password is None) or (username is None):
    #     username = input("Please input ntulearn username:   ")
    #     password = getpass.getpass('Password:')
    #     errorCheck = input("Are you sure the information are correct? press n to input again, press any other key to continue..")
    #     if (errorCheck == "n"):
    #         continue

    print("\n Loading... \n\n")
    login_url = "https://ntulearn.ntu.edu.sg/webapps/login/"

    driver.get(login_url)
    time.sleep(2)
    # driver.implicitly_wait(2)
    driver.find_element_by_id("userNameInput").send_keys(username)
    driver.find_element_by_id("passwordInput").send_keys(password)
    driver.find_element_by_id("submitButton").click()
    driver.implicitly_wait(2)
    try:
        driver.find_element_by_id("agree_button").click()
    except:
        pass

    cookies = driver.get_cookies()
    for cookie in cookies:
        requests_session.cookies.set(cookie['name'], cookie['value'])

    html = driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
    time.sleep(1)
    lst = re.findall("termCourses",driver.page_source)
    mainCourseLink = driver.current_url
    soup = BeautifulSoup(driver.page_source,features="lxml")
    mydivs = soup.findAll("ul", {"class": "portletList-img courseListing coursefakeclass u_indent"})

    if (len(mydivs) == 0):
        print("Log in information not correct, try again")
        username = None
        password = None
        continue
    else:
        break

while True:
    courseLst = []
    NEWLY_DOWNLOADED_FILES = []

    for div in mydivs:
        soup = BeautifulSoup(str(div),features="lxml")
        myList = soup.findAll("li")

        for lst in myList:
            course = BeautifulSoup(str(lst),features="lxml").findAll("a")
            course = course[0].get_text()
            courseLst.append(course)

    print(f"Welcome to NTU Lecture Content Downloader (CWD : '{CWD}')")
    print("\n   Please Select the Subject: ")
    for (index,item) in enumerate(courseLst):
        print(str(index + 1) + ") " + item)
    
    download_all_int = index + 2
    print("--------------------------------")
    print(f"{download_all_int}) --- Download All")

    print("\n\n")

    while True:
        userChoice = (input("Please enter the course number: "))
        try:
            all = False
            userChoiceInt = int(userChoice)
            if (userChoiceInt <= 0 or userChoiceInt > len(courseLst)+1):
                raise IndexError
            if userChoiceInt == download_all_int:
                userChoiceCourseLst = courseLst
            else:
                userChoiceCourseLst = [str(courseLst[userChoiceInt - 1])]
            print(userChoiceCourseLst)
            break
        except ValueError:
            print("Please input only digits, not any other character: \n")
            continue
        except IndexError:
            print("Invalid Input, the choice is not listed, please try again: \n")
            continue
  
    for course in userChoiceCourseLst:
        skip = False
        print(f"Curr course : {course}")
        element = driver.find_element_by_link_text(course)
        driver.execute_script("arguments[0].click();", element)

        try:
            element = driver.find_element_by_partial_link_text("Content")
            driver.execute_script("arguments[0].click();", element)
            time.sleep(1)
            # driver.implicitly_wait(2)
        except:
            try:
                print("[!INFO] 'Content' match failed. Trying for 'material' match...")
                driver.switch_to.window(driver.window_handles[0])
                driver.get(mainCourseLink)
                element = driver.find_element_by_link_text(course)
                driver.execute_script("arguments[0].click();", element)
                time.sleep(1)
                
                element = driver.find_element_by_partial_link_text("material")
                driver.execute_script("arguments[0].click();", element)
                time.sleep(1)
                # driver.implicitly_wait(2)
            except:
                skip = True
                print("[!INFO] No content to download.\n")
                driver.switch_to.window(driver.window_handles[0])
                driver.get(mainCourseLink)

        if (not skip):    
            soup = BeautifulSoup(driver.page_source,features="lxml")
            containerHTML = soup.findAll("ul", {"class": "contentList"})
            if len(containerHTML) == 0: 
                print("[!INFO] No content to download.\n")
                driver.switch_to.window(driver.window_handles[0])
                driver.get(mainCourseLink)
                continue
            containerHTML = containerHTML[0]
            anonymous_elements = re.findall("anonymous_element_\d+",str(containerHTML))
            print("\n")
            print("      List of Content      ")
            print("=============================")
            ContentNames = BeautifulSoup(str(containerHTML),features="lxml").find("ul").findAll("li", recursive=False)
            print("Parent Length : ", len(ContentNames))
            ContentNamesList = []
            for (index, contentName) in enumerate(ContentNames):
                children = BeautifulSoup(str(contentName),features="lxml").findAll("a", href=True)
                for child in children:
                    name = child.get_text()
                    print(f"{index + 1}) {name} ")
                    ContentNamesList.append(name)
                    url = check_url(child['href'])
                    if "/webapps/blackboard/content/listContent.jsp" in child['href']:
                        # is folder
                        navigate_folder(url, name, course.replace(":", ""))
                    elif "/bbcswebdav/" in child['href']:
                        # is file
                        success = download_file(url, os.path.join(course, str(name)).replace(":", ""))
                        if (success[0]): NEWLY_DOWNLOADED_FILES.append(success[1])

            print("--------------------------------")
            print(f"[!INFO] Download finished for [{course}]\n")
            time.sleep(2)
            driver.switch_to.window(driver.window_handles[0])
            driver.get(mainCourseLink)

    if NEWLY_DOWNLOADED_FILES:
        print(f"\n================= New Files ({len(NEWLY_DOWNLOADED_FILES)}) =================")
        print(*NEWLY_DOWNLOADED_FILES, sep="\n")
        print()

    # print(ContentNamesList)

    # userContinueChoice = input("Do u want to download more files? \nPress y to continue, press any other key to quit\n")
    # if (userContinueChoice != "y" and userContinueChoice != "Y"):
    #     print("Bye")
    #     break

    driver.switch_to.window(driver.window_handles[0])
    driver.get(mainCourseLink)

driver.quit()