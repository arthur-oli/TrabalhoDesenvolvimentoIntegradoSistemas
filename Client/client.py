import socket as st
import random
import pickle
import pandas as pd
from numpy import sqrt
import matplotlib.pyplot as plt
import reportlab
import os

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import reportlab.pdfgen
from reportlab.lib.styles import getSampleStyleSheet
import reportlab.pdfgen.canvas

SERVER = 'localhost'
PORT = 5050
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
HEADERSIZE = 10

possible_users = ["Arthur", "Gabriel", "Mistério", "Professor", "Jean Grey"]
possible_module_files = ["H-1", "H-2"]
possible_signal_files_H_1 = ["G-1", "G-2", "A-60x60-1"]
possible_signal_files_H_2 = ["g-30x30-1", "g-30x30-2", "A-30x30-1"]

def aplicar_ganho_sinal(signal_file_name, module_file_name):
    g = pd.read_csv("Client/" + signal_file_name + ".csv", header=None).to_numpy().flatten()  # Vetor g
    N = 64
    S = 794 if module_file_name == "H-1" else 436

    if len(g) != N * S:
        print(signal_file_name)
        raise ValueError(f"Tamanho de g ({len(g)}) não corresponde ao esperado ({N} x {S} = {N * S})")

    for c in range(N):
        for l in range(S):
            y = 100 + (1 / 20) * l * sqrt(l)
            g[l + c * S] = g[l + c * S] * y  # Atualiza o valor de g aplicando o ganho

    return g

def pickle_format(info):
    msg = pickle.dumps(info)
    return bytes(f'{len(msg):<{HEADERSIZE}}', FORMAT) + msg

def generateReport(imageNumber, result):
    pdf_path = "ImageReport.pdf"
    temp_pdf_path = 'temp_page.pdf'
    c = reportlab.pdfgen.canvas.Canvas(temp_pdf_path, pagesize=letter)

    image_path = "Client\Images\Image" + str(imageNumber) + ".png"
    c.drawImage(image_path, inch, 2*inch, width=5*inch, height=4*inch)
    text = [
        f"User Name: {result['user_name']}",
        f"Iterations: {result['iterations']}",
        f"Start Time: {result['start_time']}",
        f"End Time: {result['end_time']}",
        f"Elapsed Time: {result['elapsed_time']}",
        f"CPU Usage: {result['cpu_usage']}",
        f"Memory Usage: {result['memory_usage']}",
        f"Size in Pixels: {result['size_in_pixels']}",
        f"Algorithm: {result['algorithm']}"
    ]

    y_position = 10*inch
    for line in text:
        c.drawString(inch, y_position, line)
        y_position -= 0.25*inch

    c.showPage()
    c.save()
    if os.path.exists(pdf_path):
        output_pdf = PdfWriter()
        pdf_reader = PdfReader(pdf_path)
        
        for page in pdf_reader.pages:
            output_pdf.add_page(page)

        with open(temp_pdf_path, 'rb') as temp_pdf_file:
            temp_pdf_reader = PdfReader(temp_pdf_file)
            output_pdf.add_page(temp_pdf_reader.pages[0])

        with open(pdf_path, 'wb') as final_pdf_file:
            output_pdf.write(final_pdf_file)
    else:
        os.rename(temp_pdf_path, pdf_path)
    
    try:
        os.remove(temp_pdf_path)
    except FileNotFoundError:
        pass
    
def main():

    while True:
        option = input("Digite 1 para enviar a requisição de reconstruir imagens, ou 2 para receber os resultados.")

        if option == "1":
            client = st.socket(st.AF_INET, st.SOCK_STREAM)
            client.connect(ADDR)
            print("Start: Image reconstruction request to server.")
            data = {
                'function': 'reconstruct',
                'user_name': '',
                'module_file_name': '',
                'signal': '',
            }

            # Preencher dados da requisição
            data['user_name'] = random.choice(possible_users)
            data['module_file_name'] = random.choice(possible_module_files)

            signal_file_name = random.choice(possible_signal_files_H_1 if data['module_file_name'] == "H-1" else possible_signal_files_H_2)
            data['signal'] = aplicar_ganho_sinal(signal_file_name, data['module_file_name'])
            print(f"Signal chosen: {signal_file_name}, module chosen: {data['module_file_name']}, Username = {data['user_name']}")

            # Serializar e enviar os dados
            message = pickle_format(data)
            client.send(message)
            #client.close()

        elif option == "2":
            client = st.socket(st.AF_INET, st.SOCK_STREAM)
            client.connect(ADDR)
            print("Start: Receiving results from server.")

            # Solicitação para receber resultados armazenados
            data = {
                'function': 'receive'
            }

            message = pickle_format(data)
            client.send(message)

            # Receber e acumular dados
            received_message = b''
            while True:
                temp_message = client.recv(1024)
                if not temp_message:
                    break
                received_message += temp_message

            # Decodificar os dados recebidos
            results = pickle.loads(received_message)

            # Exibir os resultados recebidos
            if results:
                result_number = 1
                for result in results:
                    print("Resultado da Reconstrução:")
                    print(f"Usuário: {result['user_name']}")
                    print(f"Número de iterações: {result['iterations']}")
                    print(f"Tempo de início: {result['start_time']}")
                    print(f"Tempo de fim: {result['end_time']}")
                    print(f"Tempo decorrido: {result['elapsed_time']:.2f} segundos")
                    print(f"Uso de CPU: {result['cpu_usage']:.2f}%")
                    print(f"Uso de memória: {result['memory_usage']:.2f} MB")
                    print(f"Tamanho da imagem (em pixels): {result['size_in_pixels']}")
                    print(f"Algoritmo utilizado: {result['algorithm']}")
                    print("-" * 40)

                    f = result['image']
                    plt.imshow(f, 'gray')
                    plt.title('Image' + str(result_number))
                    plt.savefig("Client\Images\Image" + str(result_number) + ".png")
                    plt.close()
                    generateReport(result_number, result)
                    result_number += 1

            else:
                print("Nenhum resultado disponível no servidor.")
            client.close()

if __name__ == '__main__':
    main()
