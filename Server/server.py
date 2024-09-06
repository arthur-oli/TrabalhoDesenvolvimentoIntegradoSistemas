import os, psutil
import socket as st
import threading
import numpy as np
import pandas as pd
import pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import time

PORT = 5050
SERVER = 'localhost'
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
HEADERSIZE = 10

# Lista para armazenar todos os resultados
stored_results = []
lock = threading.Lock()  # Para garantir acesso seguro à lista em threads

max_error = 1e-4

def pickle_format(info):
    msg = pickle.dumps(info)
    return bytes(f'{len(msg):<{HEADERSIZE}}', FORMAT) + msg

def cgnr(H, g):
    f = np.zeros(H.shape[1])  # Inicializa f como um vetor de zeros
    r = g - np.dot(H, f)
    z = np.dot(H.T, r)
    p = z
    iter_count = 0

    for i in range(len(g)):
        w = np.dot(H, p)
        alpha = np.dot(z.T, z) / np.dot(w.T, w)
        f = f + alpha * p
        r_next = r - alpha * w
        z_next = np.dot(H.T, r_next)

        error = abs(np.linalg.norm(r, ord=2) - np.linalg.norm(r_next, ord=2))

        if error < max_error:
            break

        beta = np.dot(z_next.T, z_next) / np.dot(z.T, z)
        p = z_next + beta * p
        r = r_next
        z = z_next
        iter_count += 1

    return f, iter_count

def reconstruct_image(module, g, algorithm):
    H = pd.read_csv('Server/' + module + '.csv', header=None).to_numpy()
    if algorithm == "cgnr":
        res_image, iter_count = cgnr(H, g)
    
    len_image  = int(np.sqrt(len(res_image)))
    res_image = res_image.reshape((len_image, len_image), order='F')
    return res_image, iter_count

def handle_info(data, conn):
    if data['function'] == "reconstruct":
        print("Iniciando reconstrução da imagem.")
        process = psutil.Process(os.getpid())
        start_time = time.time()
        str_start_time = time.strftime("%Y-%m-%d %H:%M:%S")
        cpu_usage = process.cpu_percent(interval = 4)
        start_mem = process.memory_info().rss

        image, iter_count = reconstruct_image(data['module_file_name'], data['signal'], "cgnr")

        end_time = time.time()
        str_end_time = time.strftime("%Y-%m-%d %H:%M:%S")
        end_mem = process.memory_info().rss

        elapsed_time = end_time - start_time
        memory_usage = ((end_mem + start_mem) / 2) / (1024 * 1024)

        result = {
            'user_name': data['user_name'],
            'image': image,
            'iterations': iter_count,
            'start_time': str_start_time,
            'end_time': str_end_time,
            'elapsed_time': elapsed_time,
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'size_in_pixels': len(image),
            'algorithm': 'cgnr'
        }
        
        # Armazena o resultado na lista global de resultados
        with lock:
            print("Salvando resultados.")
            stored_results.append(result)
        
        print(f"Resultado armazenado para o usuário {data['user_name']}. Tamanho da fila de resultados: {len(stored_results)}")

    if data['function'] == "receive":
        print("Iniciando reconstrução da imagem.")
        # Envia todos os resultados armazenados de volta ao cliente
        with lock:
            serialized_results = pickle.dumps(stored_results)
        conn.sendall(serialized_results)

def handle_client(client_socket, client_address):
    print(f'Conexão de {client_address}')

    received_message = b''
    new_msg = True
    connected = True
    while connected:
        msg = client_socket.recv(1024)
        print("Pacote recebido")
        if msg != b'':
            if new_msg:
                msglen = int(msg[:HEADERSIZE])
                new_msg = False

            received_message += msg

            if len(received_message) - HEADERSIZE == msglen:
                info = pickle.loads(received_message[HEADERSIZE:])
                new_msg = True
                received_message = b''
                handle_info(info, client_socket)
                connected = False

    client_socket.close()

def start_server():
    print('Start: Starting Server')
    server = st.socket(st.AF_INET, st.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()

    print('Servidor ligado!')

    while True:
        client_socket, address_client = server.accept()
        thread_client = threading.Thread(target=handle_client, args=(client_socket, address_client))
        thread_client.start()

if __name__ == '__main__':
    start_server()
