from eth_account import Account
from mnemonic import Mnemonic
from web3 import Web3
from tkinter import Tk, Label, Entry, Button, messagebox, Listbox, Scrollbar, Menu, Toplevel, StringVar, END
import threading
import webbrowser
import pyperclip
import os

# Enable unaudited HD wallet features
Account.enable_unaudited_hdwallet_features()

# === Default Settings ===
DEFAULT_RPC = 'https://rpc.sepolia.org'
DEFAULT_GAS_PRICE_GWEI = '10'

# Settings storage
settings = {
    'rpc_url': DEFAULT_RPC,
    'gas_price': DEFAULT_GAS_PRICE_GWEI,
}

# Connect Web3
def connect_web3(rpc_url):
    return Web3(Web3.HTTPProvider(rpc_url))

w3 = connect_web3(settings['rpc_url'])

# USDT contract setup
usdt_contract_address = Web3.to_checksum_address('0x2b4e26f67a36b240f3f50c7fe0acb9a287f10af1')
usdt_abi = [
    {
        "constant": False,
        "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]
usdt = w3.eth.contract(address=usdt_contract_address, abi=usdt_abi)

# === Functions ===

def generate_mnemonic():
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=128)

def generate_ethereum_address(mnemonic):
    acct = Account.from_mnemonic(mnemonic)
    private_key = acct._private_key.hex()
    address = acct.address
    return private_key, address

def send_fake_usdt(from_private_key, to_address, amount_usdt):
    acct = Account.from_key(from_private_key)
    nonce = w3.eth.get_transaction_count(acct.address)
    gas_price = w3.to_wei(settings['gas_price'], 'gwei')
    amount = int(amount_usdt * (10 ** 6))

    tx = usdt.functions.transfer(to_address, amount).build_transaction({
        'chainId': 11155111,
        'gas': 100000,
        'gasPrice': gas_price,
        'nonce': nonce,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key=from_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    return w3.to_hex(tx_hash)

def save_to_log_file(mnemonic, eth_address, tx_hash):
    if not os.path.exists('logs'):
        os.makedirs('logs')
    with open('logs/transactions.txt', 'a') as f:
        f.write(f"Mnemonic: {mnemonic}\n")
        f.write(f"Address: {eth_address}\n")
        f.write(f"TxHash: {tx_hash}\n")
        f.write("-" * 60 + "\n")

def send_button_action():
    def send_transaction():
        try:
            receiver = entry_address.get()
            amount = float(entry_amount.get())

            send_button.config(state="disabled", text="⏳ Sending...")

            mnemonic = generate_mnemonic()
            private_key, eth_address = generate_ethereum_address(mnemonic)

            tx_hash = send_fake_usdt(private_key, receiver, amount)

            # Save to logs
            save_to_log_file(mnemonic, eth_address, tx_hash)

            pyperclip.copy(tx_hash)

            send_button.config(state="normal", text="Send Fake USDT")

            short_receiver = receiver[:6] + "..." + receiver[-4:]
            short_tx = tx_hash[:8] + "..." + tx_hash[-6:]
            history_listbox.insert(END, f"Sent {amount} USDT ➔ {short_receiver} (Tx: {short_tx})")
            history_listbox.insert(END, f"Mnemonic: {mnemonic}")
            history_listbox.insert(END, "-"*60)

            explorer_link = f"https://sepolia.etherscan.io/tx/{tx_hash}"
            answer = messagebox.askyesno("✅ Transaction Sent!",
                f"Transaction Hash copied!\n\n"
                f"Open in Explorer?"
            )
            if answer:
                webbrowser.open(explorer_link)

        except Exception as e:
            send_button.config(state="normal", text="Send Fake USDT")
            messagebox.showerror("Error", str(e))

    threading.Thread(target=send_transaction).start()

# === Settings Window ===
def open_settings_window():
    settings_window = Toplevel(root)
    settings_window.title("⚙️ Settings")
    settings_window.geometry("400x300")
    settings_window.configure(bg="#1e1e1e")

    Label(settings_window, text="RPC URL:", fg="white", bg="#1e1e1e").pack(pady=5)
    rpc_entry = Entry(settings_window, width=50)
    rpc_entry.insert(0, settings['rpc_url'])
    rpc_entry.pack(pady=5)

    Label(settings_window, text="Gas Price (Gwei):", fg="white", bg="#1e1e1e").pack(pady=5)
    gas_entry = Entry(settings_window, width=20)
    gas_entry.insert(0, settings['gas_price'])
    gas_entry.pack(pady=5)

    def save_settings():
        settings['rpc_url'] = rpc_entry.get()
        settings['gas_price'] = gas_entry.get()
        global w3, usdt
        w3 = connect_web3(settings['rpc_url'])
        usdt = w3.eth.contract(address=usdt_contract_address, abi=usdt_abi)
        settings_window.destroy()
        messagebox.showinfo("Saved", "Settings Saved Successfully!")

    Button(settings_window, text="Save Settings", command=save_settings, bg="#00cc66", fg="white").pack(pady=20)

# === Theme Switch ===
def toggle_theme():
    global current_theme
    if current_theme == "dark":
        root.configure(bg="white")
        label_title.configure(bg="white", fg="black")
        label_address.configure(bg="white", fg="black")
        label_amount.configure(bg="white", fg="black")
        label_history.configure(bg="white", fg="black")
        history_listbox.configure(bg="#eeeeee", fg="black")
        current_theme = "light"
    else:
        root.configure(bg="#1e1e1e")
        label_title.configure(bg="#1e1e1e", fg="white")
        label_address.configure(bg="#1e1e1e", fg="white")
        label_amount.configure(bg="#1e1e1e", fg="white")
        label_history.configure(bg="#1e1e1e", fg="white")
        history_listbox.configure(bg="#2a2a2a", fg="white")
        current_theme = "dark"

# === GUI Setup ===
root = Tk()
root.title("🪙 Fake USDT Sender PRO By Iamkloyd")
root.geometry("520x680")
root.configure(bg="#1e1e1e")
current_theme = "dark"

# Menu Bar
menu_bar = Menu(root)
root.config(menu=menu_bar)
settings_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Options", menu=settings_menu)
settings_menu.add_command(label="⚙️ Settings", command=open_settings_window)
settings_menu.add_command(label="🌓 Toggle Theme", command=toggle_theme)

# Labels
label_title = Label(root, text="Send Fake USDT", font=("Helvetica", 18, "bold"), fg="white", bg="#1e1e1e")
label_title.pack(pady=10)

label_address = Label(root, text="Receiver Address:", fg="white", bg="#1e1e1e")
label_address.pack(pady=5)
entry_address = Entry(root, width=55)
entry_address.pack(pady=5)

label_amount = Label(root, text="Amount (USDT):", fg="white", bg="#1e1e1e")
label_amount.pack(pady=5)
entry_amount = Entry(root, width=20)
entry_amount.pack(pady=5)

# Send button
send_button = Button(root, text="Send Fake USDT", command=send_button_action, bg="#00cc66", fg="white", font=("Helvetica", 13), width=25)
send_button.pack(pady=20)

# History Section
label_history = Label(root, text="📜 Transaction History", font=("Helvetica", 12, "bold"), fg="white", bg="#1e1e1e")
label_history.pack(pady=5)

scrollbar = Scrollbar(root)
scrollbar.pack(side="right", fill="y")

history_listbox = Listbox(root, width=70, yscrollcommand=scrollbar.set, bg="#2a2a2a", fg="white", font=("Courier", 9))
history_listbox.pack(pady=5)
scrollbar.config(command=history_listbox.yview)

# Start GUI
root.mainloop()
