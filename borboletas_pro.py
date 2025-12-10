# -*- coding: utf-8 -*-

import cv2, base64, os, requests
import tkinter as tk
from tkinter import filedialog, messagebox

# Configuração
IMG_RED = 240  # Tamanho máximo da imagem enviada
root = tk.Tk()
root.title("Cadastro Facial – Offline")

# Labels + campos
tk.Label(root, text="Nome da pessoa:").pack()
nome = tk.Entry(root, width=30); nome.pack(pady=5)

tk.Label(root, text="Vínculo (amigo, cuidador etc):").pack()
vinculo = tk.Entry(root, width=30); vinculo.pack(pady=5)

# Seleção de um único arquivo
tk.Label(root, text="Selecionar foto:").pack()
foto = tk.Entry(root, width=40); foto.pack(pady=5)
tk.Button(
    root, text="Escolher foto",
    command=lambda: foto.delete(0, tk.END) or foto.insert(0, filedialog.askopenfilename(
        filetypes=[("Imagens", "*.jpg;*.jpeg;*.png")]
    ))
).pack(pady=5)

tk.Label(root, text="IP do ESP32:").pack()
esp_ip = tk.Entry(root, width=30); esp_ip.pack(pady=5)
tk.Label(root, text="Exemplo: 192.168.0.100:5000").pack()


def enviar():
    caminho = foto.get()
    n = nome.get()
    v = vinculo.get()
    ip = esp_ip.get()

    if not caminho or not n or not ip:
        return messagebox.showerror("Erro", "Informe nome, foto e IP do ESP32!")

    img = cv2.imread(caminho)
    if img is None:
        return messagebox.showerror("Erro", "Erro ao abrir a imagem!")

    # Recorta para quadrado central antes de redimensionar para evitar distorções
    h, w = img.shape[:2]
    side = min(h, w)
    y0 = (h - side) // 2
    x0 = (w - side) // 2
    img_cropped = img[y0:y0 + side, x0:x0 + side]

    # Resize to 240x240 exactly for ESP32 face detection
    img_red = cv2.resize(img_cropped, (IMG_RED, IMG_RED))

    # Codifica em Base64
    _, buf = cv2.imencode(".jpg", img_red, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
    img_b64 = base64.b64encode(buf).decode()

    pacote = {
        "nome": n,
        "vinculo": v,
        "imagem": img_b64
    }

    # Enviar ao ESP32
    try:
        url = f"http://{ip}/cadastrar"
        res = requests.post(url, json=pacote, timeout=5)

        if res.status_code == 200:
            messagebox.showinfo("Sucesso", "Cadastro enviado com sucesso!")
        else:
            detalhe = (res.text or "").strip()
            if detalhe:
                message = f"Falha ao enviar (HTTP {res.status_code}).\n{detalhe}"
            else:
                message = f"Falha ao enviar. Status code: {res.status_code}"
            messagebox.showerror("Erro", message)

    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível enviar para o ESP32.\n{e}")


tk.Button(root, text="Cadastrar e Enviar", command=enviar, bg="blue", fg="white").pack(pady=10)
tk.Button(root, text="Sair", command=root.destroy, bg="red", fg="white").pack(pady=5)

root.mainloop()
