import socket 
import threading
import base64
import pyaudio
import cv2
from PIL import ImageTk, Image
import time
import cv2
import numpy as np
import tkinter as tk
import zlib
import struct

CHUNK = 1024
PAYLOAD = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 20000
IMG_PAYLOAD = 320 * 240 * 3
IMG_SIZE = [240, 320, 3]


class Chatting():
    def __init__(self):
        self.connInfo = Connect()
        self.connection = True
        p = pyaudio.PyAudio()
        self.receive_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
        self.send_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        self.cap = cv2.VideoCapture(0)

    def clearResources(self):
        self.connection = False
        self.send_stream.stop_stream()
        self.receive_stream.stop_stream()
        self.send_stream.close()
        self.receive_stream.close()
        self.connInfo.voice_socket.close()
        self.connInfo.text_socket.close()
        self.connInfo.user_socket.close()
        self.cap.release()

    def exitClick(self, event):
        self.clearResources()
        exit(0)

    def sendMessageClick(self, event, textField):
        print(textField.get())
        sendData = bytes(textField.get(), "utf-8") 
        self.connInfo.text_socket.send(sendData)
        textField.delete(0, "end") #clears textField

    def receivingMsg(self): 
        while self.connection:
            try :
                recvData = self.connInfo.text_socket.recv(PAYLOAD).decode('utf-8')
                self.chat.configure(state="normal")
                self.chat.insert(tk.INSERT, '%s\n' % recvData)
                self.chat.configure(state="disabled")
            except:
                print("Error was occured during receiving message")
                self.connection = False

    def sendingVoice(self):
        while self.connection:
            try:
                data = self.send_stream.read(CHUNK, exception_on_overflow=False)
                self.connInfo.voice_socket.send(data)
            except:
                print("Error was ouccured during sending voice")
                self.connection = False

    def receivingVoice(self):
        while self.connection:
            try:
                data = self.connInfo.voice_socket.recv(PAYLOAD)
                self.receive_stream.write(data, CHUNK)
            except Exception as e:
                print(e)
                self.connection = False

    def sendingVideo(self):
        while self.connection:
            try:
                # Capture frame-by-frame
                ret, frame = self.cap.read()
                send_frame = cv2.resize(frame, (IMG_SIZE[1], IMG_SIZE[0]))

                img = cv2.cvtColor(send_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)	
                img = ImageTk.PhotoImage(img)
                
                self.sendVideoPanel.configure(image=img)
                self.sendVideoPanel.image = img        
                       
                send_frame = np.array(send_frame, dtype = np.uint8).reshape(1, IMG_PAYLOAD)
                jpg_as_text = bytearray(send_frame)

                send_frame_bytes = jpg_as_text #zlib.compress(jpg_as_text, 9) 

                self.connInfo.video_socket.send(send_frame_bytes)
                time.sleep(0.1)
            except Exception as e :
                print(e)
                self.connection = False
    
    def receivingVideo(self):
        while self.connection:
            try:

                databytes = b''                

                while len(databytes) != IMG_PAYLOAD:
                    to_read = IMG_PAYLOAD - len(databytes)
                    if to_read > IMG_PAYLOAD:
                        databytes += self.connInfo.video_socket.recv(IMG_PAYLOAD)
                    else:
                        databytes += self.connInfo.video_socket.recv(to_read)


                #databytes = self.connInfo.video_socket.recv(IMG_PAYLOAD)

                #recv_frame = zlib.decompress(databytes)
                recv_frame = np.array(list(databytes))
                recv_frame = np.array(recv_frame, dtype = np.uint8).reshape(IMG_SIZE)
                cv2.imshow('Friends', recv_frame)
                
                if cv2.waitKey(100) & 0xFF == ord('q'):
                    break
            except Exception as e:
                print(e)
                self.connection = False

    def receivingUsers(self):
        while self.connection:
            try:
                data = self.connInfo.user_socket.recv(PAYLOAD).decode('utf-8')
                self.usersPanel.delete(0, "end")  # clears textField
                for i, user in enumerate(data.split(',')):
                    self.usersPanel.insert(i+1, '%s\n' % user)
            except:
                print("Error was occured during receiving user message")
                self.connection = False

    def run(self):
        self.root = tk.Tk()

        self.root.title = ("Chatting")
        self.root.minsize(600,400)
        self.root.bind("<Return>", lambda event: self.sendMessageClick(event,self.textField) ) #enter

        self.mainFrame = tk.Frame(self.root)
        self.mainFrame.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E)

        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        #ChatField
        self.chat = tk.Text(self.mainFrame)
        self.chat.configure(state = "disabled") 
        self.chat.grid(column=0, row=0, sticky=tk.N + tk.S + tk.W + tk.E)

        #TextFieldToSend
        self.textField = tk.Entry(self.mainFrame)
        self.textField.grid(column=0, row=1, sticky=tk.N + tk.S + tk.W + tk.E)

        #SendMessageButton
        self.buttonSend = tk.Button(self.mainFrame)
        self.buttonSend["text"] = "Send Message"
        self.buttonSend.grid(column=0, row=2, sticky=tk.N + tk.S + tk.W + tk.E)
        self.buttonSend.bind("<Button-1>", lambda event: self.sendMessageClick(event,self.textField))

        #usersPanel
        self.usersPanel= tk.Listbox(self.mainFrame)
        self.usersPanel.grid(column=2, row=0, sticky=tk.N + tk.S + tk.W + tk.E)


        #sendVideoPanel
        self.sendVideoPanel = tk.Label(self.root)
        self.sendVideoPanel.grid(column=3, row=0, sticky=tk.N + tk.S + tk.W + tk.E)

        #recvVideoPanel
        # self.recvVideoPanel = tk.Label(self.root)
        # self.recvVideoPanel.grid(column=3, row=0, sticky=tk.N + tk.S + tk.W + tk.E)

        #ExitButton
        self.buttonExit = tk.Button(self.mainFrame)
        self.buttonExit["text"] = "Exit"
        self.buttonExit["background"] = "gray"
        self.buttonExit.grid(column=2, row=2, sticky=tk.N + tk.S + tk.W + tk.E)
        self.buttonExit.bind("<Button-1>", self.exitClick)

        thread_name_lists = [self.receivingMsg, self.sendingVoice, self.sendingVideo, self.receivingVoice, self.receivingUsers, self.receivingVideo]
        for thread_name in thread_name_lists:
            thread = threading.Thread(target=thread_name, args=())
            thread.daemon = True
            thread.start()
        
        try:
            self.root.mainloop()
        finally:
            self.clearResources()
            print("\nDisconnected")


class Connect():
    def __init__(self):
        window = tk.Tk()
        window.title = ("Log-In")
        window.minsize(200, 200)
        
        hostText = tk.Label(window, text="Host")
        hostText.pack()

        host = tk.StringVar()
        hostField = tk.Entry(window, text=host)
        hostField.pack()

        portText = tk.Label(window, text="Port")
        portText.pack()

        port = tk.StringVar()
        portField = tk.Entry(window, text=port)
        portField.pack()

        usernameText = tk.Label(window, text="Username")
        usernameText.pack()

        username = tk.StringVar()
        usernameField = tk.Entry(window, text = username)
        usernameField.pack()

        loginButton = tk.Button(text = "Login")
        loginButton.bind("<Button-1>", lambda event: self.loginClick(event,host, port, username,window))
        loginButton.pack()

        window.mainloop()

    def loginClick(self, event, host, port, username, window):
        
        self.host = host.get()
        self.port = int(port.get())
        self.user_name = username.get()

        self.text_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.text_socket.connect((self.host, self.port))
        self.text_socket.send(bytes("text"+self.user_name, "utf-8"))

        self.voice_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.voice_socket.connect((self.host, self.port))
        self.voice_socket.send(bytes("voice"+self.user_name, "utf-8"))

        self.user_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.user_socket.connect((self.host, self.port))
        self.user_socket.send(bytes("user"+self.user_name, "utf-8"))

        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.video_socket.connect((self.host, self.port))
        self.video_socket.send(bytes("video"+self.user_name, "utf-8"))

        window.destroy()


def main():
    chat = Chatting()
    chat.run()

if __name__ == "__main__":
    # execute only if run as a script
    main()
