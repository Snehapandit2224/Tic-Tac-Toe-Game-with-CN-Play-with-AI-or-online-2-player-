import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
import random
import select
import sys

class TicTacToeMenu:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Tic Tac Toe")
        self.root.geometry("300x400")
        
        # Title label
        title_label = tk.Label(self.root, text="TIC TAC TOE", font=("Arial", 24, "bold"))
        title_label.pack(pady=30)
        
        # Multiplayer button
        multiplayer_btn = tk.Button(self.root, text="Local Player", width=20, height=2, 
                                    command=self.start_multiplayer, font=("Arial", 12))
        multiplayer_btn.pack(pady=20)
        
        # AI button
        ai_btn = tk.Button(self.root, text="Play Against AI", width=20, height=2, 
                          command=self.start_ai_game, font=("Arial", 12))
        ai_btn.pack(pady=20)
        
        # Exit button
        exit_btn = tk.Button(self.root, text="Exit", width=10, height=1, 
                            command=self.root.destroy, font=("Arial", 10))
        exit_btn.pack(pady=20)
        
        self.root.mainloop()
    
    def start_multiplayer(self):
        self.root.destroy()
        root = tk.Tk()
        client = TicTacToeClient(root)
        root.mainloop()
    
    def start_ai_game(self):
        self.root.destroy()
        root = tk.Tk()
        game = TicTacToeAI(root)
        root.mainloop()


class TicTacToeClient:
    def __init__(self, root, host='192.168.56.1', port=5555):
        self.root = root
        self.root.title("Tic Tac Toe - Multiplayer")
        self.root.geometry("600x500")  # Increased window size to accommodate chat
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            self.client.connect((self.host, self.port))
            
            # Create a frame for the game board
            self.game_frame = tk.Frame(self.root)
            self.game_frame.grid(row=0, column=0, padx=10, pady=10)
            
            # Status label
            self.status_label = tk.Label(self.game_frame, text="Connected! Waiting for opponent...", font=("Arial", 10))
            self.status_label.grid(row=3, column=0, columnspan=3, pady=10)
            
            self.symbol = self.client.recv(1024).decode()
            self.turn = self.symbol == 'X'
            
            if self.turn:
                self.status_label.config(text=f"You are {self.symbol}. Your turn!")
            else:
                self.status_label.config(text=f"You are {self.symbol}. Opponent's turn!")

            self.buttons = [[None for _ in range(3)] for _ in range(3)]
            self.build_grid()
            
            # Create chat frame
            self.chat_frame = tk.Frame(self.root)
            self.chat_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
            
            # Chat display area
            self.chat_display = scrolledtext.ScrolledText(self.chat_frame, width=30, height=15, wrap=tk.WORD, state=tk.DISABLED)
            self.chat_display.grid(row=0, column=0, padx=5, pady=5)
            
            # Chat entry area
            self.chat_entry = tk.Entry(self.chat_frame, width=25)
            self.chat_entry.grid(row=1, column=0, padx=5, pady=5, sticky="w")
            self.chat_entry.bind("<Return>", self.send_chat_message)
            
            # Send button
            self.send_button = tk.Button(self.chat_frame, text="Send", command=self.send_chat_message)
            self.send_button.grid(row=1, column=0, padx=5, pady=5, sticky="e")
            
            # Add a label for the chat area
            chat_label = tk.Label(self.chat_frame, text="Chat with Opponent", font=("Arial", 10, "bold"))
            chat_label.grid(row=2, column=0, padx=5, pady=5)
            
            # Back to menu button
            back_btn = tk.Button(self.root, text="Back to Menu", command=self.back_to_menu)
            back_btn.grid(row=1, column=0, columnspan=2, pady=10)

            # Start receiving thread
            thread = threading.Thread(target=self.receive_data)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
            self.root.destroy()
            TicTacToeMenu()

    def build_grid(self):
        board_frame = tk.Frame(self.game_frame)
        board_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
        
        for row in range(3):
            for col in range(3):
                self.buttons[row][col] = tk.Button(board_frame, text='', width=10, height=3, font=("Arial", 14, "bold"),
                                                  command=lambda r=row, c=col: self.send_move(r, c))
                self.buttons[row][col].grid(row=row, column=col, padx=2, pady=2)

    def back_to_menu(self):
        try:
            self.client.close()
        except:
            pass
        self.root.destroy()
        TicTacToeMenu()

    def send_move(self, row, col):
        if self.turn and not self.buttons[row][col]['text']:
            self.buttons[row][col]['text'] = self.symbol
            self.buttons[row][col]['disabledforeground'] = 'black' if self.symbol == 'X' else 'red'
            self.buttons[row][col]['state'] = 'disabled'
            self.client.send(f'MOVE:{row},{col}'.encode())  # Add message type prefix
            self.turn = False
            self.status_label.config(text=f"You are {self.symbol}. Opponent's turn!")

    def send_chat_message(self, event=None):
        message = self.chat_entry.get().strip()
        if message:
            self.client.send(f'CHAT:{message}'.encode())  # Add message type prefix
            self.update_chat_display(f"You: {message}")
            self.chat_entry.delete(0, tk.END)

    def update_chat_display(self, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.see(tk.END)  # Auto-scroll to the bottom
        self.chat_display.config(state=tk.DISABLED)

    def receive_data(self):
        while True:
            try:
                data = self.client.recv(1024).decode()
                if not data:
                    break
                
                print(f"Client received: {data}")  # Debug print
                
                # Handle different message types
                if data.startswith('CHAT:'):
                    chat_msg = data[5:]  # Remove the 'CHAT:' prefix
                    # Make a copy of the message for the lambda
                    msg_copy = chat_msg
                    self.root.after(0, lambda m=msg_copy: self.update_chat_display(f"Opponent: {m}"))
                elif data == 'WIN':
                    self.root.after(0, lambda: messagebox.showinfo("Game Over", "You win!"))
                    self.root.after(100, self.ask_play_again)
                    break
                elif data == 'LOSE':
                    self.root.after(0, lambda: messagebox.showinfo("Game Over", "You lose!"))
                    self.root.after(100, self.ask_play_again)
                    break
                elif data == 'DRAW':
                    self.root.after(0, lambda: messagebox.showinfo("Game Over", "It's a draw!"))
                    self.root.after(100, self.ask_play_again)
                    break
                elif data.startswith('MOVE:'):
                    move = data[5:]  # Remove the 'MOVE:' prefix
                    row, col = map(int, move.split(','))
                    opponent_symbol = 'O' if self.symbol == 'X' else 'X'
                    
                    # Use root.after to update UI from the main thread
                    def update_button(r=row, c=col, sym=opponent_symbol):
                        self.buttons[r][c]['text'] = sym
                        self.buttons[r][c]['disabledforeground'] = 'black' if sym == 'X' else 'red'
                        self.buttons[r][c]['state'] = 'disabled'
                        self.turn = True
                        self.status_label.config(text=f"You are {self.symbol}. Your turn!")
                    
                    self.root.after(0, update_button)
            except Exception as e:
                print(f"Error receiving data: {e}")
                import traceback
                traceback.print_exc()
                break
        
    def ask_play_again(self):
        response = messagebox.askyesno("Play Again", "Do you want to play again?")
        if response:
            # Close current connection and start fresh
            try:
                self.client.send("RESTART".encode())  # Notify server about restart
                self.client.close()
            except:
                pass
                
            # Start a new game
            self.root.destroy()
            new_root = tk.Tk()
            TicTacToeClient(new_root, self.host, self.port)
            new_root.mainloop()
        else:
            try:
                self.client.close()
            except:
                pass
            self.root.destroy()


class TicTacToeAI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tic Tac Toe - AI Mode")
        
        # Initialize game variables
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.player_symbol = 'X'
        self.ai_symbol = 'O'
        self.current_turn = 'X'  # X always goes first
        
        # Status label
        self.status_label = tk.Label(self.root, text="Your turn (X)", font=("Arial", 10))
        self.status_label.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Create the game grid
        self.buttons = [[None for _ in range(3)] for _ in range(3)]
        self.build_grid()
    
    def build_grid(self):
        frame = tk.Frame(self.root)
        frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
        
        for row in range(3):
            for col in range(3):
                self.buttons[row][col] = tk.Button(frame, text='', width=10, height=3, font=("Arial", 14, "bold"),
                                                 command=lambda r=row, c=col: self.make_move(r, c))
                self.buttons[row][col].grid(row=row, column=col, padx=2, pady=2)
        
        # Back to menu button
        back_btn = tk.Button(self.root, text="Back to Menu", command=self.back_to_menu)
        back_btn.grid(row=4, column=0, columnspan=3, pady=10)
    
    def back_to_menu(self):
        self.root.destroy()
        TicTacToeMenu()
    
    def make_move(self, row, col):
        # Handle player move
        if self.current_turn == self.player_symbol and self.board[row][col] == '':
            self.board[row][col] = self.player_symbol
            self.buttons[row][col]['text'] = self.player_symbol
            self.buttons[row][col]['disabledforeground'] = 'black'
            self.buttons[row][col]['state'] = 'disabled'
            
            # Check for win or draw
            if self.check_winner(self.player_symbol):
                messagebox.showinfo("Game Over", "You win!")
                self.ask_play_again()
                return
            
            if self.check_draw():
                messagebox.showinfo("Game Over", "It's a draw!")
                self.ask_play_again()
                return
            
            # Switch turn to AI
            self.current_turn = self.ai_symbol
            self.status_label.config(text="AI is thinking...")
            self.root.after(500, self.ai_move)  # Delay AI move for better UX
    
    def ai_move(self):
        # Simple AI logic - first try to win, then block, then random
        # Try to find a winning move
        for row in range(3):
            for col in range(3):
                if self.board[row][col] == '':
                    self.board[row][col] = self.ai_symbol
                    if self.check_winner(self.ai_symbol):
                        self.buttons[row][col]['text'] = self.ai_symbol
                        self.buttons[row][col]['disabledforeground'] = 'red'
                        self.buttons[row][col]['state'] = 'disabled'
                        messagebox.showinfo("Game Over", "AI wins!")
                        self.ask_play_again()
                        return
                    self.board[row][col] = ''  # Undo move
        
        # Try to block player's winning move
        for row in range(3):
            for col in range(3):
                if self.board[row][col] == '':
                    self.board[row][col] = self.player_symbol
                    if self.check_winner(self.player_symbol):
                        self.board[row][col] = self.ai_symbol
                        self.buttons[row][col]['text'] = self.ai_symbol
                        self.buttons[row][col]['disabledforeground'] = 'red'
                        self.buttons[row][col]['state'] = 'disabled'
                        self.current_turn = self.player_symbol
                        self.status_label.config(text="Your turn (X)")
                        return
                    self.board[row][col] = ''  # Undo move
        
        # Take center if available
        if self.board[1][1] == '':
            self.board[1][1] = self.ai_symbol
            self.buttons[1][1]['text'] = self.ai_symbol
            self.buttons[1][1]['disabledforeground'] = 'red'
            self.buttons[1][1]['state'] = 'disabled'
            self.current_turn = self.player_symbol
            self.status_label.config(text="Your turn (X)")
            return
        
        # Random move
        empty_cells = [(r, c) for r in range(3) for c in range(3) if self.board[r][c] == '']
        if empty_cells:
            row, col = random.choice(empty_cells)
            self.board[row][col] = self.ai_symbol
            self.buttons[row][col]['text'] = self.ai_symbol
            self.buttons[row][col]['disabledforeground'] = 'red'
            self.buttons[row][col]['state'] = 'disabled'
            
            # Check for win or draw
            if self.check_winner(self.ai_symbol):
                messagebox.showinfo("Game Over", "AI wins!")
                self.ask_play_again()
                return
            
            if self.check_draw():
                messagebox.showinfo("Game Over", "It's a draw!")
                self.ask_play_again()
                return
            
            # Switch turn back to player
            self.current_turn = self.player_symbol
            self.status_label.config(text="Your turn (X)")
    
    def check_winner(self, symbol):
        # Check rows
        for row in self.board:
            if all(cell == symbol for cell in row):
                return True
        
        # Check columns
        for col in range(3):
            if all(self.board[row][col] == symbol for row in range(3)):
                return True
        
        # Check diagonals
        if all(self.board[i][i] == symbol for i in range(3)) or all(self.board[i][2-i] == symbol for i in range(3)):
            return True
        
        return False
    
    def check_draw(self):
        return all(all(cell != '' for cell in row) for row in self.board)
    
    def ask_play_again(self):
        response = messagebox.askyesno("Play Again", "Do you want to play again?")
        if response:
            self.reset_game()
        else:
            self.root.destroy()
            TicTacToeMenu()
    
    def reset_game(self):
        # Reset board
        self.board = [['' for _ in range(3)] for _ in range(3)]
        
        # Reset buttons
        for row in range(3):
            for col in range(3):
                self.buttons[row][col]['text'] = ''
                self.buttons[row][col]['state'] = 'normal'
        
        # Reset turn
        self.current_turn = self.player_symbol
        self.status_label.config(text="Your turn (X)")


class TicTacToeServer:
    def __init__(self):
        print("Server started, waiting for connections...")
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.start_server()

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("192.168.56.1", 5555))
        server.listen(2)
        print("Waiting for players...")

        client1, _ = server.accept()
        print("Player X connected")
        client1.send("X".encode())

        client2, _ = server.accept()
        print("Player O connected")
        client2.send("O".encode())

        # Create separate threads to handle each client
        threading.Thread(target=self.handle_clients, args=(client1, client2)).start()

    def handle_clients(self, client1, client2):
        clients = {
            'X': client1,
            'O': client2
        }
        current_player = 'X'  # X always goes first
        
        # Set socket timeout to prevent blocking indefinitely
        client1.settimeout(0.5)
        client2.settimeout(0.5)
        
        running = True
        while running:
            try:
                # Try to receive from current player first
                try:
                    data = clients[current_player].recv(1024).decode()
                    if not data:
                        print(f"Empty data received from {current_player}, checking connection")
                        continue
                    
                    print(f"Received from {current_player}: {data}")  # Debug print
                    
                    # Handle different message types
                    if data.startswith('CHAT:'):
                        # Forward chat message to the other player
                        other_player = 'O' if current_player == 'X' else 'X'
                        clients[other_player].send(data.encode())
                        # Don't change turn for chat messages
                    elif data.startswith('MOVE:'):
                        # Handle move
                        move_data = data[5:]  # Remove 'MOVE:' prefix
                        row, col = map(int, move_data.split(','))
                        self.board[row][col] = current_player
                        
                        # Check for game end conditions
                        if self.check_winner(current_player):
                            clients[current_player].send('WIN'.encode())
                            other_player = 'O' if current_player == 'X' else 'X'
                            clients[other_player].send('LOSE'.encode())
                            running = False
                            break
                        elif self.check_draw():
                            clients['X'].send('DRAW'.encode())
                            clients['O'].send('DRAW'.encode())
                            running = False
                            break
                        else:
                            # Forward move to other player
                            other_player = 'O' if current_player == 'X' else 'X'
                            clients[other_player].send(data.encode())
                            # Switch turn
                            current_player = other_player
                    elif data == 'RESTART':
                        print(f"Player {current_player} requested restart")
                        running = False
                        break
                
                except socket.timeout:
                    # Timeout is expected, try the other player
                    pass
                
                # Now check for chat messages from the non-current player
                other_player = 'O' if current_player == 'X' else 'X'
                try:
                    data = clients[other_player].recv(1024).decode()
                    if data and data.startswith('CHAT:'):
                        clients[current_player].send(data.encode())
                        print(f"Forwarded chat from {other_player} to {current_player}")
                    elif data == 'RESTART':
                        print(f"Player {other_player} requested restart")
                        running = False
                        break
                except socket.timeout:
                    # Timeout is expected
                    pass
                    
            except ConnectionResetError:
                print(f"Connection reset by {current_player}")
                running = False
                break
            except ConnectionAbortedError:
                print(f"Connection aborted by {current_player}")
                running = False
                break
            except Exception as e:
                print(f"Error in handle_clients: {e}")
                import traceback
                traceback.print_exc()
                running = False
                break
        
        print("Game session ended")
        
        # Clean up safely
        try:
            client1.close()
        except:
            pass
        try:
            client2.close()
        except:
            pass
        
        print("Game ended, server restarting...")
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.start_server()
    """
def handle_clients(self, client1, client2):
        clients = {
            'X': client1,
            'O': client2
        }
        current_player = 'X'  # X always goes first
        
        while True:
            try:
                # Use select to listen to both clients
                readable, _, _ = select.select([client1, client2], [], [], 0.1)
                
                for client in readable:
                    data = client.recv(1024).decode()
                    if not data:
                        continue
                    
                    # Determine which client sent the message
                    sender = 'X' if client == client1 else 'O'
                    receiver = 'O' if sender == 'X' else 'X'
                    
                    print(f"Received from {sender}: {data}")  # Debug print
                    
                    if data.startswith('CHAT:'):
                        # Forward chat message to the other player
                        clients[receiver].send(data.encode())
                        print(f"Forwarded chat to {receiver}")  # Debug print
                    elif data.startswith('MOVE:'):
                        # Only process moves from the current player
                        if sender != current_player:
                            continue
                            
                        # Handle move
                        move_data = data[5:]  # Remove 'MOVE:' prefix
                        row, col = map(int, move_data.split(','))
                        self.board[row][col] = current_player
                        
                        # Check for game end conditions
                        if self.check_winner(current_player):
                            clients[current_player].send('WIN'.encode())
                            clients[receiver].send('LOSE'.encode())
                            break
                        elif self.check_draw():
                            clients['X'].send('DRAW'.encode())
                            clients['O'].send('DRAW'.encode())
                            break
                        else:
                            # Forward move to other player
                            clients[receiver].send(data.encode())
                            # Switch turn
                            current_player = receiver
                            
                # Small delay to prevent CPU overload
                import time
                time.sleep(0.01)
                    
            except Exception as e:
                print(f"Error in handle_clients: {e}")
                import traceback
                traceback.print_exc()
                break
                
        # Clean up
        client1.close()
        client2.close()
        print("Game ended, server restarting...")
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.start_server()
"""
    def check_winner(self, symbol):
        for row in self.board:
            if all(cell == symbol for cell in row):
                return True

        for col in range(3):
            if all(self.board[row][col] == symbol for row in range(3)):
                return True

        if all(self.board[i][i] == symbol for i in range(3)) or all(self.board[i][2 - i] == symbol for i in range(3)):
            return True

        return False

    def check_draw(self):
        return all(all(cell != '' for cell in row) for row in self.board)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'server':
            TicTacToeServer()
        elif sys.argv[1] == 'client':
            TicTacToeMenu()
        else:
            print("Invalid argument. Use 'server' or 'client'.")
    else:
        print("Usage: python script.py [server/client]")
"""
    def handle_clients(self, client1, client2):
        clients = {
            'X': client1,
            'O': client2
        }
        current_player = 'X'  # X always goes first

        while True:
            try:
                # Get data from current player
                data = clients[current_player].recv(1024).decode()
                if not data:
                    break
                
                # Handle different message types
                if data.startswith('CHAT:'):
                    # Forward chat message to the other player
                    other_player = 'O' if current_player == 'X' else 'X'
                    clients[other_player].send(data.encode())
                    # Don't change turn for chat messages
                elif data.startswith('MOVE:'):
                    # Handle move
                    move_data = data[5:]  # Remove 'MOVE:' prefix
                    row, col = map(int, move_data.split(','))
                    self.board[row][col] = current_player
                    
                    # Check for game end conditions
                    if self.check_winner(current_player):
                        clients[current_player].send('WIN'.encode())
                        other_player = 'O' if current_player == 'X' else 'X'
                        clients[other_player].send('LOSE'.encode())
                        break
                    elif self.check_draw():
                        clients['X'].send('DRAW'.encode())
                        clients['O'].send('DRAW'.encode())
                        break
                    else:
                        # Forward move to other player
                        other_player = 'O' if current_player == 'X' else 'X'
                        clients[other_player].send(data.encode())
                        # Switch turn
                        current_player = other_player
            except Exception as e:
                print(f"Error: {e}")
                break

        # Clean up
        client1.close()
        client2.close()
        print("Game ended, server restarting...")
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.start_server()
"""
