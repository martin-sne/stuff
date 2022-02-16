#!/usr/bin/python

import re
import sys
import fileinput
from influxdb import InfluxDBClient



def usage():
    print('###########################################################')
    print('#')
    print('e.g.: ' + sys.argv[0] + ' device' + ' ifAlias')
    print('#')
    print('###########################################################')
    sys.exit(1)



def main(device,regexIfalias):

    # JSON Template File
    templateFilePath = '/opt/grafana/templatefiles/'
    templateFile = 'template_panel_type_graph_2sources_ipv6_influx.txt'
    outputFile = 'output.txt'

    # JavaScript Template Datei
    jsInputFilePath = '/opt/grafana/templatefiles/'
    jsInputFile = 'my_jsTemplate.txt'

    # Datei in die das Java Script geschrieben werden soll
    # Path fuer JS Output File
    outputJsFilePath = '/usr/share/grafana/public/dashboards/'
    outputJsFile = 'my_jsConfigFile.js'

    text = read_template_file(templateFilePath,templateFile)
    points = query_influx()
    sorted_data = sort_data(points,device,regexIfalias)
    write_json(sorted_data,text,outputFile,jsInputFilePath,jsInputFile,outputJsFilePath,outputJsFile)



def sort_data(points,device,regexIfalias):
 
    dict = {}

    for item in points:

        #print str(item.values())

        if re.match(r'.*ifAlias.*', str(item.values())) and re.match(r'.*hostname.*', str(item.values())):
            match =  re.match( r'.*hostname=(.*),ifAlias=(.*),ifDescr=(.*).*\'\]', str(item.values()))

            hostname_new =  re.sub('.test.de', '',match.group(1))
            hostname = match.group(1)

            ifAlias = re.sub('\\\\', '', match.group(2))
            ifDescr = match.group(3)

            re_hostname = '.*' + device + '.*'
            re_ifAlias = '.*' + regexIfalias + '.*'


            if re.search(re_hostname, hostname_new, re.IGNORECASE) and re.search(re_ifAlias, ifAlias, re.IGNORECASE):
                #print "match ", hostname, ifAlias, ifDescr
                panel_title = hostname_new  +  " - " + ifDescr + " - " + ifAlias 
                dict[ifDescr] = [panel_title,hostname,ifAlias]  

    return(dict)



def write_json(sorted_data,text,outputFile,jsInputFilePath,jsInputFile,outputJsFilePath,outputJsFile):

    open(outputFile, 'w').close()           # Output File leeren
    file_output = open(outputFile,'a+')

    allIfAlias = []
    id=0



    for k,v in sorted (sorted_data.items()):
        id += 1
        #print(k,v) 
        hostname_new =  re.sub('.test.de', '',v[1])
        panel_title = hostname_new  +  " - " + k + " - " + v[2]
        new_text = text.replace('<PANEL_TITLE>', v[0])
        new_text = new_text.replace('<DESCRIPTION>', v[0])
        new_text = new_text.replace('<HOSTNAME>', v[1])
        new_text = new_text.replace('<IFDESCR>',k)
        new_text = new_text.replace('<IFALIAS>', v[2])
        new_text = new_text.replace('<IN_COLOR>', v[2])
        new_text = new_text.replace('<OUT_COLOR>', v[2])
        new_text = new_text.replace('<ID>', str(id))

        allIfAlias.append(v[2])

        file_output.write(new_text)

    file_output.close()

    # JavaScript Template Datei
    fin = open(jsInputFilePath + jsInputFile, 'r')
    jsConfigFile = fin.read()
    fin.close()
    #print(jsConfigFile)

    # Datei die in der vorangegangenen Schleife anhand Device und Regex erstellt wurde
    rFile = open(outputFile,'r')
    replaceInhalt = rFile.read()
    rFile.close()

    # Daten ersetzen
    new_data = jsConfigFile.replace('<INPUT>',replaceInhalt)


    # Datei in die das Java Script geschrieben werden soll
    open(outputJsFilePath + outputJsFile, 'w').close()           # Output File leeren
    jsOutput = open(outputJsFilePath + outputJsFile, 'w')
    jsOutput.write(new_data)
    jsOutput.close()

    if len(allIfAlias) > 0:
        y = 1
        print('#########################################################################################')
        print('Es wurden ' + str(len(allIfAlias)) + ' Panel vom "' + device + '" fuer Interfaces mit folgendem IfAlias erstellt:')
        for i in range(0, len(allIfAlias)):
            print( str(y) + ': ' + allIfAlias[i])
            y += 1

        print('#########################################################################################')
        print('Gehe zu:')
        print('http://localhost:3000/dashboard/script/my_jsConfigFile.js?orgId=1')
        print('dann auf "Settings" (ganz oben das Zahnrad)')
        print('und speichere dein erzeugtes Dashboard unter einem anderen Namen mittels "Save as"')

    else:
        print('Es konnten keine Panel erstellt werden, siehe unten!')


    
def query_influx():

    measurement = "interface"
    client = InfluxDBClient(host='localhost', port=8086)
    client.switch_database('telegraf')
    results = client.query('SHOW SERIES')
    points = results.get_points()
    return(points)




def read_template_file(templateFilePath,templateFile):

    try:
        panelTemplate = open(templateFilePath + templateFile, 'r')

    except FileNotFoundError:
        print('Files sind nicht vorhanden, versuchen Sie es nochmal!')
        sys.exit()

    except:
        print('Es trat ein unbestimmter Fehler auf, versuchen Sie es nochmal!')
        sys.exit()

    text = panelTemplate.read()
    panelTemplate.close()
    return(text)



if __name__ == '__main__':
    if len(sys.argv) == 3:
        device = sys.argv[1]
        regexIfalias = sys.argv[2]
        main(device,regexIfalias)
    elif len(sys.argv) == 2:
        device = sys.argv[1]
        regexIfalias = '.*'
        main(device,regexIfalias)
    elif len(sys.argv) < 2:
        print('Zu wenig Argumente!')
        usage()
    else:
        usage()
