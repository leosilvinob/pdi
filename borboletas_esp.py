# -*- coding: utf-8 -*-


import cv2, base64, torch, numpy as np, os, requests
import tkinter as tk
from tkinter import filedialog, messagebox
from facenet_pytorch import InceptionResnetV1, MTCNN

# Configuração
IMG_RED = 240 #tamanho máximo (em pixels) para a pré-visualização enviada ao ESP32.
dev = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(image_size=160, device=dev)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(dev)

# Tkinter
root = tk.Tk()
root.title("Cadastro Facial – Offline")

# Labels + campos
tk.Label(root, text="Nome da pessoa:").pack()
nome = tk.Entry(root, width=30); nome.pack(pady=5)

tk.Label(root, text="Vínculo (amigo, cuidador etc):").pack()
vinculo = tk.Entry(root, width=30); vinculo.pack(pady=5)

tk.Label(root, text="Pasta das imagens:").pack()
pasta = tk.Entry(root, width=30); pasta.pack(pady=5)
tk.Button(root, text="Selecionar pasta", command=lambda: pasta.delete(0, tk.END) or pasta.insert(0, filedialog.askdirectory())).pack(pady=5)

tk.Label(root, text="IP do ESP32:").pack()
esp_ip = tk.Entry(root, width=30); esp_ip.pack(pady=5)
tk.Label(root, text="Exemplo: 192.168.0.100:5000").pack()

# Função de envio
def enviar():
    p, n, v, ip = pasta.get(), nome.get(), vinculo.get(), esp_ip.get()
    if not p or not n or not ip:
        return messagebox.showerror("Erro", "Informe nome, pasta e IP do ESP32!")

    imgs = [f for f in os.listdir(p) if f.lower().endswith((".jpg",".png",".jpeg"))]
    if not imgs: 
        return messagebox.showerror("Erro", "Nenhuma imagem na pasta.")

    embs = []
    for f in imgs:
        img = cv2.imread(os.path.join(p,f))
        if img is None: continue
        face = mtcnn(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if face is None: continue
        embs.append(resnet(face.unsqueeze(0)).detach().cpu().numpy()[0])
    if not embs: 
        return messagebox.showerror("Erro", "Nenhuma face detectada!")

    emb_final = np.mean(embs, axis=0).tolist()

    # Pré-visualização da primeira imagem (Cria imagem reduzida e codifica em Base64)
    img = cv2.imread(os.path.join(p, imgs[0])) #pega a primeira imagem da pasta
    h, w = img.shape[:2]; esc = IMG_RED / max(h,w)
    img = cv2.resize(img, (int(w*esc), int(h*esc)))
    _, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
    img_b64 = base64.b64encode(buf).decode()

    pacote = {
        "nome": n,
        "vinculo": v,
        "embedding": emb_final,
        "imagem": img_b64,
        "n_imagens_usadas": len(embs)
    }

    # Envia via HTTP POST para o ESP32
    try:
        url = f"http://{ip}/cadastrar"
        res = requests.post(url, json=pacote, timeout=5)
        if res.status_code == 200:
            messagebox.showinfo("Sucesso", "Cadastro enviado com sucesso!")
        else:
            messagebox.showerror("Erro", f"Falha ao enviar. Status code: {res.status_code}")
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível enviar para o ESP32.\n{e}")

tk.Button(root, text="Cadastrar e Enviar", command=enviar, bg="blue", fg="white").pack(pady=10)

tk.Button(root, text="Sair", command=root.destroy, bg="red", fg="white").pack(pady=5)

root.mainloop()
