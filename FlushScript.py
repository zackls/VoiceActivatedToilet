from firebase import firebase, FirebaseAuthentication
import time
import subprocess, os, signal


#how often to check for new keywords, in seconds
DATABASE_CHECK_TIMER = 60

#database info
DATABASE_URL = os.environ['DATABASE_URL']
DATABASE_KEY = os.environ['DATABASE_KEY']

#path to voice recognition config file
CONFIG_FILE = 'PiAUISuite/VoiceCommand/commands.conf'

db = firebase.FirebaseApplication(DATABASE_URL)
db.authentication = FirebaseAuthentication(DATABASE_KEY, '')
currentKeywords = None
listener = None

#periodically check database for new keywords
while True:
    try:
        databaseKeywords = set(map(lambda x: x.encode('ascii'), db.get('', None).keys()))
    except:
        print 'Database connection failed'
        databaseKeywords = currentKeywords
    
    if currentKeywords != databaseKeywords:
        if currentKeywords:
            print 'Flush keywords changed,changing config and restarting listener'
        currentKeywords = databaseKeywords
        print currentKeywords

        #kill previous process if necessary
        if listener:
            os.killpg(os.getpgid(listener.pid), signal.SIGTERM)

        #rewrite config file
        with open(CONFIG_FILE, 'w') as config:
            for phrase in currentKeywords:
                config.write('~' + phrase + '==flushtoilet ...\n')

        #start listening process
        listener = subprocess.Popen(['voicecommand -c'], stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        
    time.sleep(DATABASE_CHECK_TIMER)


#flush toilet
def flushToilet(phrase):
    #update database
    try:
        count = db.get('', phrase)
        count = count + 1 if count else 1

        result = db.put('', phrase, count)

        print 'Keyword "' + phrase + '" has been used ' + str(result) + ' times.'
    except:
        print 'Database connection failed'
