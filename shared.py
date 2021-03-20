bDoneStart = False
config = []
commands = {}
cv = ["00", "40", "80", "FF"]   # colours available on Virpil devices
cfFile = "conf.json"
dCmd = "1"                      # default command
fName = "Journal.*.log"
langFile = "lang.$.json"
langFileName = langFile.replace("$", "*")

def expandCommands(j, debug=False):
    # expand commands
    c = []
    for a in j[ 'commands' ]:
        if len( a ) == 1:
            c.append( a[ 0 ] )
        else:
            p = len( str( a[2 ] ) )
            for d in range( a[ 1], a[ 2 ]+1 ):
                c.append( a[ 0 ].replace( '{d}', (('0' * p) + str(d) )[-p:] ))
    if debug:
        print( c )
    return c

def loadLanguages(debug=False):
    import glob
    import json

    languages = {}

    langFileList = sorted( glob.glob(f"{langFileName}") )
    
    for fl in langFileList:
        try:
            f = open(fl,"r", encoding="utf-8")
        except:
            continue
        txt = f.read().replace('\n', '')
        f.close()
        j = json.loads( txt )
        j[ 'commands' ] = expandCommands( j )
        languages[ j[ 'code' ]] = j
        if debug:
            print(languages[ j[ 'code' ]])
    return languages

def main():
    print( f'{loadLanguages()}\n' )

if __name__ == '__main__':
    main()
