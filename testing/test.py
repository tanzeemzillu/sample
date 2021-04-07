import os

log = open("logs.txt","w+")
fileDir = os.path.dirname(os.path.abspath(__file__))


def checkresponse(api, no_of_request):

    for i in range(no_of_request):
        os.system("curl -I {}".format(api))
    nginx_container_id_command = "docker ps | grep nginxlocal | awk '{print $1}'"
    nginx_container_id= os.popen(nginx_container_id_command).read()
    logs= os.popen("docker logs -t {}".format(nginx_container_id)).read()
    print(str(logs))
    log.write(str(logs))


def calculatetraficdistribution():

    total_no_of_request = 0
    no_of_response_from_java_app = 0
    no_of_response_from_go_app = 0

    f = open("{}/logs.txt".format(fileDir), 'r')
    for line in f:
        total_no_of_request +=1

        if ':8081' in line:
            no_of_response_from_java_app +=1
        elif ':8082' in line:
            no_of_response_from_go_app +=1

    print("total no of request is {}".format(total_no_of_request))
    print("total no of response from go app are {}".format(no_of_response_from_go_app))
    print("total no of response from java app are {}".format(no_of_response_from_java_app))

    # Calculate the percentage

    response_from_java_in_percent = (no_of_response_from_java_app * 100.0)/total_no_of_request
    response_from_go_in_percent = (no_of_response_from_go_app * 100.0)/total_no_of_request

    print("Result in percentage \n Response from Golang app {go} \n Response from Java app {java}".format(go=response_from_go_in_percent, java=response_from_java_in_percent))


if __name__=='__main__':

    checkresponse('http://application.net/', 100)
    checkresponse('http://application.net/hotels', 100)
    checkresponse('http://application.net/ready', 100)
    checkresponse('http://application.net/metrics', 100)
    checkresponse('http://application.net/health', 100)
    calculatetraficdistribution()
