from multiprocessing.connection import Listener


pgm_addr = ('localhost', 9999)
pgm_lsn = Listener(pgm_addr)
conn = pgm_lsn.accept()
print(f'conn: {pgm_lsn.last_accepted}')
while True:
    msg = conn.recv()
    if msg == 'colse':
        conn.close()
        break
pgm_lsn.close()

