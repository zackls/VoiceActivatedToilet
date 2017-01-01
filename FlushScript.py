from firebase import firebase, FirebaseAuthentication
import time
import subprocess, os, signal
import sys

#database info
DATABASE_URL = os.environ['DATABASE_URL']
DATABASE_KEY = os.environ['DATABASE_KEY']
db = firebase.FirebaseApplication(DATABASE_URL)
db.authentication = FirebaseAuthentication(DATABASE_KEY, '')

if sys.argv[1] == '-c' and len(sys.argv) == 2:

    #how often to check for new keywords, in seconds
    DATABASE_CHECK_TIMER = 60

    #path to voice recognition config file
    CONFIG_FILE = 'PiAUISuite/VoiceCommand/commands.conf'

    currentKeywords = None
    listener = None

    #periodically check database for new keywords
    while True:
        try:
            databaseKeywords = set(map(lambda x: x.encode('ascii'), db.get('', None).keys()))
        except Exception as e:
            print str(e)
            databaseKeywords = currentKeywords
        
        if currentKeywords != databaseKeywords:
            if currentKeywords:
                print 'Flush keywords changed, changing config and restarting listener'
            currentKeywords = databaseKeywords

            #kill previous process if necessary
            if listener:
                os.killpg(os.getpgid(listener.pid), signal.SIGTERM)

            #rewrite config file
            with open(CONFIG_FILE, 'w') as config:
                for phrase in currentKeywords:
                    config.write('~' + phrase + '==flush ' + phrase.replace(' ', '_') + '\n')

            #start listening process
            listener = subprocess.Popen(['voicecommand -c'], stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
            
        time.sleep(DATABASE_CHECK_TIMER)

elif sys.argv[1] == '-p' and len(sys.argv) == 3:
    #flush toilet
    
    #update database
    phrase = sys.argv[2].replace('_', ' ')
    try:
        count = db.get('', phrase)
        count = count + 1 if count else 1

        result = db.put('', phrase, count)

        print 'Keyword "' + phrase + '" has been used ' + str(result) + ' times.'
    except Exception as e:
        print str(e)
else:
    print 'Invalid arguments, valid options include "-c" to begin continuous listener, and "-p <phrase>" to flush with a certain phrase'
