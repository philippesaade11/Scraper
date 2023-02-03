import subprocess
import re
import time

while True:
    output = subprocess.check_output(['docker', 'stats', '--no-stream'])
    output = output.decode().strip().split('\n')
    with open('output.csv', 'a+') as f:
        for i in range(1, len(output)):
            f.write(re.sub('\s{2,}', ',', output[i]) + f',{time.time()}\n')
