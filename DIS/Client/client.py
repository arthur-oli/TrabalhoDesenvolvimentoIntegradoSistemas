import socket as st
import random
import time
import pickle
import pandas as pd
from numpy import sqrt

SERVER = 'localhost'
PORT = 5050
ADDR = (SERVER, PORT)

possible_users = ["Arthur", "Gabriel", "Mistério"]
possible_module_files = ["H-1", "H-2"]
possible_signal_files_H_1 = ["G-1", "G-2"]#, "A-60x60-1"]
possible_signal_files_H_2 = ["g-30x30-1", "g-30x30-2"]#, "A-30x30-1"]

def aplicar_ganho_sinal(signal_file_name):
    g = pd.read_csv("Client/" + signal_file_name + ".csv", header=None).to_numpy().flatten()  # Vetor g
    N = 64
    S = 794 if signal_file_name == "H-1" else 436

    for c in range(N):
        for l in range(S):
            y = 100 + (1 / 20) * l * sqrt(l)
            g[l + c * S] = g[l + c * S] * y  # Atualiza o valor de g aplicando o ganho

    return g

def main():
    
    #while True:
        option = input("Digite 1 para enviar a requisição de reconstruir imagens, ou 2 para recebê-las reconstruídas.")

        if option == "1":
            print("Start: Image reconstruction request to server.")
            data = {
                'function': 'reconstruct',
                'user_name':'',
                'module_file_name':'',
                'signal':'',
            }

            #time_end = time.time() + 15
           # while time.time() < time_end:
                #time.sleep(random.uniform(0.3, 1.5))
            client = st.socket(st.AF_INET, st.SOCK_STREAM)
            client.connect(ADDR)

            data['user_name'] = random.choice(possible_users)
            data['module_file_name'] = random.choice(possible_module_files)

            signal_file_name = random.choice(possible_signal_files_H_1 if data['module_file_name'] == "H-1" else possible_signal_files_H_2)
            data['signal'] = aplicar_ganho_sinal(signal_file_name)
            print(f"Signal chosen: {signal_file_name}, module chosen: {data['module_file_name']}, Username = {data['user_name']}")

            message = pickle.dumps(data)
            client.send(message)
            client.close()

        elif option == 2:
            print("Start: Receiving image from server.")
            client = st.socket(st.AF_INET, st.SOCK_STREAM)
            client.connect(ADDR)
            data = {
                'function': 'receive'
            }

            message = pickle.format(data)
            client.send(message)
            received_message = b''
            while True:
                temp_message = client.recv(4096)
                if not temp_message: break
                received_message += temp_message
            
            data = pickle.loads(received_message)
if __name__ == '__main__':
    main()