import pika
import uuid
import pprint
import re
from io import StringIO, BytesIO
from lxml import etree
from neo4jrestclient.client import GraphDatabase
gdb = GraphDatabase("http://localhost:7474/db/data/", username="neo4j", password="S3r3ngu3")

import xml.etree.ElementTree as ET

class rpcget(object):
    def __init__(self):

        credentials = pika.PlainCredentials('admin', 'admin')
        parameters = pika.ConnectionParameters('7.188.101.16',
                                               5672, '/',
                                               credentials)

        self.connection = pika.BlockingConnection(parameters)

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, router, rpc):

        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='NETCONF_ASYNC_BROKER',
                                   routing_key='NETCONF.request.' + router,
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue,
                                       correlation_id=self.corr_id,
                                   ),
                                   body=rpc)
        while self.response is None:
            self.connection.process_data_events()
        return (self.response)

    def convert_xml(var, rpcs):
        # global rpcs
        # print '------------------------------------------------------------------------------'
        # print 'BIENVENIDO A LA FUNCION DE CONVERSION A XML'
        f = StringIO(rpcs.replace('xmlns=', 'asd='))
        config = etree.parse(f)
        xml = config.xpath('//isis-adjacency-information/isis-adjacency/')
        return xml


def main():
    # var = '//isis-adjacency-information/isis-adjacency/'
    rpc = '''<rpc>
        <get-interface-information>
                <descriptions/>
        </get-interface-information>
        </rpc>'''
    rpcs = rpcget()
    servicios = []
    print("=============")
    router = input("Ingrese Equipo: ")
    regex = re.compile(r"(?<!\d)\d{5}(?!\d)")
    responses = rpcs.call(router, rpc)
    answer = responses.decode("utf-8")
    f = StringIO(answer.replace('xmlns=', 'asd='))
    print(f)
    print("====")
    config = etree.parse(f)
    xml = config.xpath('result/rpc-reply/interface-information/logical-interface')
    ifaces = []
    transitos = []
    contadortransitos = 0
    contadorconfigurados = 0
    for i in xml:
        for j in i:
            if 'description' in j.tag:
                    for match in regex.findall(j.text):
                        if match != [] and match not in servicios:
                            servicios.append(match)
                            contadorconfigurados = contadorconfigurados +1

    with open('query.txt', 'rt') as texto:
            q = texto.read()
            q = q[:77] + router + q[89:]
            results = gdb.query(q, data_contents=True)
            marta = str(results.rows)
            for match in regex.findall(marta):
                if match != [] and match not in transitos and match not in servicios:
                    transitos.append(match)
                    contadortransitos=contadortransitos+1

    s = ','.join(map(str, servicios))
    strtransit = ','.join(map(str, transitos))

    s = s.replace('[', '').replace(']', '').replace("'", '').replace("55259", '').replace("18747", '').replace(",,", ',').replace(",,", ',').replace(" ", '').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace("15259", '').replace("10002", '').replace(",,", ',')
    strtransit = strtransit.replace('[', '').replace(']', '').replace("'", '').replace("55259", '').replace("18747", '').replace(",,", ',').replace(",,", ',').replace(" ", '').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace(",,", ',').replace("15259", '').replace("10002", '').replace(",,", ',').replace(",,", ',').replace("15002", '').replace("10001", '')

    print("Son %s servicios configurados en el router y %s transitos" % (contadorconfigurados, contadortransitos))
    print("Configurados:", s)
    print("Transitos:   ",strtransit)

    print("C'ya at Disney, my friend")

if __name__ == '__main__':
    main()
