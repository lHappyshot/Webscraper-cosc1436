

#! ---------------------------------------------------------------------------- #
#!                                 Prerequisites                                #
#! ---------------------------------------------------------------------------- #

#! pip install mysql-connector-python
#! pip install beautifulsoup4
#! pip install requests
#! pip install tabulate
#! pip install twilio
#! npm install twilio-cli -g
#! pip install pandas
#! pip install numpy==1.19.3
    #TODO: numpy==1.19.3 IS A WORKAROUND FOR A NunPy ISSUE CAUSED BY WINDOWS 10 VERSION 2004 --11/26/2020

#* ---------------------------------------------------------------------------- #
#*                               Modules and APIs                               #
#* ---------------------------------------------------------------------------- #

import os
import io # python 2 compatible
from os.path import basename
from datetime import datetime
from datetime import time
from datetime import date
import re
import requests
from tabulate import tabulate
import smtplib
import mysql.connector
from bs4 import BeautifulSoup
from twilio.rest import Client
import pandas as austin


#* ---------------------------------------------------------------------------- #
#*                                Root Variables                                #
#* ---------------------------------------------------------------------------- #

time = str(datetime.now().strftime("%d-%m-%y %H.%M")) # today's date
timeCount = datetime.now() # today's date with mins and secs as an object

mainURL = 'https://dealsea.com/' # used to combine with individual deal links
websiteSource = "https://dealsea.com/Laptops-Desktops-completeTablets/b?node=3001" # website to be scraped

#* ---------------------------------------------------------------------------- #
#*                                  Credentials                                 #
#* ---------------------------------------------------------------------------- #

twilioCredKeyOpen = open('twilioKEY.txt', 'r')
twilioCredKey = twilioCredKeyOpen.readline()
twilioCredKeyOpen.close()
databasePassOpen = open('sqlPASSWORD.txt', 'r')
databasePass = databasePassOpen.readline()
databasePassOpen.close()
emailPassOpen = open('emailPASSWORD.txt', 'r')
emailPass = emailPassOpen.readline()
emailPassOpen.close()
emailAddressOpen = open('emailADDRESS.txt', 'r')
emailAddress = emailAddressOpen.readline()
emailAddressOpen.close()
twilioNumberOpen = open('twilioNUMBER.txt', 'r')
twilioNumber = twilioNumberOpen.readline()
twilioNumberOpen.close()
receiverNumberOpen = open('receiverNUMBER.txt', 'r')
receiverNumber = receiverNumberOpen.readline()
receiverNumberOpen.close()
twilioAuthenticateOpen = open('twilioAUTH.txt', 'r')
twilioAuthenticate = twilioAuthenticateOpen.readline()
twilioAuthenticateOpen.close()

#* ---------------------------------------------------------------------------- #
#*                                   Functions                                  #
#* ---------------------------------------------------------------------------- #

#? Website Data Function - used to receive and decode the desired website. Additionally, the
#? use of the pageNumber import is used to navigate to the next page of the website to extract
#? more information.

def websiteData(pageNumber, websiteSource):
    print('Receiving data from website...')
    try:
        if pageNumber == 1:
            # receive website data
            response = requests.get(websiteSource)
            print('Website source code retrieved.')
            print()
            return response
        else:
            # receive website data for the next pages
            websiteSourcedPaged = websiteSource + '&page=' + pageNumber
            response = requests.get(websiteSourcedPaged)
            print('Website source code retrieved.')
            print()
            return response
    except:
        print('Failed to extract website source code.')
        print()

#* ---------------------------------------------------------------------------- #

#? Scraper Function - main function to the program; used to extract information from the web,
#? separate the information, categorize information, and place it inside a list object.

def scrapeEverything(response, mainURL):
    print('Begining to parse website...')
    soup = ''
    try:
        soup = BeautifulSoup(response.content, "html.parser") # text rich html decode
        print('Website successfully parsed.')
        print()
    except:
        print('Website parseing failed.')
        print()

    completeTable = [] # start of the deal's core list
    simpleTable = [] # start of the simplified deal's core list

    # loop to sort categories in to a list
    try:
        print('Begining to scrape website...')
        for d in soup.findAll('div', class_='dealbox'):

            # Get title of the deal
            foundTitle = d.findAll('a')
            title = str(foundTitle[1].find(text=True))

            # Get price of the deal from the main vendor, if it exists
            price = 'No price.'
            priced = ''
            if '$' in title:
                price = title[title.find("$"):].split()[0]
                priced = price
            else: # if price is not applicable, skip and continue
                pass

            # Get the primary vendor
            mainVendor = str(foundTitle[2].find(text=True))
            if mainVendor == 'shop All':
                mainVendor = ''

            # Get deal link that takes you to the deals page and post
            dealLink = mainURL + d.a.get('href')

            # Get other vendor options for the deal
            vendorOptions = d.findAll(href=re.compile(r"\/j\/4\/\?pid\="))
            allVendorOptions = {}
            for v in vendorOptions:
                mainVendor = str(v.find(text=True))
                # prevent duplicate vendor links
                if mainVendor != 'Here': # filters false vendor names
                    vendorLink = mainURL + str(v['href'])
                    if mainVendor not in allVendorOptions:
                        allVendorOptions[mainVendor] = []
                    allVendorOptions[mainVendor].append(vendorLink)
                elif mainVendor == 'Here': # skips false vendor names
                    pass

        # ALTERNATIVE METHOD - less efficient
            #// dealDetails = d.findAll(class_='dealcontent')
            #// for h in dealDetails:
            #//     dealDetails = str(h.getText())
            #//     if '\r' in dealDetails:
            #//         dealDetails = dealDetails.split('\r', 1)[0]
            #//     elif '\n' in dealDetails:
            #//         dealDetails = dealDetails.split('\n', 1)[0]
            #//     elif '›' in dealDetails:
            #//         dealDetails = dealDetails.split('›', 1)[0]
            #//     else:
            #//         pass
            #//     print(dealDetails)\

            # Get deal details, if it exists (more efficient)
            if d.findAll('div', {'class':'posttext'}):
                dealDetails = d.findAll('div', {'class':'posttext'})[0].text
                if '\n' in dealDetails: # remove unnecessary empty lines
                    dealDetails = dealDetails.rsplit('\n', 1)[0]
            else: # catch deals with no details
                dealDetails = 'No details about deal.'

            # Add information to the list
            completeTable.append([title, price, dealLink, allVendorOptions, dealDetails])
            simpleTable.append([title, priced, mainVendor, dealLink, dealDetails])

        print('Website scrape successful.')
        print()
        return completeTable, simpleTable
    except:
        print('Website scraper failed.')
        print()

#* ---------------------------------------------------------------------------- #

#?  Save File Function - A simple function that open a file by name, and write information
#? to that file by using data as input for the function.

def saveDataToFile(table, time):
    print("Creating new .txt file...")
    dataFileName = time + ' Deals time!.txt'
    headers = ["Title", "Price", "dealLink", "Vendors", "deal Details"]
    # io. for py 2 compatibility
    with io.open(dataFileName, 'w', encoding='utf-8') as scraper_table:
        # write table .txt file
        scraper_table.write(tabulate(table, headers, tablefmt='fancy_grid')) 
    print("New .txt file created.")
    print()

#* ---------------------------------------------------------------------------- #

#?  Open File Function - A simple function that open a file by name, and reads information
#?  of that file.

def openDataOfFile(table, time):
    dataFileName = time + ' Deals time!.txt'

    isExist = os.path.exists(dataFileName) # check if file exists
    try:
        if isExist == True: # if exists open and return it to use
            print("Existing .txt file found.")
            myFile = open(dataFileName, 'r', encoding='utf8') # encoder must be specified
            myFile.readlines()
            myFile.close()
            print("Existing .txt file opened.")
            print()
            return myFile

        elif isExist == False: # runs if file doesn't exists
            print("Existing .txt file with today's date not found.")
            print()
            newFile = saveDataToFile(table, time) # makes new file
            return newFile
    except:
        print('Error identifying data existence. Program failure.')
        print()

#* ---------------------------------------------------------------------------- #

#?  Status Update 1 Function - A simple function that displays a message showing how
#? many deals there are, and displays wether a table was saved successfully.

def statusUpdate1(table):
    print('There are', str(len(table)), 'deals found.')
    print()

#* ---------------------------------------------------------------------------- #

#? Table to Text Function - Serves the propose to transpose a list object (table) 
#? to a formatted text file.

def tableToTextConverter(table, time):
    
    textFileName = time + 'DealstextExport.txt'

    with open(textFileName, 'w') as scraper_table:
        textFile = scraper_table.write(tabulate(table))
        textFile.close()
    return textFile

#* ---------------------------------------------------------------------------- #

#?  Display Deals Function - A simple function that print the deals found to the
#? terminal in a pretty and organized fashion for beautiful viewing.

#// - try striping list brackets of inner lists


def displayDealsInTableOutput(prettyTable):
    for i in prettyTable: # pull the inner table
        for j in i: # pull category from inside the current inner table
            print(j) # print current element from inside the inner list

#* ---------------------------------------------------------------------------- #

#? Send to Database Function - a list can be send to a database with a set category
#? of columns using the pandas library.

#! NOT USEABLE - CANNOT SEND TO DATABASE.
def sendToDatabase(table, connection):
    try:
        print('Sending data to database...')
        dataCursor = connection.cursor()
        dataCursor.execute('CREATE TABLE deals (title, price, dealLink, allVendorOptions, dealDetails)')
        dataCursor.commit()

        numOfDeals = len(table)
        columns = ['title', 'price', 'dealLink', 'allVendorOptions', 'dealDetails']
        sqlReady = austin.DataFrame(table, columns=columns)

        print(sqlReady)
        connection.close()
        print('Data sent to database.')
        print()
    except:
        print('Error: Data to database not send.')
        print()

    # for i in table[0:numOfDeals]:
    #     sql = "INSERT INTO `Dealsea` (`title`, `link`, `content`, `vendor`) VALUES (%s, %s, %s, %s);"
    #     val = (i.getTitle(),i.getLink(),i.getContent(),i.getVendor())
    #     director.execute(sql, val)

        # databaseConnector.commit()

#* ---------------------------------------------------------------------------- #

#? Connect Database Function - using the login credentials, this function will connect
#? to a mysql based database.

def connectToDatabase(databaseKey):
    print('attempting to connect to database...')
    try:
        connection = mysql.connector.connect(
            host = 'localhost',
            user = 'root',
            password = databaseKey,
            database = 'all_deals')

        print("Connection successful.")
        print()
        return connection
    except:
        print('Database connection error.')
        print()

#* ---------------------------------------------------------------------------- #

#? Deals extractor Function - used to take the large all-in-one deals list and  
#? take one deal set at a time for adequate deals display via text and email.

def dealsExtractor(table, numberOfDeals):
    num = 0
    info = 0
    dealsTable = [] # master deal list with all captured deals
    while num < numberOfDeals:
        tableInstance = table[num]
        info = [] # empty list and location of current deal
        for h in tableInstance:
            if h == dict: # take first vendor from dictionary of vendors
                for key, value in h.items():
                    info.append(value) # add first vendor empty list
                    #// info.append('\n\n')
            elif h == 'No Price.': 
                pass # skip if price was not found
            else:
                info.append(h) # all other info add to list
                #// info.append('\n\n')
        dealsTable.append([info])
        num += 1 # while loop control and next deal
    else:
        print('All deal counts have been extracted.')
        print()
        return dealsTable

#* ---------------------------------------------------------------------------- #

#? Text Message Function - using the twilio api, this function send a text message
#? to a sender with deals.

def textMessage(twilioCredKey, twilioNumber, receiverNumber, twilioAuthenticate, table):
    client = 0
    account_sid = twilioCredKey
    auth_token = twilioAuthenticate

    # retrieve 1st deal
    singleDealTitle = table[0]
    singleDealLink = table[3]

    try:
        print('connecting to text messaging service...')
        client = Client(account_sid, auth_token) # connect to twilio rest.API service
    except:
        print('connection to text messaging service failed.')

    try:
    #! CODE NOT AVAILABLE TO TWILIO TRIAL ACCOUNTS. PLEASE UPGRADE TO PAID ACCOUNT TO USE.
        print('checking if phone number is verified...')
        toPhoneNumber = str(validatedNumber('''Please enter receiver of the text message.
Input a 10 digit phone number(no spaces or dashes): ''')) # get phone number from user
        print()

        outgoing_caller_ids = client.outgoing_caller_ids.list(limit=20) # list of verified numbers

        if toPhoneNumber not in outgoing_caller_ids: # cross check inputted number with verified list
            validation_request = client.validation_requests \
                .create( # if not present, add phone number to verified list after validation
            friendly_name=validatedString('Please enter what to call this new number: '),
                phone_number='+1' + str(toPhoneNumber))

            print(validation_request.friendly_name) # validation code
    except:
        print('Error: Twilio account is in trial.')
        print('Please upgrade to utilize validation of phone number with rest API.')
        print()

    try:
        print('sending message...')
        message = client.messages.create( # send message command with details
            to = '+1' + str(receiverNumber),
            from_ = str(twilioNumber),
            body = singleDealTitle + '\n' + '\n' + singleDealLink)

        print("message send.") # display body of the message
        print()
    except:
        print('Error sending message.')
        print()

#* ---------------------------------------------------------------------------- #

#? Validated Number Function - validates and makes sure that the number is useable.

def validatedNumber(statement):
    while True:
        try:
            rawNumber = int(input(statement))
        except ValueError:
            print('Response is not a number only. try again.')
            print()
            continue
        else:
            break

    return rawNumber

#* ---------------------------------------------------------------------------- #

#? Validated String Function - validates and makes sure that the string is useable.

def validatedString(statement):
    while True:
        try:
            rawString = str(input(statement))
        except ValueError:
            print('Response is not valid. try again.')
            print()
            continue
        else:
            break

    return rawString

#* ---------------------------------------------------------------------------- #

#? Validated Statement Function - validates and makes sure that the statement is useable.

def validatedStatement(statement):
    rawStatement = input(statement)
    while True:
        try:
            if rawStatement.isnumeric == True:
                print('Statement cannot be a number')
                rawStatement = input(statement)
            elif rawStatement.isalnum() == True:
                print('Statement cannot be a number')
                rawStatement = input(statement)
            elif rawStatement == '':
                print('Statement cannot be a empty')
                rawStatement = input(statement)
            elif any(char.isdigit() for char in rawStatement) == True:
                print('Statement cannot be a number')
                rawStatement = input(statement)
            else:
                break
        except ValueError:
            print('Statement is invalid')
            rawStatement = input(statement)
    return rawStatement

#* ---------------------------------------------------------------------------- #

#? Time Tracker Function - determines how long it took the code to execute in
#? seconds and milliseconds. 

def elapseTime(time):
    # action code
    timeCounted = datetime.now()
    elapsed_time = timeCounted - time
    print('total program excecuting time: ', elapsed_time.seconds, '.', elapsed_time.microseconds, ' seconds', sep='')
    print()
    return elapsed_time

#* ---------------------------------------------------------------------------- #

#? Email Message Function - using SMTP library, this function sends an email with
#? information of the current deals by email with the chosen server and 
#? corrent email/ password credentials to send from.

def emailMessage(emailAddress, emailKey, table):
    print('Starting email service...')
    numOfDeals = validatedNumber("please enter number of deals to email: ")
    extractedDeal = dealsExtractor(table, numOfDeals)

    #// dealNameCount = str(1)
    #// while True:
    #//     for i in extractedDeal:
    #//         title  = i[0]
    #//         price = i[1]
    #//         dealLink = i[2]
    #//        vendor = i[3]
    #//         details = i[4]
    #//         'deal' + dealNameCount = title + price + dealLink + vendor + details
    #//        dealNameCount += 1

    sendFrom = 'hapcoscdemo@gmail.com'
    sendTo = str(validatedStatement('Please enter receiver of the email: '))

    subject = "Subject: Best deals of the day"
    body = extractedDeal

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(emailAddress, emailKey)

            subject = "Subject: Best deals of the day"
            body = str(extractedDeal)
            msg = f'Subject: {subject}\n\n{body}'

            smtp.sendmail(sendFrom, sendTo, msg)

            print('Email message send.')
            print()
    except:
        print('error: Connection to e-mail server failed or unable to send email.')
        print()

#? ---------------------------------------------------------------------------- #
#?                                 Main Program                                 #
#? ---------------------------------------------------------------------------- #

print('Webscraper program initiated.')
print()
webData = websiteData(1, websiteSource)
table, simTable = scrapeEverything(webData, mainURL)
statusUpdate1(table)
prettyTextTable = openDataOfFile(table, time)
dataBaseObject = connectToDatabase(databasePass)
sendToDatabase(table, dataBaseObject)
emailMessage(emailAddress, emailPass, simTable)
textMessage(twilioCredKey, twilioNumber, receiverNumber, twilioAuthenticate, simTable[0])
end = elapseTime(timeCount)
print('program complete. Thank you for using our Webscraper.')
print()