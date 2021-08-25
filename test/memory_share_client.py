from multiprocessing.connection import Client

con_addr = ('localhost', 9999)
conn = Client(con_addr)
while True:
    aa = input()
    conn.send(aa)
conn.close()